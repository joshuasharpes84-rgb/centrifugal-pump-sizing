"""
performance_curve_cases.py  --  prototype/validate the performance-curve computational math
(deck slides 19-21: "Computational Math: BEP Anchor", "Table 3: Component Efficiency
Expressions", "Computational Math: Shape of the Curve") against the Steps 1-9 case studies
in workflow_cases.py.

Entirely local: no HTML/JS touched. This is a methodology check before deciding whether/how
to update Case Study Sizing Tool.html's performance-curve section.

  BEP anchor        Table 3 (a): eta_HY = eta_I - zeta_c*(psi_i/2 + phi_i^2/(2*psi_i))
                    Table 3 (b): Jekat shortcut  eta_HY ~= 1 - 0.8/Q(gpm)^0.25
                    Table 3 (h): eta_m = 1 - (Cm/2)*eta_p / (Omega_s^2 * psi^2.5)
                    Table 3 (j): eta_v = 1 / (1 + 5*[(delta/rR)*(re/r2)^2 / (Omega_s^2*psi)])
  Shape of curve    non-recirculating branch: beta2b fixed, slip velocity locked at BEP,
                    resweep Q -> ideal psi_i(Q) -> Table 3(a) eta_HY(Q) -> real psi(Q) -> H(Q)
                    shutoff (full):   Hs/o = [kimp*(U2^2 - Uh1^2) + kex*U2^2] / (2g)
                    shutoff (Stepanoff shortcut, what the HTML tool currently uses): psi_s/o ~= 0.585

Cross-checks performed, not assumed:
  - eta_m (h)'s direct nondimensional formula vs. the HTML tool's P_df/P_hyd formulation --
    these are DIFFERENT derivations; this script checks whether they actually agree numerically.
  - Full shutoff (kimp/kex) vs. the HTML tool's Stepanoff-only shortcut -- the full formula needs
    a hub-inlet tip speed U_h1 this project has never computed; approximated here as Omega*r_s
    (shaft radius as a hub-radius stand-in) and flagged as such, not silently assumed elsewhere.

    "C:\\Users\\Administrator\\Downloads\\ChemE\\Python\\python.exe" "performance_curve_cases.py"

Nothing is plotted; results print as tables plus flags, same style as workflow_cases.py.
"""

import numpy as np

from workflow_cases import (
    CASES, run_case, _psi_real,
    G, FT_TO_M, IN_PER_M, RPM_TO_RADS, GPM_TO_M3S,
)

# ------------------------------------------------------------------ Table 3 constants (slide 20)
ETA_I, ZETA_C = 0.925, 0.25          # (a) impeller hydraulic eff. / collector loss -- same as steps_789
CM_PREFACTOR = 0.085                  # (f) disk friction coefficient prefactor, two-sided disk
DELTA_RR = 0.0015                     # (j) ring clearance ratio delta/r_R (single ring, front only)
DELTA_RR_TWO_RINGS = 2 * DELTA_RR     # (j)'s own note: front+back rings ~doubles the leakage constant

# ------------------------------------------------------------------ shape-of-curve constants (slide 21)
K_IMP = 1.00                          # centrifugal term coefficient (deck: "k_imp ~ 1")
K_EX = 0.20                           # recirculation "pitot" term (deck: "k_ex ~ 0.2 +/- 0.1")
PSI_SO_STEPANOFF = 0.585              # what the HTML tool currently uses (shortcut, not full formula)

CURVE_FRACS = [0.50, 0.65, 0.80, 0.90, 1.00, 1.10, 1.20, 1.30]


# ------------------------------------------------------------------ Table 3 (b),(f),(h),(j)
def jekat_eta_hy(Q_gpm):
    """(b) practical-experience shortcut, works at all specific speeds per the deck."""
    return 1.0 - 0.8 / Q_gpm ** 0.25


