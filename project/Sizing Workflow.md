# Centrifugal Pump Sizing — Written Workflow (Steps 1 → Impeller Eye Radius)

Written form of `Centrifugal Pump Sizing.pptx`, slides 2–10. **Scope: single-stage, radial-flow
only.** Covers the workflow through the **impeller eye radius** in detail; exit radius → exit
width → blade angle/count (slides 10–13) are implemented in `Sizing Tool/workflow_cases.py`
(Fig. 12 fits + Pfleiderer slip, ported from the HTML tool) but not written out here.

Source: Karassik *Pump Handbook* 4th ed., §2.1 (Cooper) and §2.1.3. Equation numbers (Eq. 44,
45, 49, 50; Table 1; Fig. 10, 12, 25) refer to that section.

---

## Notation

| Symbol | Meaning | Working units |
|---|---|---|
| Q | volumetric flow (BEP / design point) | gpm (USCS) · m³/s (SI) |
| H | total head (per stage = total, single-stage) | ft · m |
| T | pumping temperature | °F · K |
| ρ, μ, P_v | liquid density, viscosity, vapor pressure @ T | lb/ft³, cP, psia |
| N | rotative speed | rpm |
| Ω | angular velocity = 2πN/60 | rad/s |
| N_s | specific speed = N·√Q / H^0.75 (USCS) | — |
| N_ss | suction specific speed = N·√Q / NPSH_r^0.75 (USCS) | — |
| Ω_ss | universal suction specific speed = Ω·√Q / (g·NPSH_r)^0.75 ; N_ss,US ≈ 2733·Ω_ss | — |
| NPSH_a / NPSH_r | available / required net positive suction head | ft · m |
| η_p | overall pump efficiency (first pass) | — |
| P_hyd, P_shaft | hydraulic power ρgQH, shaft power P_hyd/η_p | W, hp |
| M | shaft torque = P_shaft / Ω | lbf·ft, N·m |
| S_s | allowable shear stress of shaft material | psi, Pa |
| r_s | shaft radius (blocks the impeller eye) | in · m |
| r_e | impeller eye radius (≈ blade-tip radius at inlet, r_t,1) | in · m |
| φ_e | eye flow coefficient = V_e/U_e (axial inlet velocity / eye tip speed) | — |
| τ | cavitation coefficient = NPSH / (U_e²/2g), U_e = Ω·r_e | — |

Convention (matches the deck / HTML tool): compute in SI internally, take inputs and report
geometry in USCS.

---

## Step 0 — Inputs (process conditions)

From the process: **Q, H, T, fluid**. Look up **ρ, μ, P_v at T** (deck/tool use a precomputed
`thermo` table; any liquid-phase property source is fine).

For NPSH_a you also need the suction-side layout: static suction head `H_s`, head-space
(gas-blanket / tank) pressure head `H_hs`, and suction friction head `H_f`.

Pick a **service category** (drives the NPSH margin and, later, materials): clean cold water /
hydrocarbons / hot water near boiling / viscous / slurry-erosive / critical-no-spare.

---

## Step 1 — Impeller speed N  *(slide 4)*

**Rule:** choose the **highest practical** speed — smallest impeller, lowest cost, easiest
pressure containment, and generally better efficiency (Fig. 10).

Speed is set by the driver: `N = 120·f / poles`, f = 60 Hz (US):

| Poles | N (rpm) |
|---|---|
| 2 | 3600 |
| 4 | 1800 |
| 6 | 1200 |
| 8 | 900 |

**Ceiling:** N must not push N_ss above what a first-stage impeller can accommodate (checked in
Step 3). Eq. 45 gives the NPSH an impeller of target N_ss capability needs at a candidate speed:

```
NPSH_req(ft) = ( N(rpm) / N_ss,US )^(4/3) · [Q(gpm)]^(2/3)
```

**Procedure:** start at 3600 rpm (2-pole); if Step 3 fails, drop one pole step and repeat.

**Output:** N (rpm), Ω (rad/s).

---

## Step 2 — NPSH  *(slide 5)*

**Step 2a — available:**

```
NPSH_a = H_s + H_hs − H_f − H_vp        [ft of fluid;  H_vp = P_v / (ρg)]
```

**Step 2b — required**, via service-based margin (NPSH_a must exceed NPSH_r by this factor, so
size the pump to `NPSH_r = NPSH_a / margin`):

| Service condition | NPSH_a / NPSH_r margin |
|---|---|
| Clean cold water, non-critical | 1.1–1.2 (HI minimum) |
| Hydrocarbons, hot water near boiling | 1.2–1.3 |
| Viscous fluids | 1.3–1.5 |
| Slurries, erosive service | 1.5–2.0 |
| Critical service, no spare | 2.0 |

