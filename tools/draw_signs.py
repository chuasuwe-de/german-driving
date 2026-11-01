#!/usr/bin/env python3
"""补画官方图库里没有的路标，按 StVO 的配色和比例画简化示意图。

用法：
    python3 tools/draw_signs.py            # 只生成 signs/img 里还没有的文件
    python3 tools/draw_signs.py --force    # 重画所有自绘图（不会覆盖官方图）

自绘图只是示意，细节和官方图有出入。想换成官方图，把官方 SVG 放到
signs/img/<编号>.svg 覆盖即可，再跑一遍本脚本不会覆盖它（除非文件尾部有
本脚本留下的 <!--drawn--> 标记）。
"""
import os
import sys

RED = "#c1121c"
BLUE = "#154889"
YELLOW = "#f7ba0b"
GREEN = "#008754"
ORANGE = "#e8640a"
GREY = "#8a8a8a"
BLACK = "#000"
WHITE = "#fff"
FONT = "'DIN Alternate','DIN 1451 Mittelschrift','Roboto Condensed','Arial Narrow',Arial,Helvetica,sans-serif"

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "signs", "img")
MARK = "<!--drawn-->"


# ---------------------------------------------------------------- 基本框架

def svg(body, w=100, h=100, title=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img">'
            f'<title>{title}</title>{body}</svg>{MARK}\n')


def text(x, y, s, size=20, color=BLACK, weight="bold", anchor="middle", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}" dominant-baseline="central" {extra}>{s}</text>')


def tri(body, title=""):
    """警告三角：红边白底，内容中心大约在 (50,62)。"""
    outer = f'<polygon points="50,9 94,86 6,86" fill="{RED}" stroke="{RED}" stroke-width="7" stroke-linejoin="round"/>'
    inner = f'<polygon points="50,25 83,81 17,81" fill="{WHITE}" stroke="{WHITE}" stroke-width="3" stroke-linejoin="round"/>'
    return svg(outer + inner + body, title=title)


def circ_red(body, title=""):
    return svg(f'<circle cx="50" cy="50" r="46" fill="{WHITE}" stroke="{RED}" stroke-width="8"/>' + body, title=title)


def circ_blue(body, title=""):
    return svg(f'<circle cx="50" cy="50" r="48" fill="{WHITE}"/><circle cx="50" cy="50" r="46" fill="{BLUE}"/>' + body,
               title=title)


def circ_end(body, title="", stripes=1):
    """解除类（白底黑细边、灰图案、黑斜杠）。"""
    s = ""
    if stripes == 1:
        s = f'<line x1="22" y1="78" x2="78" y2="22" stroke="{BLACK}" stroke-width="5"/>'
    else:
        for i in range(-2, 3):
            d = i * 11
            s += f'<line x1="{18 + d}" y1="{82 + d}" x2="{82 + d}" y2="{18 + d}" stroke="{BLACK}" stroke-width="4"/>'
    return svg(f'<circle cx="50" cy="50" r="46" fill="{WHITE}" stroke="{BLACK}" stroke-width="3"/>'
               f'<clipPath id="c"><circle cx="50" cy="50" r="46"/></clipPath><g clip-path="url(#c)">{body}{s}</g>',
               title=title)


def rect(body, w=100, h=100, fill=BLUE, border=WHITE, bw=3, r=6, title=""):
    return svg(f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{r}" fill="{border}"/>'
               f'<rect x="{1 + bw}" y="{1 + bw}" width="{w - 2 - 2 * bw}" height="{h - 2 - 2 * bw}" rx="{r - 2}" fill="{fill}"/>'
               + body, w, h, title)


def rect_white(body, w=100, h=100, title="", r=6):
    return svg(f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" rx="{r}" fill="{WHITE}" stroke="{BLACK}" stroke-width="3"/>'
               + body, w, h, title)


def zusatz(lines, w=100, h=60, size=16, title=""):
    """辅助标志：白底黑边，几行文字。"""
    n = len(lines)
    body = ""
    for i, ln in enumerate(lines):
        y = h / 2 + (i - (n - 1) / 2) * (size * 1.15)
        body += text(w / 2, y, ln, size)
    return rect_white(body, w, h, title, r=3)


# ---------------------------------------------------------------- 图案

def g(body, x=0, y=0, s=1.0, color=None):
    c = f' fill="{color}"' if color else ""
    return f'<g transform="translate({x},{y}) scale({s})"{c}>{body}</g>'


def arrow(x1, y1, x2, y2, w=8, color=BLACK, head=1.9):
    """带箭头的直线，箭头在 (x2,y2)。"""
    import math
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    hl = w * head
    bx, by = x2 - ux * hl, y2 - uy * hl
    px, py = -uy, ux
    hw = w * 1.5
    return (f'<line x1="{x1}" y1="{y1}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{color}" stroke-width="{w}"/>'
            f'<polygon points="{x2},{y2} {bx + px * hw:.1f},{by + py * hw:.1f} {bx - px * hw:.1f},{by - py * hw:.1f}" fill="{color}"/>')


def path_arrow(d, end, dirn, w=8, color=BLACK):
    """沿路径 d 的粗线，终点 end=(x,y)，箭头方向 dirn=(dx,dy) 单位向量。"""
    x, y = end
    ux, uy = dirn
    hl, hw = w * 1.9, w * 1.5
    bx, by = x - ux * hl, y - uy * hl
    px, py = -uy, ux
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linejoin="round"/>'
            f'<polygon points="{x},{y} {bx + px * hw:.1f},{by + py * hw:.1f} {bx - px * hw:.1f},{by - py * hw:.1f}" fill="{color}"/>')


