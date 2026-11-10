# α7 V Creative Look 视频 LUT

本 LUT 用于使 S-Log3 视频呈现与 α7 V 照片 Creative Look 一致的色调。共包含 12 种外观 × 2 种输入色域，计 24 个 65³ `.cube`，输出为 Rec.709 / Gamma 2.4。

**下载**：[Sony-A7-V-SLog3-Video-LUTs.zip](https://github.com/751K/sony-look-bridge/releases/download/v2.0.0/Sony-A7-V-SLog3-Video-LUTs.zip)（[v2.0.0 发布页](https://github.com/751K/sony-look-bridge/releases/tag/v2.0.0)）。`.cube` 文件不存放于仓库；本目录保留生成记录 [`manifest.json`](manifest.json) 和独立校验结果 [`validation.json`](validation.json)。

## 中灰

默认 LUT 以测光 **+1⅔ 档**（相机显示 +1.7）的 S-Log3 素材为输入。18% 灰对应约 547 / 1023；测光为 0 时对应 420 / 1023。素材曝光不同时，应在 LUT 之前调整曝光；例如素材实际为 +1 档时，需提亮约 0.67 档。

**输出亮度随外观变化**：ST 的 18% 灰约为 0.607，FL、FL2、FL3 分别约为 0.749、0.714、0.705；Sepia 的三个通道数值不同。以上数值均为归一化 Gamma 2.4 码值。Sony LC-709TypeA 的同一灰阶约为 0.40；本 LUT 的中灰亮度更高，ST 白点约位于中灰以上 3 档。其他曝光约定可通过生成器的 `--exposure` 参数生成，详见[生成说明](../../docs/video.md#生成与验证)。

## 文件

| 文件名包含 | 输入 |
| --- | --- |
| `SLog3_SGamut3_` | S-Log3 / S-Gamut3 |
| `SLog3_SGamut3Cine_` | S-Log3 / S-Gamut3.Cine |

外观代号与相机的 Creative Look 一致：ST、PT、NT、VV、VV2、FL、IN、SH、BW、Sepia（相机上为 SE）、FL2、FL3。IN、SH、FL2、FL3 使用相机默认的 Fade，分别为 3、6、1、1。

## DaVinci Resolve 使用方法

在 DaVinci YRGB 项目（不启用色彩管理）中，将 LUT 加在接收 S-Log3 素材的节点上，曝光和白平衡调整置于其前。LUT 已包含 Log 解码和显示输出，同一路径上不应再叠加 Log 至 Rec.709 或 ACES 输出转换。

LUT 的输入为 `10-bit CV / 1023` 的 S-Log3 码值，输出为 Rec.709 / Gamma 2.4 码值。时间线与输出色彩空间设为 Rec.709 Gamma 2.4，插值方式选择 Tetrahedral（四面体）。

生成原理、测量数据与局限见 [docs/video.md](../../docs/video.md)。
