---
name: persona-simulation
description: >-
  Use when the user wants to stress-test a product's screens against a diverse
  user cohort — triggers "페르소나 시뮬", "페르소나 검증", "페르소나 시뮬레이션",
  "다양성 검증", "유아부터 90대", "누가 막히나", "persona simulation",
  "diversity audit", "accessibility cohort", "who gets stuck". Builds a 4-axis
  persona matrix (age infant/guardian→90s, job, income very-poor→wealthy,
  culture KR/US/JP/SEA/EU/MENA/LATAM), walks EACH persona through the actual
  first-run + core loop by reading the REAL screen code, and flags
  blocker/dropout/distrust/confusion grounded in file:line. PRODUCES a prioritized
  code-grounded findings report (HTML, sorted by frequency × severity) plus a queue
  block and per-AI routing. Can fan out via agent-delegate for large cohorts —
  the reusable form of hub PROTOCOL §26.2 / §27.9. Different from design-review
  (one eye) and grill-me (plan); NOT for picking a direction (simon-design-first).
version: 0.1.0
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch
compatibility: [claude-code]
author: simon-stack
---

# persona-simulation

다양성 페르소나 군집으로 제품 화면을 강제 완주시켜, **실제 화면 코드 근거(file:line)**로
막힘·이탈·불신·오해 지점을 찾아 빈도×심각도로 집계하는 skill. 허브 PROTOCOL §26.2(4축 매트릭스)
+ §27.9(주기적 군집 시뮬, deep-research 모방 fan-out)의 재사용 가능한 형태.

## When to use / boundaries

발동:
- "페르소나 시뮬", "다양성 검증", "유아부터 90대 다 돌려봐", "이 온보딩 누가 막히나"
- 대형 UX 사이클 종료 직후, 중대 화면 변경 후 (분기 1회 정기 점검)
- `app-dev-orchestrator` 단계 15.5 diversity-gate(D-16) / `dev-orchestrator` 시나리오 단계에서 호출

쓰지 말 것 (경계):
- 디자인 **방향 선택** → `simon-design-first` (인테이크 인터뷰)
- **한 명의 디자이너 시선** 시각 QA → `design-review`
- **계획/스펙 구멍** 캐묻기 → `grill-me`
- **권한/IDOR** 점검 → `authz-designer`
- 이건 "여러 가상 인간을 **돌아가는 코드** 위로 걷게 한다"가 핵심. 코드를 안 읽으면 이 skill이 아니다.

## 선행 체크 (코드 근거 없으면 중단)

페르소나가 걸을 **실제 화면 코드**가 있어야 한다. 추측 금지.

```bash
# 1) 화면 코드 디렉터리 확인 (Expo/RN 예: src/app, web 예: app/ 또는 src/pages)
ROOT="${1:-.}"
ls "$ROOT/src/app"/*.tsx 2>/dev/null || ls "$ROOT/app"/*.tsx 2>/dev/null \
  || ls "$ROOT/src/pages" 2>/dev/null \
  || { echo "NO_SCREEN_CODE — 화면 코드 경로를 먼저 지정"; exit 0; }

# 2) 첫 실행 경로(엔트리) 식별: 라우트/온보딩/권한
grep -rln "onboarding\|first.?run\|permission\|consent\|initialRoute" "$ROOT/src/app" 2>/dev/null | head

# 3) i18n/locale 자원 유무 (문화 축 근거)
ls "$ROOT/src/i18n" "$ROOT/locales" "$ROOT/src/locales" 2>/dev/null
```

근거 디렉터리가 없으면 "코드 근거 없는 페르소나 시뮬은 의견글" 이므로 **중단하고 경로를 묻는다**.

## 워크플로 (6단계)

### 1. 시뮬 대상 정의 — first-run + core loop

전 기능을 다 걷지 않는다. **두 경로만 강제 완주**시킨다(나머지는 표본 부족 시 확장):

