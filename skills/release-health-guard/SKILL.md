---
name: release-health-guard
description: "앱 릴리즈 헬스 게이트 — 트리거 \"크래시 모니터\", \"릴리즈 헬스\", \"crash-free\", \"롤아웃 차단\", \"ANR 점검\", \"top crash 비교\", \"staged rollout 멈춰\", \"crash monitor\", \"release health\", \"block rollout\", /release-health-guard. EAS 빌드별 Sentry/Crashlytics 의 crash-free% · ANR% · top crash 를 읽어 직전 릴리즈와 diff 하고, 임계 하회 시 staged rollout 중단/차단 + 알림을 만든다. crash-free% 가 모바일 리텐션을 직접 깎는 핵심 지표라는 전제로 OOM·ANR·네이티브 크래시 패턴 체크리스트를 동반한다. 신규 앱 출시는 store-launcher, 사후 모니터는 canary, 사고 대응은 incident-runbook 으로 라우팅."
allowed-tools: Read, Write, Bash, Grep, WebFetch, AskUserQuestion
version: 1.0.0
author: simon-stack
---

# release-health-guard

릴리즈가 안전한지 **데이터로 판정**하고, 기준 미달이면 staged rollout 을 멈추는 게이트 skill.
"빌드 올렸으니 됐다"가 아니라 "crash-free% 가 기준선 위인가"로 출시를 결정한다.

## 발동 조건

- "크래시 모니터링 붙여줘", "릴리즈 헬스 보고 싶어", "crash-free 몇 %야"
- "이번 빌드 롤아웃 멈춰야 하나", "staged rollout 차단 조건 만들어줘"
- "ANR 늘었어", "top crash 직전 버전이랑 비교해줘"
- canary(사후 모니터) / store-launcher(출시) / incident-runbook(사고)에서 호출

## 왜 crash-free% 인가 (전제)

- 크래시·ANR 을 겪은 세션은 다음 세션 복귀율이 떨어진다. 즉 **crash-free% 하락은 리텐션 하락의 선행 지표**다.
- store(Play Console / App Store Connect)도 같은 신호를 본다. Android Vitals 의 "나쁜 동작" 임계(ANR rate·crash rate)를 넘으면 노출·추천에서 불이익을 받는다.
- 따라서 릴리즈 게이트는 "기능 동작"이 아니라 **세션 단위 안정성 지표**로 잡아야 한다.
- 단, 절대 수치는 트래픽이 적을 때 출렁인다. 표본이 임계 미만이면 "판정 보류(데이터 부족)"로 두고 절대 자동 차단하지 않는다(아래 §4).

## 핵심 지표 정의

| 지표 | 정의 | 보는 곳 |
|---|---|---|
| **crash-free sessions %** | 크래시 없이 끝난 세션 / 전체 세션 | Sentry Release Health, Crashlytics |
| **crash-free users %** | 크래시 안 겪은 유저 / 전체 유저 | 동일 |
| **ANR rate** (Android) | ANR 발생 세션 / 전체 (App Not Responding) | Crashlytics, Play Android Vitals |
| **adoption** | 해당 릴리즈를 받은 세션/유저 수 | 표본 충분성 판정에 사용 |
| **top crash (issue)** | 영향 세션 수 상위 이슈 + 신규 여부 | Sentry Issues, Crashlytics |

sessions % 와 users % 는 같이 본다. users 는 높은데 sessions 가 낮으면 **소수 유저가 반복 크래시**(루프) 신호다.

## 기본 임계값 (프로젝트가 안 정했으면 이걸로 제안)

측정 기반 권고치이며 절대 기준은 아니다. 트래픽·앱 성격에 맞춰 사용자와 확정한다.

| 게이트 | 기준 | 동작 |
|---|---|---|
| crash-free sessions | < 99.0% | 롤아웃 **차단/중단** |
| crash-free sessions | < 99.5% (≥99.0%) | **경고** (확대 보류) |
| crash-free users | < 99.5% | 경고 |
| ANR rate (Android) | > 0.47% | 차단 (Play "나쁜 동작" 임계) |
| 직전 릴리즈 대비 회귀 | crash-free −0.3%p 이상 하락 | 차단 (신규 회귀로 간주) |
| 신규 top crash | 직전엔 없던 이슈가 상위 진입 | 경고+조사 |
| adoption(표본) | 임계 세션 수 미만 | **판정 보류** (차단 아님) |

회귀 게이트가 핵심이다. 99.2% 라도 직전이 99.7% 였으면 이번 빌드가 무언가 깨뜨린 것이다.

## Workflow

### 1. 소스·기준 파악 (Read + AskUserQuestion)

- 크래시 도구 확인: `sentry`, `@sentry/react-native`, `crashlytics`, `firebase` 를 코드·`package.json`·`app.json`/`app.config.*`·`eas.json` 에서 탐색.
- 현재/직전 릴리즈 식별: `app.json` 의 `version` + `ios.buildNumber` / `android.versionCode`. EAS 라면 build profile 도 확인.
- 임계값·표본 최소치를 사용자와 확정(없으면 위 기본값 제안). 둘 다 정해지기 전엔 차단 결정을 내리지 않는다.

### 2. 지표 수집 (env 인증, 하드코딩 금지)

토큰·DSN·org slug 는 **반드시 env** 로 읽는다. 코드/문서/리포트에 시크릿을 절대 쓰지 않는다.

