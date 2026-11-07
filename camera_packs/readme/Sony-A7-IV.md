# Sony A7 IV Creative Looks

适用机型为 Sony A7 IV（ILCE-7M4）。配置使用公开 RAW 样张中提取的外观参数，目标为 Sony 的 sRGB 颜色和影调。

原生外观包括 ST、VV、NT、PT、FL、VV2、IN、SH、BW、SE。样张以 CC0-1.0 提供。[样张来源](https://raw.pixls.us/getfile.php/6929/nice/Sony%20-%20ILCE-7M4%20-%2014bit%20(4:3).ARW)

另附从 α7 V 移植的 FL2 和 FL3，采用 Adobe D65 Forward Matrix 换算相机 RGB，褪色量设为 1。

外观的色彩参数统一采用日光白平衡下的取值（RGB2YCC 混合权重 `0 1024 0 0`），不随照片的白平衡变化。Sony Imaging Edge Edit 会按每张照片拍摄时的白平衡混合暖光与日光两组参数，因此在暖光下拍摄的照片，两者的色彩会有差别。

## Capture One

把 `Capture One` 内的 ICC 复制到 `~/Library/ColorSync/Profiles/`，重启 Capture One。在「基本特性」选择 `SonyA7M4 Look XX`，曲线设为 **Linear Response**。

## Adobe Camera Raw / Lightroom

把 DCP 复制到 `~/Library/Application Support/Adobe/CameraRaw/CameraProfiles/`，把 XMP 复制到 `~/Library/Application Support/Adobe/CameraRaw/Settings/`。重启应用，在配置文件浏览器的 **Sony A7 IV** 分组选取外观。

## DxO PhotoLab Elite

把 DCP 和 CUBE 放在固定位置，从 **6 – No correction** 预设开始。在 **Color/B&W Rendering** 中导入 `SonyA7M4 Linear Base v2.dcp`，将 **DCP Curve** 设为 **Adobe**、强度设为 100、饱和色保护设为 0 并关闭自动模式。在 **LUT Grading** 中导入 CUBE，选择 **ProPhoto RGB**，强度设为 100。

## 验证范围

已核对样张校验值、配置文件和机型标识。两个 DCP 使用本机型的 Adobe Standard 色彩矩阵，DxO 的高光模型使用样张的拍摄白平衡。软件输入响应和默认褪色量沿用 α7 V 模型。软件内导入和实拍色差待验证。
