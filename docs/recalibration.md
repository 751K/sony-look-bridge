# 软件输入重新标定

## 合成色卡

![合成色卡（Sony ST 外观渲染）](../chart/SonyChart_preview.png)

`chart/SonyChart.ARW` 是一张合法的 A7M5 ARW：

- raw 数据换成了 264 个已知线性值的色块：48 级灰阶，加上相机 RGB 的 6×6×6 立方体；
- 元数据（白平衡、黑电平、镜头等）保持原照片的值；
- 每个色块的 raw 值、Sony 线性值和位置见 `chart/SonyChart.json`。
### 重新标定（换软件版本时）

1. 合成色卡已经放在 `chart/` 里，可以直接用。也可以用 `python3 capture_one/make_chart.py SOURCE.ARW` 从自己的 A7M5 照片重新生成。
   - 内容是 48 级灰阶加 6³ 立方体，原 ARW 只读不改。
   - 每个色块按 Sony 前端增益反算写入，所以线性值精确已知。
   - 文件里三张内嵌 JPEG（缩略图、预览、全尺寸）也换成了色卡的 ST 外观渲染。
2. **Capture One**：
   - 运行 `c1_look_profile.py --probes`，安装生成的探针配置；
   - 用 Probe 导出色卡，运行 `measure_chart.py` 测量，再运行 `fit_c1_encoding.py` 拟合；
   - 用 Probe-Sq / Probe-Mono 检查 ICC 之后还有没有处理。
3. **Camera Raw**：
   - 运行 `acr_profiles.py probes`，安装生成的探针配置；
   - 用 Probe 导出色卡（16 位 ProPhoto，关闭镜头校正），运行 `measure_acr_chart.py` 测量，再运行 `acr_encoding.py` 拟合。
4. **DxO PhotoLab**：
   - 运行 `dxo/dxo_profiles.py probes` 生成探针 LUT，`dxo/dxo_profiles.py base2` 生成底座 DCP；
   - 用 Probe 导出色卡（16 位 TIFF、ProPhoto RGB、不勾 Preserve color details），运行 `measure_acr_chart.py` 测量；
   - 用测量结果检验 `dxo/dxo_model.py` 里的模型。
5. 照片对比：`compare_c1_export.py` / `compare_acr_export.py EXPORT.tif EDIT.tif`；拼对照图用 `compare_figure.py`。