# 以下图案都画在自己的局部坐标里，用 g() 放到位置上。

def car_side(color=BLACK):
    """侧视小汽车，约 60×30，车头朝左。"""
    return (f'<path d="M2,24 L6,14 L18,12 L26,3 L46,3 L52,12 L60,15 L60,24 Z" fill="{color}"/>'
            f'<circle cx="14" cy="24" r="6" fill="{color}"/><circle cx="48" cy="24" r="6" fill="{color}"/>'
            f'<circle cx="14" cy="24" r="2.5" fill="{WHITE}"/><circle cx="48" cy="24" r="2.5" fill="{WHITE}"/>')


def car_rear(color=BLACK, w=30, h=22):
    """后视小汽车，约 30×28。"""
    return (f'<path d="M2,{h} L2,10 L7,1 L{w - 7},1 L{w - 2},10 L{w - 2},{h} Z" fill="{color}"/>'
            f'<rect x="1" y="{h - 1}" width="6" height="6" fill="{color}"/><rect x="{w - 7}" y="{h - 1}" width="6" height="6" fill="{color}"/>'
            f'<path d="M7,9 L10,3 L{w - 10},3 L{w - 7},9 Z" fill="{WHITE}"/>')


def truck_side(color=BLACK):
    """侧视卡车，约 60×30，车头朝左。"""
    return (f'<path d="M2,24 L2,10 L8,4 L20,4 L20,24 Z" fill="{color}"/>'
            f'<rect x="22" y="1" width="38" height="23" fill="{color}"/>'
            f'<circle cx="12" cy="25" r="5" fill="{color}"/><circle cx="34" cy="25" r="5" fill="{color}"/><circle cx="50" cy="25" r="5" fill="{color}"/>'
            f'<rect x="5" y="7" width="10" height="7" fill="{WHITE}"/>')


def person(color=BLACK):
    """行人剪影，约 24×44，向右走。"""
    return (f'<circle cx="11" cy="5" r="5" fill="{color}"/>'
            f'<path d="M9,11 L15,11 L19,24 L16,25 L14,19 L14,28 L20,42 L15,44 L9,31 L6,42 L1,41 L5,27 L5,19 L3,25 L0,24 L4,11 Z" fill="{color}"/>')


def child_pair(color=BLACK):
    """两个跑动的孩子，约 40×36。"""
    k = (f'<circle cx="8" cy="4" r="4" fill="{color}"/>'
         f'<path d="M6,9 L11,9 L16,18 L13,19 L10,15 L11,22 L17,32 L13,34 L7,25 L3,34 L-1,32 L4,22 L3,15 L0,18 L-2,16 Z" fill="{color}"/>')
    return g(k, 0, 2, 0.95) + g(k, 20, 0, 1.0)


def bike(color=BLACK):
    """自行车，约 60×36。"""
    return (f'<circle cx="12" cy="26" r="10" fill="none" stroke="{color}" stroke-width="3"/>'
            f'<circle cx="48" cy="26" r="10" fill="none" stroke="{color}" stroke-width="3"/>'
            f'<path d="M12,26 L24,8 L40,8 L48,26 M24,8 L30,26 L12,26 M30,26 L40,8 M40,8 L36,2 L44,2" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"/>')


def cow(color=BLACK):
    """牛，约 60×40，头朝左。"""
    return (f'<path d="M10,8 L4,2 L2,8 L6,12 L4,22 L10,24 L12,36 L17,36 L17,26 L36,26 L38,36 L43,36 L45,26 L54,24 L58,10 L52,4 L46,8 L16,8 Z" fill="{color}"/>'
            f'<path d="M48,22 L52,36 L56,36 L55,22 Z M24,26 L26,36 L30,36 L29,26 Z" fill="{color}"/>')


def locomotive(color=BLACK):
    """蒸汽机车侧视，约 64×36，头朝右。"""
    return (f'<rect x="0" y="4" width="16" height="22" fill="{color}"/>'
            f'<rect x="16" y="10" width="40" height="16" fill="{color}"/>'
            f'<rect x="44" y="2" width="7" height="9" fill="{color}"/>'
            f'<rect x="56" y="18" width="8" height="8" fill="{color}"/>'
            f'<rect x="3" y="8" width="8" height="7" fill="{WHITE}"/>'
            f'<circle cx="10" cy="30" r="5" fill="{color}"/><circle cx="26" cy="30" r="5" fill="{color}"/>'
            f'<circle cx="42" cy="30" r="5" fill="{color}"/><circle cx="56" cy="30" r="4" fill="{color}"/>')


def plane(color=BLACK):
    """飞机俯视，约 50×50，头朝右上。"""
    return (f'<g transform="rotate(-35 25 25)"><path d="M23,0 L27,0 L29,16 L50,24 L50,29 L29,27 L28,40 L35,45 L35,48 L25,46 L15,48 L15,45 L22,40 L21,27 L0,29 L0,24 L21,16 Z" fill="{color}"/></g>')


