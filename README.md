# SimonK-Stack

> Claude Code용 스킬 182개를 다섯 플러그인으로 묶은 작업 도구 상자입니다. 아이디어 검증부터 기획·개발·테스트·보안·배포, 디자인, AI 기능, 마케팅까지 "무엇을 하고 싶은지"만 말하면 알맞은 스킬과 모델로 이어 줍니다.

![license](https://img.shields.io/badge/license-MIT-green) [![validate](https://github.com/Simon-YHKim/SimonK-stack/actions/workflows/validate-plugin.yml/badge.svg)](https://github.com/Simon-YHKim/SimonK-stack/actions/workflows/validate-plugin.yml) ![plugins](https://img.shields.io/badge/plugins-5-5b8cff) ![skills](https://img.shields.io/badge/skills-182-brightgreen)

**사이트**: [simonk-stack.pages.dev](https://simonk-stack.pages.dev) · **English**: [README.en.md](README.en.md) · **변경 기록**: [CHANGELOG.md](CHANGELOG.md)

## 목차

1. [SimonK-Stack이란](#1-simonk-stack이란)
2. [다섯 플러그인](#2-다섯-플러그인)
3. [설치](#3-설치)
4. [처음 써 보기](#4-처음-써-보기)
5. [하고 싶은 일별 스킬 찾기](#5-하고-싶은-일별-스킬-찾기)
6. [안전 모드 — careful · freeze · guard · unfreeze](#6-안전-모드--careful--freeze--guard--unfreeze)
7. [업데이트 · 되돌리기 · 제거](#7-업데이트--되돌리기--제거)
8. [예전 `simonk-stack` 0.1.0에서 옮기기](#8-예전-simonk-stack-010에서-옮기기)
9. [문제 해결](#9-문제-해결)
10. [함께 들어 있는 앱 — AI 사용량 위젯](#10-함께-들어-있는-앱--ai-사용량-위젯)
11. [개발자 안내](#11-개발자-안내)
12. [라이선스](#12-라이선스)

---

## 1. SimonK-Stack이란

스킬은 Claude에게 "이런 일은 이렇게 하라"는 절차와 도구를 담은 묶음입니다. SimonK-Stack은 혼자 제품을 만드는 사람이 매번 같은 지시를 반복하지 않도록, 자주 쓰는 일하는 방식을 스킬로 정리해 둔 모음입니다.

사용 흐름은 단순합니다.

1. 하고 싶은 일을 말합니다. 예: "이 아이디어 시장성 있는지 검증해줘", "로그인 기능 만들고 배포까지 해줘".
2. 각 플러그인의 진입 스킬(`vibe`, `skstack`, `skdesign`, `skaihub`, `skmarket`)이 의도를 파악하고 필요한 하위 스킬로 넘깁니다. 자연어로 요청해도 Claude가 스킬 설명을 보고 알맞은 스킬을 고릅니다.
3. 결과는 검증을 거쳐 보고됩니다. 테스트·실측 근거가 없으면 "완료"라고 하지 않습니다.

지키는 원칙:

- **목표와 권한은 사용자가 정합니다.** 머지·배포·삭제·결제처럼 되돌리기 어렵거나 비용이 드는 일은 사용자의 권한 범위 안에서만 실행합니다.
- **추가 과금 0이 기본입니다.** `/vibe`는 구독에 포함된 사용량 안에서만 모델을 쓰고, 과금이나 사용량이 확인되지 않으면 실행하지 않습니다.
- **확인한 것만 말합니다.** 실측하지 않은 부분은 "미확인"이라고 적습니다.

## 2. 다섯 플러그인

| 플러그인 | 하는 일 | 스킬 | 진입점 |
| --- | --- | ---: | --- |
| `simonk-core` | 공용 기반. 작업 조정(`vibe`), 스프린트(`simonk`), 모델 배정, AI 토론, 메모리·위키, 보고서, 세션 인수인계, 안전(`careful`·`unfreeze`) | 61 | `/simonk-core:vibe` |
| `simonk-stack` | 제품 만들기. 기획·스펙, 개발·리팩터링, 디버깅, QA, 보안, 배포·릴리스, 안전(`freeze`·`guard`) | 60 | `/simonk-stack:skstack` |
| `simonk-aihub` | AI 기능 만들기. 모델 선택, 프롬프트, 에이전트, RAG, LLM 평가·안전 평가 | 7 | `/simonk-aihub:skaihub` |
| `simonk-design` | 디자인. UI 방향 잡기, 디자인 시스템, 로고·소셜 그래픽, 슬라이드, 접근성 점검 | 22 | `/simonk-design:skdesign` |
| `simonk-market` | 시장과 매출. 아이디어 검증, PMF, 그로스·리텐션, 광고·결제·구독, 출시 | 32 | `/simonk-market:skmarket` |

플러그인 스킬을 슬래시로 부를 때는 `/<플러그인>:<스킬>` 형식이 확실합니다(예: `/simonk-core:careful`). 각 플러그인에 들어 있는 스킬 전체 목록은 [5절 끝](#전체-스킬-목록)에 있습니다.

## 3. 설치

### 준비물

- 플러그인을 지원하는 Claude Code. 2.1.289에서 설치·업데이트·롤백을 실측했습니다.
- Git.
- 안전 모드(6절)를 쓰려면 Windows, Git for Windows(Git Bash), PATH에 잡힌 Python 3.7 이상.

### 설치 명령

Claude Code 세션 안에서:

```
/plugin marketplace add Simon-YHKim/SimonK-stack
/plugin install simonk-core@simonk-stack
/plugin install simonk-stack@simonk-stack
/plugin install simonk-aihub@simonk-stack
/plugin install simonk-design@simonk-stack
/plugin install simonk-market@simonk-stack
```

터미널에서는 같은 일을 `claude plugin marketplace add Simon-YHKim/SimonK-stack`, `claude plugin install <id>@simonk-stack`로 합니다. 세션 안에서 설치했다면 `/reload-plugins`로 바로 적용하거나 새 세션을 엽니다.

필요한 플러그인만 골라 설치해도 되지만, 진입 스킬이 다른 플러그인의 스킬로 넘기는 경우가 많아 다섯 개를 모두 설치하는 것을 권장합니다.

### 설치 확인

다섯 줄이 나오면 정상입니다.

```powershell
(claude plugin list --json | Out-String | ConvertFrom-Json) | Where-Object id -like 'simonk-*@simonk-stack' | Select-Object id, version, enabled
```

POSIX 셸에서는 `claude plugin list --json | grep -o 'simonk-[a-z]*@simonk-stack'`입니다.

> **flat 설치와 함께 쓰지 마세요.** `~/.claude/skills`에 같은 스킬을 이미 복사해 두었다면, 플러그인을 켰을 때 스킬이 두 벌로 보입니다. 2026-10-05 실측에서는 563개, 설명 3만 자를 넘겨 목록이 잘렸고, 이러면 모델이 스킬을 자동으로 고를 때 정확도가 떨어집니다. 플러그인과 flat 중 한 쪽만 쓰세요.

## 4. 처음 써 보기

아래처럼 평소 말로 요청하면 됩니다. 괄호 안은 주로 이어지는 스킬입니다.

```
이 아이디어 사람들이 돈 낼까? 출시 전에 검증하는 방법 알려줘     (idea-validation)
할 일 관리 앱 MVP 만들자                                        (app-dev-orchestrator, skstack)
로그인하면 500 에러가 나. 원인 찾아서 고쳐줘                      (investigate)
이 페이지 QA 돌려줘                                              (qa)
랜딩페이지 디자인 방향부터 잡아줘                                 (simon-design-first)
고객 문의에 답하는 RAG 챗봇 만들고 싶어                           (skaihub, rag-builder)
결제 붙이고 구독 요금제 설계해줘                                  (skmarket, paywall-designer)
```

여러 단계를 한 번에 맡기고 싶다면 조정자를 부릅니다.

```
/simonk-core:vibe 회원가입부터 결제까지 되는 웹앱을 만들고 배포 직전까지 검증해줘
```

`vibe`는 필요한 스킬과 모델, 사용량, 검증 단계를 하나의 계획으로 묶고 승인된 범위 안에서 실행합니다. `/simonk-core:simonk`는 같은 조정자 아래에서 6단계 스프린트(명확화 → 계획 → 실행 → 검증·복구 → 범위 내 Git 반영 → 보고)를 돌립니다.

어떤 스킬이 있는지 모르겠으면 `/simonk-core:find-skill 영수증 OCR`처럼 찾아보세요.

## 5. 하고 싶은 일별 스킬 찾기

| 하고 싶은 일 | 스킬 | 플러그인 |
| --- | --- | --- |
| 아이디어 검증, 수요 테스트 | `idea-validation`, `pmf-analyzer` | market |
| 요구사항·스펙 정리 | `spec`, `office-hours` | stack, core |
| 새 앱을 처음부터 | `app-dev-orchestrator`, `skstack` | stack |
| 기술 스택·DB 고르기 | `stack-architect`, `db-selector`, `app-platform-selector` | stack |
| 테스트 먼저 개발(TDD) | `simon-tdd`, `test-gen` | stack |
| 버그 원인 찾기 | `investigate`, `debug` | stack |
| 웹 QA와 수정 | `qa`, `qa-only` | stack |
| 보안 점검 | `cso`, `security-checklist`, `security-orchestrator` | stack |
| PR·배포·릴리스 | `ship`, `land-and-deploy`, `release-notes` | stack |
| 디자인 방향·시스템 | `simon-design-first`, `design-consultation`, `design-system-keeper` | design |
| 슬라이드·로고·소셜 이미지 | `slides`, `logo-generator`, `social-graphic` | design |
| 접근성 점검 | `accessibility-audit`, `inclusive-ux` | design |
| AI 모델·프롬프트·에이전트 | `ai-model-selector`, `prompt-engineering`, `agent-builder` | aihub |
| RAG, LLM 평가 | `rag-builder`, `llm-eval`, `ai-safety-eval` | aihub |
| 그로스·리텐션 | `growth-engine`, `aarrr-growth-planner`, `cohort-retention-analyzer` | market |
| 수익화·결제·구독 | `monetization-planner`, `payment-integrator`, `paywall-designer` | market |
| 중요한 결정을 여러 AI와 토론 | `ai-debate` | core |
| 작업에 맞는 모델 고르기 | `model-router` | core |
| 세션 인수인계 | `simon-handoff` | core |
| 결과 보고서(HTML) | `completion-report` | core |
| 화면 조작이 꼭 필요한 일 | `vibe-bot` | core |

### 전체 스킬 목록

<details>
<summary><code>simonk-core</code> — 61개</summary>

agent-delegate, ai-debate, ai-usage-widget-install, careful, caveman, checkpoint, completion-report, defuddle, designmd-upgrade, domain-glossary, find-skill, founder-context, gcloud-helper, grill-me, gstack-upgrade, html-default-output, human-voice-guard, json-canvas, keepass-helper, learn, llm-wiki-builder, model-router, multi-terminal-dispatcher, notebooklm-import, obsidian-bases, obsidian-cli, obsidian-markdown, office-docs, office-hours, omc-upgrade, omo-upgrade, open-gstack-browser, opencowork-upgrade, openharness-upgrade, pair-agent, persona-validate, perspectives, plan-ceo-review, project-context-md, semantic-recall, session-context-export, session-context-tracker, session-start-hook, setup-browser-cookies, simon-handoff, simon-instincts, simon-ohmo, simon-research, simon-worktree, simonk, simonk-report, sprint-optimizer, stack-update, tech-preference-tracker, unfreeze, vibe, vibe-bot, web-publisher, wiki-ingest, wiki-lint, wiki-query
</details>

<details>
<summary><code>simonk-stack</code> — 60개</summary>

analytics-ad-wiring, app-dev-orchestrator, app-platform-selector, auth-builder, authz-designer, autoplan, benchmark, browse, building-native-ui, canary, code-health-guard, codex, consent-manager, cso, data-flow-mapper, data-retention-planner, db-selector, debug, deeplink-integrator, deploy-configurator, dev-orchestrator, devex-review, document-release, explain, freeze, guard, health, i18n-localizer, iap-product-configurator, incident-runbook, investigate, karpathy-guidelines, land-and-deploy, minor-consent-compliance, nextjs-optimizer, offline-first, paid-api-guard, phase4-game-orchestrator, plan-devex-review, plan-eng-review, qa, qa-only, refactor, release-health-guard, release-notes, retro, security-checklist, security-orchestrator, setup-deploy, ship, simon-tdd, simple-static-site, skstack, spec, stack-architect, store-privacy-disclosure, test-gen, vercel-react, vue-best-practices, zoom-out
</details>

<details>
<summary><code>simonk-aihub</code> — 7개</summary>

agent-builder, ai-model-selector, ai-safety-eval, llm-eval, prompt-engineering, rag-builder, skaihub
</details>

<details>
<summary><code>simonk-design</code> — 22개</summary>

accessibility-audit, coloring-art, consistency-guard, dashboard-review, design-consultation, design-html, design-review, design-shotgun, design-system-keeper, design-system-page, inclusive-ux, logo-generator, persona-simulation, photo-album, plan-design-review, remotion-best-practices, scientific-paper, simon-design-first, skdesign, slides, social-graphic, stitch-design-flow
</details>

<details>
<summary><code>simonk-market</code> — 32개</summary>

aarrr-growth-planner, ad-monetization, aha-moment-optimizer, analytics-integrator, churn-recovery-planner, cohort-retention-analyzer, community-marketing, exit-strategy-planner, experiment-analyzer, export-channel, feedback-and-review-collector, global-payment-planner, growth-engine, idea-validation, lifecycle-campaign-designer, mobile-attribution-integrator, monetization-planner, nocode-monetization, onboarding-flow-builder, paid-ads-campaign, payment-integrator, paywall-designer, pink-tax-advisor, pmf-analyzer, referral-program-builder, revenue-scenario-tester, skmarket, store-launcher, subscription-manager-selector, tag-manager-integrator, unit-economics-modeler, viral-launch
</details>

## 6. 안전 모드 — careful · freeze · guard · unfreeze

운영 서버나 공유 PC에서 작업할 때 실수를 막는 장치입니다. 켜면 그 세션 동안 Claude가 명령을 실행하거나 파일을 고치기 전에 검사합니다.

| 스킬 | 하는 일 |
| --- | --- |
| `careful` (core) | 위험한 명령을 검사합니다. 루트·드라이브·홈의 재귀 삭제, 기본 브랜치 force push 같은 HIGH 명령은 막고(deny), `rm -r`·`git reset --hard`·`DROP` 같은 MEDIUM Bash 명령은 실행 전에 확인을 묻습니다(ask). PowerShell 명령은 위험한 모양만 막고 묻지는 않습니다. 검사 자체가 실패해도 막습니다. |
| `freeze` (stack) | 편집 범위를 한 폴더로 묶습니다. 경계 밖이나 판정할 수 없는 경로의 편집은 막습니다. |
| `guard` (stack) | `careful`과 `freeze`를 함께 켭니다. |
| `unfreeze` (core) | `freeze`·`guard`의 편집 경계를 풉니다. 성공하면 `FREEZE_CLEARED` 줄이 나옵니다. |

> **안전 훅은 Windows 전용입니다.** `careful`, `freeze`, `guard`, `investigate`의 훅은 Windows에서만 판정합니다. 다른 OS에서는 스킬을 켜는 순간부터 해당 명령이나 편집을 **일부러 모두 막습니다**(fail-closed). Python이 없어도 마찬가지입니다. 빠져나오려면 그 스킬 없이 새 세션을 시작하거나, `/plugin disable simonk-core@simonk-stack`(careful) 또는 `/plugin disable simonk-stack@simonk-stack`(freeze·guard·investigate)을 실행한 뒤 새 세션을 엽니다. 비Windows에서는 `/unfreeze`로 풀리지 않습니다. 근거와 실측은 [INSTALL.md 비Windows 안전 훅](docs/INSTALL.md#비windows-안전-훅--인터프리터-가드-d-76-4단계)에 있습니다.

## 7. 업데이트 · 되돌리기 · 제거

### 업데이트

서드파티 마켓플레이스는 자동 업데이트가 기본으로 꺼져 있습니다. 새 버전은 이렇게 받습니다.

```
claude plugin marketplace update simonk-stack
claude plugin update simonk-core@simonk-stack
claude plugin update simonk-stack@simonk-stack
claude plugin update simonk-aihub@simonk-stack
claude plugin update simonk-design@simonk-stack
claude plugin update simonk-market@simonk-stack
```

버전은 `1.<숫자>.0` 형식이고 새 릴리스마다 숫자가 커집니다. 업데이트한 뒤에는 새 세션을 열거나 `/reload-plugins`로 적용합니다.

### 문제가 생긴 릴리스를 되돌릴 때

사용자 쪽에서 따로 할 일은 없습니다. 문제가 있는 릴리스는 이전 내용을 **더 높은 버전**으로 다시 내보내는 방식으로 되돌립니다. 위 업데이트 명령을 한 번 더 실행하면 됩니다(2026-10-05 실측: 1.766.0 → 1.767.0으로 이전 내용 복원).

### 제거

```
claude plugin uninstall simonk-core@simonk-stack
```

나머지 플러그인도 같은 형식입니다. 잠깐 끄기만 하려면 `claude plugin disable <id>@simonk-stack`, 다시 켜려면 `enable`입니다. 마켓플레이스까지 지우려면 `claude plugin marketplace remove simonk-stack`입니다.

## 8. 예전 `simonk-stack` 0.1.0에서 옮기기

2026-10-05 이전에 이 마켓플레이스를 쓴 분이 해당됩니다. 예전에는 플러그인이 `simonk-stack` 0.1.0 하나였습니다. 지금 `/plugin update`(또는 `claude plugin update simonk-stack@simonk-stack`)를 하면 같은 ID가 새 `simonk-stack`으로 바뀌지만 **나머지 넷은 자동으로 설치되지 않습니다.** 그러면 예전 스킬 10개(`simonk-market`으로 옮긴 9개, `simonk-design`으로 옮긴 `consistency-guard`)가 사라집니다. 업데이트한 뒤 아래 네 줄을 실행하세요.

```
claude plugin install simonk-core@simonk-stack
claude plugin install simonk-market@simonk-stack
claude plugin install simonk-design@simonk-stack
claude plugin install simonk-aihub@simonk-stack
```

그다음 [3절의 설치 확인](#설치-확인)으로 다섯 개가 모두 있는지 봅니다. plugin.json의 `dependencies`는 새로 설치할 때만 따라오고 업데이트에서는 동작하지 않습니다. 실측 기록은 [INSTALL.md 레거시 이전](docs/INSTALL.md#레거시-simonk-stack-010-사용자-이전-d-76-4단계)에 있습니다.

## 9. 문제 해결

| 증상 | 확인할 것 |
| --- | --- |
| 설치했는데 스킬이 안 보임 | `/reload-plugins`를 실행하거나 새 세션을 엽니다. `claude plugin list`에서 `enabled`가 true인지 봅니다. |
| 새 버전이 안 들어옴 | 자동 업데이트가 꺼져 있습니다. 7절 명령으로 `marketplace update` 뒤 `plugin update`를 합니다. |
| 스킬이 두 번씩 보이고 목록이 잘림 | flat 설치(`~/.claude/skills`)와 플러그인을 함께 켠 경우입니다. 한 쪽만 쓰세요. |
| macOS·Linux에서 명령이 전부 막힘 | `careful`·`freeze`·`guard`를 켠 상태입니다. 안전 훅은 Windows 전용입니다. 6절의 빠져나오는 방법을 따르세요. |
| Windows에서 안전 훅이 모든 명령을 막음 | Git for Windows와 Python 3.7 이상이 PATH에 있는지 확인합니다. 검사기를 실행할 수 없으면 일부러 막습니다. |
| `/vibe`가 실행하지 않고 "blocked"라고 함 | 구독 포함 사용량이 확인되지 않았거나 상한에 가까운 경우입니다. 추가 과금을 막기 위한 동작이며, 보고에 막힌 이유가 적혀 있습니다. |
| 예전 스킬이 사라짐 | 8절의 네 줄을 실행합니다. |

## 10. 함께 들어 있는 앱 — AI 사용량 위젯

`apps/ai-usage-widget/`는 Windows 작업 표시줄 옆에 Claude·Codex·Grok·Antigravity의 구독 사용량(5시간·주간 한도, 리셋까지 남은 시간)을 띄우는 Electron 앱입니다.

- 각 공급자의 공식 CLI 경로만 씁니다. 조회에 실패하면 가짜 숫자 대신 "미확인"과 마지막 실측 시각을 보여 줍니다.
- 한도 사용률이 평소보다 빠르게 오르면 해당 계정을 강조하고 잠깐 말풍선을 띄웁니다.
- 공식 문서에서 새 모델 출시가 확인되면 배지로 알려 줍니다.

Claude Code에서 `/simonk-core:ai-usage-widget-install` 또는 "AI 사용량 위젯 설치해줘"라고 하면 소스에서 빌드·검증한 뒤 설치합니다(node, pnpm, git 필요). 로그인은 위젯 화면에서 사용자가 직접 합니다. 자세한 설계는 [앱 설계 문서](apps/ai-usage-widget/docs/DESIGN.md)에 있고, 타사 로고의 권리는 [NOTICE](NOTICE)를 따릅니다.

## 11. 개발자 안내

### 저장소 구조

```
skills-src/        배포할 스킬 소스 137개 (SKILL.md, evals/, scripts/, references/)
.claude/skills/    이 저장소에서 쓰는 개발용 스킬 4개
scripts/           빌드·검증 도구 (skill_release, plugin_bundle, codex_overlay, codex_safe_subset, dist_release)
scripts/windows/   Windows 사용자 홈 설치 도구 (update-local.ps1)
distribution/      배포 입력과 게이트 (plugin-inputs, dist-publish.allow, 보류 파일)
apps/              AI 사용량 위젯
docs/              설치 기록(INSTALL.md), 인수인계(HANDOFF.md) 등
```

다섯 플러그인은 `skills-src/`와 플러그인별 원본 저장소(`distribution/plugin-inputs.v1.json`에 커밋으로 고정)를 합쳐 빌드합니다.

### 스킬 추가·수정

1. 새 스킬은 `skill-gen-agent`로 만듭니다(설명 형식·이름·길이 검사를 거칩니다).
2. 고친 뒤에는 검증합니다. 오류와 경고가 0이어야 합니다.

   ```bash
   python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py skills-src/<name>
   python3 .github/skill-ci/run_ci.py
   ```

3. `evals/cases.json`에 테스트 케이스를 2개 이상 둡니다.
4. 스킬 버전을 올리고(`SKILL.md`, `evals/cases.json`, 버전을 고정한 테스트) CHANGELOG에 한 줄 남깁니다.
5. 커밋은 Conventional Commits 형식(`feat(skills):`, `fix(...)`, `docs:` …)으로 합니다.

자주 쓰는 테스트:

```bash
python3 -B -m unittest discover -s scripts/tests -p 'test_*.py'
(cd skills-src/vibe/scripts && python3 -B -m unittest discover -s . -p 'test_*.py' -q)
```

### 릴리스가 사용자에게 가는 길

1. main에 push되면 `five-plugin-dist.yml`이 Windows 러너에서 공개 입력만으로 다섯 플러그인을 다시 빌드합니다. 빌드한 트리에는 경로 감사와 안전 런타임 테스트를 돌리고, 별도 job에서 bundle·Codex·안전 훅 단위 테스트를 돌립니다.
2. 게시 job은 두 가지가 모두 있을 때만 `dist` 브랜치에 새 커밋을 올립니다. 하나는 저장소 변수 `SIMONK_DIST_PUBLISH`, 다른 하나는 커밋된 `distribution/dist-publish.allow`(결정 코드, 기준 커밋, 콘텐츠 digest)입니다. 내용이 같으면 건너뛰고, 이미 게시된 것보다 낮은 버전은 거부하며, force push는 하지 않습니다.
3. 마켓플레이스 카탈로그(`.claude-plugin/marketplace.json`)는 `dist` 브랜치의 다섯 폴더를 가리킵니다.

새 내용을 내보내려면 기능을 머지한 뒤 승인 파일의 digest를 그 빌드 값으로 바꾸는 PR을 머지합니다. 되돌릴 때는 main에서 원인 커밋을 revert합니다. 그러면 이전 내용이 더 높은 버전으로 다시 나갑니다. **카탈로그 커밋은 되돌리지 마세요.** 되돌리면 이미 설치한 사용자의 플러그인이 "not found"가 됩니다. 자세한 절차와 근거는 [docs/INSTALL.md](docs/INSTALL.md)에 있습니다.

### Windows에서 flat 설치로 관리할 때

플러그인 대신 `~/.claude/skills`에 직접 설치해 쓰는 관리자용 경로입니다.

```powershell
pwsh -NoProfile -NonInteractive -File scripts/windows/update-local.ps1            # 미리보기
pwsh -NoProfile -NonInteractive -File scripts/windows/update-local.ps1 -Apply -Selftest
```

후보를 빌드하고, 링크를 교체하고, 바뀐 스킬만 바꾼 뒤 스스로 검증합니다. 실패하면 되돌립니다. 이 방식을 쓰는 PC에서는 플러그인을 함께 켜지 마세요(3절 참고). 예전 git clone 설치 스크립트(`scripts/install.sh`, `scripts/setup-repo.sh`)는 지금 권장하지 않습니다.

### 더 보기

| 문서 | 내용 |
| --- | --- |
| [docs/INSTALL.md](docs/INSTALL.md) | 설치·배포 절차와 검증 기록 |
| [docs/HANDOFF.md](docs/HANDOFF.md) | 최근 작업 상태와 다음 할 일 |
| [CLAUDE.md](CLAUDE.md) | 이 저장소에서 작업할 때의 규칙과 검증 명령 |
| [.claude/skills/INDEX.md](.claude/skills/INDEX.md) | 소스·개발 스킬 지도 |
| [skills-src/vibe/references/orchestration.md](skills-src/vibe/references/orchestration.md) | `vibe` 실행 계약(계획·예산·게이트) |
| [docs/skill-selection-validation.md](docs/skill-selection-validation.md) | 스킬 자동 선택 정확도 검증 절차 |

## 12. 라이선스

MIT. 자세한 내용과 upstream 크레딧(gstack: garrytan, mattpocock skills 등)은 [LICENSE](LICENSE)와 [NOTICE](NOTICE)에 있습니다.
