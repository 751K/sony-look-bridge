# Measurement notes

Local exports, experiments and verification scripts are listed in the [research index](research.md).

## Current README figure

The current Chinese and English figures are generated from real 16-bit TIFF exports of DSC03591 using ST. Image panels and residual maps are rebuilt from those TIFFs, rather than extracted from the previous comparison JPEG. Full source hashes, fitted displacements, profile identity checks and unrounded scores are in [the measurement manifest](../images/compare_ST.measurements.json).

| Role | Source export | Software | Export date |
| --- | --- | --- | --- |
| Reference | `DSC03591.TIF` | Sony Edit 4.0.00.10312 | 2026-10-16 |
| Capture One | `DSC03591.tif` | Capture One 16.8.6.25 | 2026-11-05 |
| Camera Raw | `DSC03591_STSCCS.TIF` | Adobe Camera Raw 18.7 | 2026-10-17 |

The Capture One export was recreated in an isolated session using the saved test adjustments: ST with SSCS, Linear Response, shot white balance, exposure 0. Its cached `SonyA7M5-Look-ST-SSCS.icm` has an **identical A2B0 colour transform** to the current `profiles/capture_one/SonyA7M5-Look-ST.icc`; the profile descriptions differ. The Camera Raw export's embedded XMP identifies RGBTable `33E06EAAB047FB008C76F470FEE7C752`, matching the current ST XMP. Neither exported image was adjusted to improve the scores.

The geometric fit uses the existing cubic displacement model fitted to phase correlations of image gradients. Host pixels are bilinearly sampled into Edit's coordinates before the 8 × 8 box reduction. No colour or exposure fit is applied. All component scores use the intersection of valid blocks from the two host exports: 488,573 of 511,584 blocks (95.5% of the frame). This shared mask also applies to all full-frame panels and difference maps. The crop is selected to show lit brickwork and cloud texture; its position does not affect the global scores.

| Host | Mean absolute ΔL* | Mean Δab | Median geometric fit residual, source pixels |
| --- | ---: | ---: | ---: |
| Capture One | 0.240811 | 0.577229 | 1.013555 |
| Camera Raw | 0.444792 | 0.491203 | 1.880228 |

The reduced, unquantized sRGB arrays are converted to CIELAB relative to D65 (Xn=0.95047, Yn=1, Zn=1.08883). Lightness error is `abs(L*_host − L*_Edit)`. Chromaticity error is `sqrt((a*_host − a*_Edit)^2 + (b*_host − b*_Edit)^2)`: distance in the a*, b* plane, excluding the L* component. It captures hue as well as chroma differences; it is not the scalar chroma-magnitude difference ΔC*, and not ΔE₀₀. Each reported score is the mean of that component's per-pixel error on the same shared mask.

The lightness maps use a fixed linear grayscale of 0–4 L* units, with values at or above 4 shown in white. The chromaticity maps preserve the signed residual vector `(a*_host − a*_Edit, b*_host − b*_Edit)` at a constant display L*=65: zero is neutral gray, the Lab hue indicates the direction of the colour shift, and display chroma increases with its magnitude. Residual a*, b* are amplified 15×, with Δab capped at 4 before amplification. Out-of-sRGB colours are compressed in chroma at fixed L* and Lab hue. Both hosts use the same mapping; there is no per-host normalization. The displayed chromaticity colours represent residual direction, not the original scene colours. The crop uses full-resolution samples, resized for the page; it is not labelled as a 100% display. The geometric residuals, host demosaicing and sharpening contribute to both components. These scores cover one photograph and one look, not every supported camera or look.

For reproduction, supply the three original exports to:

```sh
PYTHONPATH=sonylook:capture_one:camera_raw python camera_raw/measure_comparison.py \
  "$EDIT_TIFF" "$C1_TIFF" "$ACR_TIFF" render_output/comparison-current
python camera_raw/compare_figure_editorial.py \
  render_output/comparison-current/measurements.json images
```

The inputs are kept outside version control. The measurement manifest records their SHA-256 hashes. The TIFF export dates, software versions and profile checks are evidence for the current figure; the image itself presents the reader-facing result.

## Interpreting earlier scores

The current TIFF measurements also retain global RGB MAE for traceability: C1 0.778455 and ACR 1.203800 in 8-bit sRGB units. These RGB scores are separate from the current README's mean absolute ΔL* and mean Δab.