def snowflake(cx, cy, r, color=BLACK, w=3):
    import math
    out = ""
    for k in range(3):
        a = math.radians(k * 60)
        dx, dy = math.cos(a) * r, math.sin(a) * r
        out += f'<line x1="{cx - dx:.1f}" y1="{cy - dy:.1f}" x2="{cx + dx:.1f}" y2="{cy + dy:.1f}" stroke="{color}" stroke-width="{w}"/>'
        for sgn in (1, -1):
            for t in (0.55, 0.95):
                px, py = cx + sgn * dx * t, cy + sgn * dy * t
                for b in (a + math.radians(35), a - math.radians(35)):
                    ex, ey = px + sgn * math.cos(b) * r * 0.3, py + sgn * math.sin(b) * r * 0.3
                    out += f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{color}" stroke-width="{w * 0.8}"/>'
    return out


def wave(x, y, w, n=4, amp=3, color=BLACK, sw=3):
    seg = w / n
    d = f"M{x},{y}"
    for i in range(n):
        d += f" q{seg / 4},{-amp} {seg / 2},0 t{seg / 2},0"
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}"/>'


def skid(color=BLACK):
    """打滑的小车（后视斜放）加两条波浪轮迹，约 40×50。"""
    return (g(wave(0, 46, 20, 3, 2.5, color, 2.5) + wave(16, 46, 20, 3, 2.5, color, 2.5), 2, 0) +
            f'<g transform="rotate(-25 20 22)">{g(car_rear(color, 28, 20), 6, 6)}</g>')


def traffic_light(color=BLACK):
    """信号灯，约 24×56。"""
    return (f'<rect x="0" y="0" width="24" height="56" rx="4" fill="{color}"/>'
            f'<circle cx="12" cy="10" r="7" fill="{RED}"/><circle cx="12" cy="28" r="7" fill="{YELLOW}"/><circle cx="12" cy="46" r="7" fill="{GREEN}"/>')


def worker(color=BLACK):
    """铲土的工人，约 46×44。"""
    return (f'<circle cx="26" cy="5" r="5" fill="{color}"/>'
            f'<path d="M22,11 L30,12 L36,24 L32,26 L28,20 L27,30 L36,44 L31,44 L23,33 L16,44 L11,44 L18,28 L18,18 Z" fill="{color}"/>'
            f'<path d="M32,20 L44,34 L42,36 L30,22 Z" fill="{color}"/>'
            f'<path d="M40,30 L48,36 L44,42 L36,36 Z" fill="{color}"/>'
            f'<path d="M0,44 Q10,30 20,44 Z" fill="{color}"/>')


def windsock(color=BLACK):
    """风向袋，约 50×44。"""
    return (f'<rect x="4" y="2" width="4" height="42" fill="{color}"/>'
            f'<path d="M8,6 L46,14 L46,24 L8,26 Z" fill="{color}"/>'
            f'<path d="M20,8.5 L30,10.6 L30,25 L20,25.4 Z" fill="{WHITE}"/>')


def cone():
    """路锥，约 40×50。"""
    return (f'<path d="M14,2 L26,2 L36,44 L4,44 Z" fill="{ORANGE}"/>'
            f'<path d="M17,14 L23,14 L25,22 L15,22 Z M12,30 L28,30 L30,38 L10,38 Z" fill="{WHITE}"/>'
            f'<rect x="0" y="44" width="40" height="5" fill="{BLACK}"/>')


def handset(color=WHITE):
    """电话听筒，约 50×50。"""
    return (f'<path d="M10,2 Q2,2 2,10 Q2,30 20,46 Q30,52 44,48 L48,40 L36,30 L30,34 Q18,28 12,16 L18,10 L12,2 Z" fill="{color}"/>')


def pump(color=WHITE):
    """加油机，约 36×50。"""
    return (f'<rect x="0" y="4" width="24" height="46" rx="2" fill="{color}"/>'
            f'<rect x="4" y="8" width="16" height="12" fill="{BLUE}"/>'
            f'<path d="M26,12 L32,12 L32,36 Q32,42 26,42" fill="none" stroke="{color}" stroke-width="3"/>'
            f'<rect x="28" y="4" width="8" height="8" fill="{color}"/>')


def wheelchair(color=BLACK):
    """轮椅使用者，约 40×46。"""
    return (f'<circle cx="18" cy="5" r="5" fill="{color}"/>'
            f'<path d="M14,12 L22,12 L24,26 L34,26 L40,42 L35,44 L30,31 L18,31 Z" fill="{color}"/>'
            f'<circle cx="15" cy="34" r="11" fill="none" stroke="{color}" stroke-width="4"/>')


def bake_stripes(x, y, w, h, n):
    """铁路道口预告标（白底，红斜条 n 条）。"""
    out = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{WHITE}" stroke="{BLACK}" stroke-width="1"/>'
    gap = h / (n * 2 + 1)
    out += f'<clipPath id="b{n}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath><g clip-path="url(#b{n})">'
    for i in range(n):
        yy = y + gap * (2 * i + 1)
        out += f'<polygon points="{x},{yy + gap * 0.6} {x + w},{yy - gap * 0.6} {x + w},{yy + gap * 0.4} {x},{yy + gap * 1.6}" fill="{RED}"/>'
    return out + "</g>"


# ---------------------------------------------------------------- 各个标志

SIGNS = {}


def sign(sid, title):
    def deco(fn):
        SIGNS[sid] = (title, fn)
        return fn
    return deco


# ---- 警告标志 Gefahrzeichen

@sign("105-10", "Doppelkurve (zunächst links)")
def _():
    return tri(path_arrow("M60,80 L60,66 Q60,58 52,58 L48,58 Q40,58 40,50 L40,44", (40, 38), (0, -1), 7))


