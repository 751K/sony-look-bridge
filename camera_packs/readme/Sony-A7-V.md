# Sony α7 V Creative Looks

适用机型为 Sony α7 V（ILCE-7M5）。本包汇集项目现有的 Capture One、Adobe Camera Raw / Lightroom 和 DxO PhotoLab 配置，含 ST、VV、NT、PT、FL、VV2、IN、SH、BW、SE、FL2 和 FL3。

外观的色彩参数统一采用日光白平衡下的取值（RGB2YCC 混合权重 `0 1024 0 0`），不随照片的白平衡变化。Sony Imaging Edge Edit 会按每张照片拍摄时的白平衡混合暖光与日光两组参数，因此在暖光下拍摄的照片，两者的色彩会有差别。

## Capture One

把 ICC 复制到 `~/Library/ColorSync/Profiles/`，重启应用。ICC Profile 选择对应的 `SonyA7M5 Look XX`，Curve 选择 **Linear Response**。

## Adobe Camera Raw / Lightroom

把 DCP 复制到 `~/Library/Application Support/Adobe/CameraRaw/CameraProfiles/`，把 XMP 复制到 `~/Library/Application Support/Adobe/CameraRaw/Settings/`。重启应用，在配置文件浏览器的 **Sony A7M5** 分组选取外观。

## DxO PhotoLab Elite

把 DCP 和 CUBE 放在固定位置。从 **6 – No correction** 预设开始，在 **Color/B&W Rendering** 中导入 `SonyA7M5 Linear Base v2.dcp`。DCP Curve 选择 **Adobe**，强度 100，Protect Saturated Colors 设为 0 并关闭自动模式。在 **LUT Grading** 导入 CUBE，选择 **ProPhoto RGB**，强度 100。

## 验证范围

ST、FL2、FL3 已有 Capture One / Camera Raw 和 Sony Edit 的导出对照。其余外观使用同一处理链。DxO 的 v1.2.1 高光调整已有离线预测，软件内重新导出待验证。默认 Fade 为 IN 3、SH 6、FL2 1、FL3 1。详细测量见项目 README。
