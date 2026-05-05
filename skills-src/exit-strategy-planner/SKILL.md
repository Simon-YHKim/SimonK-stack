---
name: exit-strategy-planner
description: "Use when the user wants to plan long-term business exit strategy—triggers "exit 전략", "상장 준비", "M&A 전략", "IPO 로드맵", "투자 유치", "exit plan", "IPO roadmap", "acquisition strategy", "Series A preparation". Produces exit strategy selection (IPO/M&A/SPAC/Secondary), stage-by-stage roadmap (Seed→Series A→B→C→Exit), key metrics per stage, and case studies (Coupang NASDAQ, Korean startup exits)."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebFetch
version: 1.0.0
author: simon-stack
---

# exit-strategy-planner

최종 Exit (IPO/M&A) 전략 수립 + 단계별 로드맵.

## 발동 조건

- "exit 전략 세워줘", "상장 준비", "M&A 전략"
- "투자 유치 준비", "시리즈 A", "IPO 로드맵"
- 서비스가 성장 궤도에 올랐을 때 장기 전략 수립

## Exit 유형

| 유형 | 타임라인 | 규모 | 적합한 경우 |
|---|---|---|---|
| **IPO** | 7-10년 | $1B+ | 독립 성장, 시장 선도 |
| **M&A** | 3-7년 | $10M-$1B | 전략적 가치, 기술 인수 |
| **SPAC** | 5-8년 | $500M+ | 빠른 상장, 시장 타이밍 |
| **Secondary** | 5-7년 | 다양 | 창업자 부분 현금화 |
| **Acqui-hire** | 1-3년 | 소규모 | 팀 가치 > 제품 가치 |

## 단계별 로드맵

### Stage 1: Pre-Seed / Seed (0-1년)
- **목표**: PMF 달성
- **핵심 지표**: Retention D30 > 20%, 유기적 성장
- **자금**: 자체/엔젤 $100K-$500K
- **필요 skill**: pmf-analyzer, aha-moment-optimizer

### Stage 2: Series A (1-3년)
- **목표**: 성장 엔진 증명
- **핵심 지표**: MoM 15%+ 성장, LTV/CAC > 3, $1M ARR
- **자금**: VC $2M-$15M
- **필요 skill**: aarrr-growth-planner, monetization-planner

### Stage 3: Series B (3-5년)
- **목표**: 시장 확대, 해외 진출
- **핵심 지표**: $10M ARR, 시장 1-2위
- **자금**: $20M-$100M
- **필요 skill**: global-payment-planner, sprint-optimizer

### Stage 4: Series C+ / Pre-IPO (5-8년)
- **목표**: 수익성 + 규모 동시 달성
- **핵심 지표**: $100M ARR, 양의 FCF
- **자금**: $100M+
- **준비**: CFO 영입, 감사, SOX 준비

### Stage 5: Exit (7-10년)
- **IPO**: S-1 Filing, Roadshow, 상장
- **M&A**: LOI → Due Diligence → Close

## 사례 연구

### 쿠팡 (NASDAQ, 2021)
- 2010 설립 → 2021 IPO ($4.6B raised pre-IPO)
- 핵심: 시장 장악 (한국 이커머스 1위) → 미국 상장
- 전략: 이익보다 성장 우선 → GMV 극대화 → 상장 시 $84B 밸류

### 토스 (Pre-IPO)
- 2013 설립 → Series G ($400M)
- 핵심: 금융 슈퍼앱, 다중 수익원
- 전략: 한국 시장 독점적 포지션 → IPO 추진 중

## 핵심 지표 (투자자가 보는 것)

| 단계 | 핵심 지표 |
|---|---|
| Seed | 팀, PMF 신호, TAM |
| Series A | 성장률, 유닛 이코노미, Retention |
| Series B | ARR, Market share, Expansion revenue |
| Series C+ | 수익성, NRR > 120%, 경쟁 해자 |
| IPO | Rule of 40 (성장률 + 영업이익률 > 40%) |

## 산출물

`EXIT-STRATEGY.md`:
- 선택된 Exit 유형 + 근거
- 단계별 마일스톤 타임라인
- 각 단계 필요 지표 + 현재 상태 갭
- 투자 유치 준비 체크리스트
- 참고 사례 (동종 업계)

## Related Skills

- `pmf-analyzer` — 현재 PMF 단계 진단
- `monetization-planner` — 수익 모델이 Exit에 적합한지
- `sprint-optimizer` — 단계별 스프린트 실행
- `aarrr-growth-planner` — 성장 전략
