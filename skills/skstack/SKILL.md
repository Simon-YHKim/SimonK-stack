---
name: skstack
description: >
  SimonKStack 오케스트레이터 — 제품/서비스 빌드의 단일 진입점. 트리거 "앱 만들자", "기능 구현", "버그 고쳐줘",
  "리팩터", "배포", "보안 점검", "QA", "skstack", 또는 /skstack. 사용자 의도를 러프하게 진단한 뒤 적절한
  빌드 스킬/하위 오케스트레이터로 라우팅하고, 단계마다 사용자와 상호작용하며 반복 디벨롭한다. Plan 모드 우선,
  테스트·보안 게이트를 건너뛰지 않는다.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
  - Skill
---

# /skstack — SimonKStack 오케스트레이터

제품/서비스 빌드의 진입점. **Plan 우선, 게이트 안 건너뛴다.** 의도를 좁히고, 적절한 파이프라인으로 라우팅하고, 단계마다 디벨롭한다.

## 0. SimonKCore 감지 (graceful degrade)
- `agent-delegate`, `model-router`, `simon-worktree`, `grill-me`, `checkpoint`, `simon-instincts` 설치 확인.
- 있으면: 병렬 작업은 `simon-worktree`로 격리, 위임은 `agent-delegate`, 모호한 스펙은 `grill-me`, 중간 저장은 `checkpoint`, 반복 실수는 `simon-instincts`.
- 없으면: "SimonKCore 미설치 — 위임/워크트리/체크포인트 제한. `/plugin install simonk-core@simonk-core` 권장." 안내 후 계속.
- **교차 플러그인 의존 주의**: `app-dev-orchestrator`는 내부에서 `office-hours`·`plan-ceo-review`(Core)와 `simon-design-first`(SimonKDesign)를 부른다. 미설치 시 **인라인 fallback** — 기획은 6문답 인터뷰로, 디자인 단계는 "DESIGN.md 최소 골격 직접 작성"으로 대체하고 "전체 경험은 SimonKCore+SimonKDesign 설치 시" 안내. degrade는 수익화군에 한정하지 않는다.

## 1. 의도 진단 (러프 + 쉬운말 + 규모 티어)
대화로 **사용자 수준(개발자/비개발)과 산출물 규모**를 빠르게 감지하고 맞춰 질문한다.
`AskUserQuestion` **1회**, 각 선택지에 **일상어 별칭**:
- 새 앱 만들기 — "처음부터 앱/사이트"
- 기능·버그·리팩터 — "있는 거 고치기/추가"
- 인증·권한 — "로그인·회원·권한"
- DB·플랫폼 선택 — "어떤 기술 쓸지"
- 보안 점검 — "보안 검사"
- 배포·CI — "출시·자동배포"
- QA·테스트 — "동작 확인·테스트"
- 수익화 통합 — "결제·광고·분석 붙이기"
- (선택) **규모** 가볍게(단순 페이지/프로토타입) / 제대로(프로덕션) · **스택** 정해졌으면 명시

**라이트 레인**(규모=가볍게 또는 비개발·저연령 감지 시 기본값): `app-dev-orchestrator`(21단계)·풀 보안게이트·canary·retro **건너뜀**. 단순 정적 페이지는 **오케스트레이터가 직접 한 파일 HTML(인라인 CSS) 작성 → 로컬 브라우저 미리보기**(계정·배포 불필요). 그 외 경량 앱은 **인라인 6문답**(무엇/누구/핵심기능 3개/데이터 유무/디자인 톤/배포 방식)→스캐폴드→첫 배포만. 게이트는 산출물 규모에 자동 스케일.
**복합 목표**(인증+결제, 스펙→구현→릴리스노트)는 단일 선택으로 자르지 말고 순차 실행한다.
광범위 요청("전체 마이그레이션")은 작은 단위로 분해해 첫 파일부터 확인.

