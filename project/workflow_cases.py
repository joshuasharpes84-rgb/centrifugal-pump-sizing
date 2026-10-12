"""
workflow_cases.py  --  exercise the pump sizing workflow, Steps 1 -> impeller blade geometry.

Implements the procedure in  ../Sizing Workflow.md  (deck slides 2-13) and runs it on a spread of
duty points to test where the workflow converges cleanly vs. hits a decision / boundary.

  Steps 1-6  speed, NPSH, Nss, shaft radius, eye radius            (Sizing Workflow.md)
  Steps 7-9  exit radius, exit width, blade angle/count            (slides 10-13; Fig. 12 fits
             + Pfleiderer slip, ported from Case Study Sizing Tool.html)

    "C:\\Users\\Administrator\\Downloads\\ChemE\\Python\\python.exe" "workflow_cases.py"

Nothing is plotted; results print as a table plus per-case flags.
"""

import numpy as np
from scipy.optimize import brentq

try:
    from thermo import Chemical
    _HAVE_THERMO = True
except Exception:
    _HAVE_THERMO = False

# ------------------------------------------------------------------ constants / unit conv
G = 9.80665                       # m/s^2
GPM_TO_M3S = 6.309019640e-5
FT_TO_M    = 0.3048
IN_PER_M   = 39.3700787
PSI_TO_PA  = 6894.757
RPM_TO_RADS = 2.0 * np.pi / 60.0
NSS_UNIV_TO_US = 2733.016         # N_ss,US = 2733 * omega_ss(universal)

# Step 2 -- NPSH margin by service (slide 5)
SERVICE_MARGIN = {
    'none':                  1.00,   # validation only -- NPSHr = NPSHa
    'clean_cold_water':      1.15,   # 1.1-1.2 (HI min)
    'hydrocarbon_hot_water': 1.25,   # 1.2-1.3
    'viscous':               1.40,   # 1.3-1.5
    'slurry_erosive':        1.75,   # 1.5-2.0
    'critical_no_spare':     2.00,
}

# Step 3 -- N_ss,US acceptable band (Fig. 25 safe region + HI)
NSS_TARGET   = 9000.0
NSS_WARN     = 11000.0            # above this: marginal, prefer to drop speed
NSS_INDUCER  = 13000.0            # no normal impeller solution -> inducer

# Step 3b -- SPECIFIC-SPEED SCOPE GATE
#   slide 2's orange band ("CENTRIFUGAL" on the impeller-shape chart) marks the radial pump
#   *type* as N_s,US ~ 273 - 2733  (= omega_s 0.10 - 1.00).  That is a pump-selection limit,
#   not a sizing-method limit.
#   The deck's paper-math (Fig. 12 psi/phi fits + Pfleiderer blades) only produces a valid
#   backward-curved impeller over the tighter  omega_s 0.37 - 1.00  (N_s,US ~ 1000 - 2730):
#     - below 0.37: psi_target = 0.383/omega_s^(1/3) exceeds what a 15-35 deg blade can make
#                   -> blade solve pins near-radial, b2/D2 collapses (cases B, D, E)
#     - above 1.00: mixed-flow onset; D2/De -> 1, Fig. 12 fits degrade (case C)
#   HARD GATE below = the intersection (method-valid AND radial type).
OMEGA_S_RADIAL   = (0.37, 1.00)   # hard scope gate for this workflow
OMEGA_S_TYPE     = (0.10, 1.00)   # slide-2 pump-type band (looser, low end)

# Step 5 -- shaft
SS_ALLOW_PSI = 6000.0             # allowable shear stress, carbon-steel keyed shaft (ROT); DECISION
KEYWAY_FACTOR = 1.15             # section-modulus derate -> r_s * 1.15**(1/3)
ANDERSON_X = 1.0                  # roughness factor (X=1 => eps ~ 140 uin, rough cast)

# Step 6 -- Table 1a (Gongwer, typical pumps)
K1, K2 = 1.69, 0.102             # tau = (k1+k2)*phi_e^2 + k2
PHI_E_CAP = 0.30                 # upper limit of normal practice at BEP
RS_RE_SEED = 0.40