- Sentry: `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, `SENTRY_PROJECT`. Release Health 세션 데이터는 Sentry API 의 sessions endpoint 에서 릴리즈별로 조회.
- Crashlytics: 콘솔/ BigQuery export. CI 자동화는 Crashlytics → BigQuery 연동 후 쿼리하는 경로가 안정적.
- WebFetch 는 도구 최신 API 경로·필드명 확인용으로만 쓰고, 시크릿은 절대 URL/헤더에 노출하지 않는다.
- 수집 결과는 `templates/release-health.template.md` 의 표에 채운다.

### 3. diff 와 판정 (scripts/eval-release-health.sh)

```bash
# 현재/직전 릴리즈 지표를 JSON 으로 만들어 게이트 평가
bash skills/release-health-guard/scripts/eval-release-health.sh \
  --current  '{"version":"1.4.0","crash_free_sessions":99.2,"crash_free_users":99.6,"anr_rate":0.30,"sessions":8200}' \
  --previous '{"version":"1.3.0","crash_free_sessions":99.7,"crash_free_users":99.8,"anr_rate":0.22,"sessions":15400}' \
  --min-sessions 1000
# exit 0 = PASS(확대 가능), 10 = WARN(보류), 20 = BLOCK(중단), 30 = HOLD(표본부족)
```

스크립트는 절대 임계 + 회귀 임계 + 표본 충분성을 한 번에 평가하고, 사람이 읽을 판정 요약을 stderr 로 낸다. 판정은 제안이며 최종 결정은 사용자가 한다.

### 4. 롤아웃 제어 + 알림

- **BLOCK**: staged rollout 확대 중단을 권고. Play 는 단계 출시(rollout %) 동결 또는 중단, App Store 는 단계 출시 일시중지. EAS Update 라면 신규 채널 publish 보류. 어떤 명령도 사용자 confirm 없이 자동 실행하지 않는다.
- **WARN**: 확대 보류 + 표본 더 쌓일 때까지 관망. top crash 조사 착수.
- **HOLD(표본 부족)**: 자동 차단 금지. 세션이 임계 이상 쌓일 때까지 재평가 예약.
- **PASS**: 다음 단계(%)로 확대 OK.
- 알림: Slack/메일 등 기존 채널로 판정 요약 전송(웹훅 URL 은 env). 이 skill 은 메시지 본문만 만들고, 전송은 프로젝트의 알림 경로에 위임한다.

### 5. 기록

- 판정·근거·다음 액션을 `release-health.template.md` 에 남겨 다음 릴리즈의 baseline 으로 쓴다.
- 사고로 번지면 `incident-runbook` 으로 인계.

## 모바일 크래시 패턴 점검 체크리스트

top crash 를 분류할 때 아래 패턴부터 의심한다. RN/Expo + 네이티브 맥락.

### OOM (Out Of Memory) — 가장 흔한 무증상 크래시
- [ ] 큰 이미지·SVG·리스트 메모리 누수: `FlatList` 대신 `FlashList`, 이미지 캐시·리사이즈 적용했나
- [ ] 화면 이탈 시 타이머/리스너/구독 해제 누락(useEffect cleanup)
- [ ] 대용량 AsyncStorage 직렬화(2MB 근처) — 큰 객체를 통째로 저장하고 있지 않나
- [ ] OOM 은 스택이 얕거나 잘려 보인다. "이유 없는" 종료가 특정 화면에 몰리면 OOM 의심

### ANR (Android) — UI 스레드 블로킹
- [ ] JS/네이티브 브리지에서 동기 무거운 연산을 메인 스레드에서 돌리고 있나
- [ ] 큰 JSON 파싱·암복호화·이미지 디코드를 메인에서 처리하나
- [ ] startup ANR: 앱 시작 5초 내 입력 처리 못 함 → cold start 작업을 지연/백그라운드화
- [ ] Play Android Vitals 의 ANR rate 가 임계 근처면 store 노출이 깎인다

### 네이티브 크래시 / SIGSEGV
- [ ] Hermes / JSC 엔진 차이, 네이티브 모듈 버전 불일치
- [ ] SDK 메이저 업글 직후 회귀(Expo SDK, RN, 결제/지도/카메라 모듈)
- [ ] iOS: 백그라운드 진입 시 만료 리소스 접근, 권한 거부 경로 미처리
- [ ] ProGuard/R8 난독화로 스택이 안 풀리면 mapping/dSYM 업로드 누락 점검

### 회귀 추적
- [ ] 신규 top crash 가 **이번 릴리즈에서 처음** 등장했나(직전엔 0)
- [ ] 특정 OS 버전·기기·로캘에 몰리나(분포 확인)
- [ ] 소스맵(JS) · dSYM(iOS) · mapping(Android) 업로드돼 스택이 사람이 읽히나

## 검증 체크리스트

- [ ] 시크릿이 env 로만 읽히고 코드/리포트/URL 어디에도 평문 노출 없음
- [ ] 현재 + 직전 릴리즈 둘 다 수집됐고 표본(세션 수) 기록됨
- [ ] 절대 임계 + 회귀 임계 + 표본 충분성 세 게이트 모두 평가됨
- [ ] 표본 부족 시 자동 차단하지 않고 HOLD 로 처리됨
- [ ] BLOCK 시 어떤 롤아웃 제어 명령도 사용자 confirm 없이 실행되지 않음
- [ ] top crash 가 OOM/ANR/네이티브 중 무엇인지 분류됨
- [ ] 판정·근거·다음 baseline 이 문서로 남음

## Related Skills

- `canary` — 배포 직후 라이브 사이트/앱 모니터링(이 skill 의 모바일 안정성 게이트와 짝)
- `analytics-integrator` — Sentry/Crashlytics 등 크래시·에러 추적 SDK 설치
- `incident-runbook` — BLOCK/사고로 번질 때 대응 절차로 인계
- `store-launcher` — 신규 출시·단계 출시 설정 (게이트 통과 후 확대)