@sign("105-20", "Doppelkurve (zunächst rechts)")
def _():
    return tri(path_arrow("M40,80 L40,66 Q40,58 48,58 L52,58 Q60,58 60,50 L60,44", (60, 38), (0, -1), 7))


@sign("112", "Unebene Fahrbahn")
def _():
    return tri('<path d="M22,76 Q36,52 50,76 Q64,52 78,76 Z" fill="#000"/>')


@sign("114", "Schleuder- oder Rutschgefahr")
def _():
    return tri(g(skid(), 30, 32, 1.0))


@sign("117-10", "Seitenwind (von rechts)")
def _():
    return tri(g(windsock(), 26, 38, 1.0))


@sign("120", "Verengte Fahrbahn")
def _():
    return tri('<path d="M30,78 L30,60 Q30,52 36,48 L38,45 L38,36 L44,36 L44,45 L44,48 Q44,54 38,58 L38,78 Z" fill="#000"/>'
               '<path d="M70,78 L70,60 Q70,52 64,48 L62,45 L62,36 L56,36 L56,45 L56,48 Q56,54 62,58 L62,78 Z" fill="#000"/>')


@sign("121-10", "Einseitig (rechts) verengte Fahrbahn")
def _():
    return tri('<rect x="36" y="36" width="6" height="42" fill="#000"/>'
               '<path d="M66,78 L66,60 Q66,52 60,48 L58,45 L58,36 L64,36 L64,45 L64,48 Q64,54 70,58 L70,78 Z" fill="#000"/>')


@sign("123", "Arbeitsstelle")
def _():
    return tri(g(worker(), 26, 36, 0.95))


@sign("124", "Stau")
def _():
    return tri(g(car_rear(BLACK, 22, 16), 39, 32, 0.8) + g(car_rear(BLACK, 26, 18), 25, 46, 0.9) + g(car_rear(BLACK, 26, 18), 50, 46, 0.9))


@sign("125", "Gegenverkehr")
def _():
    return tri(arrow(42, 40, 42, 78, 7) + arrow(58, 78, 58, 40, 7))


@sign("131", "Lichtzeichenanlage")
def _():
    return tri(g(traffic_light(), 38, 30, 0.9))


@sign("133-10", "Fußgänger")
def _():
    return tri(g(person(), 38, 34, 1.0))


@sign("151", "Bahnübergang")
def _():
    return tri(g(locomotive(), 18, 42, 1.0))


@sign("156-10", "Bahnübergang mit dreistreifiger Bake (etwa 240 m)")
def _():
    body = (f'<g transform="translate(22,0) scale(0.56)">'
            f'<polygon points="50,9 94,86 6,86" fill="{RED}" stroke="{RED}" stroke-width="7" stroke-linejoin="round"/>'
            f'<polygon points="50,25 83,81 17,81" fill="{WHITE}" stroke="{WHITE}" stroke-width="3" stroke-linejoin="round"/>'
            + g(locomotive(), 18, 42) + '</g>' + bake_stripes(38, 52, 24, 46, 3))
    return svg(body, title="Bahnübergang mit dreistreifiger Bake")


@sign("157-10", "Zweistreifige Bake (etwa 160 m)")
def _():
    return svg(bake_stripes(38, 4, 24, 92, 2), title="Zweistreifige Bake")


@sign("159-10", "Einstreifige Bake (etwa 80 m)")
def _():
    return svg(bake_stripes(38, 4, 24, 92, 1), title="Einstreifige Bake")


@sign("101-10", "Flugbetrieb")
def _():
    return tri(g(plane(), 24, 34, 1.0))


@sign("101-11", "Fußgängerüberweg")
def _():
    stripes = "".join(f'<rect x="{26 + i * 10}" y="70" width="6" height="8" fill="#000"/>' for i in range(5))
    return tri(stripes + g(person(), 40, 28, 0.9))


@sign("101-12", "Viehtrieb")
def _():
    return tri(g(cow(), 22, 40, 0.95))


@sign("101-51", "Schnee- oder Eisglätte")
def _():
    return tri(snowflake(50, 40, 9, BLACK, 2) + g(skid(), 32, 50, 0.6))


@sign("101-52", "Splitt, Schotter")
def _():
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="1.8" fill="#000"/>' for x, y in
                   [(24, 54), (28, 60), (22, 66), (30, 70), (26, 76), (20, 60), (33, 64)])
    return tri(g(car_side(), 34, 46, 0.75) + dots)


@sign("101-53", "Ufer")
def _():
    return tri('<path d="M20,78 L20,66 L50,66 L50,78 Z" fill="#000"/>'
               f'<g transform="rotate(25 70 56)">{g(car_side(), 44, 44, 0.6)}</g>'
               + wave(50, 76, 28, 3, 3, BLACK, 2.5))


@sign("101-55", "Bewegliche Brücke")
def _():
    return tri('<rect x="20" y="70" width="34" height="8" fill="#000"/>'
               '<g transform="rotate(-45 54 74)"><rect x="54" y="70" width="30" height="8" fill="#000"/></g>'
               + wave(24, 84, 52, 4, 2.5, BLACK, 2))


# ---- 规定标志 Vorschriftzeichen

@sign("208", "Vorrang des Gegenverkehrs")
def _():
    return circ_red(arrow(38, 74, 38, 24, 9, RED) + arrow(62, 24, 62, 74, 9, BLACK))


@sign("209-20", "Vorgeschriebene Fahrtrichtung rechts")
def _():
    return circ_blue(arrow(24, 50, 78, 50, 10, WHITE))


