#!/usr/bin/env python3
"""Post-experiment significance + confidence-interval calculator.

Stdlib only — no scipy/numpy. Two sub-commands:

  binary      Two-proportion z-test + Wilson CI on each rate + CI on the lift.
              python significance.py binary --control 5000 520 --variant 5000 590
                (args: n converted)

  continuous  Welch's t-test (unequal variance), normal approx for p / CI.
              python significance.py continuous --control 4800 12.4 8.1 \
                                                 --variant 4750 13.9 8.6
                (args: n mean std)

Optional (both): --alpha 0.05  --srm  (run a 50/50 sample-ratio-mismatch chi-square check)
"""
import argparse
import math
import sys


def norm_cdf(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def two_sided_p_from_z(z: float) -> float:
    return 2 * (1 - norm_cdf(abs(z)))


def z_crit(alpha: float) -> float:
    # inverse-normal via bisection (kept local so this file is standalone)
    lo, hi = 0.0, 10.0
    target = 1 - alpha / 2
    for _ in range(100):
        mid = (lo + hi) / 2
        if norm_cdf(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def wilson_ci(conv: int, n: int, alpha: float):
    if n == 0:
        return (0.0, 0.0)
    z = z_crit(alpha)
    p = conv / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def srm_check(n_c: int, n_v: int):
    """Chi-square goodness-of-fit vs expected 50/50. Flags allocation bugs."""
    total = n_c + n_v
    exp = total / 2
    chi2 = (n_c - exp) ** 2 / exp + (n_v - exp) ** 2 / exp
    # 1 dof, alpha=0.001 critical value = 10.83 (conservative SRM threshold)
    return chi2, chi2 > 10.83


def run_binary(args) -> int:
    n_c, x_c = args.control
    n_v, x_v = args.variant
    n_c, x_c, n_v, x_v = int(n_c), int(x_c), int(n_v), int(x_v)
    p_c, p_v = x_c / n_c, x_v / n_v

    p_pool = (x_c + x_v) / (n_c + n_v)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_v))
    z = (p_v - p_c) / se if se > 0 else 0.0
    p_val = two_sided_p_from_z(z)

    abs_lift = p_v - p_c
    rel_lift = abs_lift / p_c if p_c > 0 else float("inf")
    se_diff = math.sqrt(p_c * (1 - p_c) / n_c + p_v * (1 - p_v) / n_v)
    zc = z_crit(args.alpha)
    ci_lo, ci_hi = abs_lift - zc * se_diff, abs_lift + zc * se_diff

    print("=== Binary metric ===")
    print(f"Control : {x_c:,}/{n_c:,} = {p_c:.4%}  Wilson "
          f"[{wilson_ci(x_c, n_c, args.alpha)[0]:.4%}, "
          f"{wilson_ci(x_c, n_c, args.alpha)[1]:.4%}]")
    print(f"Variant : {x_v:,}/{n_v:,} = {p_v:.4%}  Wilson "
          f"[{wilson_ci(x_v, n_v, args.alpha)[0]:.4%}, "
          f"{wilson_ci(x_v, n_v, args.alpha)[1]:.4%}]")
    print(f"Abs lift: {abs_lift:+.4%}   Rel lift: {rel_lift:+.2%}")
    print(f"{int((1-args.alpha)*100)}% CI on abs lift: "
          f"[{ci_lo:+.4%}, {ci_hi:+.4%}]")
    print(f"z = {z:.3f}   p = {p_val:.4f}   (alpha {args.alpha})")
    _verdict(p_val, args.alpha, ci_lo, ci_hi)
    _common_warnings(args, n_c, n_v)
    return 0


def run_continuous(args) -> int:
    n_c, m_c, s_c = args.control
    n_v, m_v, s_v = args.variant
    n_c, n_v = int(n_c), int(n_v)
    se = math.sqrt(s_c ** 2 / n_c + s_v ** 2 / n_v)
    t = (m_v - m_c) / se if se > 0 else 0.0
    p_val = two_sided_p_from_z(t)  # normal approx; valid for large n

    abs_lift = m_v - m_c
    rel_lift = abs_lift / m_c if m_c != 0 else float("inf")
    zc = z_crit(args.alpha)
    ci_lo, ci_hi = abs_lift - zc * se, abs_lift + zc * se

    print("=== Continuous metric (Welch) ===")
    print(f"Control : n={n_c:,}  mean={m_c:.4f}  std={s_c:.4f}")
    print(f"Variant : n={n_v:,}  mean={m_v:.4f}  std={s_v:.4f}")
    print(f"Abs lift: {abs_lift:+.4f}   Rel lift: {rel_lift:+.2%}")
    print(f"{int((1-args.alpha)*100)}% CI on lift: [{ci_lo:+.4f}, {ci_hi:+.4f}]")
    print(f"t = {t:.3f}   p = {p_val:.4f}   (alpha {args.alpha}, normal approx)")
    if min(n_c, n_v) < 30:
        print("WARNING: n < 30 per arm. Normal approximation weak; use a true "
              "t-distribution tool.")
    _verdict(p_val, args.alpha, ci_lo, ci_hi)
    _common_warnings(args, n_c, n_v)
    return 0


def _verdict(p_val, alpha, ci_lo, ci_hi):
    sig = p_val < alpha
    ci_excludes_zero = (ci_lo > 0) or (ci_hi < 0)
    if sig and ci_excludes_zero:
        direction = "positive" if ci_lo > 0 else "NEGATIVE"
        print(f"VERDICT: statistically significant ({direction}). "
              "Confirm business-MDE & guardrails before SHIP.")
    elif sig and not ci_excludes_zero:
        print("VERDICT: borderline — p significant but CI touches 0. ITERATE.")
    else:
        print("VERDICT: not significant. KILL or ITERATE (effect unproven).")
    print("NOTE: statistical significance != business significance. Compare the "
          "lift to your break-even MDE.")


def _common_warnings(args, n_c, n_v):
    if args.srm:
        chi2, bad = srm_check(n_c, n_v)
        tag = "SRM DETECTED" if bad else "ok"
        print(f"SRM check (expects 50/50): chi2={chi2:.2f} -> {tag}")
        if bad:
            print("WARNING: sample ratio mismatch. Suspect assignment/logging bug. "
                  "Do NOT trust this result until fixed.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Post-experiment significance test")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--srm", action="store_true",
                    help="run a 50/50 sample-ratio-mismatch chi-square check")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("binary", help="two-proportion test")
    b.add_argument("--control", nargs=2, type=float, required=True,
                   metavar=("N", "CONVERTED"))
    b.add_argument("--variant", nargs=2, type=float, required=True,
                   metavar=("N", "CONVERTED"))

    c = sub.add_parser("continuous", help="Welch t-test")
    c.add_argument("--control", nargs=3, type=float, required=True,
                   metavar=("N", "MEAN", "STD"))
    c.add_argument("--variant", nargs=3, type=float, required=True,
                   metavar=("N", "MEAN", "STD"))

    args = ap.parse_args()
    if args.cmd == "binary":
        return run_binary(args)
    return run_continuous(args)


if __name__ == "__main__":
    raise SystemExit(main())
