# {{title}} Creative Looks

{{intro}}

{{looks}}

相机按拍摄时的白平衡在暖光与日光两组色彩参数之间过渡。每个外观因此提供两个版本：名称不带后缀的为日光版（RGB2YCC 混合权重 `0 1024 0 0`），名称以 Warm 结尾的为暖光版（`1024 0 0 0`）。BW 在两种权重下结果相同，只提供一个版本。

以 α7 V 为例，白平衡色温约 3700K 以下时相机完全采用暖光参数，约 5400K 以上时完全采用日光参数，其间按色温混合。因此，约 3700K 以下拍摄的照片宜使用暖光版，约 5400K 以上的宜使用日光版，介于两者之间时按画面选择。各机型的过渡区间略有差异，α7 IV 约为 4100K 至 5200K。荧光灯等偏绿光源下，相机还会混入第三组参数，两种版本均不包含该组参数。

## Capture One

将 Capture One 包内的 ICC 配置文件复制至 `~/Library/ColorSync/Profiles/`，随后重新启动 Capture One。在「基本特性」中将配置文件设为 `{{prefix}} Look XX` 或 `{{prefix}} Look XX Warm`，并将曲线设为 **Linear Response**。

## Adobe Camera Raw / Lightroom

将 DCP 复制至 `~/Library/Application Support/Adobe/CameraRaw/CameraProfiles/`，并将 XMP 复制至 `~/Library/Application Support/Adobe/CameraRaw/Settings/`。重新启动应用，并在配置文件浏览器的 **{{group}}** 分组中选择外观。

## DxO PhotoLab Elite

将 DCP 和 CUBE 保存至固定目录，并应用 **6 – No correction** 预设。在 **Color/B&W Rendering** 中导入 `{{prefix}} Linear Base v2.dcp`，将 **DCP Curve** 设为 **Adobe**、强度设为 100、饱和色保护设为 0，并关闭自动模式。在 **LUT Grading** 中导入 CUBE，将色彩空间设为 **ProPhoto RGB**、强度设为 100。

## 验证范围

{{validation}}

