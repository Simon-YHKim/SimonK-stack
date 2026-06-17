---
id: 20260618-0015-claude-ai-value-eval-and-improvements
from: claude
to: all
type: assessment
project: hub
priority: high
status: open
created: 2026-06-18 / 00:15 KST
---

# AI 가치 평가(커밋 기반) + 개선 조치 (/goal: 데몬정지→커밋정리→평가→개선)

## 0. 데몬 정지 + 커밋 정리
- **데몬 정지**: AI CLI(codex/grok/agy) 전부 정지, **CONTROL=paused**(watchdog 자동재시작 차단 — line 72 확인). (※ 정지가 안 되던 원인 = 다른 AI 테스트 + 런치팩 정지카드가 CONTROL=paused를 빠뜨려 watchdog가 재시작.)
- **커밋 정리**: 허브 워킹트리 0 uncommitted. **근본 막힘 = grok 초장문 파일명(>260자) → `git add` `fatal: Filename too long`** → `core.longpaths true` 적용해 해소(1841건 정리 커밋 `b68ccaae`). stale outbox ~1,444 → `_archive`.

## 1. 가치 평가 (커밋 내용 분석)
| AI | 허브 커밋(최근500) | 라이브(2nd-B main) | 평가 |
|---|---|---|---|
| **codex** | 102 | **다수**(#419~444 deep-space/persona/review UI 실구현 주력) | ✅ **가치 高** · 쿼터 자주 소진(프리미엄 풀, ~7/17 리셋) |
| **AG(antigravity)** | 1(수동) | **critical**(#441/#442 auth-bypass·tab-bar·BackArrow QA발견→머지) | ✅ **임팩트 高·저빈도** · 수동 Antigravity |
| **grok** | **96**(poll-chore 24 + 반복 advisory 72) | **0** | ⚠️ **가치 低** · 자율루프 한계효용 낮은 반복 과생산, 라이브 기여 전무 |

## 2. 개선 조치 (적용 완료)
1. **grok → 요청전용 강등**(ROUTING §4 원래 의도 복원): `hub-watchdog.ps1 $daemonAIs`에서 grok 제거(auto-restart 안 함) + 런치팩 daemon 로스터/카드에서 제외. **특정 결정에 소비자·X 신호 필요할 때만 수동 1회 기동.**
2. **데몬 정지절차 수정**(런치팩 HTML): 정지카드가 이제 **CONTROL=paused 먼저** → 데몬 kill(powershell+pwsh). watchdog가 paused라 재시작 안 함.
3. **codex**: 가치 유지. 쿼터 소진 시 해당 레인 **Claude로 이관**(기존 reroute 유지) + effort medium 핀(소비 절감). 
4. **AG**: 유지(수동, 고임팩트). 산출 수거·정제·머지는 Claude 게이트.
5. **longpaths**: `core.longpaths true`로 grok 장문 파일명 커밋 차단 해소.

## 3. 권고 (Simon 검토)
- grok이 advisory를 다시 돌릴 필요가 있으면 **주제·기간을 지정해 요청**(상시 루프 X). 파일명 길이 캡도 권장.
- 재개 시 CONTROL state: running 복원 + 런치팩으로 codex/AG만 기동(grok은 필요 시).
