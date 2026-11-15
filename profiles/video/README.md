# α7 V Creative Look 视频 LUT

这套 LUT 使 S-Log3 视频呈现与 α7 V 照片 Creative Look 一致的颜色和影调。共包含 12 种外观 × 2 种输入色域 × 3 种色温版本，计 72 个 65³ `.cube`，输出为 Rec.709 / Gamma 2.4；另附 24 个可按白平衡调节的 DaVinci Resolve DCTL。

**下载**：[Sony-A7-V-SLog3-Video-LUTs.zip](https://github.com/751K/sony-look-bridge/releases/download/v4.0.0/Sony-A7-V-SLog3-Video-LUTs.zip)（[v4.0.0 发布页](https://github.com/751K/sony-look-bridge/releases/tag/v4.0.0)）。LUT 文件不存放在仓库中；本目录保留生成记录 [`manifest.json`](manifest.json) 和独立校验结果 [`validation.json`](validation.json)。

## 选择文件

按素材的输入色域选择：

| 文件名包含 | 输入 |
| --- | --- |
| `SLog3_SGamut3_` | S-Log3 / S-Gamut3 |
| `SLog3_SGamut3Cine_` | S-Log3 / S-Gamut3.Cine |

按拍摄时的白平衡选择色温版本，介于两档之间时选较近的一档：

| 外观代号 | 版本 | 拍摄白平衡 |
| --- | --- | --- |
| `ST` | 日光 | 约 5400K 以上 |
| `ST-4200K` | 4200K | 约 3800K 至 5400K |
| `ST-Warm` | 暖光 | 约 3700K 以下 |

外观代号与相机一致：ST、PT、NT、VV、VV2、FL、IN、SH、BW、Sepia（相机上为 SE）、FL2、FL3。IN、SH、FL2、FL3 使用相机默认的褪色，分别为 3、6、1、1。

## 曝光

LUT 按测光 **+1⅔ 档**（相机显示 +1.7）的 S-Log3 素材设计，18% 灰对应约 547 / 1023；测光为 0 时为 420 / 1023。素材曝光不同时，应在 LUT 之前调整曝光，例如素材为 +1 档时需提亮约 0.67 档。

输出的中灰比常见的 S-Log3 LUT 更亮：ST 的 18% 灰约为 0.607，FL、FL2、FL3 分别约为 0.749、0.714、0.705（归一化 Gamma 2.4 码值），与照片一致；Sony LC-709TypeA 的同一灰阶约为 0.40。ST 的白点约在中灰以上 3 档，因此高光余量较少。

## 在 DaVinci Resolve 中使用

1. 使用 DaVinci YRGB 项目，不启用色彩管理；时间线与输出色彩空间设为 Rec.709 Gamma 2.4。
2. 在接收 S-Log3 素材的节点上加载 LUT，曝光和白平衡调整放在它之前。LUT 已包含 Log 解码和显示输出，同一路径上不要再叠加 Log 至 Rec.709 或 ACES 输出转换。
3. 插值方式选择 Tetrahedral（四面体）。

### 按白平衡调节的 DCTL

每种外观和输入色域各有一个 DCTL，文件名以 `_WB.dctl` 结尾。DCTL 读取同一文件夹中该外观的三套 LUT，按 **White Balance K** 滑块在三套之间连续过渡：3700K 及以下为暖光版，4640K 为 4200K 版，5470K 及以上为日光版。滑块应设为素材拍摄时相机的白平衡。

1. 将 DCTL 与 72 个 LUT 放在 Resolve LUT 目录下的同一个子文件夹中。macOS 的 LUT 目录为 `/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/`。
2. 重启 Resolve，或在 DCTL 列表中刷新。
3. 在节点上添加 ResolveFX「DCTL」，选择对应文件并设置 White Balance K。

原理、标定数据与局限见[视频 LUT](../../docs/video.md)。
