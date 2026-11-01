#!/usr/bin/env python3
"""从 signs/signs.json 生成页面需要的 signs/signs.js，并更新 README 里的统计表。

    python3 tools/build.py

只用到 Python 标准库。页面用 <script src="signs/signs.js"> 读数据，
这样直接双击打开 index.html（file://）也能用，不需要起服务器。
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
MARK = "<!--drawn-->"


def main():
    with open(os.path.join(ROOT, "signs", "signs.json"), encoding="utf-8") as f:
        data = json.load(f)

    img_dir = os.path.join(ROOT, "signs", "img")
    ids = set()
    for s in data["signs"]:
        sid = s["id"]
        if sid in ids:
            raise SystemExit(f"重复的 id: {sid}")
        ids.add(sid)
        path = os.path.join(img_dir, sid + ".svg")
        if not os.path.exists(path):
            raise SystemExit(f"缺少图片: signs/img/{sid}.svg")
        with open(path, encoding="utf-8") as f:
            s["drawn"] = f.read().rstrip().endswith(MARK)
        s["img"] = f"signs/img/{sid}.svg"
        s.setdefault("core", False)
        s.setdefault("nr", "")

    extra = sorted(f[:-4] for f in os.listdir(img_dir) if f.endswith(".svg") and f[:-4] not in ids)
    if extra:
        print("提示：这些图片没有对应的数据条目，不会显示：", ", ".join(extra))

    out = os.path.join(ROOT, "signs", "signs.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("// 由 tools/build.py 从 signs/signs.json 生成，不要手改。\n")
        f.write("window.SIGN_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    # README 统计表
    cats = data["categories"]
    rows = ["| 类别 | 数量 | 其中考试重点 |", "|---|---:|---:|"]
    for key, c in cats.items():
        items = [s for s in data["signs"] if s["cat"] == key]
        rows.append(f"| {c['zh']}（{c['de']}） | {len(items)} | {sum(1 for s in items if s['core'])} |")
    total = len(data["signs"])
    core = sum(1 for s in data["signs"] if s["core"])
    drawn = sum(1 for s in data["signs"] if s["drawn"])
    rows.append(f"| **合计** | **{total}** | **{core}** |")
    table = "\n".join(rows) + f"\n\n{total} 个标志里 {total - drawn} 个用官方图，{drawn} 个是脚本画的示意图。"

    readme = os.path.join(ROOT, "README.md")
    if os.path.exists(readme):
        with open(readme, encoding="utf-8") as f:
            text = f.read()
        new = re.sub(r"<!-- stats:start -->.*?<!-- stats:end -->", lambda m: "<!-- stats:start -->\n" + table + "\n<!-- stats:end -->", text, flags=re.S)
        if new != text:
            with open(readme, "w", encoding="utf-8") as f:
                f.write(new)

    print(f"写入 signs/signs.js：{total} 个标志，{core} 个重点，{drawn} 个自绘")


if __name__ == "__main__":
    main()
