"""Draw every README figure from the aggregate result tables, in a journal (Nature-like) style.

Reads only CSV files under results/ and writes SVG and PNG to figures/. Every number shown is read from the tables at
run time. Style: double-column width (183 mm), Arial 7 pt, lower-case bold panel letters, left and bottom axes only,
outward ticks, no grid, error bars with caps. Colour carries one meaning throughout: dark blue for the main estimate,
red for battery-electric vehicles and installation support, grey for comparison vehicles and baselines, light blue-grey
for sensitivity estimates. Open markers mark the comparison group; value labels are in near-black.

Usage: python code/make_figures.py [--results results] [--out figures]
"""
import argparse
import ast
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle

MM = 1 / 25.4
W = 183 * MM                      # double-column width
INK, MUTED = "#222222", "#6b6b6b"
NAVY, RED, GREY, LGREY, SENS, TEAL = "#3C5488", "#E64B35", "#8C8C8C", "#D0D0D0", "#8491B4", "#4DBBD5"

FIPS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC",
        "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
        "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT",
        "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
        "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
        "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY"}
RECENT_15 = {"CO", "TX", "TN", "IA", "ID", "VA", "WI", "WY", "MA", "MD", "ND", "SD", "NM", "NC", "MT"}
TILES = {"AK": (0, 0), "ME": (11, 0), "WI": (6, 1), "VT": (10, 1), "NH": (11, 1),
         "WA": (1, 2), "ID": (2, 2), "MT": (3, 2), "ND": (4, 2), "MN": (5, 2), "IL": (6, 2), "MI": (7, 2), "NY": (9, 2),
         "MA": (10, 2),
         "OR": (1, 3), "NV": (2, 3), "WY": (3, 3), "SD": (4, 3), "IA": (5, 3), "IN": (6, 3), "OH": (7, 3), "PA": (8, 3),
         "NJ": (9, 3), "CT": (10, 3), "RI": (11, 3),
         "CA": (1, 4), "UT": (2, 4), "CO": (3, 4), "NE": (4, 4), "MO": (5, 4), "KY": (6, 4), "WV": (7, 4), "VA": (8, 4),
         "MD": (9, 4), "DE": (10, 4),
         "AZ": (2, 5), "NM": (3, 5), "KS": (4, 5), "AR": (5, 5), "TN": (6, 5), "NC": (7, 5), "SC": (8, 5), "DC": (9, 5),
         "OK": (4, 6), "LA": (5, 6), "MS": (6, 6), "AL": (7, 6), "GA": (8, 6),
         "HI": (0, 7), "TX": (4, 7), "FL": (9, 7)}
MAIN_SPEC = "3 + people, ZIP"
COVARIATE_NAMES = {
    "hh_size": "Household size", "ppi_score": "Purchasing-power score", "wealth_score": "Wealth score",
    "lor_years": "Years at the address", "age_oldest": "Age of oldest member", "zip_renter_share": "Renter share, ZIP code",
    "zip_median_wealth": "Median wealth, ZIP code", "educ_code_missing": "Education not recorded",
    "child_code_missing": "Children not recorded", "child_code_Y": "Children in household",
}


# ---------------------------------------------------------------------------------------------------------- style --

def style():
    plt.rcParams.update({
        "font.family": ["Arial", "Helvetica", "DejaVu Sans"], "font.size": 7, "axes.titlesize": 7, "axes.labelsize": 7,
        "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.5, "legend.frameon": False,
        "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": INK, "xtick.color": INK, "ytick.color": INK,
        "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5,
        "ytick.major.size": 2.5, "xtick.direction": "out", "ytick.direction": "out", "xtick.major.pad": 2,
        "ytick.major.pad": 2, "axes.labelpad": 3, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "figure.facecolor": "white", "savefig.facecolor": "white", "svg.fonttype": "none",
        "lines.linewidth": 0.8, "lines.solid_capstyle": "butt", "svg.hashsalt": "fig"})


def panel(ax, letter, title=""):
    ax._panel = (letter, title)


