# Case Study Sizing Tool — Parameter Limits

Internal reference for `case_study_sizing_tool.py`. Every slider/constant the script uses is
bounded to the ranges below rather than left open — the UI doesn't spell these out (per request),
but they're enforced in code via `PARAM_LIMITS` at the top of the script. Update both together if a
bound changes.

## Interactive (sliders)

| Parameter | Min | Max | Rationale |
|---|---|---|---|
| Q (gpm) | 10 | 10000 | Approximate digitization of the "Centrifugal — single stage, single suction" band in `Pump Selection Guidelines.png` (Fig. 10-24-style pump coverage chart, Perry's/Rules of Thumb). Read off a low-resolution log-log chart by eye, not pixel-digitized — treat as a rectangle approximating a diagonal band; cross-check the actual image near either edge. Outside this band the chart attributes the duty to a different pump type entirely (PD plunger/diaphragm at low Q, axial-flow at very low H + high Q, multistage/double-suction at very high H or Q). |
| H (ft) | 15 | 1000 | Same source and same caveat as Q above. |
| T (°F) | -40 | 400 | Generous process range; `thermo`'s correlations can extrapolate outside this but accuracy degrades — flagged, not blocked. |
| NPSHₐ (ft) | 2 | 200 | Below ~2 ft, essentially no real suction system provides this; above ~200 ft is unusual outside deep-well/booster contexts. |

### Corner flags within the Q/H rectangle

The rectangle above is a coarse stand-in for the chart's actual diagonal band — two corners inside the
rectangle still belong to a different pump type on the real chart:

- **Low Q + high H** (Q < 50 gpm and H > 500 ft): metering plunger/diaphragm territory on Fig. 10-24, not centrifugal.
- **High Q + low H** (Q > 3000 gpm and H < 30 ft): axial-flow territory on Fig. 10-24, not radial/mixed-flow centrifugal.

Both are heuristic corner checks against the same chart, not a full digitization of its diagonal boundary.

## Shaft radius rₛ and eye radius (slide 9/10, Eq. 49/50) — computed, not fixed

As of the slide 9/10 rework (2026-08-26/2026-09-04), φₑ and rₛ are no longer fixed constants — the
tool now runs the same Step 5/6 procedure as `workflow_cases.py`:

1. **Shaft radius rₛ** (Step 5, slide 9): sized from torque, `rₛ = (16M/(π·Sₛ))^(1/3) × keyway^(1/3)`,
   `M = P_hyd/(η_p·Ω)`, first-pass η_p from Anderson's chart fit. This runs regardless of configuration
   — every shaft has *some* radius from torque; the question below is only whether it blocks the eye.
2. **Eye radius** (Step 6, slide 10): rₛ blocks the eye **only for between-bearings (double-suction /
   shaft-through) configurations** — set via the new "Shaft configuration" dropdown. A single-suction
   overhung impeller has a clear eye, so `rₛ_eye = 0` there regardless of the shaft's actual radius.
   φₑ is back-solved from the required suction-specific speed via Eq. 50 (Table 1a / Gongwer), capped
   at 0.30 per slide 10 ("φₑ rarely exceeds 0.3 at the BEP... φₑ < 0.3 for N_s < 12,000"); rₛ/rₑ then
   iterates to convergence for the between-bearings case (seeded at 0.40).

| Parameter | Value | Source |
|---|---|---|
| Sₛ, allowable shear stress | 6000 psi | Carbon-steel keyed shaft, rule-of-thumb (this tool's own decision, see `workflow_cases.py`). |
| Keyway derate | 1.15× | Section-modulus derate for a keyway; slide 10 also flags API 610 shaft-deflection/stiffness as often the real governing limit — not modeled here. |
| Anderson roughness factor X | 1.0 | Rough-cast default for the first-pass η_p chart fit (needs only Q and N_s). |
| Table 1a (Gongwer) k₁, k₂ | 1.69, 0.102 | τ = (k₁+k₂)φₑ² + k₂ — typical-pumps row of Table 1, zero prewhirl. |
| φₑ cap | 0.30 | Slide 10: upper limit of normal practice at BEP even with unlimited NPSH. |
| rₛ/rₑ iteration seed | 0.40 | Slide 10 / Karassik §2.1.1 p.2.29 gives no numeric value — this is an iteration starting guess, not a target; overhung configs never use it (rₛ_eye=0 short-circuits the iteration). |

If φₑ's required suction-specific speed exceeds what any impeller eye can carry (i.e. it would need
φₑ > 0.30's achievable N_ss), the tool flags **INDUCER** and falls back to φₑ=0.30 for the remaining
(not physically meaningful) geometry — inducer sizing itself is not implemented, matching
`workflow_cases.py`'s case I.

### Slide 7's four Nₛₛ remedies — which ones this tool automates

Slide 7 ("Nₛₛ→ Cavitation") lists, in order: **1)** drop speed (N), **2)** add an inducer, **3)**
implement double-suction (Q→Q/2 in Nₛₛ), **4)** alter NPSHₐ. This tool only automates remedy 1 (the
drop-speed cascade above). Remedies 2-4 are surfaced as a flag, not auto-applied:

