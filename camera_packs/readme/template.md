# {{title}} Creative Looks

{{intro}}

{{looks}}

外观的色彩参数统一采用日光白平衡下的取值（RGB2YCC 混合权重 `0 1024 0 0`），不随照片的白平衡变化。Sony Imaging Edge Edit 会按每张照片拍摄时的白平衡混合暖光与日光两组参数，因此在暖光下拍摄的照片，两者的色彩会有差别。

## Capture One

把 `Capture One` 内的 ICC 复制到 `~/Library/ColorSync/Profiles/`，重启 Capture One。在「基本特性」选择 `{{prefix}} Look XX`，曲线设为 **Linear Response**。

## Adobe Camera Raw / Lightroom

把 DCP 复制到 `~/Library/Application Support/Adobe/CameraRaw/CameraProfiles/`，把 XMP 复制到 `~/Library/Application Support/Adobe/CameraRaw/Settings/`。重启应用，在配置文件浏览器的 **{{group}}** 分组选取外观。

## DxO PhotoLab Elite

把 DCP 和 CUBE 放在固定位置，从 **6 – No correction** 预设开始。在 **Color/B&W Rendering** 中导入 `{{prefix}} Linear Base v2.dcp`，将 **DCP Curve** 设为 **Adobe**、强度设为 100、饱和色保护设为 0 并关闭自动模式。在 **LUT Grading** 中导入 CUBE，选择 **ProPhoto RGB**，强度设为 100。

## 验证范围

{{validation}}

