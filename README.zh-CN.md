# Sony Look Bridge

Sony Creative Look 的照片配置与视频 LUT

[English](README.md) | 中文

天下苦创意风格久矣，CameraRaw 内迟迟没有上线A7M5的创意风格文件

本仓库通过逆向Sony Image Edit，把 Sony α7 V（ILCE-7M5）的 12 种 Creative Look移植成 Capture One、Camera Raw / Lightroom 和 DxO PhotoLab 的配置，并在 α7 V 样张上通过对比检验，色度上基本没有差异。

v1.3.0 提供 17 款 Sony 机型的配置，每台机型各有一个包含三款软件配置的 ZIP。

α7 V 还提供视频 LUT，将照片外观应用到 S-Log3 素材。

讲解视频：[Bilibili](https://www.bilibili.com/video/BV1VUH56pECK/) · [YouTube（英文）](https://youtu.be/LeK9HhhYosQ)

## 机型覆盖

每个机型包包含 Capture One、Camera Raw / Lightroom 和 DxO PhotoLab 配置。点击机型下载；[全部 17 个包及版本说明][release]。

| 系列 | 可下载的机型 |
| --- | --- |
| α1 / α9 | [α1][sony-a1] · [α1 II][sony-a1-ii] · [α9 III][sony-a9-iii] |
| α7 | [α7 IV][sony-a7-iv] · [α7 V][sony-a7-v] · [α7S III][sony-a7s-iii] |
| α7R / α7C | [α7R V][sony-a7r-v] · [α7R VI][sony-a7r-vi] · [α7C II][sony-a7c-ii] · [α7CR][sony-a7cr] |
| α6000 | [α6700][sony-a6700] |
| Cinema Line | [FX2][sony-fx2] · [FX3][sony-fx3] · [FX30][sony-fx30] |
| RX / ZV | [RX1R III][sony-rx1r-iii] · [ZV-E1][sony-zv-e1] · [ZV-E10 II][sony-zv-e10-ii] |

α7 V、α7R VI、FX2、RX1R III 包含 12 种原生外观，其余机型包含 10 种原生外观及移植的 FL2 / FL3。新增机型沿用 α7 V 输入校准；α7C II 已在 ACR 验证 ST 和 FL2。详见[机型说明](docs/cameras.md)。

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

## 效果

以下对照使用同一张 α7 V RAW 样张 DSC03591 的 ST 外观，以 Sony Imaging Edge Edit 导出为参考。Capture One 和 Camera Raw 均使用包含 SSCS 的当前 ST 色表，以及拍摄时白平衡。

![Sony ST 对照：全图、建筑与云层局部，以及明度和彩色色度误差图](images/compare_ST_zh.png)

| 软件 | 平均明度差 | 平均色度差 |
| --- | ---: | ---: |
| Capture One | 0.24 | 0.58 |
| Camera Raw | 0.44 | 0.49 |

数值为 CIELAB（D65）中共同有效区域的平均明度差和色度差。测量方法与其他外观的验证见[测量说明](docs/measurements.md)。

## 安装使用

**视频 LUT（v2.0.0）**：[下载 α7 V S-Log3 LUT](https://github.com/751K/sony-look-bridge/releases/download/v2.0.0/Sony-A7-V-SLog3-Video-LUTs.zip)，覆盖全部 12 种 Creative Look，输入为 S-Gamut3 或 S-Gamut3.Cine，输出为 Rec.709 / Gamma 2.4。默认 LUT 以测光 +1⅔ 档素材为输入；ST 的 18% 灰输出码值约为 0.607。见[使用说明](profiles/video/README.md)和[标定与生成](docs/video.md)。

以下步骤使用 α7 V 的文件名。各机型 ZIP 内附对应的安装说明。

### Capture One

1. 把 `profiles/capture_one/SonyA7M5-Look-*.icc` 复制到 `~/Library/ColorSync/Profiles/`，然后**重启** Capture One。C1 会缓存已加载的配置。
2. 在 Base Characteristics 中，ICC Profile 选 `SonyA7M5 Look XX`，**Curve 选 Linear Response**。

### Camera Raw / Lightroom

1. 把 `profiles/camera_raw/SonyA7M5 Linear Base.dcp` 复制到 `~/Library/Application Support/Adobe/CameraRaw/CameraProfiles/`。
2. 把 `profiles/camera_raw/SonyA7M5 Look *.xmp` 复制到 `~/Library/Application Support/Adobe/CameraRaw/Settings/`。
3. 重启 Photoshop / Lightroom，在配置文件浏览器的 **Sony A7M5** 组里选择外观。

> ⚠️ 兼容性提示：部分 Photoshop / Lightroom 版本可能无法正确加载这些配置（例如配置文件不显示或效果异常）。如果遇到兼容问题，建议更新到较新版本。

### DxO PhotoLab

需要 **Elite** 版 PhotoLab（*LUT Grading* 面板只在 Elite 版提供），已在 macOS 的 PhotoLab 10.1 上测试。PhotoLab 以路径引用 DCP 和 LUT 文件，请把它们放在一个固定、不会被清理的文件夹里。

1. 把 `profiles/dxo/SonyA7M5 Linear Base v2.dcp` 和 `profiles/dxo/SonyA7M5 Look *.cube` 复制到上面说的文件夹。
2. 先套用 **6 – 无校正** 预设；如果不使用预设，请确认 Smart Lighting、ClearView 和对比度都已关闭。镜头校正（畸变、色差、镜头锐度）可以重新开启，不影响外观的颜色。
3. **颜色渲染（Color/B&W Rendering）**：类型选 **DCP 配置文件**，点 *导入 DCP 配置文件…* 选择 `SonyA7M5 Linear Base v2.dcp`；DCP 曲线选 **Adobe**，强度设为 100，**饱和色保护**设为 0（关闭自动模式）。
4. **LUT**：在 **DxO PL Elite – LUT Grading** 面板中，点 LUT 文件旁的 *导入（.cube）…*，选择 `SonyA7M5 Look XX.cube`；**LUT 色彩空间**选 ProPhoto RGB，强度设为 100。
5. 可以把这套设置保存为预设；以后换外观时，只需更换 `.cube` 文件。

### 适用范围

请给 RAW 使用对应机型的 Look 包，下载状态见[机型覆盖](#机型覆盖)。

## 原理

项目复现 Sony 照片的逐像素外观链，将白平衡后的相机 RGB 映射为 sRGB；再标定目标软件的输入编码，将外观写成 ICC、XMP 或 LUT。锐化、降噪与 DRO 等空间处理仍由宿主软件完成。

记 Sony 外观映射为 *f*、宿主输入编码为 *E*，配置文件保存的是 *f* ∘ *E*⁻¹。下图展示中性显影、ST 和 FL2 对颜色分布的影响：

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="images/color_cube_zh_dark.png">
  <img alt="相机 RGB 经过中性显影、Sony ST 和 FL2 后的颜色分布" src="images/color_cube_zh_light.png">
</picture>

色彩映射图及完整推导见[照片外观的复现与标定](docs/photo_look.md)；视频链使用实拍矩阵连接 S-Log3 与照片外观，见[视频 LUT 标定](docs/video.md)。

## 重新生成

需要：Python 3.11+、在选定的 Python 环境中运行 `python3 -m pip install -r requirements.txt`（建议使用虚拟环境）、任意一张 A7M5 的 ARW，以及本机安装的 **Imaging Edge Edit 4.0.00.10312 或 4.1.00.03062**（macOS）。可选：Rust 工具链（`cargo`），用于加速的 `--rust` 解码；macOS 上另需 Xcode Command Line Tools，用于 Metal GPU 解码（`--metal`）。NumPy 路径两者都不需要。一次性 LUT 会缓存在 `~/.cache/sonylook`（`SONYLOOK_CACHE=0` 关闭，`SONYLOOK_CACHE_DIR` 改目录）。

外观链用到的一些常量表（色相 atan 表、对比度曲线族等）是在运行时从你本机安装的 Edit 里读取的（`sonylook/edit_binary.py`），本仓库不包含任何 Sony 的二进制或数据。脚本会校验 arm64 部分的 SHA-256；4.0.00.10312 与 4.1.00.03062 的表地址不同，`edit_binary.py` 里以 4.0 地址为准、对两者都做了映射。路径可以用 `SONY_EDIT_BINARY` 指定。

```bash
python3 capture_one/c1_look_profile.py /path/to/A7M5.ARW
```

```bash
python3 camera_raw/acr_look.py /path/to/A7M5.ARW --write
```

```bash
python3 dxo/dxo_look.py /path/to/A7M5.ARW --write
```

```bash
python3 sonylook/sony_render.py /path/to/A7M5.ARW Standard FL2 --scale 4
```

- 第一条生成 C1 配置，第二条生成 ACR 配置，第三条生成 DxO 的 LUT（加 `--eval` 会打印在该 ARW 上的插值误差），第四条用外观链直接渲染预览。
- 用 DSC03591 重新生成的结果，与 `profiles/` 里的文件逐字节相同。

### 解码 ARW

完整解码器会从 RawNR 一路运行到创意外观：

```bash
python3 sonylook/sony_decode.py /path/to/A7M5.ARW --out out.tif
```

解码器支持 sRGB / Adobe RGB、TIFF / JPEG / PNG，并读取 ARW 的显影设置。完整阶段和参数见[处理管线](docs/pipeline.md)。

解码器有两种可选的加速后端，输出均与 NumPy 参考实现一致（Metal ITP 除外，见说明）。使用 Rust 内核时，一张 7008×4672 的图约需 2 s；在 macOS 上再启用 Metal，约需 0.2 s：

```bash
python3 sonylook/sony_decode.py /path/to/A7M5.ARW --rust --metal --out out.tif
```

构建、覆盖范围和性能见 [Rust 说明](rust/README.md) 与 [Metal 加速](docs/metal.md)。

### Viewer 的 AI 超分

Viewer Extended Hi-Res 的输入、分块和导出链研究见[技术笔记](docs/sdm.md)。

### 重新标定

合成色卡和重新标定各软件输入编码的步骤见[重新标定说明](docs/recalibration.md)。

## 目录

| 目录             | 内容                                                                          |
| -------------- | --------------------------------------------------------------------------- |
| `profiles/`    | 照片配置及视频 LUT 的生成记录                                                          |
| `chart/`       | 合成色卡：`SonyChart.ARW`（可直接用 C1 / ACR 打开）、色块定义 `SonyChart.json`、预览图            |
| `sonylook/`    | Sony 外观链与前端的 Python 移植，以及 ARW / Edit 读取器。另含 RawNR、DRO、锐化 / Spica、Marble、镜头几何校正（都不用于配置）、BW/SE 的 Effect 阶段（用于配置），以及整图解码器 `sony_decode.py`。`sonylook/metal/` 为解码各阶段的可选 Metal GPU 实现 |
| `rust/`        | 可选的 Rust 内核（`sonylook_core`）：融合渲染 band、GeoCorr、ITP、Marble、SSCS 和表构造。见 `rust/README.md` |
| `tests/`       | Metal 各阶段和 Rust RAW 读取与参考实现的差分验证                                       |
| `capture_one/` | C1 配置生成、合成色卡、测量与对比                                                          |
| `camera_raw/`  | ACR 表格式、DCP 读写、配置生成、测量与对比                                                   |
| `dxo/`         | DxO PhotoLab 的 LUT 输入模型（`dxo_model.py`）、探针和底座 DCP 生成、LUT 生成                      |
| `video/`       | S-Log3 输入转换、传感器矩阵标定、视频 LUT 生成和测试 |
| `site/`        | Three.js 交互讲解网页“一张照片的诞生”和资源导出脚本，通过 GitHub Pages 部署 |
| `docs/`        | [文档导航](docs/README.md)：处理链、宿主标定、测量方法与本地研究资料索引。原始证据文件和测试导出保存在仓库之外 |

## 说明

- 本项目与 Sony、Capture One、Adobe、DxO 均无关联，相关名称和商标归各自所有者所有。
- 本项目通过分析软件行为来实现互操作。仓库不包含这些软件的二进制、反编译代码或从中提取的数据；需要的常量都在使用者本机从其自己安装的软件中读取。
- 配置文件中的 ColorMatrix 数值取自 Adobe Standard 的 A7M5 配置，用于让 ACR 的白平衡行为保持不变。DxO 的底座 DCP 出于同样的原因，用了 Adobe Standard 的 ColorMatrix 和 D65 ForwardMatrix。
- `dxo/dxo_model.py` 按观测到的行为重新实现了 PhotoLab 的高光恢复，并包含几个在 PhotoLab 运行时测得的数值（DxO Wide Gamut 矩阵、高光白点）；不包含 DxO 的代码或文件。

## 许可

- 代码、文档和生成配置的工作以 [MIT 许可证](LICENSE) 发布。
- 配置文件按原样提供。其中源自第三方的数据（Sony 的外观参数、Adobe 的 ColorMatrix 数值）不在本许可的授权范围内，本项目也不对其主张任何权利。