@sign("209-10", "Vorgeschriebene Fahrtrichtung links")
def _():
    return circ_blue(arrow(76, 50, 22, 50, 10, WHITE))


@sign("209-30", "Vorgeschriebene Fahrtrichtung geradeaus")
def _():
    return circ_blue(arrow(50, 78, 50, 22, 10, WHITE))


@sign("211-20", "Vorgeschriebene Fahrtrichtung hier rechts")
def _():
    return circ_blue(path_arrow("M40,78 L40,40 Q40,32 48,32 L62,32", (72, 32), (1, 0), 10, WHITE))


@sign("211-10", "Vorgeschriebene Fahrtrichtung hier links")
def _():
    return circ_blue(path_arrow("M60,78 L60,40 Q60,32 52,32 L38,32", (28, 32), (-1, 0), 10, WHITE))


@sign("214-20", "Vorgeschriebene Fahrtrichtung geradeaus oder rechts")
def _():
    return circ_blue(arrow(40, 78, 40, 22, 9, WHITE) + path_arrow("M40,70 L40,54 Q40,44 50,44 L62,44", (74, 44), (1, 0), 9, WHITE))


@sign("214-10", "Vorgeschriebene Fahrtrichtung geradeaus oder links")
def _():
    return circ_blue(arrow(60, 78, 60, 22, 9, WHITE) + path_arrow("M60,70 L60,54 Q60,44 50,44 L38,44", (26, 44), (-1, 0), 9, WHITE))


@sign("214-30", "Vorgeschriebene Fahrtrichtung links oder rechts")
def _():
    return circ_blue(path_arrow("M50,78 L50,50 Q50,40 60,40 L64,40", (74, 40), (1, 0), 9, WHITE)
                     + path_arrow("M50,78 L50,50 Q50,40 40,40 L36,40", (26, 40), (-1, 0), 9, WHITE))


@sign("223.1", "Seitenstreifen befahren")
def _():
    return rect('<line x1="20" y1="10" x2="20" y2="90" stroke="#fff" stroke-width="3"/>'
                '<line x1="80" y1="10" x2="80" y2="90" stroke="#fff" stroke-width="3" stroke-dasharray="8,6"/>'
                + arrow(37, 82, 37, 18, 7, WHITE) + arrow(63, 82, 63, 18, 7, WHITE) + arrow(89, 82, 89, 18, 5, WHITE))


@sign("223.3", "Seitenstreifen räumen")
def _():
    return rect('<line x1="20" y1="10" x2="20" y2="90" stroke="#fff" stroke-width="3"/>'
                '<line x1="80" y1="10" x2="80" y2="90" stroke="#fff" stroke-width="3" stroke-dasharray="8,6"/>'
                + arrow(37, 82, 37, 18, 7, WHITE) + arrow(63, 82, 63, 18, 7, WHITE)
                + path_arrow("M89,82 L89,60 Q89,50 80,44 L74,40", (68, 36), (-0.83, -0.55), 5, WHITE))


@sign("229", "Taxenstand")
def _():
    return rect(text(50, 50, "TAXI", 34, WHITE), r=4)


@sign("262", "Verbot für Fahrzeuge über angegebene tatsächliche Masse")
def _():
    return circ_red(text(50, 50, "5,5t", 34))


@sign("263", "Verbot für Fahrzeuge über angegebene tatsächliche Achslast")
def _():
    return circ_red('<rect x="30" y="56" width="40" height="5" fill="#000"/><circle cx="36" cy="66" r="6" fill="#000"/><circle cx="64" cy="66" r="6" fill="#000"/>'
                    + text(50, 38, "8t", 30))


@sign("264", "Verbot für Fahrzeuge über angegebene Breite")
def _():
    return circ_red(arrow(44, 72, 20, 72, 3, BLACK) + arrow(56, 72, 80, 72, 3, BLACK) + text(50, 44, "2m", 30))


@sign("265", "Verbot für Fahrzeuge über angegebene Höhe")
def _():
    return circ_red(arrow(50, 30, 50, 14, 3, BLACK) + arrow(50, 70, 50, 86, 3, BLACK) + text(50, 50, "3,8m", 24))


@sign("266", "Verbot für Fahrzeuge und Züge über angegebene Länge")
def _():
    return circ_red(g(truck_side(), 20, 20, 0.95) + text(50, 62, "10m", 15) + arrow(46, 76, 20, 76, 3, BLACK) + arrow(54, 76, 80, 76, 3, BLACK))


@sign("270.1", "Beginn einer Umweltzone")
def _():
    return rect_white(f'<circle cx="50" cy="40" r="30" fill="{WHITE}" stroke="{RED}" stroke-width="6"/>'
                      + text(50, 40, "Umwelt", 15) + text(50, 84, "ZONE", 20))


@sign("270.2", "Ende einer Umweltzone")
def _():
    return rect_white(f'<circle cx="50" cy="40" r="30" fill="{WHITE}" stroke="{GREY}" stroke-width="6"/>'
                      + text(50, 40, "Umwelt", 15, GREY) + text(50, 84, "ZONE", 20, GREY)
                      + f'<line x1="14" y1="86" x2="86" y2="14" stroke="{BLACK}" stroke-width="4"/>')


