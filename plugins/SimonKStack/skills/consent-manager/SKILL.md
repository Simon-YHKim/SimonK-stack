---
name: consent-manager
description: "Use when the user asks to build a consent management platform (CMP), cookie banner, or tracking-consent gate—triggers \"동의 관리\", \"쿠키 배너\", \"consent 게이트\", \"GDPR 동의\", \"추적 동의\", \"consent banner\", \"cookie consent\", \"GPC respect\", and /consent-manager. Produces granular consent categories (필수/분석/광고/기능), a consent-gate API that gates each tracker (GA4/Clarity/PostHog/AdMob) by category, GPC/DNT honoring, withdraw/re-consent flows, a versioned append-only consent ledger (timestamp + policy version + categories), region awareness (GDPR/PIPA/CCPA), and a minor-consent handoff to auth-builder (COPPA/PIPA §22-2)."
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# consent-manager

동의관리 플랫폼(CMP) + 버전드 consent 원장을 실제 코드로 구현하는 skill. 임의의 앱(웹/RN)에 적용하는 범용 스킬이다.

## 발동 조건

- "동의 관리", "쿠키 배너", "consent 게이트", "추적 동의 받아줘"
- "GDPR 동의", "GPC/DNT 존중", "동의 철회 플로우"
- analytics-integrator / ad-monetization 에서 트래커 게이팅이 필요할 때 호출

## 강제 베스트프랙티스 (절대 약화 금지)

| 원칙 | 규칙 |
|---|---|
| **동의 게이트** | 비필수 트래커는 동의 전 **로드 금지**. `canTrack(category)` 통과 후에만 SDK init. |
| **fail-open 금지** | 동의 상태 불명/조회 실패 시 비필수는 기본 **거부**(fail-closed). 필수만 항상 허용. |
| **감사 로그** | 모든 동의 부여/변경/철회를 append-only 원장에 기록(타임스탬프 + 정책버전 + 카테고리 + 출처). |
| **플랫폼 분기** | 저장소가 다르다 — 웹=쿠키/localStorage + `Sec-GPC` 헤더, RN=AsyncStorage + ATT/`globalPrivacyControl` 없음 → 명시 토글. |

> fail-open 의 유일한 예외는 `necessary`(필수) 카테고리뿐. 나머지는 모르면 끈다.

## 동의 카테고리 (granular)

| 카테고리 | 토글 | 끌 수 있나 | 예시 트래커 |
|---|---|---|---|
| `necessary` | 항상 ON | 불가(고지만) | 세션, CSRF, 로드밸런서 |
| `functional` | opt-in | 가능 | 언어 설정, 다크모드 저장, 채팅 위젯 |
| `analytics` | opt-in | 가능 | GA4, PostHog, Microsoft Clarity |
| `advertising` | opt-in | 가능 | AdMob, AdSense, Meta Pixel |

- 다크 패턴 금지: "모두 거부"는 "모두 동의"와 **동등한 무게**(같은 크기/대비)로 노출.
- 각 카테고리는 독립 토글. "모두 동의"는 편의일 뿐 단일 강제 게이트가 아니다.

## 지역 인지 (region-aware default)

| 지역 | 법 | 기본 상태 | 핵심 |
|---|---|---|---|
| EU/EEA/UK | GDPR | **opt-in**(전부 OFF) | 사전 동의 없이 비필수 트래커 금지. 동의=명시적 행동. |
| 한국 | PIPA + 정보통신망법 | **opt-in** | 항목별 분리 동의. 만 14세 미만 보호자 동의(§22-2). |
| 미국(CA 등) | CCPA/CPRA | **opt-out** 허용 | "Do Not Sell/Share" + GPC 신호를 opt-out 으로 인정. |
| 기타 | — | 보수적으로 opt-in 권장 | 지역 판별 실패 시 EU 규칙 적용(가장 엄격). |

판별: 서버=`Accept-Language`/IP geo/CDN 헤더, 클라=타임존+로케일. 불명 → 가장 엄격(GDPR opt-in).

