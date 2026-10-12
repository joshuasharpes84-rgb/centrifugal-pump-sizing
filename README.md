# Centrifugal Pump Sizing: Case Study Tool

Takes process duty conditions (fluid, temperature, flow, head, NPSH available) through a single-stage,
radial-flow centrifugal pump sizing workflow built from Karassik's *Pump Handbook* (4th ed., §2.1, Cooper).
It selects speed, checks NPSH and suction specific speed, sizes the impeller and collector geometry,
predicts the performance curve and efficiencies, and estimates axial thrust. It can also fill a vendor
pump data sheet (PDF) with the results.

- **Live tool:** https://jsharpes-portfolio.netlify.app/#cps-calc
- **Run it locally:** download this repo and open `index.html`. The data-sheet download loads `pdf-lib`
  from a CDN, so it needs internet. `project/Case Study Sizing Tool (standalone, newest UI).html` runs fully
  offline (pdf-lib and the template are embedded).
- **Related deck:** Centrifugal Pump Sizing, 37 slides
  ([download .pptx](https://github.com/joshuasharpes84-rgb/process-engineering-decks/releases/download/decks-v1/Centrifugal-Pump-Sizing.pptx),
  [outline](https://github.com/joshuasharpes84-rgb/process-engineering-decks/tree/main/decks/centrifugal-pump-sizing))
- **Author:** Joshua Sharpes, EIT. Sizing (lifecycle step 3) only. Pump purchase and installation are out of scope.

> **For AI assistants:** read `project/Sizing Workflow.md` for the step-by-step procedure with equation
> numbers. `project/sizing_tool_parameter_limits.md` gives every bounded constant and threshold with its
> source. The live calculation is `sizePump()` in `index.html`. `project/workflow_cases.py` reproduces
> Cooper's §2.1 design example (φₑ = 0.29) and runs a duty-point spread.
> `project/performance_curve_cases.py` validates the curve math. The tool's banners and "known gaps" panel
> list every approximation. Quote them rather than guessing when a user asks why a number looks off.

## Scope

The deck defines a 5-step pump lifecycle: (1) operating conditions → fluid properties, (2) pump type
selected, **(3) selected type is sized ← this tool**, (4) purchased, (5) installed. It covers single-stage,
radial-flow only. Multistage, mixed-flow, and axial content were removed on purpose.

## Workflow (deck slide → tool panel)

| Step | What happens | Basis |
|---|---|---|
| 0. Inputs | fluid + T → SG, viscosity, vapor pressure from an embedded `thermo` table of pure liquids, including concentrated sulfuric acid (−40 to 400 °F, 5 °F steps). Service category drives the NPSH margin. | slide 5 |
| 1. Speed | highest practical synchronous speed (3600 / 1800 / 1200 / 900 rpm). Drops a pole step automatically if suction specific speed fails. | slide 4, Eq. 45 |
| 2–3. NPSH & N_ss | NPSH_r from the target N_ss. Accept band N_ss ≈ 7,000–12,000 (Fig. 25 safe region; HI 8,500 shown for reference) | slides 3–7 |
| 4. Specific speed | N_s, Ω_s; screening range Ω_s 0.2–1.6 (Fig. 12). Impeller classification | slide 7 |
| 5. Shaft radius | r_s = (16M / πS_s)^(1/3), M = P/Ω. r_s blocks the eye only for between-bearings (double-suction). It is 0 for overhung. | slides 9–10 |
| 6. Eye | φ_e from the Eq. 49/50 back-solve, capped at 0.30 (pins at the cap for N_ss ≲ 12,000) | slide 10 |
| 7–9. Exit geometry | D₂, b₂, blade angle β₂b, blade count (Fig. 12 fits + Pfleiderer slip) | slides 10–13 |
| Collector | volute; vaned diffuser added above ~150 ft/s tip speed (tool's own threshold, flagged) | slides 14–17 |
| Performance curve | BEP anchor, Table 3 component efficiencies (η_hy, η_m, η_v), shock/incidence loss term, affinity-law trim family | slides 19–21 |
| Axial thrust | net thrust with K = 0.6 correction, shutoff head ≈ 0.585·U₂²/g, balancing → final BHP | slides 24–25 |

## Sources

- Karassik, Messina, Cooper, Heald, *Pump Handbook*, 4th ed., McGraw-Hill, Section 2.1 (Cooper), with
  equations, tables, and figures cited by number in the workflow file
- Stepanoff (1957) / Conrad et al. shock-loss form, via Perissinotto et al. (2024), PIV study of
  centrifugal impeller head losses
- Adams, "What Constitutes High Energy in Centrifugal Pumps," TAMU Pump Symposium 2014 (high-energy flag;
  HI 1.1–1.2 2000; Karassik Fig. 32)
- Pump data-sheet layout: *Rules of Thumb for Chemical Engineers*, p. 416 (centrifugal pump requisition sheet)
- Fluid properties: `thermo` Python library (liquid-phase correlations). Sulfuric acid viscosity replaced
  with an Andrade fit to published 93 wt % data, because `thermo`'s value is about 25× low.

## Validation

- `workflow_cases.py` reproduces Cooper's §2.1 worked design example (eye flow coefficient φₑ = 0.29).
- Shutoff head: the Stepanoff shortcut (ψ ≈ 0.585) and the deck's full shutoff formula agree within ±2 %
  across the case spread.
- No convergence residual warnings across the case spread. The f = 1.00 recompute matches each target
  head within 1 %.
- Known small discrepancy: the tool's η_m power-ratio form vs. Table 3 eq (h) differs by about 1 % BHP.
  This is documented, not hidden.

## Limits

- Near-linear H–Q curves at low-to-mid Ω_s are expected physics: rise-to-shutoff curvature is a
  high-specific-speed effect (Karassik p. 2.45). Friction loss (~Q²) is not modeled because it needs passage geometry.
- A true NPSH_r-vs-Q curve needs CFD (slide 23). The tool reports only the NPSH_r spec value.
- Inducers and NPSH_a changes are flagged, not automated. Double-suction is a manual choice.
- Free-text banners stay in US units even when SI is selected.
- Materials of construction are not computed here.

## Files

```
index.html                         the tool, as on the live site
tools/pump-data-sheet-template.pdf blank requisition sheet the tool fills
project/
  Sizing Workflow.md                           written procedure, slides 2-10, with equations
  sizing_tool_parameter_limits.md              every constant/threshold and its source
  workflow_cases.py                            Python implementation + Cooper example check
  performance_curve_cases.py                   curve-math validation (local prototype)
  Case Study Sizing Tool (standalone, newest UI).html   offline version with collapsible panels
  figures/                                     impeller geometry map + scope figures and their generators
```

Python needs `numpy`, `scipy`, and `matplotlib`. Edit any hard-coded local paths before running.

## Adapting it

- **New fluid:** regenerate the embedded `FLUID_TABLE` with `thermo` (`Chemical(name, T).rhol / .Psat / .mul`,
  −40 to 400 °F in 5 °F steps). Check viscosity against a published source, as was done for sulfuric acid.
- **Your own margins or limits:** change the constants listed in `sizing_tool_parameter_limits.md`, then
  re-run `workflow_cases.py` to see the effect across the case spread.