| 경로 | 의미 | 예 (2nd-B) |
|---|---|---|
| First-run | 설치~첫 가치 도달(TTFV) | `splash → onboarding.tsx → permissions.tsx → (auth) → index.tsx` |
| Core loop | 매일 반복하는 핵심 행동 | `index → capture.tsx → inbox.tsx → record-detail` |

먼저 엔트리 라우트와 핵심 루프 화면 파일을 **실제로 Read**해 화면 인벤토리를 만든다.

```bash
# 화면 인벤토리 + 크기(큰 화면 = 위험 후보) — read-only
wc -l src/app/*.tsx 2>/dev/null | sort -rn | head -20
```

### 2. 4축 페르소나 매트릭스 구축 (§26.2)

4축을 **교차**해 페르소나를 만든다. 정기 표본 = **연령밴드당 3~5명, 총 30~50명**(§27.9).
더 큰 표본(밴드당 20+)은 **§27 비용가드** 거쳐 확대.

| 축 | 밴드 | 그 축이 잡아내는 결함 |
|---|---|---|
| 연령 | 영유아(보호자)·10대·20·30·40·50·60·70·80·90대 (10밴드) | 글자크기·대비·터치타깃(≥44/48px)·읽기수준·tech-literacy 하한 |
| 직업/상황 | 학생·직장인·자영업·교대근무·은퇴·돌봄제공자·장애·저시력 | 시간압박·맥락전환·접근성 |
| 소득 | 극빈·저·중·고·부유 | 가격민감도·결제수단·무료티어 기대·구독피로 |
| 문화/국가 | KR·US·JP·EU·SEA·MENA·LATAM | 프라이버시/자기성찰 태도·금기어휘·로케일·통화·OAuth(Kakao/Naver vs Google/Apple)·종교/가족관 |

각 페르소나 = `{나이, 직업, 소득, 국가, 기기/네트워크, 1차 목표, tech-literacy, 접근성 needs}`.
극단(코너 케이스)을 일부러 넣는다: 90대 저시력 + 저소득 + 중동 프라이버시 보수 + 구형 안드로이드.

```text
P07 = 73세 · 은퇴 교사 · 저소득(연금) · KR · 구형 갤럭시/저속 LTE
     · 목표: 손주 사진 정리 · tech-literacy 낮음 · 노안(글자 키움 200%)
P22 = 19세 · 대학생 · 저소득 · US · iPhone SE · 목표: 빠른 캡처
     · tech-literacy 높음 · 프라이버시 민감(데이터 수집 거부감)
P31 = 34세 · 자영업 · 중간소득 · MENA · 목표: 비공개 일기
     · 클리니컬/진단 어휘에 강한 거부감 · 가족과 기기 공유
```

### 3. 각 페르소나로 화면 코드 워크스루 (핵심)

각 페르소나마다 first-run → core loop 화면 파일을 **순서대로 Read**하고,
그 사람의 눈으로 각 화면에서 막힘·이탈·불신·오해가 생기는지 점검한다.
모든 발견은 **반드시 `file:line` + 코드 인용**으로 못 박는다(없으면 의견글).

점검 렌즈(§20 UX 4원칙과 교차):

| 렌즈 | 무엇을 코드에서 찾나 |
|---|---|
| 막힘(blocker) | 진행 불가 — 필수 입력에 한국 전용 본인인증, OAuth provider 없음, 권한 거부 시 dead-end |
| 이탈(dropout) | TTFV 지연 — first-run 화면 수 과다, 무거운 모달 체인, 가치 도달 전 가입 강요 |
| 불신(distrust) | 데이터 수집 카피 모호, 권한 사유 누락, 결제 직전 가격 미표시 |
| 오해(confusion) | 화면당 primary action 2개+, 정보과부하, 추측 필요한 라벨, 미번역 문자열 |
| 접근성 | 폰트 스케일 무시(고정 px), 대비 부족, 터치타깃 <44px, 스크린리더 라벨 누락 |
| 문화/금기 | 임상 어휘(diagnosis/진단/치료) — MENA/보수권 거부, 통화·날짜·이름 순서 가정 |