# Steps 7-9 -- Fig. 12 fits + Pfleiderer (constants from Case Study Sizing Tool.html)
OMEGA_S_FIG12 = (0.20, 1.60)      # Fig. 12 valid range for the psi/phi fits
EPS = 0.85                        # exit openness factor (blade + BL blockage), slide 11
ETA_I, ZETA_C = 0.925, 0.25       # impeller / collector loss coeffs for eta_HY
BETA_PRIMARY, BETA_FALLBACK = (15.0, 35.0), (10.0, 60.0)   # backward-curved blade-angle windows
U2_WARN_FTS = 250.0               # tip-speed caution proxy (generic, not a stress calc)
DIFFUSION_LIMIT = 0.60            # NACA loss-onset diffusion factor


# ------------------------------------------------------------------ fluid properties
def fluid_props(name, T_F):
    """return (rho [lb/ft3], mu [cP], Psat [psia]) -- liquid phase."""
    T_K = (T_F - 32.0) / 1.8 + 273.15
    if _HAVE_THERMO:
        c = Chemical(name, T=T_K)
        rho = c.rhol * 0.0624279606        # kg/m3 -> lb/ft3
        mu  = (c.mul or 1e-3) * 1000.0      # Pa.s -> cP
        psat = (c.Psat or 0.0) / PSI_TO_PA  # Pa -> psia
        return rho, mu, psat
    # crude fallbacks if thermo unavailable
    table = {'water': (62.3, 0.7, 0.5), 'propane': (31.0, 0.10, 120.0),
             'ammonia': (38.0, 0.13, 130.0), 'toluene': (52.0, 0.55, 0.5)}
    return table.get(name, (55.0, 1.0, 1.0))


# ------------------------------------------------------------------ workflow steps
def omega_ss_achievable(phi_e, B):
    """universal suction specific speed an impeller of this phi_e and blockage B=(1-rs^2/re^2)
    can carry at 3% breakdown (Table 1a, zero prewhirl)."""
    tau = (K1 + K2) * phi_e**2 + K2
    return np.sqrt(np.pi * phi_e * B) / (tau / 2.0)**0.75


def solve_phi_e(omega_ss_req, B):
    """pick phi_e = min(high root of Eq.50, 0.30); flag inducer if the requirement exceeds
    what any impeller can carry.  Returns (phi_e, mode)."""
    # peak of omega_ss_achievable vs phi_e
    xs = np.linspace(0.02, 0.60, 600)
    ys = omega_ss_achievable(xs, B)
    i_pk = int(np.argmax(ys))
    phi_pk, omega_pk = xs[i_pk], ys[i_pk]

    if omega_ss_achievable(PHI_E_CAP, B) >= omega_ss_req:
        return PHI_E_CAP, 'phi_e capped at 0.30 (NPSH-generous; eye set by the cap)'
    if omega_ss_req > omega_pk:
        return None, f'INDUCER: required omega_ss {omega_ss_req:.2f} exceeds impeller peak {omega_pk:.2f}'
    # high root lies between phi_pk and 0.30
    phi = brentq(lambda p: omega_ss_achievable(p, B) - omega_ss_req, phi_pk, PHI_E_CAP)
    return phi, 'phi_e solved from Eq.50 (suction-limited)'


def solve_re(Q_si, Omega, phi_e, rs):
    """Eq.49 cubic  re^3 - rs^2 re - Q/(pi Omega phi_e) = 0  -- one positive root."""
    C = Q_si / (np.pi * Omega * phi_e)
    roots = np.roots([1.0, 0.0, -rs**2, -C])
    real = roots[np.abs(roots.imag) < 1e-9].real
    return float(real[real > 0][0])


def classify_omega_s(omega_s):
    """specific-speed scope gate. returns (in_scope: bool, status: str)."""
    Ns = NSS_UNIV_TO_US * omega_s
    lo, hi = OMEGA_S_RADIAL
    tlo, _ = OMEGA_S_TYPE
    if omega_s < lo:
        why = ('still a radial pump by type but' if omega_s >= tlo else 'below the radial type band;')
        return False, f'OUT: omega_s {omega_s:.2f} (Ns {Ns:.0f}) < {lo} -- {why} paper-math cannot make a backward-curved blade (multistage / special impeller)'
    if omega_s > hi:
        return False, f'OUT: omega_s {omega_s:.2f} (Ns {Ns:.0f}) > {hi} -- past the radial band; mixed-/axial-flow'
    return True, f'IN: omega_s {omega_s:.2f} (Ns {Ns:.0f}) in [{lo}, {hi}]'


