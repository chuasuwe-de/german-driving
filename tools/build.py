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

    # 规则卡片
    with open(os.path.join(ROOT, "rules", "rules.json"), encoding="utf-8") as f:
        rules = json.load(f)
    seen = set()
    for r in rules["rules"]:
        if r["id"] in seen:
            raise SystemExit(f"重复的规则 id: {r['id']}")
        seen.add(r["id"])
        if r["cat"] not in rules["categories"]:
            raise SystemExit(f"规则 {r['id']} 的类别 {r['cat']} 没有定义")
        if r.get("img") and not os.path.exists(os.path.join(img_dir, r["img"] + ".svg")):
            raise SystemExit(f"规则 {r['id']} 引用的图片不存在: {r['img']}")
    data["ruleCategories"] = rules["categories"]
    data["rules"] = rules["rules"]

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
    rrows = ["| 主题 | 卡片数 |", "|---|---:|"]
    for key, c in rules["categories"].items():
        rrows.append(f"| {c['zh']} | {sum(1 for r in rules['rules'] if r['cat'] == key)} |")
    rrows.append(f"| **合计** | **{len(rules['rules'])}** |")
    table += "\n\n规则卡片：\n\n" + "\n".join(rrows)

    readme = os.path.join(ROOT, "README.md")
    if os.path.exists(readme):
        with open(readme, encoding="utf-8") as f:
            text = f.read()
        new = re.sub(r"<!-- stats:start -->.*?<!-- stats:end -->", lambda m: "<!-- stats:start -->\n" + table + "\n<!-- stats:end -->", text, flags=re.S)
        if new != text:
            with open(readme, "w", encoding="utf-8") as f:
                f.write(new)

    # 单文件版 artifact.html：CSS、JS、数据和图全部内嵌，发布到 claude.ai 或随手发给别人用
    import base64
    one = json.loads(json.dumps(data))
    for s in one["signs"]:
        with open(os.path.join(img_dir, s["id"] + ".svg"), "rb") as f:
            s["img"] = "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode("ascii")
    with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f:
        html = f.read()
    with open(os.path.join(ROOT, "app.css"), encoding="utf-8") as f:
        css = f.read()
    with open(os.path.join(ROOT, "app.js"), encoding="utf-8") as f:
        js = f.read()
    blob = json.dumps(one, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    # 发布到 claude.ai 的版本不带 html/head/body 外壳（平台会套），title 和 style 放最前面
    body = html[html.index("<body>") + len("<body>"):html.index("</body>")]
    body = body.replace('<script src="signs/signs.js"></script>', "<script>window.SIGN_DATA = " + blob + ";</script>")
    body = body.replace('<script src="app.js"></script>', "<script>\n" + js.replace("</script", "<\\/script") + "\n</script>")
    frag = ('<title>德国路标自练</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
            "<style>\n" + css + "\n</style>" + body)
    with open(os.path.join(ROOT, "artifact.html"), "w", encoding="utf-8") as f:
        f.write(frag)
    # 单文件完整版，双击就能开
    full = html.replace('<link rel="stylesheet" href="app.css">', "<style>\n" + css + "\n</style>")
    full = full.replace('<script src="signs/signs.js"></script>', "<script>window.SIGN_DATA = " + blob + ";</script>")
    full = full.replace('<script src="app.js"></script>', "<script>\n" + js.replace("</script", "<\\/script") + "\n</script>")
    with open(os.path.join(ROOT, "standalone.html"), "w", encoding="utf-8") as f:
        f.write(full)

    print(f"写入 signs/signs.js：{total} 个标志，{core} 个重点，{drawn} 个自绘；{len(rules['rules'])} 张规则卡片；"
          f"standalone.html {os.path.getsize(os.path.join(ROOT, 'standalone.html')) // 1024} KB")


if __name__ == "__main__":
    main()