## 2. 라우팅 (의도 → 파이프라인)
| 의도 | 파이프라인 |
|---|---|
| 새 앱 (제로부터, 제대로) | `app-dev-orchestrator` (내부 21단계: 기획→설계→TDD→보안→배포) |
| 단순 정적 페이지·동아리 페이지 (라이트) | `simple-static-site`(한 파일 HTML 생성+로컬 미리보기+무계정 공유). app-dev-orchestrator **건너뜀** |
| 기능 스펙 작성 | `spec`(인터뷰→spec.md) → dev-orchestrator 0단계로 핸드오프 |
| 컴플라이언스·프라이버시 | `consent-manager`·`data-flow-mapper`·`store-privacy-disclosure`·`data-retention-planner`·`minor-consent-compliance`(미성년 C10) |
| 인앱결제 상품구성 | `iap-product-configurator`(스토어 콘솔 IAP) — payment-integrator(코드)와 store-launcher(리스팅) 사이 |
| 기능·버그·리팩터 | `dev-orchestrator` → `simon-tdd` → `debug`/`refactor` → `code-health-guard` |
| 플랫폼·DB 선택 | `app-platform-selector` → `db-selector` |
| 인증·권한 | `auth-builder` → `authz-designer` |
| 보안 점검 | `security-orchestrator` → `cso` → `security-checklist` → `paid-api-guard` |
| 웹/네이티브 구현 | `vercel-react`/`nextjs-optimizer`/`vue-best-practices`/`building-native-ui` |
| 배포·CI | `deploy-configurator` → `setup-deploy` → `ship` → `land-and-deploy` → `canary` |
| QA·테스트 | `qa`/`qa-only` → `test-gen` → `benchmark` → `health` |
| 엔지니어 리뷰 | `plan-eng-review` → `devex-review`/`plan-devex-review` |
| 수익화 통합 (자급자족) | `payment-integrator` → `ad-monetization` → `analytics-integrator` → `tag-manager-integrator` → `subscription-manager-selector` → `revenue-scenario-tester` → `store-launcher` |
| 릴리스 문서 | `release-notes` → `document-release` → `retro` |
| 게임 트랙 | `phase4-game-orchestrator` (향후 분리 예정) |

하위 스킬/오케스트레이터는 `Skill` 도구로 호출. (수익화 통합군은 SimonKMarket과 공유 — 자급자족 정책.)

## 3. 반복 디벨롭 (핵심)
단계마다 산출물 → 검증 → 사용자 확인 → 다음.
- 테스트 게이트(TDD), 보안 게이트(classifier·시크릿 스캔), lint/type 게이트를 **건너뛰지 않는다**.
- 한 세션 변경 파일은 작게 유지하고 단위마다 커밋 권고.

## 4. 빌드 무결성 원칙
- Plan 모드 기본, 파괴적 명령(`rm -rf`, `reset --hard`, `push --force`, `--no-verify`)은 사용자 confirm.
- 시크릿 하드코딩 금지, `.env`는 `.gitignore` 확인.
- 검증 루프를 도구로 제공(서버 URL·테스트 명령·브라우저).

## 5. 페르소나 인지 + 전파 (필수)
개발자(전문)=스펙·명령 위주, 비개발 창업자=선택지·트레이드오프 설명 위주. 수준에 맞춰 자동화 정도·설명 깊이 조절.
**전파**: §1에서 감지한 비개발/저연령 신호를 **하위 스킬 산출물까지** 전달 — SSG·RBAC·OpenAPI·EAS·CI/CD 같은 전문어 첫 등장 1줄 풀이, 큰글씨, TL;DR+다음 행동. 검증도 개발자 전제(서버 URL·테스트 명령) 대신 **비주얼/행동 확인**(로컬 미리보기·"이 버튼 눌러보세요")로 스위치.
**자급자족**: 단순 정적 페이지는 인라인 한 파일 HTML로 계정·git 없이 단독 완주(로컬 미리보기). 기존 사이트 자동 게시가 필요하면 Core `web-publisher`.

## 완료 기준
**출시 전 게이트**: `persona-validate`(SimonKCore)로 엔지니어링 전문가(Staff·Security·SRE·접근성)+대상 사용자 패널 검증 → 치명 리스크(보안·데이터손실) 반영. (Core 미설치 시 인라인 self-check — 보안 체크리스트+테스트 통과+전문가 렌즈 1개 자기검토로 대체, degrade 일관.)
기능이 동작하고(검증 완료) 게이트를 통과했으며 사용자가 확인했을 때 완료. 미진하면 3번 루프로.