def _blade_count(omega_s):
    return 7 if omega_s < 0.6 else 6 if omega_s < 1.0 else 5 if omega_s < 1.6 else 4


def _psi_real(beta_deg, phi_ex, nb):
    """real head coeff for a backward-curved blade at beta, with Pfleiderer slip + eta_HY."""
    b = np.radians(beta_deg)
    psi_i_inf = 1.0 - phi_ex / np.tan(b)
    mu = np.sqrt(np.sin(b)) / nb**0.7                 # Pfleiderer slip
    psi_i = psi_i_inf - mu
    if psi_i <= 0:
        return -1.0, psi_i
    eta_hy = ETA_I - ZETA_C * (psi_i / 2.0 + phi_ex**2 / (2.0 * psi_i))
    return eta_hy * psi_i, psi_i


def steps_789(out, Q_si, Omega, H_si, re, rs_eye):
    """Steps 7-9: exit radius (Fig.12 psi), exit width (Fig.12 phi2 + eps), blade angle/count."""
    omega_s = Omega * np.sqrt(Q_si) / (G * H_si)**0.75
    Ns_us = NSS_UNIV_TO_US * omega_s
    out.update(omega_s=omega_s, Ns_us=Ns_us)

    fig12 = OMEGA_S_FIG12[0] <= omega_s <= OMEGA_S_FIG12[1]
    if not fig12:
        side = 'axial/propeller' if omega_s > OMEGA_S_FIG12[1] else 'below range (steep H/Q -> multistage?)'
        out['geom_flag'] = f'omega_s={omega_s:.2f} outside Fig.12 [{OMEGA_S_FIG12[0]}, {OMEGA_S_FIG12[1]}] -- {side}'
        return out

    # -- Step 7: exit radius from head coefficient (Fig. 12 fit)
    psi = 0.383 / omega_s**(1.0/3.0)
    r2 = np.sqrt(G * H_si / psi) / Omega
    U2 = Omega * r2
    U2_fts = U2 * (1.0/FT_TO_M)
    out.update(psi=psi, r2_in=r2*IN_PER_M, D2_in=2*r2*IN_PER_M, U2_fts=U2_fts,
               D2_De=r2/re)

    # -- Step 8: exit width from exit flow coefficient (Fig. 12 fit) + openness eps
    phi2 = 0.1715 * np.sqrt(omega_s)
    b2_over_r2 = (omega_s * psi)**1.5 / (0.343 * np.pi * EPS)
    b2 = b2_over_r2 * r2
    out.update(phi2=phi2, b2_in=b2*IN_PER_M, b2_D2=b2/(2*r2))

    # -- Step 9: blade count + outlet blade angle (Pfleiderer slip, target real psi)
    nb = _blade_count(omega_s)
    def solve_beta(lo, hi):
        f = lambda beta: _psi_real(beta, phi2, nb)[0] - psi
        # _psi_real can be -1 (psi_i<=0) at low beta; scan for a sign change
        betas = np.linspace(lo, hi, 200)
        vals = np.array([f(b) for b in betas])
        good = np.where(np.isfinite(vals) & (vals > -0.99))[0]
        if len(good) < 2:
            return None
        lo2, hi2 = betas[good[0]], betas[good[-1]]
        if f(lo2) * f(hi2) > 0:
            return betas[good[np.argmin(np.abs(vals[good]))]]   # closest, no bracket
        return brentq(f, lo2, hi2)

    beta = solve_beta(*BETA_PRIMARY)
    used_fallback = False
    if beta is None or abs(_psi_real(beta, phi2, nb)[0] - psi) / psi > 0.01:
        b_fb = solve_beta(*BETA_FALLBACK)
        if b_fb is not None:
            beta, used_fallback = b_fb, True
    psi_real_final, psi_i = _psi_real(beta, phi2, nb) if beta else (np.nan, np.nan)

    # rough diffusion factor: W1 at eye shroud, W2 at exit
    Ue = Omega * re
    Ve = Q_si / (np.pi * (re**2 - rs_eye**2))
    W1 = np.hypot(Ve, Ue)
    Vm2 = phi2 * U2
    W2 = Vm2 / np.sin(np.radians(beta)) if beta else np.nan
    Vu2 = U2 - Vm2 / np.tan(np.radians(beta)) if beta else np.nan
    D_diff = 1.0 - W2/W1 + abs(Vu2) / (2.0 * nb / (2*np.pi) * W1 * (r2/re - 1) + 1e-9)
    # (the delta-Wb term needs blade geometry; this is a first-order proxy)
    out.update(nb=nb, beta2b=beta, psi_real=psi_real_final, used_fallback=used_fallback,
               W1_fts=W1/FT_TO_M, W2_fts=(W2/FT_TO_M if np.isfinite(W2) else np.nan))

    flags = []
    if U2_fts > U2_WARN_FTS:
        flags.append(f'U2={U2_fts:.0f} ft/s > {U2_WARN_FTS:.0f} (high-energy proxy)')
    if used_fallback:
        flags.append(f'beta2b={beta:.0f} deg needed fallback range -> near-radial, flat/unstable H-Q risk')
    elif beta is not None and not (BETA_PRIMARY[0] <= beta <= BETA_PRIMARY[1]):
        flags.append(f'beta2b={beta:.0f} deg outside {BETA_PRIMARY}')
    if np.isfinite(out['b2_D2']) and out['b2_D2'] < 0.02:
        flags.append(f'b2/D2={out["b2_D2"]:.3f} very thin impeller')
    out['geom_flag'] = ' ; '.join(flags) if flags else 'OK'
    return out