def place_letters(fig, pad=0.06):
    """Lower-case bold letter at the left edge of each panel (tick labels included), title beside it, one baseline."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    axes = [a for a in fig.axes if hasattr(a, "_panel")]
    top = max(a.get_position().y1 for a in axes) + pad
    for a in axes:
        bb = a.get_tightbbox(r)
        x0 = inv.transform((bb.x0, 0))[0]
        letter, title = a._panel
        fig.text(x0, top, letter, fontsize=8, fontweight="bold", ha="left", va="baseline")
        if title:
            fig.text(x0 + 0.022, top, title, fontsize=7, ha="left", va="baseline")


def save(fig, out, name, pad=0.06):
    place_letters(fig, pad)
    for ext in ("svg", "png"):
        fig.savefig(out / f"{name}.{ext}", dpi=400, metadata={"Date": None} if ext == "svg" else None)
    plt.close(fig)
    print(name)


def cat_axis(ax, labels):
    """Categories on the y axis, first label at the top; no y spine or ticks."""
    n = len(labels)
    ax.set_yticks(range(n)); ax.set_yticklabels(labels[::-1])
    ax.tick_params(axis="y", length=0, pad=3)
    ax.spines["left"].set_visible(False)
    ax.set_ylim(-0.6, n - 0.4)


def errdots(ax, est, lo, hi, colors, y=None, marker="o", face=None, size=16, label=None):
    n = len(est)
    ys = y if y is not None else [n - 1 - i for i in range(n)]
    for i in range(n):
        ax.errorbar(est[i], ys[i], xerr=[[est[i] - lo[i]], [hi[i] - est[i]]], fmt="none", ecolor=colors[i],
                    elinewidth=0.8, capsize=1.8, capthick=0.8, zorder=2)
        ax.scatter(est[i], ys[i], s=size, marker=marker, color=face[i] if face else colors[i], edgecolor=colors[i],
                   linewidth=0.8, zorder=3, label=label if i == 0 else None)


def vlabel(ax, x, y, text, color=INK, ha="left", dx=3, size=6.3):
    ax.annotate(text, (x, y), xytext=(dx if ha == "left" else -dx, 0), textcoords="offset points", ha=ha, va="center",
                fontsize=size, color=color, annotation_clip=False)


def pct(x):
    v = int(np.floor(abs(x) + 0.5))
    return f"{'−' if x < 0 else '+'}{v}%" if v else "0%"


def minus(v, d=1):
    return f"{v:.{d}f}".replace("-", "−")


def r2(v):
    return str(Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def ci(text):
    lo, hi = ast.literal_eval(text)
    return float(lo), float(hi)


def pct_axis(ax, ticks, axis="x", signed=True):
    f = (lambda v, _: (f"{v:.0f}".replace("-", "−")))
    (ax.set_xticks if axis == "x" else ax.set_yticks)(ticks)
    (ax.xaxis if axis == "x" else ax.yaxis).set_major_formatter(f)


# ---------------------------------------------------------------------------------------------------- the tables --

def load(res):
    t = {}
    t["park"] = pd.read_csv(res / "2_parking/parking_by_tenure.csv")
    t["vt"] = pd.read_csv(res / "3_renter_gap/gap_by_vehicle_type.csv").set_index("quantity")
    est = pd.read_csv(res / "3_renter_gap/ownership_renters_vs_owners.csv")
    t["est"] = est[est.specification == "full controls"].set_index(["outcome", "estimator"])
    cl = pd.read_csv(res / "3_renter_gap/net_gap_by_estimator.csv")
    t["cl"] = cl[cl.specification == "full controls"].set_index(["estimator", "control"])
    em = pd.read_csv(res / "3_renter_gap/exact_matching.csv")
    t["em"] = em[em["matching cells"] == "+ household size and years at the address"].set_index("quantity")
    po = pd.read_csv(res / "3_renter_gap/poisson_by_household_type.csv")
    t["po"] = po[(po.comparison == "building type x tenure") & (po.spec == MAIN_SPEC)].set_index("level")
    t["pol"] = pd.read_csv(res / "4_policy/policy_costs.csv").set_index("policy")
    t["chk"] = pd.read_csv(res / "4_policy/simulation_checks.csv").set_index("quantity")
    return t


COST = "cost per additional plug-in $"
P_REBATE = "purchase rebate"
P_NEW = "installation support, only new plug-in households claim, full barrier removed"
P_FULL = "installation support, all plug-in renters claim, full barrier removed"
P_HALF = "installation support, all plug-in renters claim, half the barrier removed"
P_QUARTER = "installation support, all plug-in renters claim, a quarter of the barrier removed"


def cost_rows(ax, t, rows, header=None, xlabel=None, clear=10):
    """Rows are (policy, label, colour). header = (row index, text) adds an unplotted group label above that row."""
    d = t["pol"]
    m = [d.loc[k, f"{COST}, mean"] / 1000 for k, *_ in rows]
    lo = [d.loc[k, f"{COST}, 2.5%"] / 1000 for k, *_ in rows]
    hi = [d.loc[k, f"{COST}, 97.5%"] / 1000 for k, *_ in rows]
    n = len(rows) + (1 if header else 0)
    ys, ticks, y = [], [], n - 1
    for i, (_, lab, _) in enumerate(rows):
        if header and i == header[0]:
            ticks.append((y, header[1])); y -= 1
        ys.append(y); ticks.append((y, lab)); y -= 1
    ax.axvline(m[0], color=NAVY, lw=0.6, ls=(0, (3, 2)), zorder=1)
    errdots(ax, m, lo, hi, [c for *_, c in rows], y=ys)
    for i, v in enumerate(m):
        if i and 0 < m[0] - hi[i] < clear:        # a label to the right would run into the dashed rebate line: put it above
            ax.annotate(f"{v:.1f}", (v, ys[i]), xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                        fontsize=6.3, color=INK)
        else:
            vlabel(ax, max(hi[i], v), ys[i], f"{v:.1f}", dx=5)
    ax.set_yticks([y for y, _ in ticks]); ax.set_yticklabels([lab for _, lab in ticks])
    ax.tick_params(axis="y", length=0, pad=3); ax.spines["left"].set_visible(False); ax.set_ylim(-0.6, n - 0.4)
    if header:
        for tl in ax.get_yticklabels():
            if tl.get_text() == header[1]:
                tl.set_fontweight("bold")
    ax.set_xlim(0, 60); ax.set_xticks([0, 20, 40, 60])
    ax.set_xlabel(xlabel or "US$ thousands per additional\nplug-in household")


# ------------------------------------------------------------------------------------------------------- figures --

def fig1_story(res, out, t):
    fig = plt.figure(figsize=(W, 2.15))
    gs = fig.add_gridspec(1, 3, left=0.1, right=0.97, top=0.82, bottom=0.25, wspace=0.95, width_ratios=[0.8, 1, 1])

    a = fig.add_subplot(gs[0]); panel(a, "a", "No visible private parking")
    p = t["park"][t["park"].building == "single_family"].set_index("tenure")
    keys = [("owner", "Owned", GREY), ("renter", "Rented", NAVY)]
    est = [p.loc[k, "without private parking %"] for k, *_ in keys]
    errdots(a, est, [p.loc[k, "ci low"] for k, *_ in keys], [p.loc[k, "ci high"] for k, *_ in keys], [c for *_, c in keys],
            face=["white", NAVY])
    for i, (k, _, c) in enumerate(keys):
        vlabel(a, p.loc[k, "ci high"], 1 - i, f"{est[i]:.1f}%")
    cat_axis(a, [lab for _, lab, _ in keys])
    a.set_ylim(-1.5, 1.4)
    d = p.loc["renter minus owner"]
    a.text(0.3, -1.05, f"Difference {minus(d['without private parking %'])} pp (95% CI {minus(d['ci low'])} to {minus(d['ci high'])})",
           ha="left", va="center", fontsize=6, color=INK)
    a.set_xlim(0, 16); a.set_xticks([0, 5, 10, 15])
    a.set_xlabel("Single-family homes without\nprivate off-street parking (%)")

    b = fig.add_subplot(gs[1]); panel(b, "b", "Ownership gap by vehicle type")
    vt = t["vt"]
    keys = [("recent luxury gasoline", "Luxury gasoline", GREY), ("hybrid", "Hybrid", GREY),
            ("plug-in hybrid", "Plug-in hybrid", NAVY), ("battery-electric", "Battery-electric", RED)]
    est = [vt.loc[k, "percent"] for k, *_ in keys]
    lo = [vt.loc[k, "percent ci low"] for k, *_ in keys]
    errdots(b, est, lo, [vt.loc[k, "percent ci high"] for k, *_ in keys], [c for *_, c in keys])
    hi = [vt.loc[k, "percent ci high"] for k, *_ in keys]
    for i, (k, _, c) in enumerate(keys):
        vlabel(b, hi[i], 3 - i, pct(est[i]))
    cat_axis(b, [lab for _, lab, _ in keys])
    b.set_xlim(-65, 0); b.set_xticks([-60, -40, -20, 0]); pct_axis(b, [-60, -40, -20, 0])
    b.set_xlabel("Renters vs comparable owners (%)")

    c = fig.add_subplot(gs[2]); panel(c, "c", "Cost per added plug-in household")
    cost_rows(c, t, [(P_REBATE, "Purchase rebate", NAVY), (P_FULL, "Installation, full removal", RED),
                     (P_HALF, "Installation, half removal", RED)],
              xlabel="US$ thousands per additional plug-in\nhousehold; all plug-in renters claim")
    save(fig, out, "fig1_story")


def fig2_build(res, out, t):
    st = pd.read_csv(res / "1_data/states_vs_acs.csv", dtype={"st_fips": str})
    sc = pd.read_csv(res / "1_data/county_error_by_method.csv").set_index("method")
    st["abbr"] = st.st_fips.map(FIPS)
    st["recent"] = st.abbr.isin(RECENT_15)
    old, new = st[~st.recent], st[st.recent]
    fig = plt.figure(figsize=(W, 2.25))
    gs = fig.add_gridspec(1, 3, left=0.03, right=0.98, top=0.82, bottom=0.24, wspace=0.42, width_ratios=[1.05, 1, 0.8])

    a = fig.add_subplot(gs[0]); panel(a, "a", "States with recent vehicle records")
    for ab, (cx, ry) in TILES.items():
        hot = ab in RECENT_15
        a.add_patch(Rectangle((cx + 0.05, 7 - ry + 0.05), 0.9, 0.9, fc=NAVY if hot else "#EDEDED", ec="none"))
        a.text(cx + 0.5, 7 - ry + 0.5, ab, ha="center", va="center", fontsize=5.2, color="white" if hot else INK)
    a.set_xlim(0, 12); a.set_ylim(-1.6, 8); a.set_aspect("equal"); a.set_anchor("N"); a.axis("off")
    a.add_patch(Rectangle((0.05, -1.25), 0.6, 0.6, fc=NAVY, ec="none"))
    a.text(0.9, -0.95, f"Used: {len(new)} states, {new.households.sum() / 1e6:.1f} million households", fontsize=6, va="center")

    b = fig.add_subplot(gs[1]); panel(b, "b", "Plug-in share by state")
    lim = 22
    b.set_xscale("log"); b.set_yscale("log")
    b.plot([1, lim], [1, lim], color=GREY, lw=0.6, ls=(0, (3, 2)))
    b.scatter(old.acs_ev_pct, old.plugin_pct, s=9, color="white", edgecolor=GREY, linewidth=0.6, zorder=2,
              label=f"Older records ({len(old)})")
    b.scatter(new.acs_ev_pct, new.plugin_pct, s=11, color=NAVY, edgecolor="none", zorder=3,
              label=f"Recent records ({len(new)})")
    b.set_xlim(1, lim); b.set_ylim(0.05, lim)
    b.set_xticks([1, 2, 5, 10, 20]); b.set_xticklabels(["1", "2", "5", "10", "20"])
    b.set_yticks([0.1, 1, 10]); b.set_yticklabels(["0.1", "1", "10"]); b.minorticks_off()
    b.set_xlabel("ACS: households with a vehicle\nthat have an EV (%)")
    b.set_ylabel("Linked table: households\nowning a plug-in (%)")
    b.legend(loc="upper left", handletextpad=0.2, borderaxespad=0.2)
    p1, p2 = b.transData.transform([(2, 2), (10, 10)])
    ang = np.degrees(np.arctan2(p2[1] - p1[1], p2[0] - p1[0]))
    b.text(14, 15.5, "Equal shares", rotation=ang, rotation_mode="anchor", ha="center", va="bottom", fontsize=5.8,
           color=INK)

    c = fig.add_subplot(gs[2]); panel(c, "c", f"County error ({int(sc.loc['raw', 'counties'])} counties)")
    rows = [("raw", "As built", GREY), ("state_scaled", "Scaled to\nstate total", GREY), ("model_scaled", "Calibrated", NAVY)]
    vals = [sc.loc[k, "mae_pp"] for k, *_ in rows]
    c.bar(range(3), vals, width=0.6, color=[col for *_, col in rows], edgecolor="none")
    moe = sc.filter(like="reference", axis=0).mae_pp.iloc[0]
    for i, v in enumerate(vals):
        if v < moe < v + 0.3:      # a label above the bar would touch the reference line: put it inside the bar
            c.text(i, v - 0.06, r2(v), ha="center", va="top", fontsize=6.3, color=INK)
        else:
            c.text(i, v + 0.05, r2(v), ha="center", va="bottom", fontsize=6.3, color=INK)
    c.axhline(moe, color=MUTED, lw=0.6, ls=(0, (3, 2)))
    c.text(2.45, moe + 0.06, f"ACS median 90%\nmargin, {r2(moe)}", ha="right", va="bottom", fontsize=5.8, color=INK)
    c.set_xticks(range(3)); c.set_xticklabels([lab for _, lab, _ in rows]); c.tick_params(axis="x", length=0)
    c.set_ylim(0, 2.8); c.set_yticks([0, 1, 2])
    c.set_ylabel("Mean absolute error (pp)")
    c.set_xlim(-0.6, 2.6)
    save(fig, out, "fig2_build")


def fig3_measure(res, out, t):
    base = res / "2_parking"
    d = pd.read_csv(base / "parking_shares.csv")
    g0 = d[d.group == "all homes"].set_index("estimator")
    r = pd.read_csv(base / "parking_by_garage_record.csv")
    r = r[r.building == "single_family"].set_index("garage_in_property_record")
    au = pd.read_csv(base / "audit_vs_model.csv").set_index(pd.read_csv(base / "audit_vs_model.csv").columns[0])
    priv, other = ["carport", "driveway_only", "garage"], ["none_visible", "shared_lot"]
    judged = au.loc[priv + other, priv + other]               # both the reviewer and the model could judge
    agree = judged.loc[priv, priv].values.sum() + judged.loc[other, other].values.sum()
    audit_txt = f"{100 * agree / judged.values.sum():.1f}% agreement on {int(judged.values.sum())}"
    fig = plt.figure(figsize=(W, 2.25))
    gs = fig.add_gridspec(1, 3, left=0.03, right=0.98, top=0.82, bottom=0.24, wspace=0.75, width_ratios=[0.95, 0.9, 1])

    a = fig.add_subplot(gs[0]); panel(a, "a", "From image to estimate")
    a.axis("off"); a.set_xlim(0, 1); a.set_ylim(0, 1)
    boxes = [(f"{int(g0.imaged_homes.iloc[0]):,} street-level images", "one per sampled home"),
             ("Vision-model label", f"{g0.usable_by_model_pct.iloc[0]:.0f}% of images usable"),
             (f"Blind audit of {int(g0.audited_homes.iloc[0])} images", audit_txt),
             ("Prediction-powered inference", "audit corrects model labels")]
    h, gap = 0.18, 0.075
    for i, (head, sub) in enumerate(boxes):
        y = 0.98 - h - i * (h + gap)
        a.add_patch(FancyBboxPatch((0.03, y), 0.94, h, boxstyle="round,pad=0,rounding_size=0.02",
                                   fc="#F2F4F8" if i < 3 else "#DCE3F0", ec=NAVY if i == 3 else LGREY, lw=0.6))
        a.text(0.5, y + h * 0.65, head, ha="center", va="center", fontsize=6.5, fontweight="bold", color=NAVY)
        a.text(0.5, y + h * 0.28, sub, ha="center", va="center", fontsize=6, color=MUTED)
        if i < len(boxes) - 1:
            a.annotate("", xy=(0.5, y - gap + 0.005), xytext=(0.5, y - 0.005),
                       arrowprops=dict(arrowstyle="-|>", color=GREY, lw=0.7, mutation_scale=6))

    b = fig.add_subplot(gs[1]); panel(b, "b", "Property record vs image")
    rows = [(k, lab) for k, lab in [("attached", "Attached garage"), ("other", "Other parking entry"),
                                     ("detached", "Detached garage"), ("unrecorded", "Garage field blank")] if k in r.index]
    vals = [r.loc[k, "no_private_parking_pct_of_usable"] for k, _ in rows]
    b.barh(range(len(rows))[::-1], vals, height=0.6, color=[NAVY if k == "unrecorded" else GREY for k, _ in rows],
           edgecolor="none")
    for i, v in enumerate(vals):
        vlabel(b, v, len(rows) - 1 - i, f"{v:.1f}%")
    cat_axis(b, [lab for _, lab in rows])
    b.set_xlim(0, 15); b.set_xticks([0, 5, 10, 15])
    b.set_xlabel("Single-family homes without\nprivate parking in the image (%)")

    # c: single-family homes on their own scale (the comparison used in section 3), multi-unit homes below
    p = t["park"].set_index(["building", "tenure"])
    groups = [("owner", GREY, "white", 0.17, "Owners"), ("renter", NAVY, NAVY, -0.17, "Renters")]

    def tenure_rows(ax, blds):
        n = len(blds)
        for tenure, color, face, off, lab in groups:
            est = [p.loc[(bd, tenure), "without private parking %"] for bd, _ in blds]
            lo = [p.loc[(bd, tenure), "ci low"] for bd, _ in blds]
            hi = [p.loc[(bd, tenure), "ci high"] for bd, _ in blds]
            ys = [n - 1 - i + off for i in range(n)]
            errdots(ax, est, lo, hi, [color] * n, y=ys, face=[face] * n, label=lab)
            for i in range(n):
                vlabel(ax, hi[i], ys[i], f"{est[i]:.1f}%" if n == 1 else f"{est[i]:.0f}%", size=6)
        cat_axis(ax, [lab for _, lab in blds])

    sub = gs[2].subgridspec(2, 1, height_ratios=[1, 1.9], hspace=0.7)
    c = fig.add_subplot(sub[0]); panel(c, "c", "Owners vs renters")
    tenure_rows(c, [("single_family", "Single-family")])
    c.set_xlim(0, 15); c.set_xticks([0, 5, 10, 15])
    c2 = fig.add_subplot(sub[1])
    tenure_rows(c2, [("condo", "Condo"), ("multi_unit", "Other multi-unit")])
    c2.set_xlim(0, 100); c2.set_xticks([0, 25, 50, 75, 100])
    c2.set_xlabel("Homes without private\nparking in the image (%)")
    c2.legend(loc="upper left", handletextpad=0.1, borderaxespad=0.1)
    save(fig, out, "fig3_measure")


def fig4_predictions(res, out, t):
    fig = plt.figure(figsize=(W, 2.25))
    gs = fig.add_gridspec(1, 3, left=0.07, right=0.98, top=0.82, bottom=0.24, wspace=0.9, width_ratios=[0.9, 1, 1])

    a = fig.add_subplot(gs[0]); panel(a, "a", "Comparable households")
    est = t["est"]
    rows = [("All\nowners", est.loc[("plug-in", "unadjusted"), "rate, comparison %"], GREY),
            ("Comparable\nowners", est.loc[("plug-in", "AIPW (ATT)"), "rate, comparison %"], SENS),
            ("Renters", est.loc[("plug-in", "AIPW (ATT)"), "rate, renters %"], NAVY)]
    a.bar(range(3), [v for _, v, _ in rows], width=0.62, color=[c for *_, c in rows], edgecolor="none")
    for i, (_, v, c) in enumerate(rows):
        a.text(i, v + 0.06, f"{v:.2f}", ha="center", va="bottom", fontsize=6.3)
    ratio = est.loc[("plug-in", "AIPW (ATT)"), "ratio"]
    y0 = rows[1][1] + 0.45
    a.plot([1, 1, 2, 2], [rows[1][1] + 0.3, y0, y0, rows[2][1] + 0.3], color=INK, lw=0.6)
    a.text(1.5, y0 + 0.05, pct(100 * (ratio - 1)), ha="center", va="bottom", fontsize=6.5, fontweight="bold", color=NAVY)
    a.set_xticks(range(3)); a.set_xticklabels([lab for lab, *_ in rows], fontsize=6); a.tick_params(axis="x", length=0)
    a.set_ylim(0, 3.3); a.set_yticks([0, 1, 2, 3]); a.set_xlim(-0.6, 2.6)
    a.set_ylabel("Households owning a plug-in (%)")

    b = fig.add_subplot(gs[1]); panel(b, "b", "Net of vehicles without a plug")
    po = t["po"].loc["single_family renter"]
    methods = ["AIPW", "Exact matching", "Within-ZIP Poisson"]
    for j, (key, face, off, lab) in enumerate([("hybrid", "white", 0.15, "vs hybrids"),
                                              ("recent luxury gasoline", None, -0.15, "vs luxury gasoline")]):
        r1 = t["cl"].loc[("AIPW (ATT)", key)]
        r2_ = t["em"].loc[f"net gap vs {key}"]
        col = "net gap vs hybrid" if key == "hybrid" else "net gap vs luxury gasoline"
        p_lo, p_hi = ci(po[f"{col} % ci"])
        est = [r1["net gap %"], r2_["percent"], po[f"{col} %"]]
        lo = [r1["net gap % ci low"], r2_["percent ci low"], p_lo]
        hi = [r1["net gap % ci high"], r2_["percent ci high"], p_hi]
        colors = [NAVY, SENS, SENS]
        errdots(b, est, lo, hi, colors, y=[2 - i + off for i in range(3)],
                face=[face or c for c in colors], label=lab)
        for i in range(3):
            vlabel(b, lo[i], 2 - i + off, pct(est[i]), ha="right", size=5.8)
    cat_axis(b, methods)
    b.set_xlim(-45, 0); pct_axis(b, [-40, -30, -20, -10, 0])
    b.set_xlabel("Plug-in gap net of the\ncomparison vehicle (%)")
    from matplotlib.lines import Line2D
    key = [Line2D([], [], ls="none", marker="o", ms=4, mfc=mfc, mec=INK, mew=0.8) for mfc in ("white", INK)]
    b.set_ylim(-1.45, 2.6)
    b.legend(key, ["vs hybrids", "vs luxury gasoline"], loc="lower center", ncol=2, handletextpad=0.1,
             columnspacing=0.8, borderaxespad=0.1)

    c = fig.add_subplot(gs[2]); panel(c, "c", "Step in charging reliance")
    vt = t["vt"]
    steps = [("plug-in hybrid vs hybrid", "Hybrid → PHEV", GREY),
             ("battery-electric vs plug-in hybrid", "PHEV → battery-electric", RED)]
    est = [vt.loc[k, "percent"] for k, *_ in steps]
    lo = [vt.loc[k, "percent ci low"] for k, *_ in steps]
    hi = [vt.loc[k, "percent ci high"] for k, *_ in steps]
    c.axvline(0, color=GREY, lw=0.6)
    errdots(c, est, lo, hi, [s[2] for s in steps])
    for i, s in enumerate(steps):
        vlabel(c, hi[i], 1 - i, pct(est[i]))
    cat_axis(c, [s[1] for s in steps])
    c.set_xlim(-35, 10); pct_axis(c, [-30, -20, -10, 0, 10])
    c.set_xlabel("Change in renter–owner\nownership ratio (%)")
    save(fig, out, "fig4_predictions")


def fig5_policy(res, out, t):
    d = t["pol"]
    fig = plt.figure(figsize=(W, 2.3))
    gs = fig.add_gridspec(1, 3, left=0.07, right=0.95, top=0.82, bottom=0.24, wspace=1.05, width_ratios=[0.62, 1.1, 0.8])

    a = fig.add_subplot(gs[0]); panel(a, "a", "Rebate recipients")
    share = d.loc[P_REBATE, "share of recipients who would own one anyway %, mean"]
    a.bar([0], [share], width=0.55, color=GREY, edgecolor="none")
    a.bar([0], [100 - share], bottom=[share], width=0.55, color=NAVY, edgecolor="none")
    a.text(0.36, share / 2, f"Would own one\nanyway: {share:.0f}%", va="center", fontsize=6.3)
    a.text(0.36, share + (100 - share) / 2, f"Added by the\nrebate: {100 - share:.0f}%", va="center", fontsize=6.3)
    a.set_xlim(-0.4, 1.6); a.set_ylim(0, 100); a.set_xticks([]); a.spines["bottom"].set_visible(False)
    a.set_yticks([0, 25, 50, 75, 100]); a.set_ylabel("Share of recipients (%)")
    m = t["chk"].loc["rebate that offsets the barrier, $ per vehicle, mean", "simulation"]
    a.set_xlabel(f"Mean rebate ${m:,.0f} per vehicle")

    b = fig.add_subplot(gs[1]); panel(b, "b", "Cost per added plug-in household")
    cost_rows(b, t, [(P_REBATE, "Purchase rebate", NAVY), (P_NEW, "new plug-in households, full", RED),
                     (P_FULL, "all plug-in renters, full", RED), (P_HALF, "all plug-in renters, half", RED),
                     (P_QUARTER, "all plug-in renters, quarter", RED)],
              header=(1, "Installation support"), clear=7)

    c = fig.add_subplot(gs[2]); panel(c, "c", "Installation costs less")
    col = "share of draws cheaper than the purchase rebate %"
    rows = [(P_FULL, "Full"), (P_HALF, "Half"), (P_QUARTER, "Quarter")]
    vals = [d.loc[k, col] for k, _ in rows]
    c.barh([2, 1, 0], vals, height=0.6, color=RED, edgecolor="none")
    for i, v in enumerate(vals):
        vlabel(c, v, 2 - i, f"{v:.0f}%", color=INK)
    cat_axis(c, [lab for _, lab in rows])
    c.set_xlim(0, 100); c.set_xticks([0, 50, 100])
    c.set_ylabel("Barrier removed")
    c.set_xlabel("Share of 500 draws (%);\nall plug-in renters claim")
    save(fig, out, "fig5_policy")


def fig6_who(res, out, t):
    base = res / "5_which_renters"
    f = pd.read_csv(base / "forest_fifths.csv")
    tg = pd.read_csv(base / "shortfall_share_by_ranking.csv")
    s = pd.read_csv(base / "auc_by_held_out_state.csv")
    s = s[(s.target == "has_plugin") & (s["sample"] == "all households") & (s.features == "people, home and place")]
    fig = plt.figure(figsize=(W, 2.35))
    gs = fig.add_gridspec(1, 3, left=0.11, right=0.97, top=0.76, bottom=0.24, wspace=0.8, width_ratios=[0.9, 0.95, 0.7])

    a = fig.add_subplot(gs[0]); panel(a, "a", "Causal forest, held-out households")
    m = len(f)
    pred = list(f["mean predicted effect pp"]); estv = list(f["plug-in: effect pp"])
    ys = [m - 1 - i for i in range(m)]
    a.axvline(0, color=GREY, lw=0.6)
    a.scatter(pred, [y + 0.12 for y in ys], s=14, color="white", edgecolor=GREY, linewidth=0.8, zorder=3, label="Predicted")
    a.scatter(estv, [y - 0.12 for y in ys], s=14, color=NAVY, edgecolor="none", zorder=3, label="Estimated")
    cat_axis(a, ["Fifth 1 (most)", "Fifth 2", "Fifth 3", "Fifth 4", "Fifth 5 (least)"][:m])
    a.set_xlim(-3.4, 0.3); a.set_xticks([-3, -2, -1, 0]); pct_axis(a, [-3, -2, -1, 0])
    a.set_xlabel("Effect of renting on plug-in\nownership (percentage points)")
    a.legend(loc="lower left", ncol=2, handletextpad=0.1, columnspacing=0.8, borderaxespad=0.2, bbox_to_anchor=(0.0, 1.0))

    b = fig.add_subplot(gs[1]); panel(b, "b", "Share of the shortfall in the top fifth")
    tg20 = tg[tg["renters ranked highest"] == "top 20%"].set_index("ranking")
    rows = [("ownership model (predicted probability of a plug-in)", "Ownership model", NAVY),
            ("causal forest (predicted loss from renting)", "Causal forest", SENS), ("random", "Random fifth", GREY)]
    vals = [tg20.loc[k, "share of missing plug-ins %"] for k, *_ in rows]
    b.barh([2, 1, 0], vals, height=0.6, color=[c for *_, c in rows], edgecolor="none")
    for i, (k, _, c) in enumerate(rows):
        lo, hi = tg20.loc[k, "ci low"], tg20.loc[k, "ci high"]
        if hi > lo:
            b.errorbar(vals[i], 2 - i, xerr=[[vals[i] - lo], [hi - vals[i]]], fmt="none", ecolor=INK, elinewidth=0.7,
                       capsize=1.5, capthick=0.7)
        vlabel(b, max(vals[i], hi), 2 - i, f"{vals[i]:.0f}%")
    cat_axis(b, [lab for _, lab, _ in rows])
    b.set_xlim(0, 100); b.set_xticks([0, 50, 100])
    b.set_xlabel("Share of estimated ownership\nshortfall (%)")

    c = fig.add_subplot(gs[2]); panel(c, "c", "AUC in held-out states")
    s = s.sort_values("auc")
    c.scatter(s.auc, range(len(s)), s=10, color=NAVY, edgecolor="none")
    c.set_yticks(range(len(s))); c.set_yticklabels(s.held_out_state, fontsize=5.6)
    c.tick_params(axis="y", length=0); c.spines["left"].set_visible(False)
    c.set_ylim(-0.7, len(s) - 0.3)
    for y in (0, len(s) - 1):
        vlabel(c, s.auc.iloc[y], y, f"{s.auc.iloc[y]:.2f}", size=5.8)
    c.set_xlim(0.69, 0.84); c.set_xticks([0.70, 0.75, 0.80])
    c.set_xlabel(f"AUC, trained on the\nother {len(s) - 1} states")
    save(fig, out, "fig6_who", pad=0.12)


def figA_diagnostics(res, out, t):
    base = res / "3_renter_gap"
    bal = pd.read_csv(base / "balance.csv")
    raw_col, w_col = bal.columns[1], bal.columns[2]
    top = bal.reindex(bal[raw_col].abs().sort_values(ascending=False).index).head(10)
    ov = pd.read_csv(base / "overlap.csv")
    qrow = pd.to_numeric(ov["quantile"], errors="coerce")
    q = ov[qrow.notna()].assign(q=qrow[qrow.notna()]).set_index("q")
    fig = plt.figure(figsize=(W, 2.4))
    gs = fig.add_gridspec(1, 2, left=0.2, right=0.98, top=0.76, bottom=0.22, wspace=0.35)

    a = fig.add_subplot(gs[0]); panel(a, "a", "Covariate balance")
    m = len(top)
    ys = list(range(m))[::-1]
    for x in (-0.1, 0.1):
        a.axvline(x, color=GREY, lw=0.5, ls=(0, (3, 2)))
        a.text(x, 1.01, f"{x:+.1f}".replace("-", "−"), transform=a.get_xaxis_transform(), ha="center", va="bottom",
               fontsize=5.6, color=INK)
    a.axvline(0, color=GREY, lw=0.6)
    a.scatter(top[raw_col], ys, s=12, color=GREY, edgecolor="none", label="Unweighted", zorder=3)
    a.scatter(top[w_col], ys, s=12, color=NAVY, marker="D", edgecolor="none", label="Weighted", zorder=3)
    names = []
    for c_ in top.covariate:
        if c_ in COVARIATE_NAMES:
            names.append(COVARIATE_NAMES[c_])
        elif c_.startswith("educ_code_"):
            names.append("Education category " + c_[len("educ_code_"):])
        else:
            names.append(c_.replace("_", " ").capitalize())
    cat_axis(a, names)
    lim = top[raw_col].abs().max() * 1.15
    a.set_xlim(-lim, lim); a.set_xticks([-0.5, 0, 0.5]); pct_axis(a, [-0.5, 0, 0.5])
    a.xaxis.set_major_formatter(lambda v, _: f"{v:g}".replace("-", "−"))
    a.set_xlabel("Standardized difference, renters − owners")
    a.legend(loc="upper right", handletextpad=0.1, borderaxespad=0.1)

    b = fig.add_subplot(gs[1]); panel(b, "b", "Propensity overlap")
    for i, (col, name, color) in enumerate([("propensity, renters", "Renters", NAVY), ("propensity, owners", "Owners", GREY)]):
        y = 1 - i
        b.plot([q.loc[0.01, col], q.loc[0.99, col]], [y, y], color=color, lw=0.8)
        b.barh(y, q.loc[0.95, col] - q.loc[0.05, col], left=q.loc[0.05, col], height=0.18, color=color, alpha=0.35,
               edgecolor="none")
        b.barh(y, q.loc[0.75, col] - q.loc[0.25, col], left=q.loc[0.25, col], height=0.38, color=color, edgecolor="none")
        b.scatter(q.loc[0.5, col], y, s=16, color="white", edgecolor=color, linewidth=0.8, zorder=3)
    cat_axis(b, ["Renters", "Owners"])
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    key = [Line2D([], [], ls="none", marker="o", ms=4, mfc="white", mec=INK, mew=0.8),
           Patch(fc=MUTED, ec="none"), Patch(fc=MUTED, alpha=0.35, ec="none"), Line2D([], [], color=MUTED, lw=0.8)]
    b.legend(key, ["Median", "25th–75th", "5th–95th", "1st–99th percentile"], loc="lower left", ncol=4,
             bbox_to_anchor=(0, 1.0), handlelength=1.2, handletextpad=0.3, columnspacing=0.8, borderaxespad=0.2,
             fontsize=5.8)
    b.set_xlim(0, 1); b.set_xticks([0, 0.5, 1]); b.xaxis.set_major_formatter(lambda v, _: f"{v:g}")
    b.set_xlabel("Estimated probability of renting")
    save(fig, out, "figA_diagnostics", pad=0.12)


def main():
    ap = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    ap.add_argument("--results", default=str(root / "results"))
    ap.add_argument("--out", default=str(root / "figures"))
    args = ap.parse_args()
    res, out = Path(args.results), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    style()
    t = load(res)
    for f in (fig1_story, fig2_build, fig3_measure, fig4_predictions, fig5_policy, fig6_who, figA_diagnostics):
        f(res, out, t)


if __name__ == "__main__":
    main()
