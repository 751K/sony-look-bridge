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
| DxO PhotoLab Elite | DCP + `.cube` | 64³ CUBE | 底座 DCP 后接 LUT Grading，LUT 色彩空间选 ProPhoto RGB |

SonyA7M5 的三套配置位于 `profiles/`。多机型配置由
`camera_packs/build_packs.py` 为每款机型生成一个 ZIP，ZIP 内包含三种宿主
格式及动态生成的安装说明。

### 生成命令

```bash
python3 capture_one/c1_look_profile.py /path/to/A7M5.ARW
python3 camera_raw/acr_look.py /path/to/A7M5.ARW --write
python3 dxo/dxo_look.py /path/to/A7M5.ARW --write
python3 camera_packs/build_packs.py SAMPLES_DIR OUTPUT_DIR
```

所有命令都从仓库根目录执行。生成器需要本机安装对应版本的 Imaging Edge
Edit，以读取外观常量表；需要生成其他机型包时，还需要对应 ARW 与 Adobe
Standard DCP。

## 验证与测量

当前 README 对照图使用 DSC03591 的 ST 外观，以 Sony Edit 导出为参考。
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

1. 用探针配置测量合成色卡的实际输入值。
2. Capture One：生成 Probe，导出后用 `measure_chart.py` 测量，
   `fit_c1_encoding.py` 拟合并更新 `c1_encoding_table.json`。
3. Camera Raw：生成 Probe，导出 16 位 ProPhoto，关闭镜头校正，使用
   `measure_acr_chart.py` 和 `acr_encoding.py`。
4. DxO：用 `dxo_profiles.py probes` 和 `base2` 生成探针与底座，按同样方法
   检验 `dxo_model.py`。
5. 重新生成三种宿主配置，并用实拍 RAW 与 Edit 导出做几何配准和色差检查。

合成色卡可通过以下命令从自己的 A7M5 RAW 重建：

```bash
python3 capture_one/make_chart.py SOURCE.ARW
```

## 限制

- 当前公开验证主要集中在 A7M5 的 ST、FL2 和 FL3。
- 其他机型沿用 A7M5 的软件输入校准；相机矩阵和高光模型使用各自样片更新。
- 各机型包统一使用日光 RGB2YCC 权重，在暖光下与相机按拍摄白平衡混合的结果
  可能不同。
- Camera Raw 自身的自适应高光压缩和宿主去马赛克无法由固定 RGBTable 完全消除。
