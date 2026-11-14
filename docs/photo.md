# 照片外观、宿主配置与测量

本页汇总 Creative Look 的照片映射、Capture One / Camera Raw / DxO PhotoLab
输入模型、验证方法和重新标定流程。逐阶段实现和参数见[处理管线](pipeline.md)。

## 外观映射

Sony Creative Look 可以视为白平衡后的相机 RGB 到显示 sRGB 的逐像素映射
*f*。配置文件不直接保存 *f*，而是保存 `f ∘ E⁻¹`，其中 *E* 是宿主软件在
配置文件之前施加的内部输入编码：

```text
相机 RGB ── E ──▶ 配置文件 f ∘ E⁻¹ ──▶ f(相机 RGB)
```

外观链包含 SSCS、LinearMatrix16、MainGamma、RGB2YCC、AreaComp、
ChromaSuppress、YGamma、YCC2RGB，以及 BW / SE 的 Effect。锐化、降噪、
DRO 和 Marble 等空间阶段不进入宿主配置。

![相机 RGB 经 RAW 中性显影、Sony ST 和 FL2 后的颜色分布](../images/color_cube_zh_light.png)

配置文件使用相机默认外观参数。Fade 为 IN 3、SH 6、FL2 1、FL3 1，其他
外观滑块为 0。

## 宿主格式

| 宿主 | 文件 | 查找表 | 工作方式 |
| --- | --- | --- | --- |
| Capture One | ICC | 65³ A2B0 CLUT | 输入经 `c1_encoding_table.json` 的 *E*，输出 Lab D50；必须使用 Linear Response 曲线 |
| Camera Raw / Lightroom | DCP + XMP | XMP RGBTable 64³ | 线性底座 DCP 保持白平衡行为，XMP 保存 ProPhoto γ1.8 外观表 |
| DxO PhotoLab Elite | DCP + `.cube` | 64³ CUBE | 底座 DCP 后接 LUT Grading，LUT 色彩空间设为 ProPhoto RGB |

SonyA7M5 的三套配置位于 `profiles/`。多机型配置由
`camera_packs/build_packs.py` 为每款机型生成一个 ZIP，ZIP 内包含三种宿主
格式及动态生成的安装说明。

每个外观生成日光与暖光两个版本，分别采用 RGB2YCC 混合权重 `0 1024 0 0` 与
`1024 0 0 0`；A7M5 的暖光版同时采用暖光 LinearMatrix16 表。暖光版的文件名和
配置名称以 Warm 结尾。在两种权重下结果相同的外观（BW、α7 V 的 SE）只生成一个版本。权重、
暖光表与白平衡的关系见[照片管线 §4.1 与 §4.3](pipeline.md)。

### Camera Raw 自动版本

Camera Raw 的 XMP 配置只能保存一张外观表，但其引用的底座 DCP 可以带两个
标定光源；Camera Raw 按当前白平衡（以 mired 计）在两个光源的 HueSatMap
之间插值。自动版本 `Look XX Auto` 利用这一机制随白平衡过渡：

- 底座 `Auto Base XX.dcp` 的 ForwardMatrix 与线性底座相同，标定光源为 ISO
  摄影棚钨丝灯（3200K）和 D55（5500K）；ColorMatrix 由该机型 Adobe Standard
  的 StdA 与 D65 矩阵按 mired 插值到这两个色温，白平衡行为与 Adobe Standard
  一致。
- XMP 保存日光外观表，底座在 3200K 端的 HueSatMap 预先调整输入颜色，使结果
  等于暖光外观；5500K 端为恒等映射。
- FL2 的暖光外观能输出日光外观表无法达到的高饱和黄色，因此方向相反：XMP
  保存暖光外观表，5500K 端的 HueSatMap 将结果调整为日光外观。FL2 的
  HueSatMap 另含 16 级亮度轴，其余外观为 90×30 的色相、饱和度表。

HueSatMap 逐格拟合（色相偏移、饱和度和亮度缩放），目标为两种外观在 CIELAB
中的差异，由 `camera_raw/acr_auto.py` 生成。Capture One 与 DxO PhotoLab 没有
对应机制。

### 色卡验证

以 A7M5 在 2600K、4200K、6500K 三种光源下拍摄 ColorChecker Classic（自定义
白平衡，ISO 100，f/5.6，DRO 关闭），每种光源拍摄全部 12 种外观，将相机 HEIF
的 24 个色块与配置在同一 RAW 上的模拟渲染比较。相机在三种光源下的 RGB2YCC 权重
分别为 `1024 0 0 0`、`644 380 0 0` 和 `0 1024 0 0`；自动版本按 Camera Raw 由
拍摄白平衡计算的色温（2777K、4560K、6503K）混合 HueSatMap。十种彩色外观的
ΔE2000 平均值如下：

| 配置 | 2600K | 4200K | 6500K |
| --- | --- | --- | --- |
| 按拍摄参数解码 | 0.23–0.43 | 0.26–0.53 | 0.25–0.81 |
| 日光版 | 1.77–2.38 | 1.19–1.97 | 0.25–0.81 |
| 暖光版 | 0.23–0.43 | 0.83–1.20 | 1.88–2.64 |
| 自动版本 | 0.27–0.75 | 0.71–1.34 | 0.25–0.84 |