@sign("272", "Verbot des Wendens")
def _():
    return circ_red(path_arrow("M36,76 L36,42 Q36,26 50,26 Q64,26 64,42 L64,54", (64, 66), (0, 1), 8)
                    + f'<line x1="22" y1="78" x2="78" y2="22" stroke="{RED}" stroke-width="7"/>')


@sign("273", "Mindestabstand für Kfz über 3,5 t")
def _():
    return circ_red(g(truck_side(), 10, 26, 0.55) + g(truck_side(), 56, 26, 0.55) + text(50, 66, "70m", 20))


@sign("280", "Ende des Überholverbots für Kfz aller Art")
def _():
    return circ_end(g(car_side(GREY), 16, 36, 0.55) + g(car_side(GREY), 50, 36, 0.55), stripes=5)


@sign("281", "Ende des Überholverbots für Kfz über 3,5 t")
def _():
    return circ_end(g(truck_side(GREY), 16, 34, 0.55) + g(car_side(GREY), 50, 36, 0.55), stripes=5)


@sign("282", "Ende sämtlicher Streckenverbote")
def _():
    return circ_end("", stripes=5)


@sign("353", "Einbahnstraße")
def _():
    return rect(arrow(50, 86, 50, 14, 12, WHITE))


# ---- 指示标志 Richtzeichen

@sign("308", "Vorrang vor dem Gegenverkehr")
def _():
    return rect(arrow(38, 24, 38, 76, 9, RED) + arrow(62, 76, 62, 24, 9, WHITE))


@sign("327", "Tunnel")
def _():
    return rect('<path d="M18,88 L18,46 Q18,14 50,14 Q82,14 82,46 L82,88 Z" fill="#fff"/>'
                '<path d="M26,88 L26,50 Q26,24 50,24 Q74,24 74,50 L74,88 Z" fill="#000"/>'
                '<path d="M34,88 L42,62 L58,62 L66,88 Z" fill="#fff"/>')


@sign("328", "Nothalte- und Pannenbucht")
def _():
    return rect('<path d="M30,10 L30,90 M70,10 L70,36 Q70,44 78,44 L84,44 L84,66 L78,66 Q70,66 70,74 L70,90" fill="none" stroke="#fff" stroke-width="4"/>'
                + g(handset(WHITE), 50, 40, 0.45) + text(50, 24, "SOS", 11, WHITE))


@sign("333", "Ausfahrt (Autobahn)")
def _():
    return rect(path_arrow("M30,80 L30,42 Q30,32 40,28 L60,22", (72, 18), (0.95, -0.3), 7, WHITE) + text(62, 70, "Ausfahrt", 13, WHITE), w=100, h=100)


@sign("356", "Verkehrshelfer")
def _():
    return rect(g(person(WHITE), 32, 24, 1.1) + f'<circle cx="68" cy="34" r="10" fill="{WHITE}"/><circle cx="68" cy="34" r="7" fill="{RED}"/>'
                '<rect x="66" y="44" width="4" height="34" fill="#fff"/>')


@sign("358", "Erste Hilfe")
def _():
    return rect('<rect x="40" y="18" width="20" height="64" fill="#fff"/><rect x="18" y="40" width="64" height="20" fill="#fff"/>')


@sign("363", "Polizei")
def _():
    return rect(text(50, 50, "Polizei", 24, WHITE), r=4)


@sign("365-51", "Notrufsäule")
def _():
    return rect(g(handset(WHITE), 24, 24, 1.0))


@sign("365-52", "Tankstelle")
def _():
    return rect(g(pump(WHITE), 30, 24, 1.0))


@sign("380", "Richtgeschwindigkeit (abgeschafft 2021, noch vorhanden)")
def _():
    return rect(text(50, 50, "130", 40, WHITE))


@sign("390", "Mautpflicht nach dem Bundesfernstraßenmautgesetz")
def _():
    return rect_white(g(truck_side(), 20, 18, 1.0) + text(50, 76, "Maut", 26))


@sign("401", "Bundesstraßennummer")
def _():
    return rect(text(50, 32, "B 27", 32), w=100, h=64, fill=YELLOW, border=BLACK, bw=2, r=4)


@sign("405", "Autobahnnummer")
def _():
    return rect(text(50, 32, "A 3", 32, WHITE), w=100, h=64, fill=BLUE, border=WHITE, bw=2, r=4)


@sign("415", "Wegweiser auf Bundesstraßen")
def _():
    return svg(f'<path d="M2,8 L86,8 L118,30 L86,52 L2,52 Z" fill="{BLACK}"/><path d="M5,11 L85,11 L113,30 L85,49 L5,49 Z" fill="{YELLOW}"/>'
               + text(44, 30, "Ulm  23", 22, anchor="middle"), w=120, h=60, title="Wegweiser auf Bundesstraßen")


@sign("430", "Pfeilwegweiser zur Autobahn")
def _():
    return svg(f'<path d="M2,8 L86,8 L118,30 L86,52 L2,52 Z" fill="{WHITE}"/><path d="M5,11 L85,11 L113,30 L85,49 L5,49 Z" fill="{BLUE}"/>'
               f'<path d="M12,20 L16,20 L18,40 L10,40 Z M22,20 L26,20 L28,40 L20,40 Z M8,26 L30,26 M9,33 L29,33" fill="{WHITE}" stroke="{WHITE}" stroke-width="2"/>'
               + text(66, 30, "Stuttgart", 15, WHITE), w=120, h=60, title="Pfeilwegweiser zur Autobahn")


