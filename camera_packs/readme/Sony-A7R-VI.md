# Sony α7R VI Creative Looks

适用机型为 Sony α7R VI（ILCE-7RM6）。配置使用 [RawDB 全画幅无损 ARW](https://rawdb.dnglab.org/sets/Sony/ILCE-7RM6) 中的 12 种原生 Creative Look 参数和 SSCS 阈值生成，目标为 Sony 的 sRGB 色彩和色调。

包含 ST、VV、NT、PT、FL、VV2、IN、SH、BW、SE、FL2 和 FL3。

外观的色彩参数统一采用日光白平衡下的取值（RGB2YCC 混合权重 `0 1024 0 0`），不随照片的白平衡变化。Sony Imaging Edge Edit 会按每张照片拍摄时的白平衡混合暖光与日光两组参数，因此在暖光下拍摄的照片，两者的色彩会有差别。

## Capture One

把 `Capture One` 内的 ICC 复制到 `~/Library/ColorSync/Profiles/`，重启 Capture One。在「基本特性」选取对应的 `SonyA7RM6 Look XX`，曲线设为 **Linear Response**。

## Adobe Camera Raw / Lightroom

把 DCP 复制到 `~/Library/Application Support/Adobe/CameraRaw/CameraProfiles/`，把 XMP 复制到 `~/Library/Application Support/Adobe/CameraRaw/Settings/`。重启应用，在配置文件浏览器的 **Sony A7R VI** 分组选取外观。

## DxO PhotoLab Elite

把 DCP 和 CUBE 放在固定位置，从 **6 – No correction** 预设开始。在 **Color/B&W Rendering** 中导入 `SonyA7RM6 Linear Base v2.dcp`，将 **DCP Curve** 设为 **Adobe**、强度设为 100，**Protect Saturated Colors** 设为 0 并关闭自动模式。在 **LUT Grading** 中导入对应的 CUBE，色彩空间设为 **ProPhoto RGB**，强度设为 100。

## 验证范围

已核对样张 SHA-256、配置结构和机型标识。两个 DCP 使用 α7R VI 的 Adobe Standard 色彩矩阵，DxO 的高光模型使用这张 RAW 的拍摄白平衡系数。Capture One、Camera Raw / Lightroom、DxO 的输入响应沿用 α7 V 的实测模型。IN、SH、FL2、FL3 的褪色量沿用 α7 V 的默认值 3、6、1、1。软件内的导入效果和相对 Imaging Edge Edit 的成片色差待实测。