코드 근거를 잡는 read-only 그렙(2nd-B 예시 패턴):

```bash
# 고정 폰트 px (노안 페르소나가 글자 못 키움)
grep -rn "fontSize:\s*1[0-3]\b" src/app src/components 2>/dev/null | head

# 터치타깃 < 44px 의심 (작은 hitSlop/height)
grep -rn "height:\s*[0-3][0-9]\b\|hitSlop" src/app src/components 2>/dev/null | head

# 권한 요청에 '왜' 사유가 붙어있나 (불신 축)
grep -rn "requestPermission\|usageDescription\|NSCamera\|RECORD_AUDIO" src ios android 2>/dev/null | head

# 한국 전용 가정 (글로벌 페르소나 막힘) — 본인인증/카카오만
grep -rni "kakao\|naver\|본인인증\|PASS\|CI/DI" src/app src/lib 2>/dev/null | head

# 임상/금기 어휘 (문화 축) — 2nd-B는 lexicon.ts로 차단됨
grep -rni "diagnos\|진단\|치료\|therapy\|disorder" src/app src/components 2>/dev/null | head
```

발견 기록 포맷(한 줄 = 한 발견):

```text
[P07·P12·P19] BLOCKER  onboarding.tsx:84  "다음" 버튼 height:36 < 44px →
  노안·떨림 손가락이 못 누름. 근거: <Pressable style={{height:36}}>
[P22·P31]     DISTRUST permissions.tsx:41 카메라 권한에 사유 텍스트 없음 →
  프라이버시 민감 페르소나 즉시 거부. 근거: requestCameraPermission() 직호출
[ALL-KR-only] BLOCKER  (auth)/sign-in.tsx:55 OAuth가 kakao만 →
  US/EU/일본 페르소나 가입 불가. 근거: providers=['kakao']
```

### 4. 빈도 × 심각도 집계 (§27.9)

발견을 묶어 **얼마나 많은 페르소나에게(빈도)** × **얼마나 치명적인가(심각도)**로 우선순위화.

| 심각도 | 기준 | 빈도 가중 |
|---|---|---|
| P0 Blocker | 일부 코호트가 진행 자체 불가 | 영향 페르소나 수 / 전체 |
| P1 Dropout | TTFV 지연·핵심 루프 마찰로 이탈 | 〃 |
| P2 Distrust | 신뢰 훼손(권한·데이터·가격) | 〃 |
| P3 Confusion | 오해·정보과부하(완주는 함) | 〃 |

우선순위 = `심각도 등급 × (영향 페르소나 수 / 전체 페르소나 수)`. 예: P0 × (12/40)이
P1 × (30/40)보다 위. 동률이면 **수정 비용 낮은 것 먼저**.

### 5. fan-out 확장 (대형 코호트 — 선택)

밴드당 20명+ 또는 다축 동시 점검이면 `agent-delegate`로 축별 fan-out (§27.9 deep-research 모방):
- 축별 sub-agent: 연령 / 소득 / 문화 / 접근성 각 1개
- **context envelope = 화면 파일 경로만**(내용은 sub-agent가 Read) — 토큰 절약
- output contract = 위 "발견 기록 포맷" 그대로 텍스트 반환
- **검증은 schema 없는 텍스트 회수**(§28.6 — `agent(…,{schema})`는 자주 미호출 실패)
- 비용가드: 표본 폭증 = 토큰 폭증 → 착수 전 Simon 확인(§27 비용 게이트)

```text
Fan-out: [age-agent] [income-agent] [culture-agent] [a11y-agent]
  각자 first-run+core-loop 화면 경로 받아 → 발견 리스트(텍스트) 반환
Supervisor(Claude): 중복 머지 + 빈도 재집계 + 적대적 검증(거짓 양성 제거)
```

### 6. 리포트 산출 (§27.5 — HTML 기본)

