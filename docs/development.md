# 开发与发布

本页说明如何在本地生成配置文件与视频 LUT、如何重新标定宿主软件，以及发布附件如何构建。各配置的原理与验证见[照片配置](photo.md)和[视频 LUT](video.md)。

## 环境

- Python 3.11 或更高版本，以及 `requirements.txt` 中列出的依赖。视频 LUT 的独立校验另需 `colour-science`，屏幕色块拟合另需 `ffmpeg` / `ffprobe`。
- 所有命令均从仓库根目录执行。
- 一次性计算的 LUT 缓存于 `~/.cache/sonylook`。`SONYLOOK_CACHE=0` 可禁用缓存，`SONYLOOK_CACHE_DIR` 可修改缓存目录。

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install colour-science
```

## 外部数据

生成器需要三类不随仓库分发的数据。

| 数据 | 用途 | 本地来源 | 替代方式 |
| --- | --- | --- | --- |
| Imaging Edge Edit 的常量表 | 色相 atan 表、对比度曲线族、饱和度表等外观链共用的常量 | 本机安装的 Edit 4.0.00.10312 或 4.1.00.03062（macOS），可用 `SONY_EDIT_BINARY` 指定路径 | 常量表文件，见下文 |
| 各机型 Adobe Standard DCP | 底座 DCP 的 ColorMatrix 与 ForwardMatrix | 本机安装的 Camera Raw | 矩阵文件，见下文 |
| 样张 ARW | 各机型的外观参数；α7 V 的样张另提供视频 LUT 所用的 SSCS 参数 | 任意一张对应机型的 ARW | `camera_packs/samples.json` 列出的样张 |

`sonylook/edit_binary.py` 在运行时读取 Edit 的常量表，并校验 arm64 部分的 SHA-256。4.0 与 4.1 的表地址不同，代码以 4.0 的地址为准，并为 4.1 建立了地址映射。本仓库不包含 Sony 的程序或数据。

没有安装 Edit 或 Camera Raw 时，可以使用以下两个文件代替。两者都包含第三方数据，只能私下保存，不得提交到仓库。

```bash
python3 sonylook/edit_binary.py --export-tables edit_tables.xz
python3 camera_raw/dcp.py --export-adobe adobe_standard.json "/Library/Application Support/Adobe/CameraRaw/CameraProfiles/Adobe Standard/Sony ILCE-7M5 Adobe Standard.dcp" ...
```

设置 `SONY_EDIT_TABLES=edit_tables.xz` 与 `ADOBE_STANDARD_MATRICES=adobe_standard.json` 后，生成器从这两个文件读取数据，生成结果与读取本机安装时逐字节相同。常量表文件约 47 KB，矩阵文件约 8 KB。

样张清单 `camera_packs/samples.json` 记录每张样张的来源和 SHA-256。17 张来自 raw.pixls.us 与 rawdb.dnglab.org，许可为 CC0；α7 V 与 α7C II 的样张不在公开 RAW 库中，保存在本仓库的 `samples` 发布中。以下命令下载全部样张并核对校验值：

```bash
python3 camera_packs/fetch_samples.py SAMPLES_DIR
```

## 生成照片配置

```bash
python3 capture_one/c1_look_profile.py /path/to/A7M5.ARW
python3 camera_raw/acr_look.py /path/to/A7M5.ARW --write
python3 dxo/dxo_look.py /path/to/A7M5.ARW --write
python3 camera_packs/build_packs.py SAMPLES_DIR OUTPUT_DIR
```

前三条命令生成 `profiles/` 中的 α7 V 配置。`build_packs.py` 为每个机型生成一个 ZIP，包含三种宿主的配置和由 `camera_packs/readme/` 生成的安装说明；`--cameras Sony-A7-IV,...` 可只生成部分机型，`--jobs N` 设置并行进程数，每个进程约占 0.8 GB 内存。

## 生成视频 LUT

```bash
python3 video/video_look.py /path/to/A7M5.ARW --write --eval --out DIR
python3 video/validate_luts.py DIR
python3 video/make_dctl.py DIR
```

| 参数 | 作用 |
| --- | --- |
| `--looks ST,FL2` | 选择外观；默认全部 12 种 |
| `--gamuts SGamut3,SGamut3Cine` | 选择输入色域 |
| `--variants 2500K,4300K,...` | 选择色温版本；默认六套（2500K、3100K、4300K、4900K、5300K、7500K） |
| `--exposure -1.667` | LUT 输入的曝光补偿；默认按素材测光 +1⅔ 档设计 |
| `--sensor-matrix PATH` | 为所有版本指定同一个标定文件，代替各版本的色卡标定 |
| `--sony-scale VALUE` | 指定照片端的 Sony 原生刻度 |
| `--grid 65`、`--out DIR` | 设置网格大小和输出目录 |

LUT 只取决于 α7 V 的外观参数与 SSCS 参数，使用任何一张 α7 V ARW 都得到相同的文件。`--eval` 将每个 LUT 相对直接计算的插值误差写入 `manifest.json`；`validate_luts.py` 用 `colour-science` 独立读回 LUT，结果写入 `validation.json`。

屏幕色块的标定命令见[视频 LUT § 曝光刻度](video.md#曝光刻度)。

## 测试

```bash
python3 -m unittest discover -s video -p 'test_*.py' -v
```

单元测试覆盖 S-Log3 码值、白点、高光压缩、文件顺序和合成色块图拟合。照片外观链的各阶段已在模拟器中与 Edit 的原始函数逐位比较，方法见[处理管线](pipeline.md)。

## 重新标定宿主软件

`chart/SonyChart.ARW` 是一张合法的 α7 V ARW，包含 48 级灰阶和 6³ 个相机 RGB 色块，可由 Capture One 与 Camera Raw 直接打开。宿主软件更新后输入行为可能改变，此时按以下顺序重新标定：

1. 使用探针配置测量合成色卡的实际输入值。
2. Capture One：生成 Probe 配置并导出，用 `capture_one/measure_chart.py` 测量，再用 `capture_one/fit_c1_encoding.py` 拟合并更新 `c1_encoding_table.json`。
3. Camera Raw：生成 Probe 配置，关闭镜头校正后导出 16 位 ProPhoto，用 `camera_raw/measure_acr_chart.py` 与 `camera_raw/acr_encoding.py` 拟合。
4. DxO PhotoLab：用 `dxo/dxo_profiles.py probes` 与 `base2` 生成探针和底座，按同样方法检验 `dxo/dxo_model.py`。
5. 重新生成三种宿主的配置，并以实拍 RAW 和 Edit 导出图做几何配准与色差检查。

合成色卡可以从任意一张 α7 V ARW 重建：

```bash
python3 capture_one/make_chart.py SOURCE.ARW
```

## 发布

`camera_packs/make_release.py` 生成一次发布的全部附件：各机型的配置包、α7 V 视频 LUT 包（含 DCTL 与 `video/release_readme.txt` 生成的说明）以及 `SHA256SUMS.txt`。

```bash
python3 camera_packs/make_release.py SAMPLES_DIR OUT_DIR --version vX.Y.Z
```

`.github/workflows/release.yml` 在 GitHub 的 macOS 机器上执行同样的流程：

1. 推送 `v*` 标签后，工作流下载样张、还原常量表与矩阵文件、生成全部附件，并创建发布草稿。发布说明需要手动填写，确认后再发布。
2. 在 Actions 页面手动运行工作流时，只生成附件并保存为产物，保留 14 天，不创建发布。

一次运行约需 26 分钟。常量表文件以 base64 编码后拆分保存在仓库 Secret `EDIT_TABLES_1` 与 `EDIT_TABLES_2` 中，因为单个 Secret 最多 48 KB；矩阵文件保存在 `ADOBE_STANDARD_MATRICES` 中。升级 Edit 或 Adobe 更新相机配置后，需要重新导出这两个文件并更新 Secret。

GitHub 机器的系统数学库与本地不同，个别数值的最后一位可能不同。实测中视频 LUT 与绝大多数配置文件逐字节相同，只有自动版 FL2 底座中个别数值相差约 1e-10，对颜色没有影响。
