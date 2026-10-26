# Sources — Centrifugal Pump Sizing

Where each type of information in this project (deck, Sizing Tool, Pump Changeover Simulator) comes
from. Topic-level, not number-by-number: the aim is to show nothing was invented, and to point a
reader to the right book and section if they want to dig.

**Tiers**
- **Library** — reference textbook in `Downloads\ChemE\Textbooks (Level 1)\` (used across projects)
- **Project PDF** — paper or excerpt held in this folder's `Reference Material\`
- **Web** — public page, URL given
- **Print only** — book cited from a paper copy; no digital copy for page lookup
- **Own work** — derived, fitted or chosen in this project; the basis is stated

Copyrighted PDFs are cited here but never published.

| Topic | Source | Tier | Location |
|---|---|---|---|
| Overall sizing method: speed selection, NPSH and suction specific speed, eye radius, velocity triangles, blade angles, collector design, performance-curve prediction, axial thrust | Karassik, Messina, Cooper, Heald, *Pump Handbook*, 4th ed., McGraw-Hill, §2.1 (Cooper), equations and tables cited by number in `Sizing Workflow.md` | Library + Project PDF | `Textbooks (Level 1)\Equipment Handbooks\Pump Handbook, 4th edition Karassik.pdf`; §2.1 excerpt in `Reference Material\` |
| Worked validation case (2,500 gpm, 104 ft, 1,780 rpm; φₑ = 0.29) | Karassik §2.1 design example (Cooper) | Library | as above |
| Shutoff head (Eq. 65/66), rise-to-shutoff ≥ 15 %, low-flow blend at 0.5·Q_BEP, shutoff power (Mockridge Eq. 67 / Fig. 23), minimum flow (Table 16) | Karassik §2.1.1, pp. 2.50, 2.51, 2.57, 2.68, 2.81 | Library | as above |
| Wear-ring clearance factors (Table 3), c₀ (Fig. 48), parallel operation (Fig. 40), static-head example (§11.1 Ex. 1), allowable temperature rise (Ch. 15) | Karassik 4th ed. | Library | as above |
| Shutoff coefficient ψ ≈ 0.585, low-n_s curve droop, parallel-pump behaviour, casing effect on shutoff | Stepanoff, *Centrifugal and Axial Flow Pumps*, 2nd ed. (1957), §9.2–9.3, §14.1, Fig. 9.17 | Project PDF | `Reference Material\Centrifugal and Axial Flow Pumps ... Stepanoff.pdf` |
| Shock/incidence-loss form for the off-BEP curve | Stepanoff (1957) / Conrad et al., via Perissinotto et al. (2024), PIV study of impeller head losses | Project PDF | `Reference Material\Perissinotto_et_al(2024).pdf` |
| "High energy" pump flag | Adams, "What Constitutes High Energy in Centrifugal Pumps," TAMU Pump Symposium 2014 (cites HI 1.1–1.2 2000, Karassik Fig. 32) | Project PDF | `Reference Material\What Constitutes High Energy ... (Adams, TAMU 2014).pdf` |
| Single-stage Q/H coverage band (tool input limits) | Pump coverage chart (Fig. 10-24 style, Perry's / Rules of Thumb) | Library | `Textbooks (Level 1)\Handbooks & Quick Reference\`; image in `Reference Material\Pump Selection Guidelines.png` |
| Pump data-sheet layout | *Rules of Thumb for Chemical Engineers*, 3rd ed., p. 416 | Library + Project PDF | `Textbooks (Level 1)\Handbooks & Quick Reference\ChemE Rules of Thumb.pdf`; `Reference Material\Pump Data Sheet.pdf` |
| API 610 stable-curve clause for parallel pumps (≥ 10 % rise) | Nelik, *Pumps & Systems*, 2011 (API 610 itself not held) | Web | Pumps & Systems article |
| Fluid properties (density, vapor pressure, viscosity, c_p) for 11 fluids | `thermo` Python library (Bell et al.) | Own work (generated) | `Sizing Tool\Case Study Sizing Tool.html` (FLUID_TABLE), `generate_cp_table.py` |
| Sulfuric acid viscosity (replaces `thermo`, ~25× low) | Andrade fit to CORECHEM 93 wt % table | Web | https://corecheminc.com/sulfuric-acid-properties/ (fetched 2026-09-04) |
| Sulfuric acid heat capacity (replaces `thermo`, ~40 % low) | Perry's 9th ed., Table 2-91 | Library | `Textbooks (Level 1)\Handbooks & Quick Reference\Perry's 9th Edition.pdf` |
| Shaft allowable shear 6,000 psi, keyway derate 1.15× | Carbon-steel rule of thumb | Own work | `Sizing Tool\workflow_cases.py` |
| Vaned-diffuser threshold U₂ = 150 ft/s; axial-thrust K = 0.6; shock-loss K_SHO = 1.0 (back-solved to match shutoff) | Engineering judgment / calibration, flagged in the tool | Own work | `Sizing Tool\sizing_tool_parameter_limits.md` |

Detail behind every bounded constant: `Sizing Tool\sizing_tool_parameter_limits.md`.
