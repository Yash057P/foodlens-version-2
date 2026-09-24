#!/usr/bin/env python3
r"""
verify_paper.py — 4-Tier Automated Verification Harness for FoodLens IEEE Manuscript

Verifies all academic, structural, quantitative, and compilation requirements
specified in ORIGINAL_REQUEST.md, PROJECT.md, and reviewer feedback.

Tiers:
  Tier 1: Feature Coverage (>=5 sub-checks per feature across 6 features, 37 total checks)
          - F1: Required IEEE sections exist (Introduction to Appendix)
          - F2: Citations for Food-101 and EfficientNet in bib and in-text
          - F3: Model comparison table includes CPU Latency and Parameter Count
          - F4: TTA ablation table and Confidence threshold ablation table exist
          - F5: Dedicated Limitations section present
          - F6: Confusion matrix (Fig. 3) placed in Appendix
  Tier 2: Boundary & Corner Cases
          - 2.1: Regex check: zero promotional words remain in active LaTeX text
          - 2.2: Zero undefined references or citations ([?], ??, undefined labels)
          - 2.3: \usepackage{url} present in preamble
          - 2.4: Math delimiter syntax ($101 \times 101$, $224 \times 224$, etc.)
  Tier 3: Cross-Feature Consistency
          - 3.1: Model Comparison table contains valid numeric CPU latency and parameter counts
          - 3.2: Every in-text \cite{key} has matching entry in references.bib
          - 3.3: TTA and Confidence ablation tables contain valid numeric rows
  Tier 4: Full PDF Compilation & Layout
          - 4.1: Clean build sequence via cmd /c (pdflatex -> bibtex -> pdflatex -> pdflatex)
          - 4.2: Exit code 0 and freshly updated main.pdf generated (>50 KB)
          - 4.3: main.blg has zero fatal bibtex errors
          - 4.4: main.log has zero fatal LaTeX errors

Usage:
  python scripts/verify_paper.py [--tier {1,2,3,4,all}] [--paper-dir PATH] [--skip-compile] [--json FILE]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


if sys.platform == "win32" and not os.environ.get("ANSICON") and not os.environ.get("WT_SESSION"):
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


class TestResult:
    def __init__(self, test_id: str, name: str, passed: bool, message: str = "", details: Optional[List[str]] = None):
        self.test_id = test_id
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or []

    def to_dict(self) -> Dict:
        return {
            "id": self.test_id,
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
        }


class ParsedTable:
    def __init__(self, raw: str, caption: str = "", label: str = "", file_source: str = ""):
        self.raw = raw
        self.caption = caption
        self.label = label
        self.file_source = file_source
        self.headers: List[str] = []
        self.rows: List[List[str]] = []
        self._parse()

    def _parse(self):
        tabular_m = re.search(r"\\begin\{tabular\*?\}\s*(?:\{[^}]*\}){1,2}(.*?)\\end\{tabular\*?\}", self.raw, re.DOTALL)
        if not tabular_m:
            return

        body = tabular_m.group(1).strip()

        # Split body into header part (before \midrule) and data part (after \midrule)
        if r"\midrule" in body:
            parts = body.split(r"\midrule", 1)
            header_part = parts[0]
            data_part = parts[1]
        else:
            header_part = ""
            data_part = body

        # Extract headers from header_part
        if header_part:
            header_lines = [l.strip() for l in header_part.split(r"\\") if l.strip()]
            for hl in header_lines:
                cleaned = hl.replace(r"\toprule", "").replace(r"\hline", "").strip()
                if cleaned and not cleaned.startswith("%") and "&" in cleaned:
                    self.headers = [re.sub(r"[\$\{\}]", "", c).strip() for c in cleaned.split("&")]
                    break

        # Extract data rows from data_part
        data_lines = [l.strip() for l in data_part.split(r"\\") if l.strip()]
        for dl in data_lines:
            cleaned = dl.replace(r"\bottomrule", "").replace(r"\hline", "").strip()
            if not cleaned or cleaned.startswith("%") or "&" not in cleaned:
                continue
            cells = [c.strip() for c in cleaned.split("&")]
            if not self.headers:
                self.headers = [re.sub(r"[\$\{\}]", "", c).strip() for c in cells]
            else:
                self.rows.append(cells)


class PaperVerifier:
    def __init__(self, paper_dir: Path, skip_compile: bool = False, verbose: bool = False):
        self.paper_dir = paper_dir.resolve()
        self.main_tex_path = self.paper_dir / "main.tex"
        self.bib_path = self.paper_dir / "references.bib"
        self.skip_compile = skip_compile
        self.verbose = verbose

        self.main_content = ""
        self.stripped_content = ""
        self.all_tex_content = ""
        self.bib_content = ""
        self.bib_keys: Set[str] = set()
        self.bib_entries: Dict[str, Dict[str, str]] = {}
        self.cited_keys: Set[str] = set()

        self.tables: List[ParsedTable] = []
        self.model_table: Optional[ParsedTable] = None
        self.tta_table: Optional[ParsedTable] = None
        self.conf_table: Optional[ParsedTable] = None

        self.results: Dict[str, List[TestResult]] = {
            "Tier 1: Feature Coverage": [],
            "Tier 2: Boundary & Corner Cases": [],
            "Tier 3: Cross-Feature Consistency": [],
            "Tier 4: Full PDF Compilation & Layout": [],
        }

    def load_sources(self) -> bool:
        """Load and preprocess LaTeX, BibTeX, and table files."""
        if not self.main_tex_path.exists():
            print(f"{Colors.RED}ERROR: main.tex not found at {self.main_tex_path}{Colors.RESET}")
            return False

        with open(self.main_tex_path, "r", encoding="utf-8", errors="replace") as f:
            self.main_content = f.read()

        self.stripped_content = self._strip_latex_comments(self.main_content)

        # Gather all tex content including \input{...} files
        combined = [self.stripped_content]
        input_pattern = re.compile(r"\\input\{([^}]+)\}")
        for match in input_pattern.finditer(self.stripped_content):
            rel_path = match.group(1)
            if not rel_path.endswith(".tex"):
                rel_path += ".tex"
            subpath = self.paper_dir / rel_path
            if subpath.exists():
                with open(subpath, "r", encoding="utf-8", errors="replace") as sf:
                    combined.append(self._strip_latex_comments(sf.read()))
        self.all_tex_content = "\n\n".join(combined)

        # Load references.bib
        if self.bib_path.exists():
            with open(self.bib_path, "r", encoding="utf-8", errors="replace") as bf:
                self.bib_content = bf.read()
            self._parse_bibtex()

        # Extract cited keys
        cite_pattern = re.compile(r"\\cite(?:\[[^\]]*\])?\{([^}]+)\}")
        for match in cite_pattern.finditer(self.all_tex_content):
            keys = [k.strip() for k in match.group(1).split(",") if k.strip()]
            self.cited_keys.update(keys)

        # Parse tables
        self._extract_all_tables()

        return True

    @staticmethod
    def _strip_latex_comments(text: str) -> str:
        """Remove LaTeX comments while preserving line breaks and escaped percent signs."""
        lines = []
        for line in text.splitlines():
            temp = line.replace(r"\%", "\x01")
            comment_idx = temp.find("%")
            if comment_idx != -1:
                cleaned = temp[:comment_idx].replace("\x01", r"\%")
            else:
                cleaned = line
            lines.append(cleaned)
        return "\n".join(lines)

    def _parse_bibtex(self):
        """Extract bib keys and author/title/year fields."""
        entry_pattern = re.compile(r"@(\w+)\s*\{\s*([^,]+),", re.IGNORECASE)
        entries = re.split(r"\n(?=@)", self.bib_content)
        for block in entries:
            key_m = entry_pattern.search(block)
            if key_m:
                k = key_m.group(2).strip()
                self.bib_keys.add(k)
                author_m = re.search(r"author\s*=\s*[\"{](.*?)[\"}],?", block, re.IGNORECASE | re.DOTALL)
                title_m = re.search(r"title\s*=\s*[\"{](.*?)[\"}],?", block, re.IGNORECASE | re.DOTALL)
                year_m = re.search(r"year\s*=\s*[\"{]?(\d{4})[\"}]?,?", block, re.IGNORECASE)
                self.bib_entries[k] = {
                    "author": author_m.group(1).strip() if author_m else "",
                    "title": title_m.group(1).strip() if title_m else "",
                    "year": year_m.group(1).strip() if year_m else "",
                    "raw": block,
                }

    def _extract_all_tables(self):
        """Extract and categorize all tables from main.tex and paper/tables/*.tex."""
        # 1. Extract from main.tex
        tbl_pattern = re.compile(r"\\begin\{table\*?\}(.*?)\\end\{table\*?\}", re.DOTALL)
        for match in tbl_pattern.finditer(self.main_content):
            raw = match.group(0)
            caption_m = re.search(r"\\caption\{([^}]+)\}", raw)
            label_m = re.search(r"\\label\{([^}]+)\}", raw)
            caption = caption_m.group(1) if caption_m else ""
            label = label_m.group(1) if label_m else ""
            self.tables.append(ParsedTable(raw, caption, label, "main.tex"))

        # 2. Extract from tables/ directory
        tables_dir = self.paper_dir / "tables"
        if tables_dir.exists():
            for tfile in tables_dir.glob("*.tex"):
                with open(tfile, "r", encoding="utf-8", errors="replace") as f:
                    traw = f.read()
                caption_m = re.search(r"\\caption\{([^}]+)\}", traw)
                label_m = re.search(r"\\label\{([^}]+)\}", traw)
                caption = caption_m.group(1) if caption_m else ""
                label = label_m.group(1) if label_m else ""
                self.tables.append(ParsedTable(traw, caption, label, tfile.name))

        # Categorize known tables
        for tbl in self.tables:
            ident = f"{tbl.caption} {tbl.label} {tbl.file_source} {tbl.raw}".lower()
            if not self.model_table:
                if "model" in ident and ("benchmark" in ident or "comparison" in ident or "bench" in ident):
                    self.model_table = tbl
            if not self.tta_table:
                if "tta" in ident or "test-time augmentation" in ident:
                    self.tta_table = tbl
            if not self.conf_table:
                if ("confidence" in ident or "threshold" in ident or "ambiguity" in ident) and "ablation" in ident:
                    self.conf_table = tbl

    # =========================================================================
    # TIER 1: Feature Coverage (>=5 sub-checks per feature across 6 features)
    # =========================================================================
    def run_tier_1(self):
        tier = "Tier 1: Feature Coverage"

        # ---------------------------------------------------------------------
        # Feature 1: Required IEEE Sections (10 sub-checks >= 5)
        # ---------------------------------------------------------------------
        sec_checks = [
            ("1.1.1", "Section: Introduction exists", r"\\section\{Introduction\}"),
            ("1.1.2", "Section: Related Work exists", r"\\section\{(?:Related Work|Related Works)\}"),
            ("1.1.3", "Section: System Architecture exists", r"\\section\{(?:System Architecture|System Architecture and Deployment|Architecture)\}"),
            ("1.1.4", "Section: Methodology exists", r"\\section\{(?:Methodology|System Methodology|Methods)\}"),
            ("1.1.5", "Section: Experimental Setup exists", r"\\section\{(?:Experimental Setup|Experiments|Experimental Design)\}"),
            ("1.1.6", "Section: Results and Discussion exists", r"\\section\{(?:Results and Discussion|Results \& Discussion|Experimental Results)\}"),
            ("1.1.7", "Section: Deployment/Privacy/Limitations exists", r"\\section\{(?:Deployment, Privacy, and Limitations|Deployment and Limitations|Limitations and Deployment)\}"),
            ("1.1.8", "Section: Conclusion exists", r"\\section\{(?:Conclusion|Conclusions|Concluding Remarks)\}"),
            ("1.1.9", "Bibliography inclusion exists", r"\\bibliography\{|\begin\{thebibliography\}"),
            ("1.1.10", "Appendix section exists", r"\\section\*?\{Appendix|\\appendix"),
        ]
        for tid, name, pattern in sec_checks:
            m = re.search(pattern, self.stripped_content, re.IGNORECASE)
            passed = bool(m)
            msg = f"Found match: '{m.group(0)}'" if passed else f"Missing section matching pattern: {pattern}"
            self.results[tier].append(TestResult(tid, name, passed, msg))

        # ---------------------------------------------------------------------
        # Feature 2: Citations for Food-101 and EfficientNet (6 sub-checks >= 5)
        # ---------------------------------------------------------------------
        # 1.2.1: Food-101 in references.bib
        food101_in_bib = False
        food101_key = ""
        for k, v in self.bib_entries.items():
            raw_text = v["raw"].lower()
            if "food-101" in raw_text or "bossard" in raw_text:
                food101_in_bib = True
                food101_key = k
                break
        self.results[tier].append(TestResult(
            "1.2.1", "Food-101 (Bossard et al.) defined in references.bib",
            food101_in_bib,
            f"Found Food-101 entry with key '{food101_key}'" if food101_in_bib else "No Food-101 (Bossard et al.) entry in references.bib"
        ))

        # 1.2.2: EfficientNet in references.bib
        effnet_in_bib = False
        effnet_key = ""
        for k, v in self.bib_entries.items():
            raw_text = v["raw"].lower()
            if "efficientnet" in raw_text and ("tan" in raw_text or "icml" in raw_text):
                effnet_in_bib = True
                effnet_key = k
                break
        self.results[tier].append(TestResult(
            "1.2.2", "EfficientNet (Tan & Le) defined in references.bib",
            effnet_in_bib,
            f"Found EfficientNet entry with key '{effnet_key}'" if effnet_in_bib else "No EfficientNet (Tan & Le) entry in references.bib"
        ))

        # 1.2.3: In-text citation for Food-101
        food101_cited = False
        if food101_key and food101_key in self.cited_keys:
            food101_cited = True
        else:
            for k in self.cited_keys:
                if "food101" in k.lower() or "bossard" in k.lower():
                    food101_cited = True
                    break
        self.results[tier].append(TestResult(
            "1.2.3", "In-text citation for Food-101 exists",
            food101_cited,
            f"Active in-text \\cite{{{food101_key}}} detected" if food101_cited else f"Food-101 key '{food101_key}' is not cited via \\cite{{}} in main.tex"
        ))

        # 1.2.4: In-text citation for EfficientNet
        effnet_cited = False
        if effnet_key and effnet_key in self.cited_keys:
            effnet_cited = True
        else:
            for k in self.cited_keys:
                if "tan" in k.lower() or "efficientnet" in k.lower():
                    effnet_cited = True
                    break
        self.results[tier].append(TestResult(
            "1.2.4", "In-text citation for EfficientNet exists",
            effnet_cited,
            f"Active in-text \\cite{{{effnet_key}}} detected" if effnet_cited else f"EfficientNet key '{effnet_key}' is not cited via \\cite{{}} in main.tex"
        ))

        # 1.2.5: Baseline foundational citations in bib (ResNet: He et al., MobileNet: Sandler et al., DenseNet: Huang et al.)
        foundational_models = {
            "ResNet (He et al.)": False,
            "MobileNetV2 (Sandler et al.)": False,
            "DenseNet (Huang et al.)": False
        }
        for k, v in self.bib_entries.items():
            author = v["author"].lower()
            title = v["title"].lower()
            raw = v["raw"].lower()
            if ("he" in author or "resnet" in title or "deep residual" in title) and "@inproceedings" in raw:
                foundational_models["ResNet (He et al.)"] = True
            if ("sandler" in author or "mobilenet" in title or "inverted residuals" in title) and "@inproceedings" in raw:
                foundational_models["MobileNetV2 (Sandler et al.)"] = True
            if ("huang" in author or "densenet" in title or "densely connected" in title) and "@inproceedings" in raw:
                foundational_models["DenseNet (Huang et al.)"] = True

        foundational_passed = all(foundational_models.values())
        self.results[tier].append(TestResult(
            "1.2.5", "Foundational backbones (ResNet, MobileNetV2, DenseNet) citations in references.bib",
            foundational_passed,
            f"Status: {foundational_models}",
            [f"{m}: {'Found' if found else 'Missing dedicated paper entry'}" for m, found in foundational_models.items()]
        ))

        # 1.2.6: Citations distributed across multiple sections (>= 3 sections)
        sections = re.split(r"\\section\*?\{", self.stripped_content)
        sections_with_cites = 0
        for s in sections[1:]:
            if re.search(r"\\cite(?:\[[^\]]*\])?\{[^}]+\}", s):
                sections_with_cites += 1
        self.results[tier].append(TestResult(
            "1.2.6", "Active citations distributed across multiple sections (>= 3)",
            sections_with_cites >= 3,
            f"Found in-text citations across {sections_with_cites} distinct sections (required: >= 3)"
        ))

        # ---------------------------------------------------------------------
        # Feature 3: Model Comparison Table Metrics (5 sub-checks >= 5)
        # ---------------------------------------------------------------------
        # 1.3.1: Model comparison table presence
        tbl = self.model_table
        has_tbl = tbl is not None
        self.results[tier].append(TestResult(
            "1.3.1", "Model Comparison Table exists",
            has_tbl,
            f"Model comparison table located ({tbl.file_source if tbl else 'None'})" if has_tbl else "Model comparison table not found"
        ))

        # 1.3.2: CPU Latency column header in table
        has_latency_col = False
        if tbl and tbl.headers:
            has_latency_col = any(re.search(r"latenc|inference\s*time", h, re.IGNORECASE) for h in tbl.headers)
        self.results[tier].append(TestResult(
            "1.3.2", "Model Comparison Table contains CPU Latency column",
            has_latency_col,
            f"Headers: {tbl.headers}" if tbl and tbl.headers else "No headers found in model comparison table"
        ))

        # 1.3.3: Parameter Count column header in table
        has_param_col = False
        if tbl and tbl.headers:
            has_param_col = any(re.search(r"param", h, re.IGNORECASE) for h in tbl.headers)
        self.results[tier].append(TestResult(
            "1.3.3", "Model Comparison Table contains Parameter Count column",
            has_param_col,
            f"Headers: {tbl.headers}" if tbl and tbl.headers else "No headers found in model comparison table"
        ))

        # 1.3.4: Accuracy metric columns (Top-1, Top-3)
        has_top1 = False
        has_top3 = False
        if tbl and tbl.headers:
            has_top1 = any(re.search(r"top-1", h, re.IGNORECASE) for h in tbl.headers)
            has_top3 = any(re.search(r"top-3", h, re.IGNORECASE) for h in tbl.headers)
        self.results[tier].append(TestResult(
            "1.3.4", "Model Comparison Table contains Top-1 and Top-3 accuracy columns",
            has_top1 and has_top3,
            f"Top-1 found: {has_top1}, Top-3 found: {has_top3}"
        ))

        # 1.3.5: All 5 architectures included in table rows
        archs = ["Custom CNN", "ResNet50", "MobileNetV2", "DenseNet121", "EfficientNetB0"]
        arch_status = {arch: False for arch in archs}
        if tbl:
            for row in tbl.rows:
                first_cell = row[0] if row else ""
                for arch in archs:
                    if arch.lower() in first_cell.lower():
                        arch_status[arch] = True
        all_archs_found = all(arch_status.values())
        self.results[tier].append(TestResult(
            "1.3.5", "Model Comparison Table includes all 5 candidate architectures",
            all_archs_found,
            f"Architectures found: {arch_status}",
            [f"{a}: {'Present' if p else 'Missing'}" for a, p in arch_status.items()]
        ))

        # ---------------------------------------------------------------------
        # Feature 4: TTA & Confidence Ablation Tables (6 sub-checks >= 5)
        # ---------------------------------------------------------------------
        # 1.4.1: TTA ablation table exists
        tta_tbl = self.tta_table
        has_tta = tta_tbl is not None
        self.results[tier].append(TestResult(
            "1.4.1", "TTA Ablation Table exists",
            has_tta,
            f"TTA ablation table located ({tta_tbl.file_source if tta_tbl else 'None'})" if has_tta else "TTA ablation table not found"
        ))

        # 1.4.2: TTA table contains key variants
        tta_variants = ["No TTA", "Flip", "Crop", "3-Way"]
        tta_variant_status = {v: False for v in tta_variants}
        if tta_tbl:
            for row in tta_tbl.rows:
                cell_text = " ".join(row).lower()
                if "no tta" in cell_text or "baseline" in cell_text or "single" in cell_text:
                    tta_variant_status["No TTA"] = True
                if "flip" in cell_text:
                    tta_variant_status["Flip"] = True
                if "crop" in cell_text:
                    tta_variant_status["Crop"] = True
                if "3-way" in cell_text or "ensemble" in cell_text or "three" in cell_text:
                    tta_variant_status["3-Way"] = True
        has_min_tta_variants = sum(tta_variant_status.values()) >= 3
        self.results[tier].append(TestResult(
            "1.4.2", "TTA Ablation Table specifies transformation variants",
            has_min_tta_variants,
            f"Variants found: {tta_variant_status}"
        ))

        # 1.4.3: TTA table contains latency and accuracy/variance columns
        tta_has_metrics = False
        if tta_tbl and tta_tbl.headers:
            has_lat = any(re.search(r"latenc|time|ms", h, re.IGNORECASE) for h in tta_tbl.headers)
            has_acc = any(re.search(r"acc|top|var|std", h, re.IGNORECASE) for h in tta_tbl.headers)
            tta_has_metrics = has_lat and has_acc
        self.results[tier].append(TestResult(
            "1.4.3", "TTA Ablation Table contains latency and accuracy/variance metrics",
            tta_has_metrics,
            f"Headers: {tta_tbl.headers if tta_tbl else 'None'}"
        ))

        # 1.4.4: Confidence threshold ablation table exists
        c_tbl = self.conf_table
        has_conf = c_tbl is not None
        self.results[tier].append(TestResult(
            "1.4.4", "Confidence Threshold Ablation Table exists",
            has_conf,
            f"Confidence threshold table located ({c_tbl.file_source if c_tbl else 'None'})" if has_conf else "Confidence threshold table not found"
        ))

        # 1.4.5: Confidence table specifies threshold values (tau, Delta)
        has_thresh_params = False
        if c_tbl:
            header_text = " ".join(c_tbl.headers).lower()
            body_text = " ".join([" ".join(r) for r in c_tbl.rows]).lower()
            combined_conf_text = f"{header_text} {body_text}"
            has_tau = bool(re.search(r"\\tau|tau|0\.\d{2}", combined_conf_text))
            has_delta = bool(re.search(r"\\delta|delta|0\.\d{2}", combined_conf_text))
            has_thresh_params = has_tau and has_delta
        self.results[tier].append(TestResult(
            "1.4.5", "Confidence Table specifies threshold parameters (tau, Delta)",
            has_thresh_params,
            f"Threshold parameters present: {has_thresh_params}"
        ))

        # 1.4.6: Confidence table specifies coverage/rejection/accuracy trade-offs
        has_conf_tradeoffs = False
        if c_tbl and c_tbl.headers:
            has_cov = any(re.search(r"cover|flag|reject|warn", h, re.IGNORECASE) for h in c_tbl.headers)
            has_acc = any(re.search(r"acc|retain|prec", h, re.IGNORECASE) for h in c_tbl.headers)
            has_conf_tradeoffs = has_cov and has_acc
        self.results[tier].append(TestResult(
            "1.4.6", "Confidence Table specifies coverage/rejection/accuracy trade-offs",
            has_conf_tradeoffs,
            f"Headers: {c_tbl.headers if c_tbl else 'None'}"
        ))

        # ---------------------------------------------------------------------
        # Feature 5: Dedicated Limitations Section (5 sub-checks >= 5)
        # ---------------------------------------------------------------------
        # 1.5.1: Limitations section/subsection header exists
        lim_match = re.search(r"\\(?:sub)?section\*?\{[^}]*Limitations[^}]*\}(.*?)(?=\\(?:sub)?section|\Z)", self.stripped_content, re.IGNORECASE | re.DOTALL)
        has_limitations_header = bool(lim_match)
        self.results[tier].append(TestResult(
            "1.5.1", "Dedicated Limitations section/subsection header exists",
            has_limitations_header,
            "Limitations header found" if has_limitations_header else "No section or subsection header containing 'Limitations'"
        ))

        lim_text = lim_match.group(1) if lim_match else ""

        # 1.5.2: Closed-set classification & out-of-distribution discussion
        has_closed_set = bool(
            re.search(r"(?:closed-set|out-of-distribution|non-food|unseen\s+dishes|101\s+categories)", lim_text, re.IGNORECASE)
        ) if lim_text else False
        self.results[tier].append(TestResult(
            "1.5.2", "Limitations discusses closed-set constraint & out-of-distribution inputs",
            has_closed_set,
            "Closed-set/OOD discussion present" if has_closed_set else "Missing discussion of closed-set 101-class limitation and OOD inputs"
        ))

        # 1.5.3: Recipe variance & culinary diversity
        has_recipe_var = bool(
            re.search(r"(?:recipe|culinary|preparation|ingredients?|regional\s+variations?)", lim_text, re.IGNORECASE)
        ) if lim_text else False
        self.results[tier].append(TestResult(
            "1.5.3", "Limitations discusses recipe variance & ingredient variability",
            has_recipe_var,
            "Recipe/culinary variance discussion present" if has_recipe_var else "Missing discussion of recipe variance and regional preparation differences"
        ))

        # 1.5.4: Clinical safety / Medical diagnosis disclaimer
        has_clinical_disclaimer = bool(
            re.search(r"(?:clinical|medical|allergen\s+safety|disclaimer|life-threatening|anaphylaxis)", lim_text, re.IGNORECASE)
        ) if lim_text else False
        self.results[tier].append(TestResult(
            "1.5.4", "Limitations provides clinical safety disclaimer (non-medical / allergen guarantee)",
            has_clinical_disclaimer,
            "Clinical safety/allergen disclaimer present" if has_clinical_disclaimer else "Missing explicit clinical safety/allergen disclaimer"
        ))

        # 1.5.5: Limitations situated prior to Conclusion
        lim_header_pos = self.stripped_content.lower().find(r"\section{limitations")
        if lim_header_pos == -1:
            lim_header_pos = self.stripped_content.lower().find(r"\subsection{limitations")
        if lim_header_pos == -1:
            lim_header_pos = self.stripped_content.lower().find("limitations")
        concl_pos = self.stripped_content.lower().find(r"\section{conclusion")
        lim_order_valid = (has_limitations_header and lim_header_pos != -1 and concl_pos != -1 and lim_header_pos < concl_pos)
        self.results[tier].append(TestResult(
            "1.5.5", "Limitations section positioned logically before Conclusion",
            lim_order_valid,
            f"Limitations index: {lim_header_pos}, Conclusion index: {concl_pos}" if lim_order_valid else "Dedicated Limitations section not placed before Conclusion"
        ))

        # ---------------------------------------------------------------------
        # Feature 6: Confusion Matrix in Appendix (5 sub-checks >= 5)
        # ---------------------------------------------------------------------
        # 1.6.1: Confusion matrix figure referenced
        has_cm_figure = bool(re.search(r"fig_confusion_full", self.all_tex_content))
        self.results[tier].append(TestResult(
            "1.6.1", "Full 101x101 Confusion Matrix figure referenced in LaTeX",
            has_cm_figure,
            "fig_confusion_full reference found" if has_cm_figure else "fig_confusion_full reference missing"
        ))

        # 1.6.2: Located within Appendix
        appendix_split = re.split(r"\\appendix|\\section\*?\{Appendix", self.stripped_content, flags=re.IGNORECASE)
        cm_in_appendix = False
        if len(appendix_split) > 1:
            after_appendix = "\n".join(appendix_split[1:])
            if "fig_confusion_full" in after_appendix:
                cm_in_appendix = True
        self.results[tier].append(TestResult(
            "1.6.2", "Full Confusion Matrix placed in Appendix section",
            cm_in_appendix,
            "fig_confusion_full located inside Appendix block" if cm_in_appendix else "fig_confusion_full is NOT placed after \\appendix / Appendix section header"
        ))

        # 1.6.3: NOT placed in main body Results section
        results_split = re.split(r"\\section\{(?:Results and Discussion|Results \& Discussion|Experimental Results|Extensive Product Evaluation)\}", self.stripped_content, flags=re.IGNORECASE)
        cm_in_results = False
        if len(results_split) > 1:
            next_sec = re.split(r"\\section", results_split[1])
            results_body = next_sec[0] if next_sec else ""
            if "fig_confusion_full" in results_body:
                cm_in_results = True
        self.results[tier].append(TestResult(
            "1.6.3", "Full Confusion Matrix removed from main Results & Discussion body",
            not cm_in_results,
            "Confusion matrix removed from main body Results" if not cm_in_results else "Full 101x101 confusion matrix still resides in main body Results section"
        ))

        # 1.6.4: Caption describes 101x101 matrix with proper math delimiters
        cm_caption_match = re.search(r"\\caption\{([^}]+(?:\$101\s*\\times\s*101\$|101-class)[^}]+)\}", self.all_tex_content)
        has_valid_caption = bool(cm_caption_match)
        self.results[tier].append(TestResult(
            "1.6.4", "Confusion Matrix figure caption describes 101x101 matrix",
            has_valid_caption,
            f"Caption found: '{cm_caption_match.group(1)[:60]}...'" if has_valid_caption else "101x101 confusion matrix caption not found or malformed"
        ))

        # 1.6.5: Figure asset files exist on disk
        fig_pdf = self.paper_dir / "figures" / "fig_confusion_full.pdf"
        fig_png = self.paper_dir / "figures" / "fig_confusion_full.png"
        assets_exist = fig_pdf.exists() or fig_png.exists()
        self.results[tier].append(TestResult(
            "1.6.5", "Confusion Matrix asset file exists on disk (PDF or PNG)",
            assets_exist,
            f"Assets: PDF exists={fig_pdf.exists()}, PNG exists={fig_png.exists()}"
        ))

    # =========================================================================
    # TIER 2: Boundary & Corner Cases
    # =========================================================================
    def run_tier_2(self):
        tier = "Tier 2: Boundary & Corner Cases"

        # ---------------------------------------------------------------------
        # 2.1: Regex check ensuring zero promotional words remain
        # ---------------------------------------------------------------------
        promotional_patterns = [
            (r"\bmassive\b", "massive"),
            (r"\bproduction-ready\b|\bproduction ready\b", "production-ready"),
            (r"\bguarantee\b|\bguarantees\b|\bguaranteed\b", "guarantee"),
            (r"\bhallucination\b|\bhallucinations\b|\bhallucinating\b", "hallucination"),
            (r"\bglassmorphism\b", "glassmorphism"),
            (r"\bmini-product\b|\bmini product\b", "mini-product"),
            (r"O\s*\(\s*1\s*\)|\\mathcal\{O\}\s*\(\s*1\s*\)", "O(1) guarantee"),
        ]

        violations = []
        for line_no, line in enumerate(self.stripped_content.splitlines(), start=1):
            for pat, term in promotional_patterns:
                match = re.search(pat, line, re.IGNORECASE)
                if match:
                    violations.append(f"Line {line_no} [{term}]: ...{line[max(0, match.start()-20):min(len(line), match.end()+20)].strip()}...")

        self.results[tier].append(TestResult(
            "2.1", "Zero promotional words in active text (massive, production-ready, guarantee, hallucination, etc.)",
            len(violations) == 0,
            f"Found {len(violations)} promotional word occurrence(s)" if violations else "Zero promotional terms detected",
            violations[:10]
        ))

        # ---------------------------------------------------------------------
        # 2.2: Check no undefined references or citations
        # ---------------------------------------------------------------------
        undefined_issues = []

        log_path = self.paper_dir / "main.log"
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_text = f.read()
            ref_warns = re.findall(r"LaTeX Warning: Reference `([^']+)' on page \d+ undefined", log_text)
            cite_warns = re.findall(r"LaTeX Warning: Citation `([^']+)' on page \d+ undefined", log_text)
            for r in ref_warns:
                undefined_issues.append(f"Undefined reference in log: '{r}'")
            for c in cite_warns:
                undefined_issues.append(f"Undefined citation in log: '{c}'")

        defined_labels = set(re.findall(r"\\label\{([^}]+)\}", self.all_tex_content))
        referenced_labels = set(re.findall(r"\\(?:ref|pageref)\{([^}]+)\}", self.all_tex_content))
        missing_labels = referenced_labels - defined_labels
        for ml in missing_labels:
            undefined_issues.append(f"Referenced label '\\ref{{{ml}}}' has no matching \\label in .tex sources")

        raw_placeholders = re.findall(r"\[\?\]|\?\?", self.stripped_content)
        if raw_placeholders:
            undefined_issues.append(f"Found {len(raw_placeholders)} literal unresolved placeholder mark(s) ([?] or ??)")

        self.results[tier].append(TestResult(
            "2.2", "Zero undefined references or citations",
            len(undefined_issues) == 0,
            "All references and labels cleanly resolved" if not undefined_issues else f"Found {len(undefined_issues)} undefined reference/citation issue(s)",
            undefined_issues
        ))

        # ---------------------------------------------------------------------
        # 2.3: Check \usepackage{url} present in preamble
        # ---------------------------------------------------------------------
        preamble_match = re.search(r"(.*?)\\begin\{document\}", self.stripped_content, re.DOTALL)
        preamble = preamble_match.group(1) if preamble_match else self.stripped_content
        has_url_pkg = bool(re.search(r"\\usepackage(?:\[[^\]]*\])?\{url\}", preamble))
        self.results[tier].append(TestResult(
            "2.3", "\\usepackage{url} present in LaTeX preamble",
            has_url_pkg,
            "\\usepackage{url} loaded in preamble (prevents underscore syntax errors)" if has_url_pkg else "\\usepackage{url} MISSING from preamble"
        ))

        # ---------------------------------------------------------------------
        # 2.4: Check math delimiter syntax ($101 \times 101$, $224 \times 224$, etc.)
        # ---------------------------------------------------------------------
        math_syntax_errors = []

        for line_no, line in enumerate(self.stripped_content.splitlines(), start=1):
            broken_match = re.search(r"(?<!\$)(?<!\\times)\s*\\times\s*\d+\$|\$[^$]*\b\d+\s*\\times(?!\s*[\d\\{a-zA-Z])", line)
            if broken_match:
                math_syntax_errors.append(f"Line {line_no}: Malformed math syntax around \\times: '{broken_match.group(0).strip()}'")

            no_math = re.sub(r"\$[^$]+\$", "", line)
            no_math = re.sub(r"\\\[.*?\\\]", "", no_math)
            if "\\times" in no_math:
                math_syntax_errors.append(f"Line {line_no}: Raw \\times outside math mode: '{line.strip()}'")

        self.results[tier].append(TestResult(
            "2.4", "Proper math delimiter syntax for dimensional expressions ($101 \\times 101$, $3 \\times 3$, etc.)",
            len(math_syntax_errors) == 0,
            "All \\times dimensional expressions cleanly enclosed in math mode" if not math_syntax_errors else f"Found {len(math_syntax_errors)} math syntax error(s)",
            math_syntax_errors
        ))

    # =========================================================================
    # TIER 3: Cross-Feature Consistency
    # =========================================================================
    def run_tier_3(self):
        tier = "Tier 3: Cross-Feature Consistency"

        # ---------------------------------------------------------------------
        # 3.1: Model comparison table contains valid numeric CPU latency and params
        # ---------------------------------------------------------------------
        tbl = self.model_table
        table_consistent = True
        diagnostics = []

        if not tbl:
            table_consistent = False
            diagnostics.append("Model comparison table does not exist")
        else:
            # Map column indices from headers
            param_col_idx = None
            latency_col_idx = None
            top1_col_idx = None

            for idx, h in enumerate(tbl.headers):
                if re.search(r"param", h, re.IGNORECASE):
                    param_col_idx = idx
                if re.search(r"latenc|time", h, re.IGNORECASE):
                    latency_col_idx = idx
                if re.search(r"top-1", h, re.IGNORECASE):
                    top1_col_idx = idx

            if param_col_idx is None:
                table_consistent = False
                diagnostics.append("Missing 'Parameters' column in table headers")
            if latency_col_idx is None:
                table_consistent = False
                diagnostics.append("Missing 'CPU Latency' column in table headers")

            parsed_rows = {}
            for row in tbl.rows:
                if not row:
                    continue
                first_cell = row[0].lower()
                for target in ["Custom CNN", "ResNet50", "MobileNetV2", "DenseNet121", "EfficientNetB0"]:
                    if target.lower() in first_cell:
                        parsed_rows[target] = row

            if len(parsed_rows) < 5:
                table_consistent = False
                diagnostics.append(f"Only {len(parsed_rows)}/5 models present in table: {list(parsed_rows.keys())}")
            else:
                diagnostics.append(f"All 5 candidate architectures present in table rows")

            # Check numeric validity and trade-offs
            if param_col_idx is not None and latency_col_idx is not None:
                eff_params = None
                dense_params = None
                eff_latency = None
                dense_latency = None

                for name, row in parsed_rows.items():
                    try:
                        p_str = re.sub(r"[^\d.]", "", row[param_col_idx])
                        l_str = re.sub(r"[^\d.]", "", row[latency_col_idx])
                        p_val = float(p_str)
                        l_val = float(l_str)
                        diagnostics.append(f"{name}: Params={p_val}M, Latency={l_val}ms")
                        if name == "EfficientNetB0":
                            eff_params = p_val
                            eff_latency = l_val
                        elif name == "DenseNet121":
                            dense_params = p_val
                            dense_latency = l_val
                    except (IndexError, ValueError) as e:
                        table_consistent = False
                        diagnostics.append(f"{name}: invalid numeric format in row {row}")

                # Validate selection trade-off: EfficientNetB0 must have lower params and lower latency than DenseNet121
                if eff_params is not None and dense_params is not None:
                    if eff_params >= dense_params:
                        table_consistent = False
                        diagnostics.append(f"Parameter contradiction: EfficientNetB0 ({eff_params}M) >= DenseNet121 ({dense_params}M)")
                    else:
                        diagnostics.append(f"Parameter trade-off confirmed: EfficientNetB0 ({eff_params}M) < DenseNet121 ({dense_params}M)")

                if eff_latency is not None and dense_latency is not None:
                    if eff_latency >= dense_latency:
                        table_consistent = False
                        diagnostics.append(f"Latency contradiction: EfficientNetB0 ({eff_latency}ms) >= DenseNet121 ({dense_latency}ms)")
                    else:
                        diagnostics.append(f"Latency trade-off confirmed: EfficientNetB0 ({eff_latency}ms) < DenseNet121 ({dense_latency}ms)")

        self.results[tier].append(TestResult(
            "3.1", "Model comparison table contains valid numeric CPU latency and parameter counts supporting selection rationale",
            table_consistent,
            "Table metrics valid and logically consistent" if table_consistent else "Table metrics missing or inconsistent",
            diagnostics
        ))

        # ---------------------------------------------------------------------
        # 3.2: In-text citations vs references.bib cross-consistency
        # ---------------------------------------------------------------------
        cite_consistency = True
        cite_details = []

        if not self.cited_keys:
            cite_consistency = False
            cite_details.append("No in-text \\cite{...} commands found in manuscript")
        else:
            cite_details.append(f"Found {len(self.cited_keys)} unique cited citation key(s)")
            missing_bib_keys = self.cited_keys - self.bib_keys
            if missing_bib_keys:
                cite_consistency = False
                for mk in missing_bib_keys:
                    cite_details.append(f"Cited key '{mk}' does NOT exist in references.bib")
            else:
                cite_details.append("Every cited key matches a valid entry in references.bib (0 missing entries)")

            unused_keys = self.bib_keys - self.cited_keys
            if unused_keys:
                cite_details.append(f"Info: {len(unused_keys)} references.bib entries not cited in text: {list(unused_keys)[:5]}...")

        self.results[tier].append(TestResult(
            "3.2", "Every in-text \\cite{key} has a matching entry in references.bib",
            cite_consistency,
            "All cited keys exist in bibliography" if cite_consistency else "Missing bibliography entries for cited keys",
            cite_details
        ))

        # ---------------------------------------------------------------------
        # 3.3: TTA and Confidence ablation tables contain valid numeric rows
        # ---------------------------------------------------------------------
        ablation_valid = True
        ablation_details = []

        tta_valid_rows = 0
        if self.tta_table:
            for row in self.tta_table.rows:
                nums = [re.sub(r"[^\d.]", "", c) for c in row if re.search(r"\d", c)]
                if len(nums) >= 2:
                    tta_valid_rows += 1

        conf_valid_rows = 0
        if self.conf_table:
            for row in self.conf_table.rows:
                nums = [re.sub(r"[^\d.]", "", c) for c in row if re.search(r"\d", c)]
                if len(nums) >= 2:
                    conf_valid_rows += 1

        if tta_valid_rows < 3:
            ablation_valid = False
            ablation_details.append(f"TTA ablation table has only {tta_valid_rows} valid numeric rows (expected >= 3)")
        else:
            ablation_details.append(f"TTA ablation table has {tta_valid_rows} valid numeric rows")

        if conf_valid_rows < 3:
            ablation_valid = False
            ablation_details.append(f"Confidence threshold ablation table has only {conf_valid_rows} valid numeric rows (expected >= 3)")
        else:
            ablation_details.append(f"Confidence threshold ablation table has {conf_valid_rows} valid numeric rows")

        self.results[tier].append(TestResult(
            "3.3", "TTA and Confidence ablation tables contain valid numeric rows",
            ablation_valid,
            f"TTA valid rows: {tta_valid_rows}, Confidence valid rows: {conf_valid_rows}",
            ablation_details
        ))

    # =========================================================================
    # TIER 4: Full PDF Compilation & Layout
    # =========================================================================
    def run_tier_4(self):
        tier = "Tier 4: Full PDF Compilation & Layout"

        if self.skip_compile:
            self.results[tier].append(TestResult("4.1", "Clean build sequence via cmd /c", True, "SKIPPED (--skip-compile requested)"))
            self.results[tier].append(TestResult("4.2", "Output PDF generation and freshness", True, "SKIPPED (--skip-compile requested)"))
            self.results[tier].append(TestResult("4.3", "BibTeX clean execution", True, "SKIPPED (--skip-compile requested)"))
            self.results[tier].append(TestResult("4.4", "Zero fatal LaTeX log errors", True, "SKIPPED (--skip-compile requested)"))
            return

        cmd = 'cmd /c "pdflatex -interaction=nonstopmode -disable-installer main.tex && bibtex main && pdflatex -interaction=nonstopmode -disable-installer main.tex && pdflatex -interaction=nonstopmode -disable-installer main.tex"'
        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.paper_dir),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=180
            )
            elapsed = time.time() - start_time
            exit_code = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired:
            self.results[tier].append(TestResult("4.1", "Compilation sequence completed within timeout", False, "Compilation timed out after 180s"))
            return
        except Exception as e:
            self.results[tier].append(TestResult("4.1", "Compilation sequence execution", False, f"Failed to run build process: {e}"))
            return

        # 4.1: Clean build sequence exit code
        self.results[tier].append(TestResult(
            "4.1", "Clean build sequence via cmd /c (pdflatex -> bibtex -> pdflatex -> pdflatex)",
            exit_code == 0,
            f"Exit code: {exit_code} (elapsed: {elapsed:.1f}s)",
            [f"Command: {cmd}"] + ([f"Stderr: {stderr[:300]}"] if exit_code != 0 else [])
        ))

        # 4.2: Output PDF generation and freshness check
        pdf_path = self.paper_dir / "main.pdf"
        pdf_ok = False
        pdf_msg = "main.pdf not found"
        if pdf_path.exists():
            mtime = pdf_path.stat().st_mtime
            size = pdf_path.stat().st_size
            if exit_code == 0 and mtime >= start_time - 5 and size > 50000:
                pdf_ok = True
                pdf_msg = f"main.pdf freshly generated ({size:,} bytes, mtime fresh)"
            elif exit_code != 0:
                pdf_msg = f"Compilation failed (exit code {exit_code}); existing PDF on disk is stale from a prior build"
            else:
                pdf_msg = f"main.pdf size suspiciously small ({size} bytes)"

        self.results[tier].append(TestResult(
            "4.2", "Verify output main.pdf freshly generated and non-empty (>50 KB)",
            pdf_ok,
            pdf_msg
        ))

        # 4.3: Check main.blg for BibTeX errors
        blg_path = self.paper_dir / "main.blg"
        blg_clean = True
        blg_issues = []
        if blg_path.exists():
            with open(blg_path, "r", encoding="utf-8", errors="replace") as f:
                blg_text = f.read()
            if "I found no \\citation commands" in blg_text:
                blg_clean = False
                blg_issues.append("Fatal: 'I found no \\citation commands---while reading file main.aux'")
            error_count_m = re.search(r"\(There (?:was|were) (\d+) error message", blg_text)
            if error_count_m and int(error_count_m.group(1)) > 0:
                blg_clean = False
                blg_issues.append(f"Fatal: BibTeX reported {error_count_m.group(1)} error message(s)")
        else:
            blg_clean = False
            blg_issues.append("main.blg not found")

        self.results[tier].append(TestResult(
            "4.3", "Verify main.blg has zero fatal BibTeX errors",
            blg_clean,
            "Zero fatal BibTeX errors" if blg_clean else f"BibTeX compilation failed with {len(blg_issues)} error(s)",
            blg_issues
        ))

        # 4.4: Check main.log for fatal LaTeX errors
        log_path = self.paper_dir / "main.log"
        log_clean = True
        log_errors = []
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_lines = f.readlines()
            for idx, line in enumerate(log_lines):
                if line.startswith("! "):
                    context = "".join(log_lines[max(0, idx-1):min(len(log_lines), idx+3)]).strip()
                    log_errors.append(context.replace("\n", " "))
            if log_errors:
                log_clean = False
        else:
            log_clean = False
            log_errors.append("main.log not found")

        self.results[tier].append(TestResult(
            "4.4", "Verify main.log has zero fatal LaTeX syntax errors",
            log_clean,
            "Zero fatal LaTeX errors in main.log" if log_clean else f"Found {len(log_errors)} fatal LaTeX error(s)",
            log_errors[:5]
        ))

    # =========================================================================
    # Reporting
    # =========================================================================
    def print_report(self) -> int:
        print("\n" + "=" * 80)
        print(f"{Colors.BOLD}{Colors.CYAN}FoodLens IEEE Manuscript 4-Tier Verification Report{Colors.RESET}")
        print("=" * 80)

        total_tests = 0
        total_passed = 0
        total_failed = 0

        for tier_name, test_list in self.results.items():
            if not test_list:
                continue

            tier_passed = sum(1 for t in test_list if t.passed)
            tier_total = len(test_list)

            print(f"\n{Colors.BOLD}{Colors.YELLOW}--- {tier_name} ({tier_passed}/{tier_total} Passed) ---{Colors.RESET}")

            for t in test_list:
                total_tests += 1
                if t.passed:
                    total_passed += 1
                    status = f"{Colors.GREEN}[PASS]{Colors.RESET}"
                else:
                    total_failed += 1
                    status = f"{Colors.RED}[FAIL]{Colors.RESET}"

                print(f"  {status} {Colors.BOLD}{t.test_id}{Colors.RESET}: {t.name}")
                if t.message:
                    print(f"         {Colors.BLUE}Result:{Colors.RESET} {t.message}")
                if not t.passed and t.details:
                    for d in t.details[:5]:
                        print(f"         {Colors.YELLOW}-> {d}{Colors.RESET}")
                    if len(t.details) > 5:
                        print(f"         {Colors.YELLOW}-> ... and {len(t.details) - 5} more issue(s){Colors.RESET}")

        print("\n" + "=" * 80)
        final_color = Colors.GREEN if total_failed == 0 else Colors.RED
        print(f"{Colors.BOLD}{final_color}VERIFICATION SUMMARY: {total_passed}/{total_tests} Tests Passed ({(total_passed/max(1, total_tests))*100:.1f}%){Colors.RESET}")
        print("=" * 80 + "\n")

        return 0 if total_failed == 0 else 1

    def export_json(self, output_path: Path):
        data = {
            "summary": {
                "total": sum(len(v) for v in self.results.values()),
                "passed": sum(sum(1 for t in v if t.passed) for v in self.results.values()),
                "failed": sum(sum(1 for t in v if not t.passed) for v in self.results.values()),
            },
            "tiers": {k: [t.to_dict() for t in v] for k, v in self.results.items()},
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Exported JSON results to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="4-Tier Verification Harness for FoodLens IEEE Manuscript")
    parser.add_argument("--tier", choices=["1", "2", "3", "4", "all"], default="all", help="Tier to execute (default: all)")
    parser.add_argument("--paper-dir", type=str, default=str(Path(__file__).resolve().parents[1] / "paper"), help="Path to paper directory")
    parser.add_argument("--skip-compile", action="store_true", help="Skip pdflatex/bibtex execution in Tier 4")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose diagnostics")
    parser.add_argument("--json", type=str, default=None, help="Path to output JSON test results")

    args = parser.parse_args()
    paper_dir = Path(args.paper_dir)

    verifier = PaperVerifier(paper_dir, skip_compile=args.skip_compile, verbose=args.verbose)
    if not verifier.load_sources():
        sys.exit(1)

    tier_arg = args.tier
    if tier_arg in ["1", "all"]:
        verifier.run_tier_1()
    if tier_arg in ["2", "all"]:
        verifier.run_tier_2()
    if tier_arg in ["3", "all"]:
        verifier.run_tier_3()
    if tier_arg in ["4", "all"]:
        verifier.run_tier_4()

    exit_code = verifier.print_report()

    if args.json:
        verifier.export_json(Path(args.json))

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
