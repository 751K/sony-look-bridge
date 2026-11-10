# S-Log3 Creative Look 视频 LUT

本页记录 α7 V 视频 LUT 的颜色桥接、标定和生成。下载、曝光约定和 DaVinci Resolve 使用步骤见[视频 LUT 使用说明](../profiles/video/README.md)。

## 处理流程

目标为将照片 Creative Look 的逐像素颜色与影调应用于 S-Log3 视频。12 种外观分别生成 S-Gamut3 和 S-Gamut3.Cine 输入版本，输出 Rec.709 / Gamma 2.4。

```text
S-Log3 / S-Gamut3(.Cine)
  → 线性 ACES2065-1（AP0）
  → 实测矩阵：线性 S-Gamut3.Cine → 白平衡后的相机 RGB
  → 曝光调整 → 负值向灰轴收缩 → 高光压缩 → Sony 原生刻度
  → 照片外观链：SSCS → LM16 → MainGamma → RGB2YCC → … → YGamma
  → sRGB 解码 → Gamma 2.4 编码
```

S-Log3 反函数、色域转换和 CAT02 白点适配对应 [Sony 的 ACES 转换代码](https://github.com/aces-aswf/aces-input-and-colorspaces/blob/main/sony/CSC.Sony.SLog3_SGamut3Cine_to_ACES.ctl)；[Sony 的说明](https://github.com/aces-aswf/aces-input-and-colorspaces/blob/main/sony/README.md)分别列出了两种输入色域。通过 ACES 接入矩阵与直接进行色域转换在数学上等价。

照片外观链接收白平衡后的相机 RGB，详见[照片管线](pipeline.md)。视频桥接采用同一机位下照片与视频的实测颜色关系，使视频进入该外观链。矩阵按灰轴归一化；屏幕色块及夜景的实测条件和结果见下文。

## 标定方法

标定工具生成屏幕色块页，并从同一画面的 RAW 和 S-Log3 视频中读取色块：

```sh
python3 video/sensor_calibration.py chart
python3 video/sensor_calibration.py fit PHOTO.ARW CLIP.MP4 --out sensor_matrix.json
```

色块页是 144 个 display-P3 色块：16 级灰阶、128 个不同亮度和饱和度的彩色色块，四角是定位块。拍摄时使用固定机位、手动白平衡、光圈和快门，不改变屏幕亮度；在暗室拍摄，关闭原彩显示、夜览和自动亮度，不使用 ND / VND，略微失焦以避免摩尔纹。ISO、快门或光圈不同时，记录参数供曝光刻度换算。

照片端通过 `front_end_sony` 取得白平衡后的相机 RGB；视频端取前 1 秒的帧平均并解码 S-Log3。程序根据四角定位块对齐，以每个色块中央 7×7 个采样点的中位数拟合，剔除过曝和过暗的色块。拟合矩阵分解为 `s · diag(wb) · N`：

- `N`：灰轴归一化后的颜色关系，满足 `N·1 = 1`；
- `wb`：两次拍摄之间的白平衡差异，不纳入 LUT；
- `s`：单次照片与视频配对的曝光比例，以 Sony 原生值 / 16384 为单位。

屏幕色块用于比较同一场景在照片和视频两条路径中的读数；不同光源和实际场景的表现可另行验证。

## 当前标定结果

### 颜色关系

色块数据来自 DSC06651（ISO 100、1/13 秒、f/4），以及同一机位的 C2687（ISO 2500、1/120 秒、f/4、5000K）和 C2688（ISO 800、1/128 秒、f/4、6000K）。视频拍摄参数读取自 XAVC 的 rtmd 元数据。结果见[标定文件](../video/calibration/A7M5_SGamut3Cine_sensor_matrix.json)。

| 拟合素材 | 可用色块 | 拟合相对误差：平均 / p95 |
| --- | --- | --- |
| DSC06651 / C2687（当前矩阵来源） | 142 / 144 | 0.49% / 1.3% |
| DSC06651 / C2688 | 142 / 144 | 0.82% / 2.9% |

```text
N (S-Gamut3.Cine → 相机 RGB) =
[[ 0.9458  0.0562 -0.0020]
 [ 0.0231  0.9133  0.0635]
 [-0.0284  0.2483  0.7801]]
```

两段视频在不同白平衡下分别拟合，结果记录于标定文件；上表误差是各自参与拟合色块的误差。当前 LUT 使用 C2687 的矩阵。

### 曝光刻度

下表按记录的标称 ISO、快门和光圈，将四组配对换算到相同拍摄条件：

| 配对 | 视频相对照片的进光量 | 换算后的 Sony 刻度 |
| --- | --- | --- |
| DSC06651 / C2688（色块图） | −0.30 档 | 5450 |
| DSC06651 / C2687（色块图） | +1.44 档 | 5239 |
| DSC06654 / C2689（夜景） | +1.32 档 | 4960 |
| DSC06654 / C2690（夜景） | −0.65 档 | 5175 |

四组几何平均为 **5203**：在上述换算约定下，S-Log3 场景线性值 1 对应 Sony 原生值 5203，0.18 对应约 937。四组刻度的极差为 0.14 档，标准差为 0.056 档。同批视频实测亮度差与拍摄参数推算相差 0.05–0.06 档。夜景 C2689 经曝光补偿后，中位显示亮度为 0.0200，照片 ST 为 0.0196。

`fit` 输出的 `exposure_scale` 表示单次配对的比例；生成器的 `sony_scale` 表示采用的 Sony 原生刻度。当前标定文件提供 `sony_scale = 5203.2`；可通过生成器的 `--sony-scale` 为新的拟合文件指定所需刻度。`--exposure` 控制 LUT 输入的曝光补偿，与标定刻度属于不同参数。

## 生成与验证

所需环境包括根目录 `requirements.txt` 中的依赖、本机安装的 Imaging Edge Edit 和一张 α7 V ARW。色块拟合需要 `ffmpeg` / `ffprobe`；独立验证脚本还需要 `colour-science`：

```sh
python3 -m pip install colour-science
python3 video/video_look.py /path/to/A7M5.ARW --write --eval --out DIR
python3 video/validate_luts.py DIR
python3 -m unittest discover -s video -p 'test_*.py' -v
```

| 参数 | 作用 |
| --- | --- |
| `--looks ST,FL2` | 选择外观；默认全部 12 种 |
| `--gamuts SGamut3,SGamut3Cine` | 选择输入色域 |
| `--exposure -1.667` | LUT 输入曝光补偿；默认按素材测光 +1⅔ 档设计 |
| `--sensor-matrix PATH` | 指定标定 JSON |
| `--sony-scale VALUE` | 指定照片端 Sony 原生刻度 |
| `--grid 65`、`--out DIR` | 设置网格和输出目录 |

生成器使用 ARW 中的外观参数和 SSCS 参数。高光压缩在曝光补偿后、相机 RGB 的最大通道超过 0.9 时开始，三个通道按同一比例缩放。

当前 65³ LUT 相对直接计算的四面体插值误差，12 种外观 MAE 为 0.10–0.23、p99 为 0.39–2.12，单位为 8 位输出码值。灰阶检查要求各通道单调递增；Sepia 检查显示亮度并允许 1e-4 舍入误差。`validate_luts.py` 记录独立插值、ACES 矩阵及两种输入色域的对照结果；`manifest.json` 记录生成参数。单元测试还覆盖 Log 码值、白点、高光压缩、文件顺序和合成色块图拟合。

## 场景验证

- 色块矩阵来自约 6500K 的显示器光源。夜景含 LED 和暖色路灯，白平衡 3000K；该场景以低饱和色为主。
- 曝光不足的夜景视频曾出现比照片更低的饱和度，低信号中的噪声和光晕可能参与其中。
- 土耳其瀑布素材 C1620 按 +1⅔ 档补偿渲染后，与相邻 ST 照片的观感接近。该组照片与视频的 VND 档位不同，用于方向检查。
- 色彩丰富的自然日光场景尚未定量验证。雾天配对素材适合检查灰雾、低饱和颜色及影调；饱和颜色可用其他日光素材补充。
- LUT 是逐像素颜色与影调变换，锐度、清晰度和 DRO 等空间处理由宿主软件完成。
