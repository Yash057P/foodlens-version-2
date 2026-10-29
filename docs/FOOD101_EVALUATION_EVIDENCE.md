# Food-101 Evaluation Evidence

The deployed `EfficientNetB0` checkpoint was evaluated in private Kaggle kernel
`sarthakkulkarni27/foodlens-official-food-101-test-evaluation`, version 3.

## Data separation

- Temperature fitting: seeded 15% development split from the official Food-101
  training partition, 11,363 images.
- Final evaluation: untouched official `meta/test.txt` partition, 25,250 images,
  250 images for each of 101 classes.
- The deployed checkpoint was not replaced or retrained during this evaluation.

## Results

| Measure | Result |
|---|---:|
| Top-1 accuracy | 73.44% |
| Top-3 accuracy | 88.21% |
| Top-5 accuracy | 92.37% |
| Temperature | 1.349977 |
| Test NLL before / after | 0.9953 / 0.9727 |
| Test ECE before / after | 4.47% / 3.57% |

## Artifact integrity

- Deployed model SHA-256: `B2E087A6BEE8EAD124C36DFA7C3E00DC82EC154B2AD311125C3A6CF7570C4944`
- Test predictions SHA-256: `E72F95738A0ECA67D5CDD9930D824926451068DBC5F22EF890AE7C664318FBDF`
- Validation predictions SHA-256: `D13297BB9109F0B125FE85A007CDAAC993E52FC3B50BBDC167019A4CBEED906A`

The downloaded probability tensors were validated as `(25250, 101)` for test
and `(11363, 101)` for development. Test labels span all integer classes 0-100,
and every probability row sums to approximately 1.