- **Remedy 2 (inducer)** can't be soundly automated — inducer τ (Table 1b) needs a blade angle β this
  deck gives no formula for (`Sizing Workflow.md` Step 6). When the eye-radius solve fails even at the
  slowest of the 4 speeds, the tool flags "Inducer sizing required" and stops there rather than
  fabricating a β.
- **Remedy 3 (double-suction, Q→Q/2)** is fully closed-form (it's just Q/2 through the same Eq. 49/50
  math) but is **not auto-applied** — deliberately, per user direction (2026-09-04), so the tool
  doesn't silently reorder past remedy 2. It stays available as a **manual** choice via the "Shaft
  configuration" dropdown (between-bearings ⇒ rₛ blocks the eye), but that dropdown does **not**
  halve Q anywhere — it only changes whether rₛ blocks the eye. A from-scratch double-suction (Q/2)
  implementation would need to be added explicitly if wanted.
- **Remedy 4 (alter NPSHₐ)** is a process/upstream decision (suction vessel elevation, line losses),
  not a pump-design choice — it's mentioned in the fallback banner as the remaining lever, never
  auto-applied.

## Other fixed internal constants (not exposed as sliders — edit the script directly if a case needs a different value)

| Parameter | Value | Range it's drawn from | Source |
|---|---|---|---|
| ε (blockage/openness) | 0.85 | 0.75–0.92 | Slide 12: 0.8–0.9 typical. |
| δ/r_R (wear-ring clearance ratio) | 0.0015 | 0.0008–0.0030 | Slide 19: 0.001–0.002 typical. |
| η_I (impeller loss) | 0.925 | 0.88–0.96 | Slide 19: 0.90–0.95. |
| ζ_c (collector loss) | 0.25 | 0.15–0.35 | Slide 19: 0.2–0.3. |
| p₂ fraction of stage Δp | 0.775 | 0.70–0.82 | Slide 24: 0.75–0.80 (impeller-OD pressure as fraction of stage rise). |
| Gap B fraction (r₃−r₂)/r₂ | 0.06 | 0.03–0.16 | Slide 16: 0.04–0.15, higher for volutes/higher-energy pumps. |
| N_ss target / acceptable-band edge | 8500 / 12000 | — | Slide 7 / `Sizing Workflow.md` Step 3: HI-recommended target ≈8,500; Fig. 25 "safe region" band runs ≈7,000–12,000. 12,000 (not 11,000) is the drop-speed cascade's accept/reject gate — see below; 8,500 is display-only (warn pill, doesn't reject a speed). |
| Tip-speed caution, U₂ | 250 ft/s | — | Generic cast-material stress proxy, not a real stress calc. |
| Viscosity caution | 300 cP | — | Centrifugal performance degrades sharply above this (Hydraulic Institute correction, not implemented). |
| Thrust magnitude bands | <200 / 200–800 / >800 lbf | — | This tool's own heuristic for recommending none / holes+ring / both balancing mechanisms — slide 25 gives no numeric threshold, so this is a documented judgment call, not a cited rule. |
| Axial thrust K-factor | 0.6 | — | Empirical correction for the naive uniform-back-shroud-pressure assumption (slide 24's formula was built without OCR access to the actual source Table 5) — see the tool's own flagged gap note. |
| Shock/incidence-loss coefficient K_SHO | 1.0 | ~0.4–1.2 across the case-study spread | See "Performance curve shock/incidence loss" below. |

## Performance curve shock/incidence loss (added 2026-09-05)

Slide 21 ("Computational Math: Shape of the Curve") says the non-recirculating branch is built by
holding β₂ᵦ fixed and the BEP slip velocity locked, then re-applying "the same Table 3 losses" at
each Q. Table 3's own eq (c) *names* a deeper impeller-loss breakdown — `L_imp = k·W1²/2 +
f·(W̄²/2)·(ℓ/Dh)` (incidence term + friction term) — as the path to real curvature beyond the
constant-η_I shortcut, but gives no value for `k` (incidence coefficient), `f` (friction factor), or
the passage geometry (ℓ, Dh) it needs. **Checked against our own resources first**: Karassik's
Section 2.1.1 (`Reference Material/Pump Handbook - Section 2.1...pdf`, pp. 2.46–2.48) confirms `k`
normally comes from cascade data or a turning-loss/sudden-expansion-loss sub-model, and `f` from a
pipe-friction chart (Fig. 31, Section 11.1) using the passage's actual hydraulic diameter — real
sub-analysis this closed-form tool has no inputs for, not a simple constant even in the primary
source.

**What's implemented instead** (user-directed, 2026-09-05): the shock/incidence term only, using the
Stepanoff (1957) functional form as adapted by Conrad et al. for centrifugal machinery generally —
cited via `Reference Material/Perissinotto_et_al(2024).pdf` eqs 13–14 (a PIV-based centrifugal-pump
head-loss study, itself citing both):

```
H_shock(Q) = (K_SHO / 2g) * [ ((Q - Q_BEP)/Q_BEP) * U_e ]^2      U_e = Omega * r_e (eye tip speed)
```

subtracted from the Table-3-corrected ideal head at every off-BEP point on the non-recirculating
branch (zero at Q=Q_BEP by construction, so the BEP anchor itself is untouched). **K_SHO=1.0 is not
from either cited source** — both call the coefficient impeller-specific / needing calibration data
this tool doesn't have. It was back-solved instead by requiring the shock-augmented curve's Q→0
extrapolation to land on this tool's own already-implemented Stepanoff shutoff head (line ~488,
`Hshutoff_ft`), for each of `workflow_cases.py`'s case studies — see `performance_curve_cases.py`
for the check. Result: K_SHO clusters at 0.96–1.2 for 6 of 7 cases (used 1.0, centered in that
cluster); one high-suction-energy validation case (Cooper's own §2.1 example) needed K_SHO≈0.4
instead.

**Update 2026-10-12, calibration claim does not hold in the HTML tool:** evaluated directly in
`Case Study Sizing Tool.html`'s engine at the defaults (500 gpm / 250 ft water), the shock-augmented
1-D curve at Q=0 gives 343 ft vs the Stepanoff 297 ft (+16%). Across a 6-duty spread it lands 6–15%
above Stepanoff, so `performance_curve_cases.py`'s check and the HTML don't agree. This no longer
affects output: the 1-D curve now stops at 0.5·Q_BEP, and below that a cubic-Hermite blend joins it
to the Stepanoff shutoff (Karassik §2.1.1 p.2.68 blends "at half of the BEP flow rate"), so K_SHO
only shapes the 50–135% range. **Rise-to-shutoff check** (same date): a banner warns when
H_shutoff/H_BEP − 1 < 15%, citing Karassik p.2.57 ("at least 15 to 20% more head H at shutoff than
at BEP" for a stable curve; conflict "more likely to occur with low-specific-speed pumps").

**Why the visible effect stays small (checked 2026-09-06, not just assumed):** the pre-existing
velocity-triangle branch (BEP slip locked, no shock loss) is *already* close to linear in Q by
construction — ψᵢ(Q) is an exact linear function of Q because Vu2,∞(Q) is linear and the locked
slip velocity is a constant offset. That pre-existing linear trend already accounts for most of the
BEP-to-shutoff rise, leaving only a small residual for the shock-loss term to close — so even a
"correctly calibrated" shock loss produces a small *bow* (deviation from a straight chord), not a
dramatic curve. Measured directly: max bow is ~0.5–1.1% of the chart's plotted height across the
entire Ωₛ 0.37–1.0 range this tool covers (checked at both ends, not just the default case) — visibly
indistinguishable from a straight line on the actual chart.

**This turns out to be expected physics, not a shortfall (per Karassik Section 2.1.1, p.2.45,
discussing Fig. 22):** a substantial "rise to shutoff" is specifically a **high-specific-speed**
effect — "the low value of W1 associated with the small eye relative to the maximum diameter...
enables the outlet velocity diagram to have a high value of Vθ,2/U2 [at BEP]... this ratio drops as
Ωₛ increases," meaning the *droop toward shutoff* is what grows with Ωₛ, and Karassik explicitly
says this is "why a high-specific-speed impeller has such a substantial 'rise to shut-off.'" This
tool's scope gate caps at Ωₛ=1.0 (Nₛ≈2733), below where that effect becomes dramatic. **Decision
(user-directed, 2026-09-06): keep the shock-loss term as a real, cited, correctly-scoped
improvement, but do not force additional curvature beyond what the physics at this specific-speed
range actually supports** — near-linear curves for this tool's typical cases are largely correct,
not evidence of a missing model term. Friction loss proper (Table 3 eq (c)'s other term, ~Q²) is
still not implemented — it needs passage hydraulic diameter and streamline length this tool has no
geometry for, and wouldn't be expected to change this conclusion at low-to-mid Ωₛ.

## Blade angle β₂ᵦ (bisection search range)

Two-tier search, both enforced in code:

1. **Primary range: 15°–35°.** Standard backward-curved pump practice (general pump engineering
   convention, not a number cited in the deck itself) — designs in this range give stable,
   continuously-rising H-Q curves. Try this range first.
2. **Fallback range: 10°–60°**, only if no solution exists in the primary range. Using it always
   raises a flag in the report — a case that needs blade angles outside 15–35° is a signal the
   Stepanoff-chart target ψ and the velocity-triangle+losses prediction are in tension for that
   Ωₛ, not a normal result. (This replaces an earlier version of the tool that searched all the way
   to 89.9° silently, which produced an unrealistically flat H-Q curve on the very first case
   tested — near-radial blade angles are a known driver of flat/unstable curves in real pumps and
   should never be reached without a flag.)

## Service category (NPSH margin, slide 5) — auto-derived, not fluid-name-only

Originally defaulted purely off the selected fluid's identity. Changed to a condition-based rule
(evaluated on fluid/T/viscosity/solids change, unless the user has manually overridden the dropdown):

1. Suspended solids checked → **Slurries, erosive service** (1.5–2.0×) — highest priority.
2. Else viscosity > **30 cP** → **Viscous fluids** (1.3–1.5×). Threshold is this tool's own judgment
   call (roughly where Hydraulic Institute viscosity corrections start to matter), not a deck-cited number.
3. Else vapor pressure at T > **10 psia** (approaching atmospheric — genuinely close to boiling) OR the
   fluid isn't water → **Hydrocarbons / hot water near boiling** (1.2–1.3×).
4. Else (water, moderate T) → **Clean cold water, non-critical** (1.1–1.2×).

**Critical service, no spare** (2.0×) is never auto-selected — it's a reliability/business decision
(whether a standby pump exists), not something derivable from physical properties. Manual override only.

## Collector: volute + vaned diffuser — auto-determined, not user-selected

Per slide 15, a volute is present on **every** single-stage centrifugal pump — it's not an alternative
to a vaned diffuser, it's the always-present final collector. A vaned diffuser, when used, sits
*between* the impeller and the volute (slide 15: "common w/ higher impeller speeds"); it's an addition,
not a substitute. This tool decides whether to add one rather than asking the user to guess:

- **Diffuser added** when tip speed U₂ > **150 ft/s**. Above this, the diffuser's throat governs
  (k=0.80, Eq. 62) and its vane count / exit area are reported; the volute downstream of it isn't
  separately re-sized (the diffuser does the bulk of the diffusion per slide 17).
- **Diffuser omitted** (volute only, k=0.925, Eq. 61) below that speed.

150 ft/s is this tool's own threshold — the deck's own language ("common w/ higher impeller speeds")
is qualitative, not numeric, so this is a documented judgment call, not a cited rule. Revisit if a case
study suggests it's miscalibrated.

## Trim-diameter family (performance curve panel)

Trim fractions plotted: **0.80, 0.85, 0.90, 0.95, 1.00** × the sized D₂ (1.00 = the diameter this
tool actually sizes to your input duty point). Generated via the standard affinity laws at constant
speed (Q ∝ D, H ∝ D²) applied pointwise to the full-diameter curve — the same simplified method
real vendor curve sheets use to interpolate a trim family from a single tested casing, not a
re-derivation of the velocity triangle at each trim.

## Low-flow limits & shutoff (added 2026-10-13) — "Low-flow limits & shutoff" panel

All from Karassik 4th ed. §2.1.1. They feed the planned parallel-pump changeover simulator.

| Quantity | Method | Source | Constants / notes |
|---|---|---|---|
| Shutoff head | H_s/o = [k_imp(U₂² − U_h1²) + k_ex·U₂²]/2g | Eq. 65/66, p.2.50 | k_imp = 1 ("kimp ≈ 1"); k_ex = 0.2, band ±0.1 ("usually in the range 0.2 ± 0.1"). r_h1 ≈ torque-sized shaft radius r_s, a stand-in because the hub isn't sized. Replaces Stepanoff's fixed ψ_s/o = 0.585, which sits inside the band. |
| Low-flow head curve | 1-D curve computed for f ≥ 0.50; cubic-Hermite blend from the shutoff head (zero slope at Q=0) | p.2.68 ("blended … at half of the BEP flow rate") | Fritsch-Carlson slope limit; end slope set to 0 when shutoff ≤ the head at half flow (no overshoot). |
| Rise-to-shutoff warning | banner if H_s/o/H_BEP − 1 < 15% | p.2.57 ("at least 15 to 20% more head") | — |
| Shutoff power | K = hp_s/o ÷ [(N/1000)³(D₂[in]/10)⁵·SG] vs b₂/D₂; P̂_s/o = 0.01966K | Eq. 67 + Mockridge Fig. 23, p.2.51 | `MOCKRIDGE_K` table digitized by eye at 300 dpi (log-log, ±5–10% in K), log-log interpolation, clamped outside 0.01–0.36. Cross-check: generic §11.1 Fig. 16B gives ~40–50% of rated for n_s 600–1500; Mockridge gives ~30–35% across the tool's radial range. |
| Low-flow power curve | straight-line blend from P_s/o at Q=0 to the 1-D BHP at 0.5·Q_BEP | this tool's construction | The 1-D BHP above 0.5·Q_BEP still uses a constant (BEP) efficiency, an existing simplification. |
| Minimum flow | Q_min = Q_R·min(1, K₁K₂K₃K₄K₅); Q_R = Q_SR if Dₑ ≥ 0.5D₂, else Q_DR | Table 16, p.2.81 | β_f,2 = exit **flow** angle (Karassik subscript f = "direction of the flow"), tan β_f2 = φ₂/(1 − ψᵢ); the blade angle would give Q_DR > Q_BEP. β₁ = atan(φₑ), which matches Table 16's own sample (tan β₁ = 0.3 at 16.7°). R = NPSHa/NPSHr. K₃ uses the configuration dropdown. K₄ = 1 (continuous) or 0.7 (intermittent, "<25% of total operating time"). K₅ = 1. **Validated:** reproduces Table 16 part B (C_SR = 0.1618; Q_SR = 24.04 vs the book's 24.03 ft³/s). |
| Casing liquid hold-up | inlet turning region Aₑ·b₁ + impeller annulus π(r₂² − rₑ²)(b₁+b₂)/2 + volute (A_t/2)·2π(r₃ + √A_t/2); b₁ = Aₑ/(2πrₑ) | this tool's geometric construction | **Lower bound**: excludes shroud side gaps, nozzles and suction-pipe backflow, so a deadhead heating rate built on it errs fast (conservative). The default duty gives 0.33 gal (2.8 lb). |
| Data-sheet Max. Work Pres. | max(peak head on the curve, upper shutoff band k_ex = 0.3) × SG/2.31 | conservative choice for a casing rating | Still a differential; doesn't add max suction pressure. |
