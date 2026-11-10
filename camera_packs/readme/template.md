# {{title}} Creative Looks

{{intro}}

{{looks}}

外观的色彩参数统一采用日光白平衡下的取值（RGB2YCC 混合权重 `0 1024 0 0`），不随照片的白平衡变化。Sony Imaging Edge Edit 会根据每张照片拍摄时的白平衡混合暖光与日光两组参数，因此暖光环境下拍摄的照片可能产生色彩差异。

## Capture One

将 Capture One 包内的 ICC 配置文件复制至 `~/Library/ColorSync/Profiles/`，随后重新启动 Capture One。在「基本特性」中将配置文件设为 `{{prefix}} Look XX`，并将曲线设为 **Linear Response**。

## Adobe Camera Raw / Lightroom

将 DCP 复制至 `~/Library/Application Support/Adobe/CameraRaw/CameraProfiles/`，并将 XMP 复制至 `~/Library/Application Support/Adobe/CameraRaw/Settings/`。重新启动应用，并在配置文件浏览器的 **{{group}}** 分组中选择外观。

## DxO PhotoLab Elite

将 DCP 和 CUBE 保存至固定目录，并应用 **6 – No correction** 预设。在 **Color/B&W Rendering** 中导入 `{{prefix}} Linear Base v2.dcp`，将 **DCP Curve** 设为 **Adobe**、强度设为 100、饱和色保护设为 0，并关闭自动模式。在 **LUT Grading** 中导入 CUBE，将色彩空间设为 **ProPhoto RGB**、强度设为 100。

## 验证范围

{{validation}}