**Output:** NPSH_r (ft) — the suction-performance spec limit the impeller eye must meet.

---

## Step 3 — Suction specific speed & cavitation check  *(slide 6, Fig. 25)*

```
N_ss = N·√Q / NPSH_r^(3/4)         (USCS: N rpm, Q gpm, NPSH_r ft)
Ω_ss = Ω·√Q / (g·NPSH_r)^(3/4)     (universal;  N_ss,US ≈ 2733·Ω_ss)
```

**Acceptable band** (Fig. 25 "safe region", Handbook text): N_ss,US ≈ **7,000–12,000**, target
**~8,500–9,000** (HI ANSI/HI recommendation ≈ 8,500). Handbook notes cavitation onset near
N_ss ≈ 6,000 for large pumps. HTML tool (2026-09-04): accept/reject gate at 12,000 (matches the band
edge, not the 11,000 used before); 8,500 is display-only (warn pill, doesn't reject a speed).

**Slide 7's four remedies, if N_ss is above the band** (first two only fully written out here; slide 7
itself lists all four — see its OMML equation text, not the plain shape text):
1. **Drop N** one pole step → return to Step 1. *(HTML tool: automated — tries all 4 standard speeds.)*
2. **Add an inducer** ahead of the first-stage impeller: lowers NPSH_r, so raises the allowable
   N_ss to ~15,000–27,000 (ss ≈ 5–10). Inducer τ comes from Table 1(b) instead of 1(a). *(HTML tool:
   flagged only — Table 1(b) needs a blade angle β this deck gives no formula for.)*
3. **Double-suction impeller:** use **Q/2** in N_ss (nominally zero axial thrust; large single-stage —
   noted, at the edge of this scope). *(HTML tool: available as a manual "Shaft configuration" choice
   — between-bearings sets r_s≠0 at the eye — but that dropdown does not itself halve Q anywhere;
   not auto-cascaded to, by user direction 2026-09-04.)*
4. **Alter NPSH_a** (process/upstream change — suction elevation, line losses). *(HTML tool: flagged
   only, as the remaining lever once remedies 1-2 are exhausted; never auto-applied — it's not a
   pump-design choice.)*

**Output:** N_ss (confirmed in band), inducer flag (y/n).

---

## Step 3b — Specific-speed scope gate  *(slide 2 impeller-shape chart)*

```
N_s   = N(rpm)·√Q(gpm) / H(ft)^0.75          Ω_s = Ω·√Q / (g·H)^0.75   (N_s,US ≈ 2733·Ω_s)
```

Slide 2's orange "CENTRIFUGAL" band marks the **radial pump type** as N_s,US ≈ 273–2,733
(Ω_s 0.10–1.00). That is a pump-*selection* limit. The deck's **paper-math sizing method**
(Fig. 12 ψ/φ fits + Pfleiderer blades) is only valid over the tighter

| | N_s,US | Ω_s | outside → |
|---|---|---|---|
| **hard gate for this workflow** | **1,000 – 2,730** | **0.37 – 1.00** | see below |
| slide-2 pump-type band | 273 – 2,733 | 0.10 – 1.00 | PD/multistage · mixed/axial |

- **Ω_s < 0.37** — still a radial pump by type, but ψ_target = 0.383/Ω_s^(1/3) rises above what a
  15–35° backward-curved blade can produce: the blade solve pins near-radial, b2/D2 collapses to
  ~0.03. → multistage, or a special impeller style (Barske / partial-emission) + CFD.
- **Ω_s > 1.00** — mixed-flow onset: D2/De → 1, Fig. 12 fits degrade. → mixed-flow method.

**Gate the workflow here** — if Ω_s is outside 0.37–1.00, stop and report; do not run Steps 5–9.

**Output:** in-scope (proceed) / out-of-scope (stop, with reason).

See `Reference Material/Workflow Specific-Speed Scope.pdf` (from `generate_scope_figures.py`):
page 1 = this band vs. the slide-2 chart + the ψ_target curve that explains the low-Ω_s cutoff;
page 2 = how the N_s limit turns the broad single-stage-centrifugal Q-H region into a diagonal
band, cutting the high-H/low-Q (multistage) and low-H/high-Q (mixed-flow) corners.

---

## Step 4 — Impeller design sequence  *(slides 7–8, orientation only)*

Sizing order: **eye radius → exit radius → exit width (+ hub radius) → hub/shroud profiles →
blades.** Steps 5–6 below cover the shaft radius (a prerequisite) and the eye radius.

---

## Step 5 — Shaft radius r_s  *(slide 9 — prerequisite to the eye)*

