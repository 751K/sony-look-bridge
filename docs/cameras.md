# 机型覆盖与样张说明


已有的 Look 包均包含 Capture One、Adobe Camera Raw / Lightroom 和 DxO PhotoLab 配置。

**✅** 已有 Look 包。**❌** 暂无专用包。

| Sony 系列 | 具体机型 | Look 包 |
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

点击表中的机型名即可下载对应 ZIP。全部 17 个包及版本说明见 [v1.3.0 Release][release]，各包的 SHA-256 见[校验文件][checksums]。每个 ZIP 都包含三款软件的配置及安装说明。

α7 V、α7R VI、FX2 和 RX1R III 的包各含 12 款原生外观。其余包各含 10 款原生外观，以及从 α7 V 移植的 FL2 和 FL3。

新增机型的 ZIP 已通过文件校验，沿用 α7 V 的软件输入校准。α7C II 已在 ACR 测过 ST 和 FL2，其余新增机型的软件内效果待验证。表外机型目前没有专用包。

α7S III 和 FX3 样张中的 SSCS 权重四项均为 255，生成时采用默认权重 32/64/32，高光颜色待实测。ZV-1 II 已有 RAW 样张，使用较旧的颜色矩阵流程，现有生成器尚缺这条处理路径。

Sony 从 4.00 固件开始为 α1 II 和 α9 III 提供原生 FL2/FL3。表中这两个包分别使用 2.00 和 1.00 固件的 RAW 样张。[α1 II 固件说明][a1ii-fw] · [α9 III 固件说明][a9iii-fw]

[sony-a1]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-A1-Creative-Looks.zip
[sony-a1-ii]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-A1-II-Creative-Looks.zip
[sony-a9-iii]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-A9-III-Creative-Looks.zip
[sony-a7-iv]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-A7-IV-Creative-Looks.zip
[sony-a7-v]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-A7-V-Creative-Looks.zip
[sony-a7r-v]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-A7R-V-Creative-Looks.zip
[sony-a7r-vi]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-A7R-VI-Creative-Looks.zip
[sony-a7s-iii]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-A7S-III-Creative-Looks.zip
[sony-a7c-ii]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-A7C-II-Creative-Looks.zip
[sony-a7cr]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-A7CR-Creative-Looks.zip
[sony-a6700]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-A6700-Creative-Looks.zip
[sony-fx2]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-FX2-Creative-Looks.zip
[sony-fx3]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-FX3-Creative-Looks.zip
[sony-fx30]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-FX30-Creative-Looks.zip
[sony-rx1r-iii]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-RX1R-III-Creative-Looks.zip
[sony-zv-e1]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-ZV-E1-Creative-Looks.zip
[sony-zv-e10-ii]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/Sony-ZV-E10-II-Creative-Looks.zip
[release]: https://github.com/751K/sony-look-bridge/releases/tag/v1.3.0
[checksums]: https://github.com/751K/sony-look-bridge/releases/download/v1.3.0/SHA256SUMS.txt
[a1ii-fw]: https://www.sony.com/electronics/support/software/00349486
[a9iii-fw]: https://www.sony.com/electronics/support/software/00341218
