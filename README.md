# 德国驾照理论自练

自用。在德国重新考驾照理论，先把路标认全。这个仓库是一个纯静态页面，不需要安装任何东西。

打开 [index.html](index.html) 就是学习页，三种模式：

- **浏览**：按类别看所有路标，点开看中文解释和考试要点。
- **翻卡**：看图想意思，翻面对答案，点「认识 / 不认识」。错过的、没见过的会更常出现。
- **测验**：看图四选一，或者看德文名选图。答完立刻显示解释，选错了也告诉你你选的那个是什么。

学习记录存在浏览器本地（localStorage），换浏览器或清缓存会丢。默认只看「考试重点」，取消勾选就是全部。

## 怎么打开

GitHub 网页上不能直接运行。两种办法：

1. 下载整个仓库（Code → Download ZIP），解压后双击 `index.html`。
2. 或者在仓库设置里开 GitHub Pages（Settings → Pages → Branch: main），之后用网址访问，手机上也能用。

## 内容

<!-- stats:start -->
| 类别 | 数量 | 其中考试重点 |
|---|---:|---:|
| 警告标志（Gefahrzeichen） | 33 | 25 |
| 规定标志（禁令 / 指令）（Vorschriftzeichen） | 86 | 52 |
| 指示标志（Richtzeichen） | 65 | 26 |
| 辅助标志（Zusatzzeichen） | 72 | 23 |
| 路面标线（Fahrbahnmarkierungen） | 8 | 7 |
| 交通设施（Verkehrseinrichtungen） | 11 | 6 |
| **合计** | **275** | **139** |

275 个标志里 180 个用官方图，95 个是脚本画的示意图。
<!-- stats:end -->

路标按 StVO 的分类：警告标志（Gefahrzeichen，1xx）、规定标志（Vorschriftzeichen，2xx）、指示标志（Richtzeichen，3xx–4xx）、辅助标志（Zusatzzeichen，10xx）、交通设施（6xx、720）。路面标线为了方便学习单独列了一类。

「考试重点」是我自己标的：在理论考试和日常开车里最常碰到的那些。编号按 Verkehrszeichenkatalog，几个只有文字的辅助标志（Ölspur、Schule 之类）没标编号。

## 目录

```
index.html          学习页
app.js / app.css    页面逻辑和样式
signs/
  signs.json        路标数据：编号、德文名、中文名、类别、含义、是否重点
  signs.js          由 signs.json 生成，页面实际读这个（自动生成）
  img/<编号>.svg    路标图
tools/
  build.py          从 signs.json 生成 signs.js，更新本文件的统计表
  draw_signs.py     画官方图库里没有的路标（示意图）
```

## 改数据

改 `signs/signs.json`，然后：

```
python3 tools/build.py
```

只用到 Python 标准库。加新路标：在 json 里加一条，把图放到 `signs/img/<编号>.svg`，再跑 build。

## 图的来源

- 大部分路标图是德国官方设计的矢量图，来自 OpenStreetMap 社区整理的 [osm-traffic-sign-tool](https://github.com/osmberlin/osm-traffic-sign-tool)（npm 包 `@osm-traffic-signs/converter`）。德国官方交通标志按《著作权法》第 5 条属于公共领域（amtliches Werk）。
- 那个图库偏重地图标注，考试常见的不少警告标志没有收。缺的由 `tools/draw_signs.py` 按官方配色和比例画了简化版，页面上标「示意」。这些图细节和真实标志有出入，只用来认大概样子。想换成官方图，把官方 SVG 覆盖到 `signs/img/<编号>.svg` 即可，`draw_signs.py` 不会覆盖没有它自己标记的文件。

## 声明

中文解释是我自己按 StVO 和驾校教材的理解写的，可能有错，以官方题库和驾校为准。考试本身用的是 TÜV / DEKRA 的官方题库，这里只练认路标，不是题库。

`tools/` 和页面代码按 MIT 许可，见 [LICENSE](LICENSE)。路标图为公共领域；`signs/signs.json` 里的中文文字随便用。