**Why first:** Eq. 49 + Eq. 50 are two equations in three unknowns (φ_e, r_e, r_s). Eq. 50
contains only the ratio r_s/r_e; Eq. 49 needs r_s as a length. The third equation is
**mechanical** — r_s is fixed by shaft strength, independent of r_e — so it is *computed*, not
found by iterating the ratio.

> **Configuration matters (case-study finding, 2026-08-26).** The shaft blocks the eye —
> the `r_s` term in Eq. 47/49/50 — **only when the shaft passes through the eye**: double-suction
> and between-bearings (BB) pumps. A **single-suction overhung** impeller (API OH, ANSI B73.1 —
> the default single-stage config) has a **clear eye**: take `r_s = 0` (B = 1) in Steps 6a/6c.
> Cooper's own §2.1 end-suction design example uses B = 1. The shaft is still sized here (below)
> — it is needed for the shaft, bearings, seal, and lateral analysis — it just is not an
> eye-sizing input for an overhung pump.

**5a — first-pass efficiency** (Anderson, Eq. 44, roughness factor X = 1):

```
N_s   = N(rpm)·√Q(gpm) / H(ft)^0.75
η_p   = 0.94 − 0.08955·[ Q(gpm) / (N(rpm)·X) ]^0.21333 − 0.29·[ log10(2286 / N_s) ]²
```

(X = [140/ε(µin)]² = [3.56/ε(mm)]²; X = 1 ⇒ ε ≈ 140 µin, rough cast. The log term is
over-conservative for N_s < 2286 — real pumps do better; treat η_p as a floor there.)
Low sensitivity: r_s ∝ M^(1/3) ∝ η_p^(−1/3), so a 20 % error in η_p moves r_s ~6 %.

**5b — power and torque:**

```
P_hyd   = ρ·g·Q·H            (SI: W)
P_shaft = P_hyd / η_p
M       = P_shaft / Ω        (SI: N·m)
```

**5c — solid shaft in torsion:**

```
r_s = ( 16·M / (π·S_s) )^(1/3)        S_s = allowable shear stress
```

**5d — derate / checks:**
- Keyway: multiply the required section modulus by **1.1–1.2** (⇒ r_s up ~3–6 %).
- Under API 610, a **lateral-deflection / shaft-stiffness** limit usually governs over pure
  torsion — not computed here; treat the torsion result as a lower bound.
- **Shortcut:** if the pump frame / driver is already selected, read r_s straight off the shaft.

**Output:** r_s — a fixed length.

> **Open decision:** S_s is not fixed by the deck. Common conservative values: carbon-steel
> keyed shaft S_s ≈ 6,000 psi; per ASME B106 / API 610, S_s = min(0.30·S_y, 0.18·S_ut) with a
> keyway factor. Pick one and record it per case.

---

## Step 6 — Impeller eye radius r_e  *(slide 10)*

Inputs: r_s (Step 5 — **use 0 for an overhung impeller**), Ω (Step 1), Q, target Ω_ss / N_ss
(Step 3), inducer flag.

> **What actually governs (case-study finding).** Across the normal single-stage radial envelope
> (N_ss ≲ 12,000), step 6a returns φ_e above the 0.30 cap, so **φ_e = 0.30 and the eye is sized
> by Eq. 49 alone** (step 6c). The Eq. 50 back-solve only becomes the active constraint for
> high suction energy — N_ss ≳ 12,000 (Cooper's own design example, at N_ss = 12,300, lands at
> φ_e = 0.29). Treat 6a as a **ceiling check**: if it cannot meet the required Ω_ss even at
> φ_e = 0.30, lower φ_e along Eq. 50; if it cannot be met at the curve's peak (Ω_ss ≈ 4.6,
> N_ss ≈ 12,600 for B = 1), an **inducer** is required.

**6a — back-solve φ_e from Eq. 50 + Table 1:**

```
Ω_ss = √[ π·φ_e·(1 − r_s²/r_e²) ] / (τ/2)^(3/4)

τ (zero prewhirl, impellers, Table 1a):   τ = (k1 + k2)·φ_e² + k2
        typical pumps:  k1 ≈ 1.69,  k2 ≈ 0.102
        large pumps:    k1 = 1.40,  k2 = 0.085
τ (inducers, Table 1b):  τ = 0.02 + 0.02·[ log10( φ_e·sinβ / (1 + cosβ) ) + 3 ]^3.5
```

Assume **r_s/r_e ≈ 0.4** to close the (1 − r_s²/r_e²) term, then solve the 1-D equation for φ_e
(substitute τ(φ_e); root-find). The result is weakly sensitive to the assumed ratio — the
bracket runs 0.91→0.75 over r_s/r_e ∈ 0.3–0.5, i.e. φ_e shifts ~±4 %.