4200K 下自动版本的残差主要来自过渡位置：相机在该光源下取 63% 暖光权重，
而 Camera Raw 按 3200K 至 5500K 的 mired 插值只取 29%；按相机权重混合时为
0.35–0.97。BW 在三种光源下为 0.5–0.6，SE 为 0.47–0.52。

相机的 SE 与 Edit 不同：相机不使用 Sepia 外观的 RGB2YCC 偏移表，亮度与 BW 一致，
棕色调也与 0x74c5 记录的值不同（见 [pipeline.md](pipeline.md) §6.1）。按 Edit 的做法
解码时，SE 的偏差为 3.1–3.4。目前仅 α7 V 有实测数据，其他机型的 SE 仍按 Edit 生成。

### 生成环境

生成器需要 Python 3.11 或更高版本、`requirements.txt` 中列出的依赖、任意
一张 A7M5 ARW，以及本机安装的 Imaging Edge Edit 4.0.00.10312 或
4.1.00.03062（macOS）。一次性 LUT 缓存于 `~/.cache/sonylook`；
`SONYLOOK_CACHE=0` 可禁用缓存，`SONYLOOK_CACHE_DIR` 可修改缓存目录。

外观链使用的部分常量表（色相 atan 表、对比度曲线族等）在运行时从本机安装
的 Edit 中读取（`sonylook/edit_binary.py`）。本仓库不包含 Sony 二进制或
数据。脚本会校验 arm64 部分的 SHA-256；4.0 与 4.1 的表地址不同，
`edit_binary.py` 以 4.0 地址为基准建立版本映射。其他路径可通过
`SONY_EDIT_BINARY` 指定。

### 生成命令

```bash
python3 capture_one/c1_look_profile.py /path/to/A7M5.ARW
python3 camera_raw/acr_look.py /path/to/A7M5.ARW --write
python3 dxo/dxo_look.py /path/to/A7M5.ARW --write
python3 camera_packs/build_packs.py SAMPLES_DIR OUTPUT_DIR
```

所有命令都从仓库根目录执行。生成器需要本机安装对应版本的 Imaging Edge
Edit，以读取外观常量表；如需生成其他机型包，还需提供对应 ARW 与 Adobe
Standard DCP。

## 验证与测量

本仓库 README 中的当前对照图使用 DSC03591 的 ST 外观，并以 Sony Edit 导出为参考。
两张宿主图在共同有效区域上比较 CIELAB D65：

- 亮度误差：`abs(L*_host − L*_Edit)`
- 色度误差：`sqrt((a*_host − a*_Edit)² + (b*_host − b*_Edit)²)`

| 软件 | 平均亮度差 ΔL* | 平均色度差 Δab |
| --- | ---: | ---: |
| Capture One | 0.240811 | 0.577229 |
| Camera Raw | 0.444792 | 0.491203 |

详细导出哈希、几何配准和未取整结果记录在
`images/compare_ST.measurements.json`。

完整解码器对 Edit 的 8 位 RGB MAE：ST 0.08、FL2 0.08、FL3 0.09（8×
缩小）。宿主配置的早期实测分别为：ST Capture One 1.17、Camera Raw 1.27；
FL2 1.05 / 1.15；FL3 1.21 / 1.27。宿主自身的去马赛克、锐化和高光处理是
剩余误差的主要来源。

ST、FL2、FL3 有 Edit 参考图；其余外观使用同一套已验证代码和各自外观参数，
尚未逐项建立 Edit 对照。α7C II 额外在 Camera Raw 中验证过 ST 和 FL2。

## 重新标定

`chart/SonyChart.ARW` 是包含 48 级灰阶和 6³ 相机 RGB 色块的合法 A7M5
ARW。更换宿主软件版本或输入行为后，按以下顺序重新标定：

1. 使用探针配置测量合成色卡的实际输入值。
2. Capture One：生成 Probe，导出后用 `measure_chart.py` 测量，
   `fit_c1_encoding.py` 拟合并更新 `c1_encoding_table.json`。
3. Camera Raw：生成 Probe，导出 16 位 ProPhoto，关闭镜头校正，使用
   `measure_acr_chart.py` 和 `acr_encoding.py`。
4. DxO：用 `dxo_profiles.py probes` 和 `base2` 生成探针与底座，按同样方法
   检验 `dxo_model.py`。
5. 重新生成三种宿主配置，并使用实拍 RAW 与 Edit 导出进行几何配准和色差检查。

合成色卡可使用以下命令从 A7M5 RAW 重建：

```bash
python3 capture_one/make_chart.py SOURCE.ARW
```

## 限制

- 色卡验证覆盖 A7M5 的全部外观；其他机型只以样片参数生成，未经实拍验证。
- 其他机型沿用 A7M5 的软件输入校准；相机矩阵和高光模型使用各自样片更新。
- 其他机型尚无暖光 LinearMatrix16 表，其暖光版与自动版本只包含 RGB2YCC
  部分的变化，暖光下的准确度低于 A7M5。
- Capture One 与 DxO 配置只提供日光与暖光两种状态，不包含过渡色温下
  的混合；Camera Raw 自动版本按 3200K 至 5500K 过渡，与相机的过渡区间
  （A7M5 约 3700K 至 5400K）不完全相同。各配置均不包含荧光灯参数组，偏绿光源
  下结果可能与相机不同。
- Camera Raw 自身的自适应高光压缩和宿主去马赛克无法由固定 RGBTable 完全消除。
