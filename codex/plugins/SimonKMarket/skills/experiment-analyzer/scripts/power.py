#!/usr/bin/env python3
"""Pre-experiment sample-size / power calculator (binary primary metric).

Stdlib only — no scipy/numpy. Uses the normal approximation for a two-proportion
test, which is standard for A/B sample sizing at typical web conversion rates.

Example:
    python power.py --baseline 0.10 --mde 0.10 --alpha 0.05 \
        --power 0.80 --daily-traffic 2000 --variants 2

  --baseline       Control conversion rate (0-1), e.g. 0.10 = 10%.
  --mde            Minimum detectable effect as RELATIVE lift, e.g. 0.10 = +10%.
                   (Use --absolute-mde to pass an absolute pp difference instead.)
  --alpha          Significance level (two-sided). Default 0.05.
  --power          Desired power (1 - beta). Default 0.80.
  --daily-traffic  Total daily users entering the experiment (split across variants).
  --variants       Number of variants incl. control. Default 2.
"""
import argparse
import math
import sys


def norm_ppf(p: float) -> float:
    """Inverse standard normal CDF (Acklam's rational approximation)."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0,1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def sample_size_per_arm(p1: float, p2: float, alpha: float, power: float) -> int:
    """Per-arm n for a two-sided two-proportion test (pooled-variance form)."""
    z_alpha = norm_ppf(1 - alpha / 2)
    z_beta = norm_ppf(power)
    p_bar = (p1 + p2) / 2
    numer = (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
             + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denom = (p2 - p1) ** 2
    return math.ceil(numer / denom)


def main() -> int:
    ap = argparse.ArgumentParser(description="A/B sample-size & power calculator")
    ap.add_argument("--baseline", type=float, required=True)
    ap.add_argument("--mde", type=float, required=True,
                    help="relative lift (e.g. 0.10 = +10%)")
    ap.add_argument("--absolute-mde", action="store_true",
                    help="treat --mde as an absolute pp difference")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--power", type=float, default=0.80)
    ap.add_argument("--daily-traffic", type=float, default=None)
    ap.add_argument("--variants", type=int, default=2)
    args = ap.parse_args()

    p1 = args.baseline
    if not 0 < p1 < 1:
        print("ERROR: --baseline must be between 0 and 1", file=sys.stderr)
        return 1
    p2 = p1 + args.mde if args.absolute_mde else p1 * (1 + args.mde)
    if not 0 < p2 < 1:
        print("ERROR: target rate out of (0,1); lower the MDE", file=sys.stderr)
        return 1

    n_arm = sample_size_per_arm(p1, p2, args.alpha, args.power)
    n_total = n_arm * args.variants

    print("=== Pre-experiment design ===")
    print(f"Baseline conversion : {p1:.4%}")
    print(f"Target conversion   : {p2:.4%}  (MDE {'abs' if args.absolute_mde else 'rel'} "
          f"{args.mde:+.2%})")
    print(f"alpha / power       : {args.alpha} / {args.power}")
    print(f"Per-arm sample (n)  : {n_arm:,}")
    print(f"Variants            : {args.variants}")
    print(f"Total sample        : {n_total:,}")

    if args.daily_traffic:
        per_arm_daily = args.daily_traffic / args.variants
        days = math.ceil(n_arm / per_arm_daily) if per_arm_daily > 0 else float("inf")
        print(f"Daily traffic       : {args.daily_traffic:,.0f} "
              f"({per_arm_daily:,.0f}/arm)")
        print(f"Estimated runtime   : {days} day(s)")
        if days > 28:
            print("WARNING: runtime > 28d. Raise the MDE, add traffic, or "
                  "accept that small effects won't be detectable here.")
    if n_arm < 100:
        print("WARNING: per-arm n < 100. Proportion tests are unstable at this "
              "size; treat results with caution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
