# Sony Creative Look → Capture One 输入配置

原始导出和实验脚本在本地 `sony/analysis/c1/`，见[研究资料索引](research.md)。安装步骤见[中文 README](../README.zh-CN.md)。

## 当前状态

当前配置为 65³ ICC，包含 SSCS，输入模型使用合成色卡测得的 `capture_one/c1_encoding_table.json`。当前 ST 成片对比见[测量说明](measurements.md#current-readme-figure)。下文保留 2026-10-16 的标定记录，当时尚未加入 SSCS，FL2/FL3 使用 Fade 0；当前配置使用 Fade 1。

## 原理

- C1 送进相机输入 ICC 的是**已白平衡、经内部编码 E 的相机 RGB**，输出要求是 Lab D50。三个通道共用同一条一维曲线，暗部近似线性、高光逐渐压缩。早期从自带配置灰轴推断出的 γ1.8 假设已被探针测量推翻。
- 每个网格节点的计算为：`v → E⁻¹(v) → Sony 线性相机 RGB → SSCS → 外观链 → sRGB → Lab D50`。E⁻¹ 在 log 域插值并按端点斜率外推。
- 外观链包含 LM16、MainGamma、RGB2YCC、AreaComp、ChromaSuppress、YGamma、YCC2RGB 和 BW/SE 的 Effect。映射使用相机默认褪色值：FL2/FL3 = 1、IN = 3、SH = 6，其他色彩滑块为 0。
- 在 C1 里选这个 ICC，并把曲线设为 **Linear Response**，显示出来的就是外观的 sRGB 结果。
- LM16 选色相时可先做水平 `[1 8 14 8 1]/32` 低通；LUT 使用像素自身的颜色。空间阶段不进入配置，见[处理管线](pipeline.md)。

## 文件

- `capture_one/c1_look_profile.py`：生成 12 种外观的 ICC，放在 `profiles/capture_one/SonyA7M5-Look-*.icc`。默认 65³ 网格、lut16，每通道 1025 点输入形状曲线 `s = √v`，用于加密暗部采样；它不是宿主编码 E。
- `capture_one/measure_chart.py`、`fit_c1_encoding.py`：色卡测量与输入模型拟合。
- `validate_profiles.py`、`reference/`、`curves/` 及照片编码旧表 `c1_encoding_table_photo.json` 在本地研究目录。

## 离线验证（DSC03591，scale 4，8 位单位 MAE）

以下为早期原型的离线结果，使用逐像素外观链。

| | ST | FL2 | FL3 |
| --- | --- | --- | --- |
| ICC 查表 vs 外观链直接渲染（插值误差） | 0.17 | 0.28 | 0.43 |
| ICC vs Imaging Edge 导出图 | 0.93 | 0.79 | 0.94 |
| 外观链 vs Imaging Edge（参考值） | 0.90 | 0.71 | 0.75 |

- 插值误差随网格大小的变化：33³ 时为 0.32 / 0.58 / 0.91，49³ 时 FL3 为 0.64。形状曲线的选择几乎没有影响。
- 用 LittleCMS（Pillow）能正常加载这些配置并建立变换。

## C1 实测与输入编码校准（2026-10-16）

**第一轮实测**：用户导出了两张 Adobe RGB 16 位 TIFF，"DSC03591 1" 为 ST，"DSC03591" 为 FL2。设置文件确认选的是 Look 配置 + Linear Response。
- 对齐方法：C1 没有像 Edit 那样做畸变校正和 1.9% 填充放大，两图之间差约 2% 缩放加平移。用梯度相位相关拟合仿射变换，残差 2.4 px（`compare_c1_export.py`）。
- 结果：ST 的 MAE 为 5.4，FL2 为 7.2；暗部和中间调偏暗 10–15 级，高光偏亮。
- 排除了 Adobe RGB → sRGB 转换的问题：手写转换与 LittleCMS 只差 0.3 级。

**探针校准**：
- `SonyA7M5-Probe.icc` 把输入 v 原样作为 sRGB 输出。用它导出的 "DSC03591 2.tif" 直接给出 C1 实际送进 ICC 的 v（`measure_c1_encoding.py`）。
- 测得：三个通道共用同一条曲线；暗部近似线性，v ≈ 线性/1950，往上逐渐压缩（log 斜率约 0.45–0.48）；v = 1 对应 Sony 线性 8171，与传感器饱和点 8183.6 吻合。原先 γ1.8 的假设在暗部高估了 3–5 倍。没有径向依赖，所以不是暗角补偿。
- 用这条曲线（`c1_encoding_table.json`）加上旧的 ST 配置去预测 C1 的 ST 导出图，误差 **0.85**（原假设下为 5.9），说明 C1 的处理就是 ICC(F(线性))，ICC 之后没有别的改动。FL2 的预测误差为 2.5，那张的导出设置可能不同。
- 配置已按 `线性 = F⁻¹(v)` 重新生成，并已覆盖安装到 `~/Library/ColorSync/Profiles`。离线预测新配置在 C1 中与 Edit 的差异：**ST 1.00、FL2 0.88、FL3 0.99**（8 位 MAE），与外观链本身对 Edit 的误差（0.90 / 0.71 / 0.75）相当。

## 合成色卡校准（2026-10-16）

**色卡 raw**（`make_chart.py` → `chart/SonyChart.ARW`）：
- 复制原始 ARW，把 140 个 512×512 的 LJ92 分块替换为色块：48 级灰阶 + 6×6×6 相机 RGB 立方体，共 264 个色块。
- 色块按 Sony 前端增益反算 raw 值，因此每个色块的线性值精确已知。
- `lj92.py` 编码器对原始分块的重新编码与原文件**逐字节相同**；色卡用 LibRaw 和 Sony 自己的解码器（模拟器）解出，都与设计值逐像素一致。

**四张导出**（全部 Linear Response；`measure_chart.py` 按色块质心配准，C1 导出的是 7244×4767 的更大区域；每块取中心 50% 的中位数，块内离散 ≤ 0.5 级）：
1. **Probe**：C1 送进 ICC 的 v 三通道共用同一条曲线，且每个通道只取决于自身的线性值。暗部严格线性（v ≈ 线性/1970），往上逐渐压缩。
2. **Probe-Sq = Probe²**（误差 0.04 级）：C1 原样输出 ICC 的结果，之后没有额外曲线。
3. **Probe-Mono = Probe 的亮度**（误差 0.02 级）：C1 不会额外加颜色。
4. **Look-ST**：导出结果 = ST 配置(Probe 测到的 v)，误差 0.18 级；**与 Sony 外观目标只差 0.30 级**。

所以 C1 的模型就是 `输出 = ICC(E(线性))`。之前照片测试中"新旧配置导出几乎相同"的现象无法用这个模型解释，可能是那几次导出时实际生效的配置或变体与预想的不同。

**最终配置**：编码表改用色卡测得的数据（`c1_encoding_table.json`；照片测得的旧表保存在 `c1_encoding_table_photo.json`）。预测在 C1 中与 Sony 外观目标的误差：ST 0.14、FL2 0.15、FL3 0.14、VV 0.13、BW 0.10（8 位 MAE）。

## 照片最终验证（2026-10-16）

用户重启 C1 后，用新的 Look-ST 导出了 DSC03591（`c1_test/final_ST_vs_edit.*`）。与 Edit 的 ST 相比（几何配准后 8 倍缩小）：

- **MAE 1.17**，p95 3.4，偏差 (+0.15, +0.63, +1.09)。之前的照片测试是 5.3。
- 各亮度段的偏差都在约 ±1 级以内，只有最暗段的蓝通道 +2.2。
- 参照：逐像素外观链对 Edit 是 0.90；后续完整解码器加入 ITP、锐化/Spica、Marble 后降至 **0.08**（8×，见[测量说明](measurements.md#archived-validation-results)）。

随后又用 FL、FL2、FL3 各导出一张（`c1_test/final_FL_vs_edit.json`）。文件名没有标明外观，按与各外观预测图的误差判定，每张都能明确对上（约 1.2 对 2.8–6.5）：

| 外观 | C1 vs Edit | 逐像素链 vs Edit | C1 vs 预测 |
| --- | --- | --- | --- |
| ST | 1.17 | 0.90 | 1.14 |
| FL | —（没有 Edit 参考图） | — | 1.14 |
| FL2 | **1.05** | 0.89 | 1.21 |
| FL3 | **1.21** | 1.00 | 1.27 |

表中的「逐像素链」只含颜色阶段，不含 ITP、锐化/Spica、Marble；完整解码器的参考值为 0.08，见 README。上表的 C1 导出早于 v1.1.0 的 SSCS。

**注意**：C1 会把用过的配置复制到会话的 `CaptureOne/Settings*/<文件>.<配置名>.icm`，而且重启前会一直使用内存中已加载的版本。更新配置后要重启 C1；必要时先切换到别的配置再切回来。

## C1 曲线文件（.fcrv）

- 位置：`Capture One.app/.../ImageProcessing.framework/Resources/FilmCurves/SonyA7M5-*.fcrv`。用 `parse_fcrv.py` 只读解析，结果在 `curves/SonyA7M5_fcrv.json`。
- 格式：小端；三段控制点曲线 A/B/C，坐标为无符号 0.32 定点数（0xffffffff = 1）。
- Film Standard / Auto / Extra Shadow / High Contrast：A 是 11 点胶片曲线，各不相同；B 是四个文件共用的一条曲线；C 是 4–6 点的近恒等曲线。
- **Linear Response 的 A/B/C 都是恒等 (0,0)–(1,1)**，曲线数据与其他相机的 Linear Scientific 相同，只有元数据不同。所以测得的输入编码 E 不在曲线文件里，而是 C1 内部固定的编码。E 也与曲线 B 不符（最大 log 误差 0.43）。
- 本项目只支持 Linear Response，不研究胶片曲线作用在 ICC 之前还是之后。

## 用法

1. 从仓库根目录运行 `python3 capture_one/c1_look_profile.py /path/to/A7M5.ARW`，把 `profiles/capture_one/SonyA7M5-Look-*.icc` 复制到 `~/Library/ColorSync/Profiles/`，然后重启 C1。
2. 在 Base Characteristics 中，ICC Profile 选 `SonyA7M5 Look XX`，Curve 选 **Linear Response**。
3. 曝光、白平衡等调整照常在 C1 里做。配置只替代 Sony 的外观色彩，不包含 DRO、锐化、降噪。
