# Camera coverage and sample notes


Each listed pack covers Capture One, Adobe Camera Raw / Lightroom and DxO PhotoLab.

**✅** Pack built. **❌** No dedicated pack.

| Sony series | Camera model | Look pack |
| --- | --- | :---: |
| **α1** | [α1][sony-a1] | ✅ |
| &nbsp; | [α1 II][sony-a1-ii] | ✅ |
| **α9** | α9 | ❌ |
| &nbsp; | α9 II | ❌ |
| &nbsp; | [α9 III][sony-a9-iii] | ✅ |
| **α7** | α7 | ❌ |
| &nbsp; | α7 II | ❌ |
| &nbsp; | α7 III | ❌ |
| &nbsp; | [α7 IV][sony-a7-iv] | ✅ |
| &nbsp; | [α7 V][sony-a7-v] | ✅ |
| **α7R** | α7R | ❌ |
| &nbsp; | α7R II | ❌ |
| &nbsp; | α7R III | ❌ |
| &nbsp; | α7R IIIA | ❌ |
| &nbsp; | α7R IV | ❌ |
| &nbsp; | α7R IVA | ❌ |
| &nbsp; | [α7R V][sony-a7r-v] | ✅ |
| &nbsp; | [α7R VI][sony-a7r-vi] | ✅ |
| **α7S** | α7S | ❌ |
| &nbsp; | α7S II | ❌ |
| &nbsp; | [α7S III][sony-a7s-iii] | ✅ |
| **α7C** | α7C | ❌ |
| &nbsp; | [α7C II][sony-a7c-ii] | ✅ |
| &nbsp; | [α7CR][sony-a7cr] | ✅ |
| **α6000** | α6000 | ❌ |
| &nbsp; | α6100 | ❌ |
| &nbsp; | α6100A | ❌ |
| &nbsp; | α6300 | ❌ |
| &nbsp; | α6400 | ❌ |
| &nbsp; | α6400A | ❌ |
| &nbsp; | α6500 | ❌ |
| &nbsp; | α6600 | ❌ |
| &nbsp; | [α6700][sony-a6700] | ✅ |
| **Cinema Line FX** | [FX2][sony-fx2] | ✅ |
| &nbsp; | [FX3][sony-fx3] | ✅ |
| &nbsp; | FX3A | ❌ |
| &nbsp; | FX5 | ❌ |
| &nbsp; | FX6 | ❌ |
| &nbsp; | FX9 | ❌ |
| &nbsp; | [FX30][sony-fx30] | ✅ |
| **RX1** | RX1 | ❌ |
| &nbsp; | RX1R | ❌ |
| &nbsp; | RX1R II | ❌ |
| &nbsp; | [RX1R III][sony-rx1r-iii] | ✅ |
| **ZV-E** | [ZV-E1][sony-zv-e1] | ✅ |
| &nbsp; | ZV-E10 | ❌ |
| &nbsp; | [ZV-E10 II][sony-zv-e10-ii] | ✅ |
| **ZV-1** | ZV-1 | ❌ |
| &nbsp; | ZV-1 II | ❌ |
| &nbsp; | ZV-1F | ❌ |

Click a camera name in the table to download its ZIP. All 17 packs and release notes are on the [v2.1.0 release page][release], with SHA-256 hashes in the [checksum file][checksums]. Each ZIP includes profiles for all three applications and installation instructions.

The α7 V, α7R VI, FX2 and RX1R III packs contain 12 native looks. The other packs contain 10 native looks plus FL2 and FL3 ported from α7 V.

The new camera packs have passed file checks and use the α7 V input calibration. ST and FL2 have been tested in ACR on the α7C II. The other new cameras await in-app validation. The project currently has no dedicated packs for unlisted models.

All packs use the daylight look colour parameters (RGB2YCC blend weights `0 1024 0 0`). The camera blends a warm-light and a daylight parameter set according to each photo's as-shot white balance (see [pipeline §4.3](pipeline.md#43-rgb2ycc-与-ycc2rgb0x1000ee0cc0x1000fb500)), so photos taken under warm light will differ in colour between these profiles and Edit. All packs are built by `camera_packs/build_packs.py`.

The α7S III and FX3 samples contain four SSCS weights of 255. Their packs use the default weights 32/64/32, with highlight colours awaiting measurement. A ZV-1 II RAW sample is available, but its older colour matrix pipeline requires a rendering path the generator has yet to implement.

Sony added native FL2/FL3 to the α1 II and α9 III in firmware 4.00. Their packs use RAW samples from firmware 2.00 and 1.00, respectively. [α1 II firmware notes][a1ii-fw] · [α9 III firmware notes][a9iii-fw]

[sony-a1]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-A1-Creative-Looks.zip
[sony-a1-ii]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-A1-II-Creative-Looks.zip
[sony-a9-iii]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-A9-III-Creative-Looks.zip
[sony-a7-iv]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-A7-IV-Creative-Looks.zip
[sony-a7-v]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-A7-V-Creative-Looks.zip
[sony-a7r-v]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-A7R-V-Creative-Looks.zip
[sony-a7r-vi]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-A7R-VI-Creative-Looks.zip
[sony-a7s-iii]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-A7S-III-Creative-Looks.zip
[sony-a7c-ii]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-A7C-II-Creative-Looks.zip
[sony-a7cr]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-A7CR-Creative-Looks.zip
[sony-a6700]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-A6700-Creative-Looks.zip
[sony-fx2]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-FX2-Creative-Looks.zip
[sony-fx3]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-FX3-Creative-Looks.zip
[sony-fx30]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-FX30-Creative-Looks.zip
[sony-rx1r-iii]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-RX1R-III-Creative-Looks.zip
[sony-zv-e1]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-ZV-E1-Creative-Looks.zip
[sony-zv-e10-ii]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/Sony-ZV-E10-II-Creative-Looks.zip
[release]: https://github.com/751K/sony-look-bridge/releases/tag/v2.1.0
[checksums]: https://github.com/751K/sony-look-bridge/releases/download/v2.1.0/SHA256SUMS.txt
[a1ii-fw]: https://www.sony.com/electronics/support/software/00349486
[a9iii-fw]: https://www.sony.com/electronics/support/software/00341218