@sign("432", "Pfeilwegweiser zu innerörtlichen Zielen")
def _():
    return svg(f'<path d="M2,8 L86,8 L118,30 L86,52 L2,52 Z" fill="{BLACK}"/><path d="M5,11 L85,11 L113,30 L85,49 L5,49 Z" fill="{WHITE}"/>'
               + text(50, 30, "Bahnhof", 20), w=120, h=60, title="Pfeilwegweiser")


@sign("450-50", "Ankündigungsbake 300 m")
def _():
    return rect("".join(f'<rect x="12" y="{18 + i * 24}" width="76" height="10" fill="#fff" transform="skewY(-16)"/>' for i in range(3)), w=100, h=130, title="Ankündigungsbake")


@sign("450-51", "Ankündigungsbake 200 m")
def _():
    return rect("".join(f'<rect x="12" y="{30 + i * 24}" width="76" height="10" fill="#fff" transform="skewY(-16)"/>' for i in range(2)), w=100, h=130)


@sign("450-52", "Ankündigungsbake 100 m")
def _():
    return rect('<rect x="12" y="42" width="76" height="10" fill="#fff" transform="skewY(-16)"/>', w=100, h=130)


@sign("453", "Entfernungstafel")
def _():
    rows = [("Frankfurt", "112"), ("Würzburg", "38"), ("Kitzingen", "9")]
    body = "".join(text(10, 22 + i * 24, a, 14, WHITE, anchor="start") + text(112, 22 + i * 24, b, 14, WHITE, anchor="end")
                   for i, (a, b) in enumerate(rows))
    return rect(body, w=120, h=90, r=4)


@sign("454-10", "Umleitungswegweiser (links)")
def _():
    return rect(text(50, 20, "Umleitung", 16) + arrow(80, 44, 20, 44, 6), w=100, h=60, fill=YELLOW, border=BLACK, bw=2, r=3)


@sign("455.1-10", "Ankündigung einer Umleitung")
def _():
    return rect(text(50, 16, "Umleitung", 15) + text(50, 32, "B 27", 13) + arrow(50, 58, 50, 40, 5), w=100, h=66, fill=YELLOW, border=BLACK, bw=2, r=3)


@sign("457.1", "Umleitungspfeil")
def _():
    return rect(arrow(14, 30, 86, 30, 9), w=100, h=60, fill=YELLOW, border=BLACK, bw=2, r=3)


@sign("521-30", "Fahrstreifentafel (zwei Fahrstreifen)")
def _():
    return rect_white(arrow(32, 86, 32, 14, 8) + arrow(68, 86, 68, 14, 8))


@sign("531-10", "Einengungstafel (rechter Fahrstreifen endet)")
def _():
    return rect_white(arrow(32, 86, 32, 14, 8) + path_arrow("M68,86 L68,60 Q68,46 56,40 L48,36", (42, 33), (-0.9, -0.45), 8))


@sign("296", "Einseitige Fahrstreifenbegrenzung")
def _():
    return svg(f'<rect width="100" height="100" fill="#6d6d6d"/><rect x="44" y="0" width="5" height="100" fill="#fff"/>'
               + "".join(f'<rect x="52" y="{i * 20 + 4}" width="5" height="12" fill="#fff"/>' for i in range(5)), title="Einseitige Fahrstreifenbegrenzung")


@sign("297", "Pfeilmarkierungen")
def _():
    return svg(f'<rect width="100" height="100" fill="#6d6d6d"/>'
               + "".join(f'<rect x="{x}" y="0" width="3" height="12" fill="#fff"/><rect x="{x}" y="30" width="3" height="12" fill="#fff"/><rect x="{x}" y="60" width="3" height="12" fill="#fff"/><rect x="{x}" y="90" width="3" height="10" fill="#fff"/>' for x in (2, 95))
               + f'<rect x="32" y="0" width="3" height="100" fill="#fff"/><rect x="65" y="0" width="3" height="100" fill="#fff"/>'
               + path_arrow("M17,90 L17,56 Q17,46 10,42", (6, 40), (-0.9, -0.45), 5, WHITE) + arrow(50, 90, 50, 40, 5, WHITE)
               + path_arrow("M82,90 L82,56 Q82,46 89,42", (93, 40), (0.9, -0.45), 5, WHITE),
               title="Pfeilmarkierungen")


@sign("341", "Wartelinie")
def _():
    return svg(f'<rect width="100" height="100" fill="#6d6d6d"/><rect x="0" y="40" width="100" height="4" fill="#fff"/>'
               + "".join(f'<rect x="{6 + i * 16}" y="54" width="9" height="7" fill="#fff"/>' for i in range(6))
               + '<rect x="47" y="60" width="5" height="40" fill="#fff" opacity="0.6"/>', title="Wartelinie")


# ---- 交通设施 Verkehrseinrichtungen

@sign("605-10", "Leitbake (Aufstellung rechts)")
def _():
    body = f'<rect x="30" y="2" width="40" height="124" fill="{WHITE}" stroke="{BLACK}" stroke-width="1"/>'
    body += '<clipPath id="lb"><rect x="30" y="2" width="40" height="124"/></clipPath><g clip-path="url(#lb)">'
    for i in range(4):
        y = -10 + i * 36
        body += f'<polygon points="30,{y + 36} 70,{y} 70,{y + 18} 30,{y + 54}" fill="{RED}"/>'
    return svg(body + "</g>", w=100, h=130, title="Leitbake")


@sign("610", "Leitkegel")
def _():
    return svg(g(cone(), 30, 24, 1.0), title="Leitkegel")


