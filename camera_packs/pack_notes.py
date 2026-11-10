"""Render the per-camera installation note included in each release ZIP."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE / "readme" / "cameras.json"
TEMPLATE = HERE / "readme" / "template.md"

NATIVE_10 = "ST、VV、NT、PT、FL、VV2、IN、SH、BW、SE"
NATIVE_12 = f"{NATIVE_10}、FL2、FL3"

DEFAULT_VALIDATION = (
    "已核对样张校验值、配置文件和机型标识。两个 DCP 使用本机型的 Adobe Standard 色彩矩阵，"
    "DxO 的高光模型使用样张的拍摄白平衡。软件输入响应和默认褪色量沿用 α7 V 模型。"
    "软件内导入和实拍色差待验证。"
)
SSCS_VALIDATION = (
    "样张的 SSCS 权重标签四项均为 255，生成时采用默认权重 32/64/32，"
    "高光色彩待用 Sony Edit 导出验证。"
)


def render_note(stem: str, model: str, prefix: str, group: str) -> str:
    """Return the Chinese installation note for one camera."""
    records = json.loads(NOTES.read_text(encoding="utf-8"))
    note = records[stem]
    title = note["title"]
    intro = note.get("intro") or (
        f"适用机型为 {title}（{model}）。配置使用公开 RAW 样张中提取的外观参数，"
        "目标为 Sony 的 sRGB 颜色和影调。"
    )
    looks = note.get("looks")
    if looks is None:
        looks = f"原生外观包括 {NATIVE_12 if note['native_fl2_fl3'] else NATIVE_10}。"
        source = note.get("source")
        if source:
            looks += f"样张以 CC0-1.0 提供。[样张来源]({source})"
        if not note["native_fl2_fl3"]:
            looks += (
                "\n\n另附从 α7 V 移植的 FL2 和 FL3，采用 Adobe D65 Forward Matrix "
                "换算相机 RGB，褪色量设为 1。"
            )
    validation = note.get("validation", DEFAULT_VALIDATION)
    if note.get("sscs_warning"):
        validation += "\n\n" + SSCS_VALIDATION
    values = {
        "title": title,
        "intro": intro,
        "looks": looks,
        "prefix": prefix,
        "group": group,
        "validation": validation,
    }
    text = TEMPLATE.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text.rstrip() + "\n"

