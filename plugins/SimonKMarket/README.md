# SimonKMarket

![version](https://img.shields.io/badge/version-0.2.0-5b8cff) ![license](https://img.shields.io/badge/license-MIT-green) [![validate](https://github.com/Simon-YHKim/SimonKMarket/actions/workflows/validate-plugin.yml/badge.svg)](https://github.com/Simon-YHKim/SimonKMarket/actions/workflows/validate-plugin.yml)

> 마케팅·시장조사·여론 분석 오케스트레이션 플러그인

오케스트레이션 진입점: `/skmarket`

### 사용 예시

```
/skmarket 이거 팔릴까 경쟁사부터 봐줘
/skmarket 출시 후 사용자 늘리는 AARRR 퍼널 짜줘
/skmarket 메타·네이버 광고 붙이고 전환추적까지
```

인자 없이 `/skmarket` 만 입력하면 무엇을 할지부터 물어본다.

## 설치
```
/plugin marketplace add Simon-YHKim/SimonKMarket
/plugin install simonk-market@simonk-market
```

## 의존
SimonKCore 권장 동반 설치 (agent-delegate, model-router, instincts 등 공유 인프라). 없으면 일부 기능 제한.

## 구조
- `skills/` — 도메인 스킬
- `agents/` — 서브에이전트
- `commands/` — 슬래시 커맨드

## 수록 스킬 (32개)

진입점 `/skmarket` 가 의도를 진단해 아래 스킬로 라우팅합니다. 개별 직접 호출도 가능.

`aarrr-growth-planner` · `ad-monetization` · `aha-moment-optimizer` · `analytics-integrator` · `churn-recovery-planner` · `cohort-retention-analyzer` · `community-marketing` · `exit-strategy-planner` · `experiment-analyzer` · `export-channel` · `feedback-and-review-collector` · `global-payment-planner` · `growth-engine` · `idea-validation` · `lifecycle-campaign-designer` · `mobile-attribution-integrator` · `monetization-planner` · `nocode-monetization` · `onboarding-flow-builder` · `paid-ads-campaign` · `payment-integrator` · `paywall-designer` · `pink-tax-advisor` · `pmf-analyzer` · `referral-program-builder` · `revenue-scenario-tester` · `skmarket` · `store-launcher` · `subscription-manager-selector` · `tag-manager-integrator` · `unit-economics-modeler` · `viral-launch`

## 기여

스킬 추가·수정은 **평가셋(`evals/cases.json`) + CI 품질게이트**를 통과해야 한다.
자세한 절차·스키마는 [`CONTRIBUTING.md`](./CONTRIBUTING.md) 참고.

```bash
python -B -m unittest discover -s .github/skill-ci -p test_run_ci_encoding.py
python -B .github/skill-ci/run_ci.py   # 머지 전 로컬 게이트
```

품질 게이트는 자식 Python을 UTF-8로 실행하고 결과를 엄격하게 해석하므로
Windows 기본 CP949 콘솔에서도 같은 검증을 수행한다. 모델/API 호출은 없다.

누락 자산 복구 브랜치에서는 추가로 Node.js 24에서 아래 회귀 테스트를 실행한다.
추천 무결성 스크립트 테스트는 가짜 `psql`만 사용하며 실제 DB에 연결하지 않는다.

```bash
node .github/validate.mjs
node --test skills/mobile-attribution-integrator/tests/parse-install-referrer.test.mjs skills/referral-program-builder/tests/check-referral-integrity.test.mjs
```

`mobile-attribution-integrator`의 referrer 파서는 Google Play 문자열을 순수 함수로
정규화할 뿐 광고 귀속을 인증하지 않는다. `referral-program-builder`의 K-factor는
수신자별 초대 ID가 없으면 미정이며, 코호트 LTV는 별도 매출 원천 매핑 전에는
계산할 수 없다. 운영 DB 조회·스키마 적용은 이 저장소 테스트에 포함되지 않는다.

## 라이선스

MIT. 일부 인프라 스킬은 Simon 의 기존 SimonK 스택에서 가져왔고 gstack(garrytan, MIT) 출신이 섞일 수 있으며 출처는 각 SKILL.md·NOTICE 에 유지. © Simon Kim (Simon-YHKim).