def run_case(c):
    out = {'name': c['name']}
    rho_lbft3, mu_cP, psat_psia = fluid_props(c['fluid'], c['T_F'])
    rho_si = rho_lbft3 / 0.0624279606
    Q_si   = c['Q_gpm'] * GPM_TO_M3S
    H_si   = c['H_ft'] * FT_TO_M
    out.update(rho=rho_lbft3, mu=mu_cP, psat=psat_psia)

    # ---- Step 2: NPSHr from NPSHa + service margin
    margin = SERVICE_MARGIN[c['service']]
    NPSHr_ft = c['NPSHa_ft'] / margin
    out.update(NPSHa=c['NPSHa_ft'], margin=margin, NPSHr=NPSHr_ft)

    # ---- Step 1 + 3: pick highest speed that keeps N_ss in band
    if c.get('force_N'):
        N_rpm = c['force_N']
        Nss_US = N_rpm * np.sqrt(c['Q_gpm']) / NPSHr_ft**0.75
    else:
        chosen = None
        for N in (3600, 1800, 1200, 900):
            Nss = N * np.sqrt(c['Q_gpm']) / NPSHr_ft**0.75
            if Nss <= NSS_WARN:
                chosen = (N, Nss); break
            chosen = (N, Nss)   # keep the lowest-speed (lowest-Nss) fallback
        N_rpm, Nss_US = chosen
    Omega = N_rpm * RPM_TO_RADS
    out.update(N=N_rpm, Nss=Nss_US)
    _tail = ' (forced N)' if c.get('force_N') else ' (even at 900 rpm)'
    out['nss_flag'] = ('OK' if Nss_US <= NSS_WARN else
                       'INDUCER?' if Nss_US >= NSS_INDUCER else 'MARGINAL: Nss high' + _tail)

    # ---- Step 3b: SPECIFIC-SPEED SCOPE GATE (slide 2)
    omega_s = Omega * np.sqrt(Q_si) / (G * H_si)**0.75
    in_scope, scope_status = classify_omega_s(omega_s)
    out.update(omega_s=omega_s, Ns_us=NSS_UNIV_TO_US * omega_s,
               in_scope=in_scope, scope_status=scope_status)
    if not in_scope:
        out['eye_flag'] = out['geom_flag'] = 'SCOPE'
        return out          # stop -- not a single-stage radial pump

    # ---- Step 5: shaft radius
    Ns_US = N_rpm * np.sqrt(c['Q_gpm']) / c['H_ft']**0.75
    eta_p = (0.94
             - 0.08955 * (c['Q_gpm'] / (N_rpm * ANDERSON_X))**0.21333
             - 0.29 * (np.log10(2286.0 / Ns_US))**2)
    eta_p = min(max(eta_p, 0.30), 0.92)
    P_hyd = rho_si * G * Q_si * H_si
    M = P_hyd / eta_p / Omega
    Ss_pa = SS_ALLOW_PSI * PSI_TO_PA
    rs = (16.0 * M / (np.pi * Ss_pa))**(1.0/3.0) * KEYWAY_FACTOR**(1.0/3.0)
    out.update(Ns=Ns_US, eta_p=eta_p, bhp=P_hyd/eta_p/745.7, M_lbfft=M*0.737562,
               rs_in=rs*IN_PER_M)

    # ---- Step 6: eye radius
    # shaft blocks the eye ONLY for between-bearings configs (double-suction, multistage).
    # a single-suction OVERHUNG impeller has a clear eye -> rs_eye = 0, B = 1.
    config = c.get('config', 'overhung')
    rs_eye = 0.0 if config == 'overhung' else rs
    out['config'] = config

    omega_ss_req = Nss_US / NSS_UNIV_TO_US
    ratio = 0.0 if rs_eye == 0.0 else RS_RE_SEED
    for _ in range(20):
        B = 1.0 - ratio**2
        phi_e, mode = solve_phi_e(omega_ss_req, B)
        if phi_e is None:
            out.update(phi_e=None, re_in=None, ratio=None, eye_flag='INDUCER',
                       eye_mode=mode); return out
        re = solve_re(Q_si, Omega, phi_e, rs_eye)
        new_ratio = rs_eye / re
        if abs(new_ratio - ratio) < 1e-4:
            ratio = new_ratio; break
        ratio = new_ratio

    flag = 'OK'
    if rs_eye > 0.0 and not (0.30 <= ratio <= 0.50):
        flag = f'rs/re = {ratio:.2f} outside 0.30-0.50'
    if phi_e < 0.15:
        flag = f'phi_e = {phi_e:.2f} < 0.15  -> re-check with inducer tau'
    elif phi_e < 0.20:
        flag = f'phi_e = {phi_e:.2f} < 0.20  -> inducer borderline'
    out.update(phi_e=phi_e, re_in=re*IN_PER_M, De_in=2*re*IN_PER_M,
               ratio=ratio, eye_mode=mode, eye_flag=flag)

    # ---- Steps 7-9: exit radius / width / blades  (slides 10-13)
    steps_789(out, Q_si, Omega, H_si, re, rs_eye)
    return out