The previous comparison JPEG reported C1 1.08 and ACR 1.45 after a **4×** reduction. They are not a before/after baseline for the new 8× figures. Earlier 8× host measurements also used different valid areas and fits. For example, the ACR SSCS export measures 1.262 on its own valid area, and 1.204 on the shared area used by the current figure. Do not attribute that difference to a profile improvement.

The SSCS figures 0.16 (C1) and 0.33 (ACR) describe a different metric: mean absolute chroma-component error within the roughly 5% bright-region mask. For each pixel, that metric subtracts the mean RGB difference from the channel differences before taking the absolute mean. It is neither global RGB MAE nor perceptual ΔE. Those values cannot be compared directly with the current README's CIELAB component scores.

## Archived validation results

The following results retain the earlier measurements and their stated conditions. They are supporting research records, not the current README figure's data. The legacy host exports predate SSCS, and the FL2/FL3 tests used Fade 0 rather than the current camera-default Fade 1.

These results use the α7 V test image DSC03591. Each profile was rendered from the same ARW and compared with Edit's export of that look. The images were registered, reduced 8×, and compared as mean absolute error in 8-bit units. The reference column is the complete Edit pipeline ported in this repository (`sonylook/sony_decode.py`: demosaicing, lens correction, sharpening and Spica, Marble), so unlike the profiles it also contains the spatial processing.

| Look | Capture One | Camera Raw | Reference: full Edit chain |
| --- | --- | --- | --- |
| ST | 1.17 | 1.27 | 0.08 |
| FL2 | 1.05 | 1.15 | 0.08 |
| FL3 | 1.21 | 1.27 | 0.09 |

*The Capture One and Camera Raw columns are exports from 2026-10-16, made before SSCS entered the profiles in v1.1.0; the SSCS bullet below measures that change.*

- **Colour and tone:** the full chain matches Edit to ΔE₀₀ 0.02–0.03 in flat areas and 0.04–0.05 on texture. The look mapping and the stages around it are essentially exact.
- **Flat areas:** the host exports differ from Edit by ΔE₀₀ ≈ 0.5 for ST (both hosts) and 0.6–0.9 for FL2/FL3 in Camera Raw. That error is the profiles' interpolation plus the hosts' own rendering, not the look mapping.
- **Global colour shift:** over flat areas the mean Lab difference in Camera Raw is ΔE₀₀ 0.25–0.79 across the three looks, with chroma difference ΔC* of +0.00 / +0.09 / +0.11 (ST / FL2 / FL3). In Capture One (ST) the chroma difference is ≈ −0.20. None is visible.
- **Edges and fine texture:** this is where the host difference sits. In Camera Raw the error is 0.6–0.9 in flat areas and 5.6–6.1 in textured ones; the full chain stays at ~0.1 in the same textured areas. It comes from each program's own demosaicing and sharpening, not from the look.
- **Synthetic chart:** profile vs. Sony look target is 0.10–0.15 for Capture One and 0.14 for Camera Raw (64³ table).
- **Bright, saturated colours (v1.1.0):** the profiles now include Sony's SSCS stage, which pulls bright, saturated colours towards their luma. On the ~5% of DSC03591 that it touches, ST's colour error against Edit drops from 0.64 to 0.16 in Capture One and from 0.61 to 0.33 in Camera Raw.
- **DxO PhotoLab (v1.2.0):** an ST export of DSC03591 from PhotoLab 10.1 (base DCP + look LUT, as-shot white balance) matches the look chain rendered with the same white balance to 1.18, with a mean colour shift of 0.25–0.67 per channel. It has not yet been compared with an Edit export. Up to about 1.7 stops below clipping PhotoLab passes colours through linearly (chart error 0.11); above that its own highlight handling takes over, and colour patches there differ by 4.6 on average (26 at most).
- **Coverage:** only ST, FL2 and FL3 have Edit exports to compare against; the other nine looks run through the same verified code with their own data but have not been checked against a Sony rendering. The FL2/FL3 numbers above are for Fade 0, which is what Edit uses for them. Since v1.0.2 the profiles apply the camera's default Fade (FL2/FL3 = 1, IN = 3, SH = 6), which Edit omits for FL2/FL3. That change has not yet been checked against in-camera JPEGs.
