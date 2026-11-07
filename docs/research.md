# 本地研究资料与验证索引

代码在 `sony-a7m5-looks/`，原始 RAW、宿主导出、实验脚本和验证报告在同级 `sony/`。目录如下：

```text
Code/
├── sony-a7m5-looks/          当前代码、生成配置、公开文档
└── sony/
    ├── DSC03591.ARW         A7M5 测试输入
    ├── Test/               其他测试素材
    └── analysis/
        ├── .venv/          本地研究 Python 环境
        ├── c1/             Capture One 标定和历史导出
        ├── acr/            Camera Raw 标定和历史导出
        ├── dxo/            PhotoLab 导出、预测和实验脚本
        ├── readme_update/  2026-10-25 完整解码链的重测结果
        ├── phantom_lut/   Phantom 视频 LUT 对照研究
        ├── dpreview/       A7M5 / A7 IV 影棚图和外观参数对比
        ├── reverse/        原始指令差分、解析、管线和 Viewer 研究
        └── _superseded_copies/  公开模块的旧副本，仅作历史对照
```

## 证据与脚本位置

下表路径相对 `sony/analysis/`。

| 内容 | 本地位置 | 对应公开文档 |
| --- | --- | --- |
| 0x780f 的 276 字节解包 | `reverse/decoder_verification/verify_decoder.py`、`verification.json` | [处理管线](pipeline.md) |
| 1024×18 色表构建，12 外观 × 6 控制组合 | `reverse/color_table_verification/verify_color_table.py`、`verification.json`、缓存 `.f32le` | [处理管线](pipeline.md) |
| 像素链、YCC 和各空间阶段 | `reverse/pixel_pipeline/verify_*.py`、`verification*.json`、`verify_*_report.json` | [处理管线](pipeline.md) |
| ToneCurve、ShadeCorrection | `reverse/pixel_pipeline/verify_tonecurve_shade.py`、`verify_tonecurve_shade_report.json` | [处理管线 §6](pipeline.md#6-后段) |
| Rust 的 Marble、参数复用、滑块与边界 | `reverse/pixel_pipeline/verify_marble_rust.py`、`verify_rust_config.py`、`verify_rust_sliders.py`、`verify_rust_bounds.py` | [Rust 内核](../rust/README.md) |
| 完整解码 ST / FL2 / FL3，2026-10-25 重测 | `readme_update/decode_looks.py`、`measure_results.py`、`results.json` | [历史测量](measurements.md#archived-validation-results) |
| Edit 参考图 | `reverse/reference/`；部分其他参考图在 `analysis/` 根目录 | [测量说明](measurements.md) |
| Edit 4.0 / 4.1 函数及常量地址对照 | `reverse/edit41_diff/` | [处理管线 §10.2](pipeline.md#102-edit-410003062) |
| AXR、Viewer 张量和 Dither | `reverse/sdm/`，包括 `axr_dev_findings.md`、`axr.py`、`dither.py` | [Viewer 技术笔记](sdm.md) |
| Phantom ARRI / Film LUT 灰阶和颜色响应 | `phantom_lut/README.md`、`results.json` | [视频 LUT 技术说明](video.md) |

视频的屏幕色块生成、照片/视频矩阵拟合代码和当前标定结果保存在本仓库的 `video/`，见[视频 LUT 技术说明](video.md)。

## 本地运行约定

研究环境 `analysis/.venv` 中的 `sony-a7m5-looks.pth` 指向本仓库的 `sonylook/`、`camera_raw/` 和 `capture_one/`。`_superseded_copies/` 保存旧版本。环境要求见[重新生成](../README.zh-CN.md#重新生成)。

从本仓库根目录查看现有证据：

```sh
SONY_RESEARCH=../sony
ls "$SONY_RESEARCH/analysis/reverse/pixel_pipeline"/verify_*.py
cat "$SONY_RESEARCH/analysis/reverse/pixel_pipeline/verify_tonecurve_shade_report.json"
```

色表验证器支持 `--cached`，直接与已保存的原始指令输出比较。部分早期脚本仍引用历史实现或会话临时路径，重跑时需调整导入和数据路径。