## GPC / DNT 존중

- 웹: 요청 헤더 `Sec-GPC: 1` 또는 `navigator.globalPrivacyControl === true` → `advertising`(및 CCPA상 "판매") 자동 opt-out 로 시드.
- DNT(`navigator.doNotTrack === '1'`)는 신호로만 참고(법적 강제 아님) — `analytics` 기본 OFF 권장.
- 신호로 시드된 상태도 원장에 `source: 'gpc'|'dnt'` 로 기록. 사용자가 이후 명시 변경하면 명시값이 우선.

## Workflow

### 1. 진단 (AskUserQuestion)
- 플랫폼? (웹 / RN / 둘 다)
- 대상 지역? (EU 포함 여부 → 기본 opt-in 강제)
- 연동할 트래커? (GA4 / Clarity / PostHog / AdMob …) 각각 카테고리 매핑
- 연령 게이트 있나? (있으면 미성년 동의 경로 → auth-builder 핸드오프)

### 2. 상태 스키마 + 게이트 함수 설치
- `templates/consent-state.json` — 동의 상태/카테고리 단일 소스
- `templates/consent-gate.ts` — `canTrack()` / `loadTracker()` (웹·RN 분기, fail-closed)

### 3. 트래커 게이팅
각 SDK init 를 게이트 뒤로 이동. 예: `if (canTrack('analytics')) initGA4()`. 동의 철회 시 쿠키 제거 + SDK teardown(가능한 범위).

### 4. 원장(ledger) 연결
- `templates/consent-ledger.sql` — append-only. UPDATE/DELETE 금지(트리거로 차단). 변경은 새 row.
- 매 동의/변경/철회마다 INSERT. 정책버전 변경 시 재동의 트리거.

### 5. 철회·재동의
- 설정 화면 상시 진입점(O-7: 뒤로가기는 한 곳). 철회 즉시 게이트 false + SDK teardown + 원장 INSERT.
- `policy_version` 이 사용자 최신 동의보다 높으면 재동의 배너 재노출.

### 6. 미성년 연동 (COPPA / PIPA §22-2)
- 연령 게이트에서 만 14세 미만(KO) / 13세 미만(US COPPA) 판별 시 **본인 동의로 비필수 트래커 활성화 금지**.
- 보호자 검증 동의 경로는 **auth-builder 로 핸드오프**(verifiable parental consent). 원장에는 `actor: 'guardian'` + 검증수단 기록.
- 미성년 확정 시 `advertising`/맞춤형 `analytics` 는 기본 영구 OFF.

## 검증 체크리스트

- [ ] 동의 전 비필수 SDK 네트워크 요청 0건 (devtools network)
- [ ] 상태 조회 실패 시 비필수 = 거부 (fail-closed) 동작
- [ ] "모두 거부" 버튼이 "모두 동의"와 동일 무게로 노출 (다크패턴 아님)
- [ ] `Sec-GPC: 1` 요청 시 advertising 자동 opt-out + 원장 source=gpc
- [ ] 철회 시 쿠키 삭제 + SDK teardown + 원장 INSERT
- [ ] 정책버전 상향 시 재동의 배너 재노출
- [ ] 원장 UPDATE/DELETE 차단 (트리거 동작 확인)
- [ ] 미성년 판별 시 보호자 경로로 핸드오프 + 광고 OFF
- [ ] 웹/RN 저장소 분기 정상 (쿠키 vs AsyncStorage)

## Related Skills

- `analytics-ad-wiring` / `analytics-integrator` — 게이팅 대상 트래커 init 를 게이트 뒤로 이동
- `auth-builder` — 미성년 보호자 검증 동의 경로 핸드오프, 연령 게이트
- `data-flow-mapper` — 어떤 데이터가 어느 카테고리/트래커로 흐르는지 매핑
- `ad-monetization` — AdMob/AdSense 를 `advertising` 카테고리에 게이팅
