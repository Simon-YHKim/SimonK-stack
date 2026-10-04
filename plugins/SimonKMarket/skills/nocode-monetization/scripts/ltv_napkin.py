#!/usr/bin/env python3
"""napkin LTV / 매출 추정기 — nocode-monetization skill 보조 도구.

코드 없이 수익화하는 사용자에게 "이 가격이면 먹고 살 만한가"를 가늠해 주는
봉투 뒷면(napkin) 계산기. 정밀 분석이 아니라 의사결정용 러프 추정이다.

사용:
  # 단건 판매: 월 방문 5000, 전환율 2%, 단가 29000원, 플랫폼 수수료 30%
  python ltv_napkin.py single --visits 5000 --conv 0.02 --price 29000 --fee 0.30

  # 구독: 월 구독료 9900원, 월 이탈률 10%, 플랫폼 수수료 10%, 현재 구독자 200명
  python ltv_napkin.py sub --price 9900 --churn 0.10 --fee 0.10 --subs 200
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


def single(args: argparse.Namespace) -> None:
    buyers = args.visits * args.conv
    gross = buyers * args.price
    net = gross * (1 - args.fee)
    print("== 단건 판매 추정 (월) ==")
    print(f"방문 {args.visits:,.0f} x 전환율 {args.conv:.1%} = 구매 {buyers:,.1f}명")
    print(f"총매출(GMV) : {won(gross)}")
    print(f"플랫폼 수수료 {args.fee:.0%} 차감")
    print(f"실수령(세전): {won(net)}")
    print("주의: 여기서 종합소득세/부가세는 별도. 실제 수령은 더 낮다.")


def sub(args: argparse.Namespace) -> None:
    if args.churn <= 0:
        raise SystemExit("churn 은 0보다 커야 한다 (0.10 = 월 10% 이탈).")
    ltv_gross = args.price / args.churn
    ltv_net = ltv_gross * (1 - args.fee)
    avg_months = 1 / args.churn
    print("== 구독 LTV 추정 ==")
    print(f"월 구독료 {won(args.price)} / 월 이탈률 {args.churn:.0%}")
    print(f"평균 구독 유지: {avg_months:.1f}개월")
    print(f"고객 1명 LTV(세전 총액): {won(ltv_gross)}")
    print(f"수수료 {args.fee:.0%} 차감 LTV : {won(ltv_net)}")
    if args.subs:
        mrr_gross = args.price * args.subs
        mrr_net = mrr_gross * (1 - args.fee)
        print(f"현재 구독자 {args.subs:,.0f}명 기준 월매출(세전): {won(mrr_gross)}")
        print(f"  수수료 차감 후: {won(mrr_net)}")
    print("판단: 손님 1명 데려오는 비용(CAC) < LTV 여야 지속 가능.")


def main() -> None:
    p = argparse.ArgumentParser(description="napkin LTV / 매출 추정기")
    sp = p.add_subparsers(dest="mode", required=True)

    s1 = sp.add_parser("single", help="단건 판매 월 매출 추정")
    s1.add_argument("--visits", type=float, required=True, help="월 방문/도달 수")
    s1.add_argument("--conv", type=float, required=True, help="구매 전환율 (0.02 = 2%)")
    s1.add_argument("--price", type=float, required=True, help="단가(원)")
    s1.add_argument("--fee", type=float, default=0.0, help="플랫폼 수수료 (0.30 = 30%)")
    s1.set_defaults(func=single)

    s2 = sp.add_parser("sub", help="구독 LTV 추정")
    s2.add_argument("--price", type=float, required=True, help="월 구독료(원)")
    s2.add_argument("--churn", type=float, required=True, help="월 이탈률 (0.10 = 10%)")
    s2.add_argument("--fee", type=float, default=0.0, help="플랫폼 수수료 (0.10 = 10%)")
    s2.add_argument("--subs", type=float, default=0.0, help="현재 구독자 수 (선택)")
    s2.set_defaults(func=sub)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
