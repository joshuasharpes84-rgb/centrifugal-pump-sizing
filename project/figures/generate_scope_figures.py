"""
generate_scope_figures.py

Two original figures for the sizing-workflow scope (companion to slide 2 / Sizing Workflow.md):

  Page 1 - specific-speed band: the deck's paper-math is valid only for N_s,US ~ 1000-2733
           (omega_s 0.37-1.00), tighter than the slide-2 chart's radial *type* band (~273-2733).
  Page 2 - Q-H coverage: how that N_s limit turns the broad "single-stage centrifugal" region
           into a diagonal band, cutting the high-head/low-flow (multistage) and
           low-head/high-flow (mixed-flow) corners.

Everything is drawn from  N_s = N*sqrt(Q)/H^0.75  -- no textbook figure is reproduced.

    "C:\\Users\\Administrator\\Downloads\\ChemE\\Python\\python.exe" "generate_scope_figures.py"
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon
from matplotlib.lines import Line2D

TEAL, ORANGE, GRAY = "#1a5c73", "#e07b39", "#8a8a8a"
ORANGE_FILL = "#f2c9a8"
OUT = "Workflow Specific-Speed Scope.pdf"

NS_CONV = 2733.016                       # N_s,US = NS_CONV * omega_s
SPEEDS = [3600, 1800, 1200, 900]         # 2/4/6/8-pole @ 60 Hz
NS_LO, NS_HI = 1000.0, NS_CONV * 1.00    # workflow paper-math band (omega_s 0.37 - 1.00)
NS_TYPE_LO = NS_CONV * 0.10              # slide-2 chart radial-type lower bound (~273)

# case studies (Q gpm, H ft, chosen N, label, in-scope)
CASES = [
    (1000, 200, 1800, "A", True), (500, 600, 3600, "B", False),
    (3000,  80, 1800, "C", False), (120, 300, 3600, "D", False),
    ( 800, 250, 1800, "E", False), (1200, 150, 1800, "F", True),
    (1500, 120, 1200, "G", True),  (2000, 100,  900, "H", True),
    (2500,  90,  900, "I", True),  (2509, 105, 1780, "V", True),
]

def H_at(Q, N, Ns):                      # head that puts (Q,N) at specific speed Ns
    return (N * np.sqrt(Q) / Ns) ** (4.0 / 3.0)


# ======================================================================= page 1
def page1(pdf):
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ns = np.logspace(np.log10(120), np.log10(16000), 400)
    omega = ns / NS_CONV

    # pump-type context bands (schematic, standard ranges)
    for x0, x1, lab, col in [
        (120, 500, "positive-displacement /\nmultistage-per-stage", "#dfe6e9"),
        (500, 4200, "radial centrifugal", "#eef4f6"),
        (4200, 9000, "mixed-flow", "#f6efe9"),
        (9000, 16000, "axial", "#efe9f0")]:
        ax.axvspan(x0, x1, color=col, zorder=0)
        ax.text(np.sqrt(x0 * x1), 0.93, lab, ha="center", va="top",
                fontsize=8.5, color=GRAY, transform=ax.get_xaxis_transform())

    # psi_target curve (Fig. 12 fit) on right axis - why low N_s fails
    ax2 = ax.twinx()
    psi = 0.383 / omega ** (1.0 / 3.0)
    ax2.plot(ns, psi, color=TEAL, lw=2)
    ax2.axhspan(0.60, 1.2, color=TEAL, alpha=0.10)
    ax2.set_ylim(0.2, 1.05)
    ax2.set_ylabel(r"head coefficient  $\psi_{target}=0.383/\Omega_s^{1/3}$  (Fig. 12)", color=TEAL)
    ax2.tick_params(axis="y", colors=TEAL)
    ax2.text(560, 0.74, "no valid 15-35 deg\nbackward-curved blade\n"
             r"above $\psi\approx0.6$", fontsize=8, color=TEAL, va="center", ha="center")

    # the bands
    ax.axvspan(NS_LO, NS_HI, color=ORANGE, alpha=0.28, zorder=1)
    ax.axvline(NS_LO, color=ORANGE, lw=2)
    ax.axvline(NS_HI, color=ORANGE, lw=2)
    ax.axvline(NS_TYPE_LO, color=GRAY, lw=1.4, ls="--")
    ax.text(NS_TYPE_LO * 1.03, 0.06, "slide-2 chart\nradial-type edge\n(~273)", fontsize=8,
            color=GRAY, transform=ax.get_xaxis_transform(), va="bottom")
    ax.text(np.sqrt(NS_LO * NS_HI), 0.52,
            "WORKFLOW\npaper-math valid\n"
            r"$N_s$ 1000-2733   ($\Omega_s$ 0.37-1.00)",
            ha="center", va="center", fontsize=10.5, fontweight="bold", color="#b5541a",
            transform=ax.get_xaxis_transform())

    # case-study ticks (stagger labels so close cases don't collide)
    for i, (Q, H, N, lab, ok) in enumerate(sorted(CASES, key=lambda t: t[0])):
        nsv = N * np.sqrt(Q) / H ** 0.75
        col = "#2e7d32" if ok else "#c0392b"
        ax.plot([nsv], [0.30], marker="v", ms=8, color=col,
                transform=ax.get_xaxis_transform(), clip_on=False)
        yoff = 0.245 if i % 2 == 0 else 0.19
        ax.text(nsv, yoff, lab, ha="center", va="top", fontsize=8, color=col,
                transform=ax.get_xaxis_transform())

    ax.set_xscale("log")
    ax.set_xlim(120, 16000)
    ax.set_yticks([])
    ax.set_xlabel(r"specific speed  $N_{s,US}=N\sqrt{Q}\,/\,H^{0.75}$   (rpm, gpm, ft)")
    axt = ax.secondary_xaxis("top", functions=(lambda x: x / NS_CONV, lambda x: x * NS_CONV))
    axt.set_xlabel(r"universal  $\Omega_s$")
    ax.set_title("Sizing-workflow specific-speed limit vs. the slide-2 radial-type band",
                 fontsize=12, fontweight="bold")
    ax.legend(handles=[Line2D([], [], marker="v", ls="", color="#2e7d32", label="case in scope"),
                       Line2D([], [], marker="v", ls="", color="#c0392b", label="case rejected")],
              loc="lower right", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    pdf.savefig(fig); plt.close(fig)


# ======================================================================= page 2
def page2(pdf):
    fig, ax = plt.subplots(figsize=(11, 7.4))
    Q = np.logspace(1, np.log10(20000), 400)

    # schematic single-stage centrifugal *type* coverage, as top/bottom curves of Q
    #   (deliberately generic - the point is the shape, not a specific chart)
    def env_hi(q):
        return np.clip(3.0e3 * (q / 3000.0) ** 0.15, None,
                       np.where(q < 3000, 1e9, 3.0e3 * (3000.0 / q) ** 0.9))
    def env_lo(q):
        return np.where(q < 2500, 14.0, 14.0 * (q / 2500.0) ** 0.9)
    e_hi = np.minimum(env_hi(Q), 1500.0)
    e_lo = env_lo(Q)
    inside_env = (Q >= 25) & (Q <= 15000)
    e_hi = np.where(inside_env, e_hi, np.nan)
    e_lo = np.where(inside_env, e_lo, np.nan)
    ax.fill_between(Q, e_lo, e_hi, color="#ededed", edgecolor=GRAY, lw=1.3, ls="--",
                    zorder=1, label="single-stage centrifugal by type (slide-2 highlight)")

    # N_s band: union over the 4 standard speeds of  N_s in [NS_LO, NS_HI]
    band_hi = H_at(Q, max(SPEEDS), NS_LO)        # N=3600, N_s=1000  (top)
    band_lo = H_at(Q, min(SPEEDS), NS_HI)        # N=900,  N_s=2733  (bottom)

    # workflow-sizeable = envelope AND band
    w_lo = np.nanmax(np.vstack([e_lo, band_lo]), axis=0)
    w_hi = np.nanmin(np.vstack([e_hi, band_hi]), axis=0)
    ok = inside_env & (w_hi > w_lo)
    ax.fill_between(Q, w_lo, w_hi, where=ok, color=ORANGE, alpha=0.55, lw=0, zorder=3,
                    label=r"workflow can size  ($N_s$ 1000-2733)")

    # "lost" wedges = envelope minus band
    ax.fill_between(Q, np.minimum(band_hi, e_hi), e_hi,
                    where=inside_env & (e_hi > band_hi), color=GRAY, alpha=0.32,
                    hatch="////", lw=0, zorder=2)
    ax.fill_between(Q, e_lo, np.maximum(band_lo, e_lo),
                    where=inside_env & (band_lo > e_lo), color=GRAY, alpha=0.32,
                    hatch="\\\\\\\\", lw=0, zorder=2)

    # constant-N_s edges (thin) for the two bounding speeds, with labels
    for N in (3600, 900):
        ax.plot(Q, H_at(Q, N, NS_LO), color="#b5541a", lw=0.9, alpha=0.75)
        ax.plot(Q, H_at(Q, N, NS_HI), color="#b5541a", lw=0.9, alpha=0.75, ls=(0, (4, 2)))
    ax.text(16500, H_at(16500, 3600, NS_LO), r"3600 rpm, $N_s$=1000", fontsize=7,
            color="#b5541a", va="center", ha="left")
    ax.text(16500, H_at(16500, 900, NS_HI), r"900 rpm, $N_s$=2733", fontsize=7,
            color="#b5541a", va="center", ha="left")

    ax.annotate(r"lost: $N_s<1000$  $\rightarrow$  multistage",
                xy=(150, 430), xytext=(45, 900), fontsize=9.5, color="#444",
                arrowprops=dict(arrowstyle="->", color="#444"))
    ax.annotate(r"lost: $N_s>2733$  $\rightarrow$  mixed-flow",
                xy=(6000, 33), xytext=(1100, 7.5), fontsize=9.5, color="#444",
                arrowprops=dict(arrowstyle="->", color="#444"))

    for Qc, Hc, N, lab, inok in CASES:
        col = "#2e7d32" if inok else "#c0392b"
        ax.plot([Qc], [Hc], "o", ms=7, mfc=col, mec="white", zorder=6)
        ax.annotate(lab, (Qc, Hc), textcoords="offset points", xytext=(6, 4),
                    fontsize=8.5, fontweight="bold", color=col, zorder=6)

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(10, 20000); ax.set_ylim(5, 2000)
    ax.set_xlabel("capacity  Q  (gpm)")
    ax.set_ylabel("head  H  (ft)")
    ax.set_title(r"How the $N_s$ 1000-2733 limit reshapes the workflow's Q-H coverage",
                 fontsize=12, fontweight="bold")
    ax.grid(True, which="both", color="#e8e8e8", lw=0.5)
    ax.legend(loc="lower left", fontsize=8, framealpha=0.95)
    ax.text(0.99, 0.02,
            r"$N_{ss}$ (suction) clips the high-Q edge further, depending on $NPSH_a$ - not shown",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5, color="#999")
    fig.tight_layout()
    pdf.savefig(fig); plt.close(fig)


if __name__ == "__main__":
    with PdfPages(OUT) as pdf:
        page1(pdf)
        page2(pdf)
    print("wrote", OUT)