# ------------------------------------------------------------------ case set
CASES = [
    dict(name='A water baseline',   fluid='water',   Q_gpm=1000, H_ft=200, T_F=80,  NPSHa_ft=25,  service='clean_cold_water'),
    dict(name='B water high-head',  fluid='water',   Q_gpm=500,  H_ft=600, T_F=80,  NPSHa_ft=20,  service='clean_cold_water'),
    dict(name='C water high-flow',  fluid='water',   Q_gpm=3000, H_ft=80,  T_F=80,  NPSHa_ft=30,  service='clean_cold_water'),
    dict(name='D water low-flow',   fluid='water',   Q_gpm=120,  H_ft=300, T_F=80,  NPSHa_ft=18,  service='clean_cold_water'),
    dict(name='E propane',          fluid='propane', Q_gpm=800,  H_ft=250, T_F=55,  NPSHa_ft=12,  service='hydrocarbon_hot_water'),
    dict(name='F hot water',        fluid='water',   Q_gpm=1200, H_ft=150, T_F=240, NPSHa_ft=15,  service='hydrocarbon_hot_water'),
    dict(name='G tight suction',    fluid='water',   Q_gpm=1500, H_ft=120, T_F=80,  NPSHa_ft=8,   service='clean_cold_water'),
    dict(name='H high suction-E',   fluid='water',   Q_gpm=2000, H_ft=100, T_F=80,  NPSHa_ft=6,   service='clean_cold_water'),
    dict(name='I inducer-territory',fluid='water',   Q_gpm=2500, H_ft=90,  T_F=80,  NPSHa_ft=4.5, service='clean_cold_water'),
    # between-bearings variants -- shaft DOES pass through the eye (rs_eye = rs)
    dict(name='A-bb (shaft thru)',  fluid='water',   Q_gpm=1000, H_ft=200, T_F=80,  NPSHa_ft=25,  service='clean_cold_water', config='between_bearings'),
    dict(name='G-bb (shaft thru)',  fluid='water',   Q_gpm=1500, H_ft=120, T_F=80,  NPSHa_ft=8,   service='clean_cold_water', config='between_bearings'),
    # validation -- Cooper's §2.1 design example: sigma_s=1, ss=4.5, N=1780, NPSH3%=14 ft, end-suction (overhung)
    dict(name='V Handbook example', fluid='water',   Q_gpm=2509, H_ft=105, T_F=68,  NPSHa_ft=14,  service='none', force_N=1780),
]