읽고 판단할 산출물이므로 **자체 완결 HTML**로 (다크·색 3개 이내·AI slop 금지, §29.2):
- 페르소나 매트릭스 표 (4축 × 표본)
- 우선순위 발견 리스트: `심각도 · 빈도 · file:line · 코드 인용 · 영향 페르소나 · 제안`
- 라우팅 제안(§26.3): 모션/네이티브 접근성=AG, 정보위계/카피/시각=Codex, 로직/라우팅=Claude, 가격/법무=Simon
- 큐 적재용 머신리더블 블록(§25 큐 E.UX 버킷)

HTML 빌드 명령:

```bash
# 리포트 작성 후 브라우저로 열어 확인 (Windows)
start "" "persona-sim-$(date +%Y%m%d-%H%M).html" 2>/dev/null \
  || open "persona-sim-$(date +%Y%m%d-%H%M).html" 2>/dev/null
```

## Decision table — 표본 크기 & 깊이

| 상황 | 표본 | 깊이 |
|---|---|---|
| 정기 분기 점검 | 밴드당 3, 총 30 | first-run + core loop |
| 중대 화면 변경 후 | 변경 화면 닿는 밴드 5+ | 변경 화면 집중 |
| 출시 전 게이트 | 밴드당 5, 총 50 + 코너케이스 | 전 기능 강제 완주 |
| 대형 코호트(밴드당 20+) | §27 비용가드 후 fan-out | 축별 sub-agent 병렬 |

## Anti-patterns (하지 말 것)

- ❌ **코드 안 읽고 페르소나 평** — file:line 근거 없는 발견은 의견글. 즉시 폐기.
- ❌ **"30명 페르소나" 나열만 하고 화면 워크스루 생략** — 매트릭스는 수단, 워크스루가 본체.
- ❌ **빈도 무시, 한 명 의견을 P0로** — 1/40 confusion < 30/40 confusion. 반드시 빈도 가중.
- ❌ **임상/진단 어휘로 페르소나 묘사** (2nd-B lexicon.ts 금지어). self-understanding/성장 어휘 사용.
- ❌ **KR만 점검** — §20.4: KR + 글로벌 양쪽. OAuth·통화·금기어휘는 문화별로 다르다.
- ❌ **iOS를 "실측·스크린샷으로 검증됨"으로 보고** — 이 머신 Windows. iOS는 HIG/Dynamic Type **정적 가정 점검만**(§27.7). 허위 증거 금지.
- ❌ **schema 붙은 fan-out 검증** — "0-0 abstain"은 반박 아니라 버그(§28.6). 텍스트로 회수.
- ❌ **bounce/elastic·4색+ 같은 slop을 "개선안"으로 제안** — §29.2 금지목록 준수.

## Verification (끝나기 전 자가 점검)

- [ ] 모든 발견에 **`file:line` + 코드 인용**이 있는가? (없으면 의견글 → 삭제)
- [ ] first-run **그리고** core loop 둘 다 걸었는가?
- [ ] 4축이 **교차**됐는가? (연령만, 국가만 = 실패) 코너케이스 1+개 포함?
- [ ] 빈도(영향 페르소나 수) × 심각도로 **정렬**됐는가?
- [ ] KR + 글로벌 양쪽 점검? OAuth/통화/금기어휘 포함?
- [ ] 리포트가 HTML(§27.5)이고 색 3개 이내·slop 없는가?
- [ ] 큐 적재용 블록(§25 E.UX) + 라우팅 제안(§26.3) 포함?

```bash
# 발견 리포트에 근거 없는 항목이 없는지 마지막 그렙 (file:line 패턴 강제)
grep -nE "BLOCKER|DROPOUT|DISTRUST|CONFUSION" persona-sim-*.html 2>/dev/null \
  | grep -vE "\.tsx:[0-9]+|\.ts:[0-9]+|\.jsx?:[0-9]+" \
  && echo "⚠ 근거(file:line) 없는 발견 존재 — 보강 필요" \
  || echo "OK — 모든 발견에 코드 근거 있음"
```