**6b — checks on φ_e:**
- **φ_e ≤ 0.3** at the BEP is the upper limit of normal practice, regardless of available NPSH.
  If Eq. 50 returns φ_e > 0.3, cap it at 0.3 and take r_e directly from Eq. 49 (6c).
- **φ_e < 0.2** → re-evaluate Ω_ss with the inducer τ (Table 1b).
- **φ_e(τ_inducer) < 0.15** → use an inducer.  **φ_e < 0.1** → inducer definitively required.

**6c — solve Eq. 49 for r_e** (with r_s a fixed number, this is a cubic in r_e with exactly one
positive root):

```
r_e = [ Q / ( π·Ω·φ_e·(1 − r_s²/r_e²) ) ]^(1/3)
  ⇔  r_e³ − r_s²·r_e − Q/(π·Ω·φ_e) = 0
```

Solve by Cardano, or 3–4 fixed-point iterations from the zero-blockage seed
`r_e⁰ = [Q/(π·Ω·φ_e)]^(1/3)` (converges geometrically; r_e > r_s always).

**6d — final ratio check:** compute the actual r_s/r_e. If outside **~0.3–0.5**, redo 6a with the
new ratio (converges in one pass — φ_e barely moves).

**Output:** r_e (eye radius), D_e = 2·r_e, φ_e, actual r_s/r_e, inducer flag.

> **"Find Source" on slide 8:** there is **no numeric r_s/r_e in Karassik** — §2.1 (p. 2.29,
> Eq. 49) introduces `r_s/r_e` only as an iteration seed with no recommended value. The
> "0.35–0.45" (or 0.3–0.5) hub/eye figure is engineering folklore traceable to Lobanoff & Ross,
> *Centrifugal Pumps: Design and Application*, and Stepanoff — cite it there, not Karassik.

---

## Case studies

`Sizing Tool/workflow_cases.py` implements Steps 1–9 (through blade angle/count) and runs a
duty-point spread. Findings:

**Steps 1–6 (2026-08-26):**
1. **Overhung vs. shaft-through-eye.** For an overhung single-suction impeller `r_s = 0` in
   Eq. 47/49/50; the r_s/r_e machinery on slide 9 applies only to double-suction /
   between-bearings pumps. See the note in Step 5.
2. **φ_e almost always pins to 0.30.** Only cases above N_ss ≈ 12,000 solve φ_e from Eq. 50 —
   for the normal range it is `φ_e = 0.30 → Eq. 49`.
3. **Validation:** Handbook §2.1 design example (case V) reproduced — φ_e = 0.29 vs Cooper's 0.29,
   and (Steps 7–9) **D2 = 12.1 in vs Cooper's "12 in"**, ψ = 0.384 vs 0.385, φ2 = 0.171 vs 0.1715.
4. **Inducer branch** (case I) flags then stops — inducer τ needs a blade angle the deck omits.

**Steps 7–9 (2026-08-28) — one gap, now closed by the Step 3b gate.**
5. Outside Ω_s ∈ [0.37, 1.00] the paper-math degrades on four fronts at once: blade solve pins
   near-radial (β2b → 60°), b2/D2 collapses (~0.03), D2/De leaves the 1.8–2.5 band, U2 goes
   high-energy. Cases B, D, E (low Ω_s) and C (mixed-flow).
6. **With the Step 3b gate in place, every remaining in-scope case is clean** — B, D, E, C are
   rejected up front; A, F, G, H, I, V and the between-bearings variants all give sane geometry
   (D2 12–21 in, U2 80–110 ft/s, β2b 24–27°, no fallback). The Handbook example (V, Ω_s 0.995)
   sits right at the upper edge and matches Cooper (D2 = 12.1 in).
7. Two flags survive the gate and are *not* specific-speed issues: case H "N_ss high" (the Fig. 25
   ceiling) and case I "inducer required" (suction energy). Both correct.

### Slide-2 recommendation

Slide 2's chart shows the radial band starting at N_s,US ≈ 273. That is the pump-*type* limit.
For the sizing method, the low end should read **N_s,US ≈ 1,000** (Ω_s 0.37) — below that a radial
pump still exists but this deck's backward-curved paper-math cannot design its impeller. Either
tighten the number on the slide or add a "paper-math valid for N_s ≳ 1,000" note.

### Still-open decisions

- **S_s value** (Step 5c) — not fixed by the deck.
- **N_ss band edges** — script uses warn 11,000 / inducer 13,000; would flag Cooper's own 12,300.
- **Anderson η_p** — first pass only; optimistic at low flow.
- **Q basis in Eq. 49** — pump Q vs impeller Q = Q/η_v.
- **Double-suction** — use Q/2 per eye in Steps 3 & 6; not yet in the workflow (see the note at
  the top of Step 5 — shaft-through-eye is the double-suction case).
