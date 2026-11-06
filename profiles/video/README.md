# α7 V Creative Look 视频 LUT

本 LUT 使 S-Log3 视频的输出模仿 α7 V 照片 Creative Look 的色调。共 12 种外观 × 2 种输入色域，计 24 个 65³ `.cube`，输出为 Rec.709 / Gamma 2.4。

**下载**：[Sony-A7-V-SLog3-Video-LUTs.zip](https://github.com/751K/sony-a7m5-looks/releases/download/v2.0.0/Sony-A7-V-SLog3-Video-LUTs.zip)（[v2.0.0 发布页](https://github.com/751K/sony-a7m5-looks/releases/tag/v2.0.0)）。`.cube` 文件不存放于仓库；本目录保留生成记录 [`manifest.json`](manifest.json) 和独立校验结果 [`validation.json`](validation.json)。

## 中灰

本 LUT 的中灰位置与常规 S-Log3 LUT 不同：

- **输入**：按测光 +1⅔ 档（相机显示 +1.7）拍摄的素材设计，18% 灰的 S-Log3 码值为 547 / 1023；常规 LUT 按测光 0 设计，为 420 / 1023。素材的实际曝光不同时，应在 LUT 之前用曝光调整补偿，例如实际为 +1 档时，提亮约 0.67 档。
- **输出**：中灰按照片的影调放置，18% 灰的输出码值为 0.607，高于常规视频 LUT 的约 0.40，高光余量相应较少。

## 文件

| 文件名包含 | 输入 |
| --- | --- |
| `SLog3_SGamut3_` | S-Log3 / S-Gamut3 |
| `SLog3_SGamut3Cine_` | S-Log3 / S-Gamut3.Cine |

外观代号与相机的 Creative Look 一致：ST、PT、NT、VV、VV2、FL、IN、SH、BW、Sepia（相机上为 SE）、FL2、FL3。IN、SH、FL2、FL3 使用相机默认的 Fade，分别为 3、6、1、1。

## 在 DaVinci Resolve 中使用

在 DaVinci YRGB 项目（不启用色彩管理）中，将 LUT 加在接收 S-Log3 素材的节点上，曝光和白平衡调整置于其前。LUT 已包含 Log 解码和显示输出，同一路径上不应再叠加 Log 至 Rec.709 或 ACES 输出转换。

LUT 的输入为 `10-bit CV / 1023` 的 S-Log3 码值，输出为 Rec.709 / Gamma 2.4 码值。时间线与输出色彩空间设为 Rec.709 Gamma 2.4；若在 Mac 上剪辑且成片主要在 Mac 或网络上播放，输出可选 Rec.709-A，该选项只改变文件标签，不改变码值。插值方式选择 Tetrahedral（四面体）。

生成原理、测量数据与局限见 [docs/video.md](../../docs/video.md)。
