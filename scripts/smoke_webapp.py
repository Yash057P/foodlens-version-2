"""Browser smoke test for the FoodLens viva demo.

Run while the Flask application is available at http://127.0.0.1:5000.
"""

from pathlib import Path
from tempfile import gettempdir

from playwright.sync_api import sync_playwright
import requests


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:5000"


def main() -> None:
    health = requests.get(f"{BASE_URL}/api/health", timeout=10)
    health.raise_for_status()
    assert health.json()["model_ready"] is True
    assert health.json()["classes"] == 101

    model = requests.get(f"{BASE_URL}/api/model", timeout=10)
    model.raise_for_status()
    assert model.json()["parameters"] > 1_000_000
    assert model.json()["tta_views"] == 3
    assert model.json()["calibration"]["status"] == "fitted"
    assert round(model.json()["calibration"]["temperature"], 3) == 1.350

    missing_upload = requests.post(f"{BASE_URL}/api/predict", timeout=10)
    assert missing_upload.status_code == 400

    evaluation = requests.get(f"{BASE_URL}/api/evaluation", timeout=10)
    evaluation.raise_for_status()
    assert round(evaluation.json()["metrics"]["top3"], 4) == 0.8821

    feedback = requests.post(
        f"{BASE_URL}/api/feedback",
        json={
            "predicted_class": "pizza",
            "corrected_class": "pizza",
            "confidence": 1.0,
            "source": "automated_smoke",
        },
        timeout=10,
    )
    assert feedback.status_code == 201
    assert requests.get(f"{BASE_URL}/api/feedback/stats", timeout=10).json()["count"] >= 1

    screenshot = Path(gettempdir()) / "foodlens-viva-smoke.png"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 947})
        console_errors: list[str] = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(BASE_URL, wait_until="networkidle")
        assert page.locator("text=Know your plate.").is_visible()
        page.evaluate("localStorage.setItem('foodlens.profile', JSON.stringify({allergies:['nuts'], diets:[], saved:true}))")
        page.reload(wait_until="networkidle")
        pipeline_size = page.locator(".pipeline").evaluate(
            "element => ({scroll: element.scrollWidth, client: element.clientWidth})"
        )
        assert pipeline_size["scroll"] <= pipeline_size["client"]
        page.evaluate("window.scrollTo(0, 400)")
        page.wait_for_timeout(100)
        assert page.locator(".sidebar-logo").is_visible()
        assert page.locator(".sidebar-logo").bounding_box()["y"] >= 0
        page.evaluate("window.scrollTo(0, 0)")
        page.get_by_role("button", name="Food profile").first.click()
        assert page.get_by_text("Build your food profile").is_visible()
        assert page.locator('input[name="allergy"][value="nuts"]').is_checked()
        page.get_by_role("button", name="Discover a dish").first.click()
        page.locator("#btnViva").click()
        assert page.locator("#vivaPanel").is_visible()
        assert page.locator("#vivaPanel").get_by_text("EfficientNetB0").is_visible()
        assert page.locator("#factParameters").inner_text() != "—"
        page.locator("#btnViva").click()
        assert page.locator("#vivaPanel").is_hidden()

        page.locator("#galleryInput").set_input_files(str(ROOT / "test_pizza_realistic.png"))
        page.locator("#btnScan").click()
        page.locator("#results").wait_for(state="visible", timeout=60_000)
        assert page.locator("#topPredictions .pred-row").count() == 3
        assert "inference time" in page.locator("#inferenceMeta").inner_text().lower()
        assert page.locator("#aiInsight").inner_text().startswith("Model assessment:")
        assert "entropy" in page.locator("#aiInsight").inner_text().lower()
        assert "Possible allergy concern" in page.locator("#guardrailResult").inner_text()
        page.locator("#btnFeedbackWrong").click()
        assert page.locator("#feedbackForm").is_visible()
        assert "google.com/maps/search" in page.locator("#findNearby").get_attribute("href")
        page.locator("#btnGradcam").click()
        page.locator("#gradcamResult").wait_for(state="visible", timeout=60_000)
        assert page.locator("#gradcamImage").get_attribute("src").startswith("data:image/jpeg;base64,")
        page.locator("#btnCompareTta").click()
        page.locator("#ttaComparison").wait_for(state="visible", timeout=60_000)
        assert "3-view TTA" in page.locator("#ttaComparison").inner_text()
        page.evaluate("window.scrollTo(0, 0)")
        page.get_by_role("button", name="Model evaluation").first.click()
        assert page.locator("#page-evaluation").is_visible()
        page.wait_for_function("document.querySelector('#evaluationMetrics').textContent.includes('88.21%')")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)
        page.screenshot(path=str(screenshot), full_page=True)

        mobile = browser.new_page(viewport={"width": 390, "height": 844})
        mobile.goto(BASE_URL, wait_until="networkidle")
        assert mobile.locator("text=Know your plate.").is_visible()
        dimensions = mobile.evaluate("({width: document.documentElement.scrollWidth, viewport: window.innerWidth})")
        assert dimensions["width"] <= dimensions["viewport"]
        mobile.close()

        browser.close()

    if console_errors:
        raise AssertionError(f"Browser console errors: {console_errors}")
    print("PASS: health, model metadata, How it works, and live inference")
    print(f"Screenshot: {screenshot}")


if __name__ == "__main__":
    main()
