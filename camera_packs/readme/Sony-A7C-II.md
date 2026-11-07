# Sony α7C II Creative Looks

适用机型为 Sony α7C II（ILCE-7CM2）。配置使用 α7C II 样张 RAW 中的 10 种 Creative Look 参数和 SSCS 参数生成，目标为 Sony 的 sRGB 色彩和色调。

包含 α7C II 的 10 款原生外观（ST、VV、NT、PT、FL、VV2、IN、SH、BW、SE）以及移植的 FL2 和 FL3。

FL2 和 FL3 使用 α7 V 的外观参数，通过两台机身的 Adobe D65 Forward Matrix 换算白平衡后的相机 RGB。两款均使用 Fade 1。

外观的色彩参数统一采用日光白平衡下的取值（RGB2YCC 混合权重 `0 1024 0 0`），不随照片的白平衡变化。Sony Imaging Edge Edit 会按每张照片拍摄时的白平衡混合暖光与日光两组参数，因此在暖光下拍摄的照片，两者的色彩会有差别。

## Capture One

把 `Capture One` 内的 ICC 复制到 `~/Library/ColorSync/Profiles/`，重启 Capture One。在「基本特性」选取对应的 `SonyA7CM2 Look XX`，曲线设为 **Linear Response**。

## Adobe Camera Raw / Lightroom

把 DCP 复制到 `~/Library/Application Support/Adobe/CameraRaw/CameraProfiles/`，把 XMP 复制到 `~/Library/Application Support/Adobe/CameraRaw/Settings/`。重启应用，在配置文件浏览器的 **Sony A7C II** 分组选取外观。

## DxO PhotoLab Elite

把 DCP 和 CUBE 放在固定位置，从 **6 – No correction** 预设开始。在 **Color/B&W Rendering** 中导入 `SonyA7CM2 Linear Base v2.dcp`，将 **DCP Curve** 设为 **Adobe**、强度设为 100，**Protect Saturated Colors** 设为 0 并关闭自动模式。在 **LUT Grading** 中导入对应的 CUBE，色彩空间设为 **ProPhoto RGB**，强度设为 100。

## 验证范围

已检查文件结构和机型标识。各软件的输入响应沿用了 A7M5 项目的校准模型，DxO 的相机矩阵和本次样张白平衡系数已按 α7C II 更新。

已在 Camera Raw 18.7 中用一张 α7C II 夜景 RAW 验证 ST。与 Sony Edit 的原生 ST 导出相比，几何配准并缩小 8 倍后，全图 RGB 平均绝对误差为 1.58 个 8 位 sRGB 色阶，平坦高光为 2.09。

已在 Camera Raw 18.7 中用一张 α7C II 夜景 RAW 验证 FL2。与移植模型直接渲染的参考图相比，几何配准并缩小 8 倍后，全图 RGB 平均绝对误差为 0.65 个 8 位 sRGB 色阶，平坦高光为 0.47。这组对照衡量 ACR 对移植模型的还原程度。Capture One、DxO 和 ACR 其余外观尚未完成同样的实拍对照。
