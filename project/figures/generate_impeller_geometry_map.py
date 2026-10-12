"""
Regenerates "Impeller Geometry (a-e) - How the Steps Depend on Each Other" with
larger text throughout (esp. the small arrow-caption annotations and legend),
so it stays legible after being pasted/scaled into the pump sizing PowerPoint.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle
from matplotlib.lines import Line2D

# --- colors ---------------------------------------------------------------
TEAL = "#1a5c73"
ORANGE = "#e07b39"
GRAY_BOX = "#e6e6e6"
GRAY_BOX_EDGE = "#999999"
GRAY_TEXT = "#4d4d4d"
ORANGE_TEXT = "#c15a1a"
DARK_TEXT = "#222222"

fig, ax = plt.subplots(figsize=(16, 13))
ax.set_xlim(0, 16)
ax.set_ylim(-1.3, 13.2)
ax.axis("off")


# --- helpers ----------------------------------------------------------------
def rounded_box(x0, x1, y0, y1, facecolor, edgecolor, lw=1.4, ls="-"):
    box = FancyBboxPatch(
        (x0, y0), x1 - x0, y1 - y0,
        boxstyle="round,pad=0.02,rounding_size=0.14",
        facecolor=facecolor, edgecolor=edgecolor, linewidth=lw, linestyle=ls,
        zorder=2,
    )
    ax.add_patch(box)


def hexagon_banner(x0, x1, y0, y1, point=0.55, facecolor=ORANGE, edgecolor="white"):
    ymid = (y0 + y1) / 2
    pts = [
        (x0, y0), (x1, y0), (x1 + point, ymid),
        (x1, y1), (x0, y1), (x0 - point, ymid),
    ]
    ax.add_patch(Polygon(pts, closed=True, facecolor=facecolor,
                          edgecolor=edgecolor, linewidth=1.2, zorder=2))


def teal_step(x0, x1, y0, y1, label, fontsize=16):
    rounded_box(x0, x1, y0, y1, TEAL, "none")
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, label, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color="white", zorder=3)


def gray_box(x0, x1, y0, y1, header, lines):
    rounded_box(x0, x1, y0, y1, GRAY_BOX, GRAY_BOX_EDGE)
    ax.text((x0 + x1) / 2, y1 - 0.32, header, ha="center", va="top",
            fontsize=14, fontweight="bold", color=DARK_TEXT, zorder=3)
    for i, line in enumerate(lines):
        ax.text((x0 + x1) / 2, y1 - 0.75 - 0.38 * i, line, ha="center", va="top",
                fontsize=12.5, color=DARK_TEXT, zorder=3)


def diamond(x0, x1, y0, y1, header, body):
    hexagon_banner(x0, x1, y0, y1)
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.17, header, ha="center", va="center",
            fontsize=14.5, fontweight="bold", color="white", zorder=3)
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 - 0.22, body, ha="center", va="center",
            fontsize=12.5, color="white", zorder=3)


def solid_arrow(p0, p1, rad=0.0):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.8,
                                 connectionstyle=f"arc3,rad={rad}",
                                 shrinkA=2, shrinkB=2), zorder=4)


def dashed_arrow(p0, p1, rad=0.0):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.8, linestyle=(0, (5, 3)),
                                 connectionstyle=f"arc3,rad={rad}",
                                 shrinkA=2, shrinkB=2), zorder=4)


def caption(x, y, text, color=GRAY_TEXT, fontsize=12, style="italic", ha="center"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fontsize, style=style,
            color=color, zorder=5, linespacing=1.4,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                      edgecolor="none", alpha=0.9))


# --- title ------------------------------------------------------------------
ax.text(0.3, 12.85, "Impeller Geometry (a\u2013e) \u2014 How the Steps Depend on Each Other",
        fontsize=24, fontweight="bold", color=DARK_TEXT, ha="left", va="center")
ax.text(0.3, 12.35,
        "Solid arrow = a computed number is passed forward.   "
        "Dashed arrow = a classification only selects which formula variant applies (no number passed).",
        fontsize=13, style="italic", color=GRAY_TEXT, ha="left", va="center")

# --- row 1: decision diamonds (y 11.1-12.0) ----------------------------------
diamond(0.4, 6.8, 11.1, 12.0, "Suction capability sufficient",
        "for a standard impeller? (\u03c3s vs. required, Table 1)")
diamond(8.2, 15.6, 11.1, 12.0, "Specific speed \u03c3 (Figure 9)?",
        "\u03c3 \u2264 1.6 \u2192 radial/mixed-flow   |   \u03c3 > 1.6 \u2192 axial-flow/propeller")

# --- row 2: gray classification-result boxes (y 9.5-10.4) --------------------
gray_box(0.4, 3.5, 9.5, 10.4, "Standard impeller",
         ["\u03c6e \u2248 0.2\u20130.3", "Table 1a \u2014 Gongwer"])
gray_box(3.7, 6.8, 9.5, 10.4, "Inducer required",
         ["\u03c6e \u2264 0.1", "Table 1b \u2014 Stripling\u2013Acosta"])

dashed_arrow((1.9, 11.1), (2.2, 10.4))
dashed_arrow((5.2, 11.1), (4.9, 10.4))
caption(3.55, 10.75, "\u03c6e value used directly in Eq. 49", color=ORANGE_TEXT)

dashed_arrow((11.9, 11.1), (11.9, 8.5), rad=0.0)
caption(13.4, 9.9, "picks \u03c8 curve vs.\n\u03c8t = 0.53/\u03c3 (Eq. 46)", color=ORANGE_TEXT, fontsize=12)

# --- row 3: a) Eye Radius / b) Exit Radius (y 7.7-8.5) -----------------------
teal_step(0.4, 6.8, 7.7, 8.5, "a)  Eye Radius (r\u2091)  \u2014  Slide 10")
teal_step(8.2, 15.6, 7.7, 8.5, "b)  Exit Radius (r\u2082)  \u2014  Slide 11")

# --- cross-check box (y 5.7-7.15) --------------------------------------------
rounded_box(4.2, 10.8, 5.7, 7.15, "#fdf1e7", ORANGE, lw=1.6, ls=(0, (5, 3)))
ax.text(7.5, 6.72, "Cross-check \u2014 Eq. 51", ha="center", va="center",
        fontsize=15, fontweight="bold", color=ORANGE_TEXT, zorder=3)
ax.text(7.5, 6.30, "r\u2091/r\u2082 ratio vs. shape expected at \u03c3 (Figure 9)",
        ha="center", va="center", fontsize=12.5, color=DARK_TEXT, zorder=3)
ax.text(7.5, 5.94, "mismatch \u2192 iterate \u03c6e (a) and/or \u03c8 (b)",
        ha="center", va="center", fontsize=12.5, style="italic", color=ORANGE_TEXT, zorder=3)

solid_arrow((3.2, 7.7), (4.4, 7.15), rad=0.0)
caption(3.6, 7.45, "r\u2091", color=GRAY_TEXT, fontsize=13, style="normal")
solid_arrow((9.6, 7.7), (10.6, 7.15), rad=0.0)
caption(10.1, 7.45, "r\u2082", color=GRAY_TEXT, fontsize=13, style="normal")

# --- row 4: c) Exit Width (y 4.65-5.45) --------------------------------------
teal_step(4.6, 11.4, 4.65, 5.45, "c)  Exit Width (b\u2082)  \u2014  Slide 12")

solid_arrow((0.6, 7.7), (3.2, 4.2), rad=-0.28)
caption(0.5, 5.9, "r\u2091 \u2192 eye area\n\u03c0(r\u2091\u00b2 \u2212 rs\u00b2)", color=GRAY_TEXT, fontsize=12, ha="left")

solid_arrow((14.2, 7.7), (11.15, 5.45), rad=0.18)
caption(13.7, 6.85, "r\u2082  (b\u2082 equation\nuses r\u2082 directly)", color=GRAY_TEXT, fontsize=12)

# --- row 5: d) Hub, Shroud Profiles (y 3.4-4.2) ------------------------------
teal_step(2.6, 9.9, 3.4, 4.2, "d)  Hub, Shroud Profiles  \u2014  Slide 13")

solid_arrow((7.9, 4.65), (7.9, 4.2), rad=0.0)
caption(8.9, 4.42, "r\u2082, b\u2082 \u2192 exit area 2\u03c0r\u2082b\u2082", color=GRAY_TEXT, fontsize=12)

# --- row 6: bottom-left decision diamonds + e) Blade Construction -----------
diamond(0.4, 6.2, 2.15, 2.85, "Collector type?", "volute / vaned / vaneless \u2192 Pfleiderer \u03b1")
diamond(0.4, 6.2, 0.9, 1.6, "Slip-factor method?", "Busemann\u2013Wiesner or Pfleiderer")
teal_step(8.2, 15.6, 1.35, 2.15, "e)  Blade Construction  \u2014  Slide 14")

dashed_arrow((6.2, 2.5), (8.2, 1.9), rad=-0.15)
solid_arrow((6.5, 3.4), (7.9, 2.15), rad=0.12)
caption(7.55, 2.85, "hub/shroud surfaces of revolution\n(built on for blade coordinates)",
        color=GRAY_TEXT, fontsize=11.5)

# --- far-right feedback spine (U2 = Omega*r2 carried down to c, d, e) --------
spine_x = 15.9
ax.add_line(Line2D([spine_x, spine_x], [7.7, 1.6], color="#555555", lw=1.8, zorder=3))
ax.annotate("", xy=(15.6, 7.7), xytext=(spine_x, 7.7),
            arrowprops=dict(arrowstyle="-", color="#555555", lw=1.8))
dashed_arrow((spine_x, 5.2), (11.4, 4.9), rad=0.1)
caption(14.6, 4.85, "picks Fig. 12 \u03c6 curve\nvs. hub-to-tip ratio", color=ORANGE_TEXT, fontsize=11.5)
dashed_arrow((spine_x, 4.1), (9.9, 3.8), rad=0.1)
caption(14.6, 3.75, "radial-outflow guideline\nvs. conical / reverse-curve", color=ORANGE_TEXT, fontsize=11.5)
solid_arrow((spine_x, 1.6), (15.6, 1.75), rad=0.0)
caption(14.4, 2.5, "U\u2082 = \u03a9r\u2082 \u2192 outlet\nvelocity triangle & slip factor", color=GRAY_TEXT, fontsize=11.5)

# --- legend -------------------------------------------------------------------
ly = -0.6
ax.add_patch(Rectangle((0.4, ly - 0.16), 0.38, 0.32, facecolor=TEAL, edgecolor="none"))
ax.text(0.95, ly, "a\u2013e process step", ha="left", va="center", fontsize=13, color=DARK_TEXT)

ax.add_patch(Rectangle((4.3, ly - 0.16), 0.38, 0.32, facecolor=ORANGE, edgecolor="none"))
ax.text(4.85, ly, "classification decision", ha="left", va="center", fontsize=13, color=DARK_TEXT)

ax.annotate("", xy=(10.1, ly), xytext=(9.0, ly),
            arrowprops=dict(arrowstyle="-|>", color="#555555", lw=1.8))
ax.text(10.25, ly, "numeric value passed forward", ha="left", va="center", fontsize=13, color=DARK_TEXT)

ax.annotate("", xy=(15.1, ly), xytext=(14.0, ly),
            arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.8, linestyle=(0, (5, 3))))
ax.text(15.25, ly, "classification selects\nformula only", ha="left", va="center", fontsize=13, color=DARK_TEXT)

out_dir = r"C:\Users\Administrator\Downloads\ChemE\Cheme Tools\Equipment Selection and Sizing\Centrifugal Pump\Reference Material"
fig.savefig(out_dir + r"\Impeller Geometry Classification Map (Large Text).pdf", bbox_inches="tight")
fig.savefig(out_dir + r"\Impeller Geometry Classification Map (Large Text).png", dpi=300, bbox_inches="tight")
print("saved.")