def disk_friction_Cm(Omega, r2_si, nu_si):
    """(f) Cm ~= 0.085 / (Omega*r2^2/nu)^0.2, two-sided disk. Returns (Cm, Re)."""
    Re = Omega * r2_si ** 2 / nu_si
    return CM_PREFACTOR / Re ** 0.2, Re


def eta_m_direct(Cm, eta_p, omega_s, psi):
    """(h) direct nondimensional mechanical efficiency -- the deck's own closed form."""
    return 1.0 - (Cm / 2.0) * eta_p / (omega_s ** 2 * psi ** 2.5)


def eta_m_power_ratio(Cm, Omega, rho_si, r2_si, P_hyd_si):
    """HTML tool's current alternate form: eta_m = 1/(1 + P_df/P_hyd), P_df = (Cm/2)*rho*Omega^3*r2^5.
    Kept separate from eta_m_direct so the two can be numerically compared, not assumed equal."""
    P_df = (Cm / 2.0) * rho_si * Omega ** 3 * r2_si ** 5
    return 1.0 / (1.0 + P_df / P_hyd_si), P_df


def eta_v_direct(delta_rR, re_si, r2_si, omega_s, psi):
    """(j) volumetric efficiency -- matches the HTML tool's existing implementation; recomputed
    here from the same inputs as an independent check, not copied."""
    term = 5.0 * (delta_rR * (re_si / r2_si) ** 2 / (omega_s ** 2 * psi))
    return 1.0 / (1.0 + term)


# ------------------------------------------------------------------ shape of the curve (slide 21)
def non_recirc_branch(Q_bep_si, Omega, r2_si, b2_si, eps, beta_deg, nb, fracs):
    """Non-recirculating branch: hold beta2b fixed, lock the BEP slip velocity, resweep Q.
    Returns a list of dicts, one per flow fraction that still gives psi_i > 0."""
    U2 = Omega * r2_si
    beta = np.radians(beta_deg)
    mu_bep = np.sqrt(np.sin(beta)) / nb ** 0.7      # Pfleiderer slip factor, locked at BEP
    Vs_bep = mu_bep * U2                             # slip velocity, locked (deck's explicit instruction)

    pts = []
    for f in fracs:
        Qp_si = Q_bep_si * f
        Vm2 = Qp_si / (2 * np.pi * r2_si * b2_si * eps)
        phi = Vm2 / U2
        Vu2_inf = U2 - Vm2 / np.tan(beta)
        Vu2 = Vu2_inf - Vs_bep
        psi_i = Vu2 / U2
        if psi_i <= 0:
            continue    # non-recirculating branch breaks down here (deck's own stated limit)
        eta_hy = ETA_I - ZETA_C * (psi_i / 2.0 + phi ** 2 / (2.0 * psi_i))
        psi_real = eta_hy * psi_i
        H_ft = psi_real * U2 ** 2 / G / FT_TO_M
        pts.append(dict(f=f, Q_gpm=Qp_si / GPM_TO_M3S, phi=phi, psi_i=psi_i,
                         eta_hy=eta_hy, psi_real=psi_real, H_ft=H_ft))
    return pts


def shutoff_head_full(U2, Uh1, kimp=K_IMP, kex=K_EX):
    """(slide 21) full shutoff formula: Hs/o = [kimp*(U2^2 - Uh1^2) + kex*U2^2] / (2g), SI in, ft out."""
    H_si = (kimp * (U2 ** 2 - Uh1 ** 2) + kex * U2 ** 2) / (2 * G)
    return H_si / FT_TO_M


# ------------------------------------------------------------------ driver
def g(x, fmt='{:.3f}'):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return '  -  '
    return fmt.format(x)


