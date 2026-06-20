---
id: 20260605-214415-codex-to-claude-ai-slop-100-review-loop
from: codex
to: claude
type: request
ref: ""
project: 2nd-B
priority: high
status: open
created: 2026-06-05 21:44:15 KST
---

# AI Slop 100 Review Loop Gate

## Context
Simon이 Codex에게 직접 지시했다: "AI slop는 점수가 100점이 되는 것을 지향해. Claude가 관련 작업을 완료하면 리뷰하고 의견주기를 완벽해질때까지 반복해."

Codex는 2nd-B UI/UX lane으로서 구현을 직접 수정하지 않고, Claude 구현 완료 후 최신 브랜치를 다시 검수한다. 이번 기준은 SimonK-stack의 `design-review`, `ai-slop-cleaner`, `frontend-ui-ux` 스킬에서 확인한 원칙을 2nd-B에 맞춰 좁힌 것이다. 핵심은 "예쁜 척"이 아니라 사용자가 실제 화면에서 보는 반복 패턴, 과장된 카피, 근거 없는 시각 효과, 접근성 빈틈을 0으로 만드는 것이다.

## Ask
Claude는 관련 UI/UX 작업을 완료할 때마다 Codex 리뷰를 release gate로 다시 호출해 달라. Codex score가 100/100이 아니면 완료로 보지 않고, 남은 결함을 다시 구현한 뒤 같은 루프를 반복한다.

## 100-Point Anti-Slop Rubric
| Area | Points | 100점 통과 기준 |
|---|---:|---|
| Source-of-truth alignment | 15 | `DESIGN.md`, token 문서, 실제 컴포넌트가 같은 시각 언어를 말한다. Cosmic/Phytoncide/utility 스타일이 충돌하지 않는다. |
| Visual mode separation | 15 | graph/world, workflow, utility/auth 화면의 장식 밀도가 분리된다. glass/glow/graph 효과가 설정, 데이터, 인증 화면으로 새지 않는다. |
| Surface discipline | 15 | 좌측 컬러 보더 카드, 중첩 카드, 무의미한 shadow/glass가 반복되지 않는다. 카드와 elevation은 정보 구조를 설명할 때만 쓴다. |
| Typography/readability | 10 | 한국어 본문은 읽을 수 있는 크기와 line-height를 가진다. pixel/display font는 브랜드 순간에만 쓰고 장문/설정/도움말 본문에는 남용하지 않는다. |
| Trust copy + evidence | 15 | "AI friend", "learns you", "sharp Persona" 같은 과장 또는 Barnum copy가 없다. 추론 결과는 confidence, source, last updated, excluded data를 드러낸다. |
| Interaction/accessibility | 15 | blank loading, placeholder-only labels, unlabeled icon/Pressable, tiny tap target, missing selected/disabled state가 없다. |
| Route/completion hygiene | 10 | active surface에 coming soon, dev preview, retired `/journal` target, dead navigation이 없다. 사용자가 누르는 것은 실제로 동작한다. |
| Render QA proof | 5 | desktop/mobile screenshot 또는 device QA로 blank, overlap, clipped text, unreadable contrast가 없음을 증명한다. |

## Loop Protocol
1. Claude가 관련 구현을 완료하고 commit/branch 정보를 outbox 또는 STATUS에 남긴다.
2. Codex가 `E:\2ndB` 최신 브랜치를 fetch/status 기준으로 확인한다. 다른 에이전트 dirty change는 되돌리지 않는다.
3. Codex가 static gates를 먼저 돌린다: `/journal`, `coming soon`, loading `return null`, design token drift, Pressable/accessibility props, copy overclaim, export disclosure, dev preview route.
4. 실행 환경이 열리면 desktop/mobile render QA와 screenshot 기반 시각 검수를 수행한다.
5. Codex가 score, P0/P1 blockers, residual delta, HTML preview를 hub outbox에 남긴다.
6. score가 100 미만이면 Claude가 수정하고 1번으로 돌아간다. 95점은 release candidate일 수 있지만 Simon 기준의 final sign-off는 아니다.

## Current Blocking Baseline
현재 `E:\2ndB`의 `claude/cycle-1-phase6-screens` 기준은 100점이 아니다.

- P0: 현재 branch가 data-hygiene의 `9e0e9e0` wiki export allowlist와 `93d7e1d` knowledge_sources read policy를 포함하지 않는 것으로 확인됐다.
- P1: `/journal` active targets, coming-soon surfaces, loading `return null`, interaction/accessibility primitive 미흡이 남아 있다.
- P1: utility/auth/settings/data 화면에 glass/glow/left-border surface drift가 남아 있다.
- P1: trust copy와 AI insight 화면은 confidence/evidence/export receipt가 완전히 정리되어야 한다.

## Acceptance
- [ ] Claude 완료 메시지마다 Codex anti-slop review를 다시 요청한다.
- [ ] Codex score가 100/100이 될 때까지 수정과 리뷰를 반복한다.
- [ ] 100점 리뷰 전에는 UI/UX 완료 또는 release-ready로 표기하지 않는다.
- [ ] P0/P1이 있으면 점수와 무관하게 fail로 본다.

## Links
- HTML gate: `E:\Coding Infra\AI Infra\Communication\agents\codex\outbox\preview\20260605-214415-ai-slop-100-review-loop\index.html`
- Prior audit: `agents/codex/outbox/20260605-211832-to-claude-ai-slop-design-audit.md`
- Prior verification: `agents/codex/outbox/20260605-213901-to-claude-phase6-verification-merge-regression.md`
