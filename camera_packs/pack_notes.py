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


def render_note(stem: str, model: str, prefix: str, group: str, single=("BW",), fluor=False,
                cool=False) -> str:
    """Return the Chinese installation note for one camera.

    single: looks built without a Warm variant (they render the same at both weights).
    fluor: the pack has Fluor variants (fluorescent set).  cool: the camera raises the daylight weight
    above 1024 at high colour temperatures and the Auto bases are triple-illuminant.
    """
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
    values = {
        "cool": "本机型在约 5400K 以上还会逐步加强日光参数，约 6400K 时达到 1.32 倍（按 α7 IV 实测），"
                "日光版对应约 5400K 及以下的状态。" if cool else "",
        "fluor": "荧光灯等偏绿光源下，相机会改用第三组参数。本机型另提供名称以 Fluor 结尾的荧光灯版"
                 "（`0 0 1024 0`），适用于以荧光灯白平衡预设拍摄、或相机判定为荧光灯光源的照片；"
                 "三种软件均可使用，自动版本不包含该组参数。" if fluor else
                 "荧光灯等偏绿光源下，相机还会混入第三组参数，各版本均不包含该组参数。",
        "auto": "约 4300K 及以下与暖光版一致，约 5000K 前后与日光版一致，约 6100K 及以上与加强后的日光参数一致，"
                "其间平滑混合" if cool else
                "约 4150K 及以下与暖光版一致，约 5500K 及以上与日光版一致，其间平滑混合",
        "c1_names": (f"`{prefix} Look XX`、`{prefix} Look XX Warm` 或 `{prefix} Look XX Fluor`" if fluor
                     else f"`{prefix} Look XX` 或 `{prefix} Look XX Warm`"),
        "title": title,
        "intro": intro,
        "looks": looks,
        "prefix": prefix,
        "group": group,
        "validation": validation,
        "single": f"{single[0]} 在两种权重下结果相同，只提供一个版本。" if len(single) == 1
                  else f"{'、'.join(single[:-1])} 与 {single[-1]} 在两种权重下结果相同，各只提供一个版本。",
    }
    text = TEMPLATE.read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text.rstrip() + "\n"