def main():
    results = run_case and [run_case(c) for c in CASES]

    print("BEP ANCHOR -- Table 3 component efficiencies (slide 19/20)")
    h1 = (f"{'case':<19}{'eta_HY':>7}{'HY,Jekat':>9}{'eta_m(h)':>9}{'eta_m(P)':>9}{'eta_v':>7}"
          f"{'BHP(h)':>8}{'BHP(P)':>8}{'BHP tool':>9}")
    print(h1); print('-' * len(h1))

    for out, c in zip(results, CASES):
        if not out.get('in_scope') or 'psi' not in out:
            continue

        # ---- recover SI geometry from run_case's inch/ft outputs (kept additive, no changes
        # to workflow_cases.py itself) ----
        N_rpm = out['N']
        Omega = N_rpm * RPM_TO_RADS
        r2_si = out['D2_in'] / (2 * IN_PER_M)
        b2_si = out['b2_in'] / IN_PER_M
        re_si = out['De_in'] / (2 * IN_PER_M)
        rs_si = out['rs_in'] / IN_PER_M
        Q_si = c['Q_gpm'] * GPM_TO_M3S
        H_si = c['H_ft'] * FT_TO_M
        rho_si = out['rho'] / 0.0624279606          # lb/ft3 -> kg/m3
        mu_si = out['mu'] * 1e-3                    # cP -> Pa.s
        nu_si = mu_si / rho_si
        omega_s = out['omega_s']
        psi = out['psi']
        eta_p = out['eta_p']

        # ---- Table 3 (a): eta_HY, recomputed from stored beta2b/phi2/nb (independent check
        # of psi_real, which steps_789 already computed) ----
        psi_real_check, psi_i = _psi_real(out['beta2b'], out['phi2'], out['nb'])
        eta_hy_detailed = psi_real_check / psi_i if psi_i else float('nan')
        eta_hy_jekat = jekat_eta_hy(c['Q_gpm'])

        # ---- Table 3 (f)+(h): direct mechanical efficiency ----
        Cm, Re = disk_friction_Cm(Omega, r2_si, nu_si)
        eta_m_h = eta_m_direct(Cm, eta_p, omega_s, psi)

        # ---- cross-check against the HTML tool's alternate P_df/P_hyd formulation ----
        P_hyd_si = rho_si * G * Q_si * H_si
        eta_m_p, P_df = eta_m_power_ratio(Cm, Omega, rho_si, r2_si, P_hyd_si)

        # ---- Table 3 (j): volumetric efficiency (single-ring constant, matches the HTML tool) ----
        eta_v = eta_v_direct(DELTA_RR, re_si, r2_si, omega_s, psi)

        # ---- real BEP power, three ways ----
        eta_total_h = eta_hy_detailed * eta_m_h * eta_v
        eta_total_p = eta_hy_detailed * eta_m_p * eta_v
        bhp_h = P_hyd_si / eta_total_h / 745.699872 if eta_total_h > 0 else float('nan')
        bhp_p = P_hyd_si / eta_total_p / 745.699872 if eta_total_p > 0 else float('nan')
        bhp_tool_style = out['bhp']   # Step 5's first-pass BHP (Anderson eta_p based, not Table 3) -- reference only

        out['_perf'] = dict(Omega=Omega, r2_si=r2_si, b2_si=b2_si, re_si=re_si, rs_si=rs_si,
                             Q_si=Q_si, H_si=H_si, rho_si=rho_si, eta_hy_detailed=eta_hy_detailed,
                             eta_m_h=eta_m_h, eta_m_p=eta_m_p, eta_v=eta_v, Cm=Cm, Re=Re,
                             bhp_h=bhp_h, bhp_p=bhp_p)

        print(f"{c['name']:<19}{g(eta_hy_detailed,'{:.3f}'):>7}{g(eta_hy_jekat,'{:.3f}'):>9}"
              f"{g(eta_m_h,'{:.3f}'):>9}{g(eta_m_p,'{:.3f}'):>9}{g(eta_v,'{:.3f}'):>7}"
              f"{g(bhp_h,'{:.0f}'):>8}{g(bhp_p,'{:.0f}'):>8}{g(bhp_tool_style,'{:.0f}'):>9}")

    print("\n  eta_m(h) = direct Table 3 formula (eq h);  eta_m(P) = HTML tool's P_df/P_hyd form.")
    print("  Divergence between BHP(h) and BHP(P) below is exactly the eta_m formulation gap --")
    print("  see the module docstring; this is a real discrepancy the HTML tool has not resolved.")

    print("\nSHUTOFF HEAD -- Stepanoff shortcut (HTML tool today) vs. full kimp/kex formula (slide 21)")
    h2 = f"{'case':<19}{'U2 ft/s':>8}{'Hs/o Stepanoff':>15}{'Hs/o full (Uh1~rs)':>19}{'delta %':>9}"
    print(h2); print('-' * len(h2))
    for out, c in zip(results, CASES):
        if not out.get('in_scope') or 'psi' not in out or '_perf' not in out:
            continue
        p = out['_perf']
        U2 = p['Omega'] * p['r2_si']
        Hso_step = PSI_SO_STEPANOFF * U2 ** 2 / G / FT_TO_M
        Uh1 = p['Omega'] * p['rs_si']     # approximation -- no separate hub radius computed anywhere yet
        Hso_full = shutoff_head_full(U2, Uh1)
        delta_pct = (Hso_full - Hso_step) / Hso_step * 100
        print(f"{c['name']:<19}{U2/FT_TO_M:>8.0f}{Hso_step:>15.1f}{Hso_full:>19.1f}{delta_pct:>+9.1f}")
    print("\n  Hs/o full uses U_h1 ~= Omega*r_s (shaft radius) as a stand-in for the true hub-inlet")
    print("  tip speed -- this project has never computed a distinct hub radius. Treat as a rough")
    print("  bound, not a resolved number; a real hub radius (slide 13, still qualitative-only in")
    print("  the deck) would sit between r_s and r_e, moving Hs/o(full) further from Stepanoff.")

    print("\nNON-RECIRCULATING BRANCH -- H(Q) at key fractions (slide 21), beta2b fixed, slip locked at BEP")
    h3 = f"{'case':<19}" + ''.join(f"{f:>8.2f}" for f in CURVE_FRACS)
    print(h3 + '   <- Q fraction of rated'); print('-' * len(h3))
    for out, c in zip(results, CASES):
        if not out.get('in_scope') or 'psi' not in out or '_perf' not in out:
            continue
        p = out['_perf']
        pts = non_recirc_branch(p['Q_si'], p['Omega'], p['r2_si'], p['b2_si'],
                                 0.85, out['beta2b'], out['nb'], CURVE_FRACS)
        row = {round(pt['f'], 2): pt['H_ft'] for pt in pts}
        cells = ''.join(f"{g(row.get(round(f,2)),'{:.0f}'):>8}" for f in CURVE_FRACS)
        print(f"{c['name']:<19}{cells}")
        target_pt = next((pt for pt in pts if abs(pt['f'] - 1.0) < 1e-9), None)
        if target_pt:
            resid_pct = (target_pt['H_ft'] - c['H_ft']) / c['H_ft'] * 100
            if abs(resid_pct) > 1:
                print(f"  -> convergence residual at f=1.00: predicted {target_pt['H_ft']:.1f} ft "
                      f"vs. target {c['H_ft']:.0f} ft ({resid_pct:+.1f}%) -- slide 21's own closure "
                      f"check (adjust phi_e/psi, blade angle/slip, or b2 and re-solve Steps 7-9).")

    print("\nKnown limits carried over unchanged from the deck (slide 21's own words):")
    print("  - doesn't reliably capture the recirculation-driven kink near shutoff on high-sigma curves")
    print("  - gives no real NPSHr-vs-Q (that's explicitly a CFD-only deliverable, slide 23)")
    print("  - Limp's deeper breakdown (Table 3 eq c: k*W1^2/2 + f*Wbar^2/2*(l/Dh)) needs passage")
    print("    hydraulic diameter/length this tool doesn't model -- eta_HY stays at the eq (a) level")


if __name__ == '__main__':
    main()
