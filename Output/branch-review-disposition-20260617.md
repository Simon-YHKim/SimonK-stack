# 미머지 브랜치 REVIEW 처리 방향 — 2026-06-17

> drain-branches 엔진이 67 → 8로 드레인 후, 자동 폐기 대상이 아닌(살아있거나 코드 보유) 8개의 처리 방향.
> 엔진은 보수적이라 이들을 자동으로 안 지운다. 아래는 Claude 권고 — 실제 drop/merge는 Simon 확인 후.

## 살릴 가치 (integrate)

| 브랜치 | ahead/behind | 내용 | 권고 |
|---|---|---|---|
| `feat/art20-export-account` | 3 / 136 | GDPR Art.20 데이터 export (backend function + UI + **테스트**), DPIA portability gap | **최우선 머지** — clean worktree 리베이스+verify+머지. 중간에 main-merge 커밋 있어 비교적 깔끔 |
| `codex/soul-core-multimodal-pilot-20260610` | 54 / 283 | OCR/capture 멀티모달 파이프라인, 대량 테스트 | 저자(codex)에 **리베이스 재제출** 오더, 또는 유효 커밋 cherry-pick. 큰 작업 |
| `claude/loving-davinci-QpZyJ` | 14 / 836 | RAG/Wiki seed SQL (self-knowledge·SDT·narrative-identity 등 research 시드, 순수 additive) | main에 RAG 시드 존재 여부 확인 후 결정. 가장 오래됨(5/25) |

## Superseded (폐기 권고)

| 브랜치 | ahead/behind | 대체된 곳 | 권고 |
|---|---|---|---|
| `handoff/20260616-1135` | 1 / 64 | cont.4(1850, 이미 main)로 대체된 docs handoff | drop |
| `wip/deep-space-20260616` | 2 / 93 | #436 deep-space(이미 main 기본값) | drop — 단 `public/landing/bg-concepts/shot-4,5,5b.png` 컨셉아트가 main에 있는지 확인 후 |
| `codex/core-label-tail-cleanup` | 9 / 371 | deep-space 전환으로 레거시 gameboy/pixel 테마 폴리시 | drop 권고(레거시 트랙) |
| `codex/pending-pre3153de4-a11y-stack` | 8 / 607 | 06-17 deepspace-a11y로 대체된 옛 화면 a11y | drop |
| `claude/cycle-1-phase6-screens` | 13 / 615 | cycle-1 시대(6/05) Android 백핸들러/dead-module 정리, 일부 타 경로 반영 | drop 권고 |

## 실행 방법
- 폐기: `git push origin --delete <branch>` (drain-branches.ps1이 stale 자동 처리하나, 이들은 ahead≥8/behind≤150이라 보수적으로 보존됨 → 수동 확인 후 drop)
- 복원 가능: 모든 drop은 `Output/branch-drain-restore-*.ps1`에 SHA 기록, origin GC 전(~90일) 복원 가능
