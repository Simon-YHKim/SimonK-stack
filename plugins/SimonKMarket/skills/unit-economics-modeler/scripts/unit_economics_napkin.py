#!/usr/bin/env python3
"""napkin 단위경제성 계산기 — unit-economics-modeler skill 보조 도구.

코호트 LTV(생존곡선 + 확장매출 + 마진 + 선택적 할인) → payback(누적 기여이익이
CAC를 넘는 첫 월) → LTV:CAC → 보수/기본/공격 3시나리오 → 가드레일 판정.

정밀 회계가 아니라 의사결정용 러프 추정이다. 모든 입력은 측정값 또는 명시된 가정이어야 한다.

사용:
  python unit_economics_napkin.py \
    --arpu 9900 --churn 0.08 --expansion 0.01 \
    --cac 18000 --var-cost-rate 0.20 --horizon 36 --discount 0.0

인자:
  --arpu          고객 1인 월평균 매출(원)                 [필수]
  --churn         월 이탈률 (0.08 = 8%)                    [필수]
  --cac           고객 획득 비용(원)                       [필수]
  --expansion     월 확장률 g (0.01 = 1%, 기본 0)
  --var-cost-rate 변동비율 (매출 대비, 0.20 = 20%, 기본 0)  → GM = 1 - rate
  --horizon       LTV 합산 지평선(개월, 기본 36; 무한 금지)
  --discount      월 할인율 r (0.0 = 할인 없음)
"""
import argparse
import sys

# Windows 콘솔(cp949)에서 ₩·한글 출력 깨짐 방지
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def won(x: float) -> str:
    return f"₩{x:,.0f}"


def cohort_ltv(arpu, churn, expansion, gm, horizon, discount):
    """월별 코호트 LTV. S(t)=잔존율, 확장 (1+g)^t, 마진 gm, 할인 (1+r)^t.

    누적 기여이익 곡선을 함께 반환 (payback 계산용).
    """
    ltv = 0.0
    survival = 1.0
    cumulative = []
    for t in range(horizon):
        # t월의 잔존 고객이 만드는 기여이익(마진 반영, 할인 반영)
        revenue = arpu * ((1 + expansion) ** t)
        contribution = survival * revenue * gm
        if discount > 0:
            contribution /= (1 + discount) ** t
        ltv += contribution
        cumulative.append(ltv)
        survival *= (1 - churn)  # 다음 달 잔존율
    return ltv, cumulative


def payback_month(cumulative, cac):
    """누적 기여이익이 CAC를 처음 넘는 월(1-indexed). 미회수면 None."""
    for i, c in enumerate(cumulative):
        if c >= cac:
            return i + 1
    return None


def verdict(ltv_cac, payback, horizon):
    """가드레일 판정: LTV:CAC >= 1 AND payback < 12개월."""
    ok_ratio = ltv_cac >= 1.0
    ok_payback = payback is not None and payback < 12
    if ltv_cac >= 3.0 and ok_payback:
        return "PASS (건강)"
    if ok_ratio and ok_payback:
        return "PASS (취약 — LTV:CAC<3)"
    if not ok_ratio:
        return "FAIL (적자 구조: LTV<CAC)"
    if payback is None:
        return f"FAIL (지평선 {horizon}개월 내 CAC 미회수)"
    return f"FAIL (payback {payback}개월 >= 12)"


def run_scenario(name, arpu, churn, expansion, gm, cac, horizon, discount):
    ltv, cum = cohort_ltv(arpu, churn, expansion, gm, horizon, discount)
    pb = payback_month(cum, cac)
    ratio = ltv / cac if cac > 0 else float("inf")
    pb_str = f"{pb}개월" if pb is not None else f">{horizon}개월"
    return {
        "name": name, "ltv": ltv, "cac": cac, "ratio": ratio,
        "payback": pb, "pb_str": pb_str,
        "verdict": verdict(ratio, pb, horizon),
    }


def main():
    p = argparse.ArgumentParser(
        description="napkin 단위경제성 계산기 (LTV/CAC/payback/민감도)")
    p.add_argument("--arpu", type=float, required=True, help="월 ARPU(원)")
    p.add_argument("--churn", type=float, required=True, help="월 이탈률 (0.08=8%)")
    p.add_argument("--cac", type=float, required=True, help="고객 획득 비용(원)")
    p.add_argument("--expansion", type=float, default=0.0, help="월 확장률 g (기본 0)")
    p.add_argument("--var-cost-rate", type=float, default=0.0,
                   dest="var_cost_rate", help="변동비율 (0.20=20%) → GM=1-rate")
    p.add_argument("--horizon", type=int, default=36, help="LTV 지평선(개월, 기본 36)")
    p.add_argument("--discount", type=float, default=0.0, help="월 할인율 r (기본 0)")
    a = p.parse_args()

    if a.churn <= 0:
        raise SystemExit("churn 은 0보다 커야 한다 (0.08 = 월 8% 이탈).")
    if a.churn <= a.expansion:
        raise SystemExit("churn > expansion 이어야 한다 (아니면 LTV가 발산).")
    if not (0 <= a.var_cost_rate < 1):
        raise SystemExit("var-cost-rate 는 0 이상 1 미만이어야 한다.")

    gm = 1 - a.var_cost_rate
    cm_unit = a.arpu * gm

    print("== 입력 (base) ==")
    print(f"ARPU {won(a.arpu)} / 월 churn {a.churn:.1%} / 확장 g {a.expansion:.1%}")
    print(f"변동비율 {a.var_cost_rate:.0%} → 기여 마진율 GM {gm:.0%}")
    print(f"CAC {won(a.cac)} / 지평선 {a.horizon}개월 / 할인율 {a.discount:.1%}")
    print(f"단위 기여이익(월): {won(cm_unit)}  (평균 유지 {1/a.churn:.1f}개월)")
    print()

    # 3시나리오: 보수 / 기본 / 공격
    scenarios = [
        run_scenario("보수", a.arpu, a.churn * 1.5, 0.0, max(gm - 0.10, 0.01),
                     a.cac * 1.3, a.horizon, a.discount),
        run_scenario("기본", a.arpu, a.churn, a.expansion, gm,
                     a.cac, a.horizon, a.discount),
        run_scenario("공격", a.arpu, a.churn * 0.7, a.expansion * 1.5, gm,
                     a.cac * 0.8, a.horizon, a.discount),
    ]

    print("== 시나리오 민감도 ==")
    print(f"{'시나리오':<6} {'LTV':>14} {'CAC':>12} {'LTV:CAC':>9} {'payback':>9}  판정")
    print("-" * 78)
    for s in scenarios:
        print(f"{s['name']:<6} {won(s['ltv']):>14} {won(s['cac']):>12} "
              f"{s['ratio']:>8.2f}x {s['pb_str']:>9}  {s['verdict']}")
    print()

    base = scenarios[1]
    cons = scenarios[0]
    print("== 가드레일 (보수 시나리오 기준) ==")
    print(f"  보수 LTV:CAC {cons['ratio']:.2f}x  /  payback {cons['pb_str']}")
    print(f"  -> {cons['verdict']}")
    if "FAIL" in cons["verdict"]:
        print("  레버: 가격↑(ARPU) · 이탈↓(churn) · CAC↓ · 변동비↓(GM↑) · 연간선결제")
    print()
    print("주의: napkin 추정. 세금/고정비 별도. 입력값 출처를 UNIT_ECONOMICS.md에 명시할 것.")
    print(f"      기본 시나리오 판정: {base['verdict']}")


if __name__ == "__main__":
    main()
