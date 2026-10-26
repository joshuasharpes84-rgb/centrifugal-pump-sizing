# Engineering Decisions — Centrifugal Pump Sizing

The calls that shaped the method, the Sizing Tool and the Pump Changeover Simulator: what was
decided, what was rejected, and why. Sources for each topic are in `SOURCES.md`.

*Built by Joshua Sharpes, EIT, with AI assistance (Claude) for drafting, coding and literature
checks. Scope, method selection, validation criteria and the corrections below are his.*

## Scope

**Single-stage, radial-flow only (2026-08-26).** An early draft of the deck covered multistage and
mixed-/axial-flow designs. That content was cut so one method could be carried through and
checked end to end, rather than several sketched.

**A specific-speed gate, checked against the source (2026-08-28).** The first case studies produced
bad geometry at the edges of the Q-H map. Rather than accept a narrower scope on assumption, the
limits were checked against Karassik's own treatment of low specific speed first. The tool now
screens Ωₛ 0.37–1.0 and refuses cases outside it. Regenerative and other special low-flow pumps
were judged a separate workflow, not a bolt-on.

**Sizing only, not procurement.** The data sheet tells a vendor what is wanted (duty plus the sized
impeller diameter, stages and a conservative max working pressure) so they can propose their nearest
catalog model. Materials, seals and motor selection belong to later steps and other projects.

## Method

**Formulas must match the deck (2026-09-05).** Rule for the HTML tool: every formula traces to a
slide and Karassik equation; no unsourced substitutes. Where the deck gives only a chart, the
approximation is documented and flagged in the tool.

**Suction-specific-speed remedies follow the deck's order.** When N_ss is out of range the tool
automatically tries the deck's remedy sequence (drop speed first) instead of asking the user to
pick one. An inducer is flagged with a pointer to NPSHₐ changes, not sized, because the deck omits
the blade angle an inducer design needs. Double-suction stays a deliberate manual choice.

**Eye radius closure.** Karassik's eye equations leave three unknowns in two equations. The shaft
radius is closed by a torque/stress calculation, not by assuming a hub/eye ratio. A widely quoted
"0.35–0.45 hub/eye ratio" was traced to Lobanoff & Ross / Stepanoff, not Karassik, and is used only
as an iteration seed. Overhung impellers carry no shaft through the eye (rₛ = 0 there).

**Near-linear H-Q curves accepted as physics, not "fixed" (2026-09-06).** The predicted curves
looked almost straight. Before changing anything, the cause was investigated: Karassik p. 2.45
ties a strong rise to shutoff to high specific speed, which this tool's scope excludes. A
shock/incidence-loss term was added because it is real physics, but curvature was not forced
beyond what the method supports.

**No result overrides (2026-10-13).** A "continuous rise" default curve was built so the
simulator's curves would look the way pump curves usually look. It was removed because it produced
the expected answer by construction. The tool now runs a low/central/high shutoff band and reports
how many of the three cases lift, stay above minimum flow, or deadhead. A vendor shutoff head, if
known, collapses the band.

**One method, not three (2026-10-13).** Showing three shutoff methods side by side read as a lack of
confidence. The Karassik Eq. 65/66 method with its stated ±0.1 band was selected; Stepanoff's
ψ ≈ 0.585 sits inside that band and serves as the cross-check.

## Data quality

**Library property data checked, not trusted.** `thermo` gave sulfuric acid viscosity ~25× low and
heat capacity ~40 % low. Both were replaced with sourced values (CORECHEM fit, Perry's Table 2-91).
Shipping the raw viscosity would have misclassified the acid as non-viscous and skipped its NPSH
margin.

## Pump Changeover Simulator

**Grounded in a real system.** The idea came from reviewing a parallel-pump pair on a furnace
P&ID from Joshua's plant experience, and Karassik's warning that adding a parallel pump can push each
pump below minimum flow.

**Scoped to one credible failure mode.** Parallel pumps are almost always identical, so the
simulator models two identical pumps and one deviation: wear-ring clearance. Clearance ratio is
capped at 4, and inputs are held to the sizing tool's single-stage screen; the simulator refuses
what the sizing tool only flags.

**Clearance ratio guidance from practice.** The input that drives the answer is the hardest to know.
Most repairs are done in house and rarely record ring clearances, so the guidance tells users how to
bound it: the running pump at 1.0 for the lift check, the standby pump from its repair record, 2.0 if
not recorded.

**A default case that shows a range under normal operation.** The default duty was moved from
500 gpm / 250 ft to 500 gpm / 300 ft so normal inputs produce ok, marginal and deadhead outcomes
without abnormal settings. The validated Karassik case (Cooper's §2.1 example) remains the
benchmark.

## Validation

- Reproduces Cooper's §2.1 worked design example (φₑ = 0.29).
- Minimum flow reproduces Karassik Table 16's sample (24.04 vs 24.03 ft³/s).
- Two independent shutoff estimates agree within ±2 % across the case spread.
- Known ~1 % BHP difference between two efficiency formulations is documented, not hidden.