def g(r, k, f='{:.2f}'):
    v = r.get(k)
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return '  -  '
    return f.format(v)


def main():
    results = [run_case(c) for c in CASES]
    print(f"thermo={_HAVE_THERMO}  S_s={SS_ALLOW_PSI:.0f}psi  |  SCOPE GATE: omega_s "
          f"{OMEGA_S_RADIAL[0]}-{OMEGA_S_RADIAL[1]}  (Ns,US {NSS_UNIV_TO_US*OMEGA_S_RADIAL[0]:.0f}-"
          f"{NSS_UNIV_TO_US*OMEGA_S_RADIAL[1]:.0f})   slide-2 type band: omega_s "
          f"{OMEGA_S_TYPE[0]}-{OMEGA_S_TYPE[1]}\n")

    print("SCOPE GATE")
    hs = f"{'case':<19}{'Q':>6}{'H':>6}{'N':>6}{'omega_s':>9}{'Ns':>7}   status"
    print(hs); print('-' * 96)
    for r in results:
        c = next(x for x in CASES if x['name'] == r['name'])
        print(f"{r['name']:<19}{c['Q_gpm']:>6}{c['H_ft']:>6}{r.get('N',0):>6}"
              f"{g(r,'omega_s','{:.3f}'):>9}{g(r,'Ns_us','{:.0f}'):>7}   {r.get('scope_status','')}")

    print("\nSTEPS 1-6  (in-scope cases)")
    h1 = (f"{'case':<19}{'cfg':<5}{'NPSHr':>7}{'Nss':>7}{'eta_p':>7}{'BHP':>6}{'rs':>6}"
          f"{'phi_e':>7}{'De':>6}{'rs/re':>7}  flags")
    print(h1); print('-' * len(h1))
    for r in results:
        if not r.get('in_scope'):
            continue
        print(f"{r['name']:<19}{r.get('config','')[:4]:<5}{g(r,'NPSHr','{:.1f}'):>7}{r['Nss']:>7.0f}"
              f"{g(r,'eta_p'):>7}{g(r,'bhp','{:.0f}'):>6}{g(r,'rs_in','{:.2f}'):>6}{g(r,'phi_e'):>7}"
              f"{g(r,'De_in','{:.1f}'):>6}{g(r,'ratio'):>7}  {r.get('nss_flag','')} | {r.get('eye_flag','')}")

    print("\nSTEPS 7-9  (in-scope cases)")
    h2 = (f"{'case':<19}{'psi':>6}{'D2':>6}{'U2fps':>7}{'D2/De':>7}{'b2':>6}{'b2/D2':>7}"
          f"{'nb':>4}{'beta2b':>8}  flags")
    print(h2); print('-' * len(h2))
    for r in results:
        if not r.get('in_scope') or 'psi' not in r:
            continue
        print(f"{r['name']:<19}{g(r,'psi','{:.2f}'):>6}{g(r,'D2_in','{:.1f}'):>6}{g(r,'U2_fts','{:.0f}'):>7}"
              f"{g(r,'D2_De','{:.2f}'):>7}{g(r,'b2_in','{:.2f}'):>6}{g(r,'b2_D2','{:.3f}'):>7}"
              f"{g(r,'nb','{:.0f}'):>4}{g(r,'beta2b','{:.0f}'):>8}  {r.get('geom_flag','')}"
              f"{'  (FALLBACK)' if r.get('used_fallback') else ''}")


if __name__ == '__main__':
    main()