@sign("615", "Fahrbare Absperrtafel")
def _():
    body = f'<rect x="4" y="4" width="92" height="72" fill="{WHITE}" stroke="{BLACK}" stroke-width="2"/>'
    body += '<clipPath id="at"><rect x="4" y="4" width="92" height="72"/></clipPath><g clip-path="url(#at)">'
    for i in range(6):
        x = -40 + i * 28
        body += f'<polygon points="{x},76 {x + 60},4 {x + 74},4 {x + 14},76" fill="{RED}"/>'
    body += "</g>" + arrow(76, 40, 22, 40, 10, BLACK)
    body += '<rect x="20" y="78" width="8" height="18" fill="#444"/><rect x="72" y="78" width="8" height="18" fill="#444"/>'
    return svg(body, title="Fahrbare Absperrtafel")


@sign("625-10", "Richtungstafel in Kurven (links)")
def _():
    body = f'<rect x="1" y="20" width="118" height="40" fill="{BLACK}"/>'
    for i in range(3):
        x = 20 + i * 36
        body += f'<polyline points="{x + 16},26 {x},40 {x + 16},54" fill="none" stroke="{WHITE}" stroke-width="7"/>'
    return svg(body, w=120, h=80, title="Richtungstafel")


@sign("630", "Parkwarntafel")
def _():
    body = f'<rect x="1" y="1" width="98" height="58" fill="{WHITE}" stroke="{BLACK}" stroke-width="2"/>'
    body += '<clipPath id="pw"><rect x="1" y="1" width="98" height="58"/></clipPath><g clip-path="url(#pw)">'
    for i in range(6):
        x = -40 + i * 28
        body += f'<polygon points="{x},60 {x + 58},0 {x + 72},0 {x + 14},60" fill="{RED}"/>'
    return svg(body + "</g>", w=100, h=60, title="Parkwarntafel")


# ---- 辅助标志 Zusatzzeichen

@sign("1002-10", "Verlauf der Vorfahrtstraße (nach links abknickend)")
def _():
    return rect_white('<path d="M50,88 L50,50 L12,50" fill="none" stroke="#000" stroke-width="12"/>'
                      '<path d="M50,50 L50,12 M50,50 L88,50" fill="none" stroke="#000" stroke-width="3"/>')


@sign("1002-20", "Verlauf der Vorfahrtstraße (nach rechts abknickend)")
def _():
    return rect_white('<path d="M50,88 L50,50 L88,50" fill="none" stroke="#000" stroke-width="12"/>'
                      '<path d="M50,50 L50,12 M50,50 L12,50" fill="none" stroke="#000" stroke-width="3"/>')


@sign("1001-30", "auf ... m (Länge der Gefahrstrecke)")
def _():
    return zusatz(["auf 800 m"], size=18)


@sign("1004-30", "... m (Entfernung zur Gefahrstelle / zum Zeichen)")
def _():
    return zusatz(["100 m"], size=22)


@sign("1040-30", "Zeitliche Beschränkung")
def _():
    return zusatz(["16 - 18 h"], size=20)


@sign("1042-33", "Zeitliche Beschränkung Mo-Fr")
def _():
    return zusatz(["Mo - Fr", "16 - 18 h"], size=16)


@sign("1040-32", "Parkscheibe, 2 Stunden")
def _():
    disc = (f'<rect x="8" y="12" width="34" height="36" rx="3" fill="{BLUE}"/><rect x="12" y="20" width="26" height="24" rx="2" fill="{WHITE}"/>'
            f'<circle cx="25" cy="32" r="9" fill="none" stroke="{BLACK}" stroke-width="1.5"/><line x1="25" y1="32" x2="25" y2="25" stroke="#000" stroke-width="1.5"/><line x1="25" y1="32" x2="30" y2="34" stroke="#000" stroke-width="1.5"/>')
    return rect_white(disc + text(70, 30, "2 Std.", 16), w=100, h=60, r=3)


@sign("1044-10", "Schwerbehinderte mit außergewöhnlicher Gehbehinderung")
def _():
    return rect_white(g(wheelchair(), 30, 8, 0.95), w=100, h=60, r=3)


@sign("1053-31", "mit Parkschein")
def _():
    return zusatz(["mit", "Parkschein"], size=15)


@sign("zz-oelspur", "Ölspur")
def _():
    return zusatz(["Ölspur"], size=20)


@sign("zz-rollsplitt", "Rollsplitt")
def _():
    return zusatz(["Rollsplitt"], size=18)


@sign("zz-spurrillen", "Spurrillen")
def _():
    return zusatz(["Spurrillen"], size=18)


@sign("zz-strassenschaeden", "Straßenschäden")
def _():
    return zusatz(["Straßen-", "schäden"], size=16)


@sign("zz-schule", "Schule")
def _():
    return zusatz(["Schule"], size=20)


# ---------------------------------------------------------------- 主程序

def main():
    force = "--force" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    written = skipped = 0
    for sid, (title, fn) in SIGNS.items():
        path = os.path.join(OUT, sid + ".svg")
        if os.path.exists(path):
            drawn = open(path, encoding="utf-8").read().rstrip().endswith(MARK)
            if not drawn or not force:
                skipped += 1
                continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(fn() if fn.__code__.co_argcount == 0 else fn(title))
        written += 1
    print(f"自绘 {len(SIGNS)} 个：写入 {written}，跳过 {skipped}（已有文件）")


if __name__ == "__main__":
    main()
