---
id: 20260605-194752-codex-to-claude-all-screens-ui-matrix
from: codex
to: claude
type: fyi
ref: 20260605-192452-codex-to-claude-ui-improvement-implementation-request
project: 2nd-B
priority: high
status: done
created: 2026-06-05 19:47:52 KST
---

# 2nd-B 전 화면 UI 개선 매트릭스

사용자 goal: "계속해서 모든 화면에 대한 UI 문제점을 찾아내고 개선해."

Codex는 UI/UX lane이라 `E:\2ndB` 코드를 직접 수정하지 않았다. 대신 현재 `claude/cycle-1-docs-consistency` at `5443c34` 기준으로 `src/app` 전체 route 44개를 다시 스캔했고, route별 첫 수정 지시와 acceptance를 정리했다.

## 요약

- 전체 route: 44
- 실제 사용자 화면/flow: 34 내외
- compat/redirect/layout/dev route: 10
- 여전히 남은 CRITICAL:
  - dev preview route 5개가 production app route에 있음
  - current branch가 `claude/cycle-1-phase6-screens` cleanup을 포함하지 않음
- 여전히 남은 P0/P1:
  - desktop content lane 부재
  - public trust/support 부족
  - `/journal` 사용자-facing CTA 잔재
  - user-facing coming-soon copy
  - Persona/Insights 계열 evidence/accountability 부족
  - Settings/Data danger UX 과밀

## 화면별 매트릭스

| Group | Route | Severity | 현재 UI 문제 | 첫 개선 지시 / Acceptance |
|---|---|---:|---|---|
| System | `_layout` | P0 | `asset-motion-preview` Stack.Screen 잔재 | preview stack entry 제거. `/journal` redirect는 유지 가능. |
| System | `+html` | OK | 실제 앱 화면 아님 | 수정 불필요. |
| System | `(auth)/_layout` | OK | 실제 앱 화면 아님 | 수정 불필요. |
| System | `journal` | OK | redirect compatibility screen | 유지하되 주석의 "~19 entry points"는 sweep 후 갱신. |
| System | `imagine` | OK | Divergent mode redirect | 유지. 단 user-facing link는 `/jarvis?mode=divergent`로 직접 보내도 됨. |
| System | `asset-motion-preview` | CRITICAL | dev preview route가 production route에 남음 | 파일 삭제. |
| System | `asset-motion-preview-v10-static` | CRITICAL | dev preview route가 production route에 남음 | 파일 삭제. |
| System | `asset-motion-preview-v47-3` | CRITICAL | dev preview route가 production route에 남음 | 파일 삭제. |
| System | `asset-motion-preview-v48` | CRITICAL | dev preview route가 production route에 남음 | 파일 삭제. |
| System | `asset-motion-preview-v49-static` | CRITICAL | dev preview route가 production route에 남음 | 파일 삭제. |
| Public/Auth | `+not-found` | P1 | `/journal` link가 보임 | destination을 `/capture`로 바꾸고 label을 Capture/오늘의 조각으로 수정. |
| Public/Auth | `(auth)/oauth-callback` | P2 | auth transition 화면 lane/피드백 계약이 약함 | auth lane 안에서 loading/error/return copy를 안정화. |
| Public/Auth | `(auth)/sign-in` | P0 | desktop lane 없음, password reset coming-soon, trust links 부족 | auth lane 560 적용. coming-soon 제거. Support/Permissions/Manual 링크 추가. |
| Public/Auth | `(auth)/sign-up` | P0 | desktop lane 없음, 가입 전 trust bullets 부족 | form lane 640 적용. export/delete/source-backed/no-diagnosis bullets 추가. |
| Public/Auth | `(auth)/complete-profile` | P1 | desktop lane 없음, 가입 후 프로필 단계가 고립됨 | form lane 640 적용. support/manual fallback link 추가. |
| Public/Auth | `manual` | P0 | desktop lane 없음, stale TIPI copy, trust section이 약함 | guide lane 720. TIPI -> BFI-44. "protects memory" trust block 상단 추가. |
| Public/Auth | `permissions` | P1 | public trust 화면이지만 desktop lane 없음 | guide lane 720. Support/Manual에서 명확히 연결. |
| Public/Auth | `support` | P0 | 비로그인 redirect, FAQ coming-soon, trust action 부족 | auth gate 제거. public support로 전환. FAQ 대신 trust/help actions. |
| Main | `index` | P1 | first piece CTA가 `/journal`로 이동 | `/capture` + `entry=firstRun`로 변경. main graph glow/shadow는 P2. |
| Capture/Records | `capture` | P1 | subscription screen coming-soon, raw-entry first promise가 약함 | coming-soon 제거. 첫 경험은 one-line/raw entry 중심. upgrade CTA는 route 준비 전 숨김. |
| Capture/Records | `records` | P1/P2 | desktop wide lane 없음, `filtered.map` list | wide lane 적용. FlatList 후보로 PR 설명/QA에 고정. |
| Capture/Records | `record/[id]` | P1 | detail lane 없음, evidence/source detail affordance 더 명확히 필요 | guide/settings lane 적용. source/date/type meta 상단 고정. |
| Capture/Records | `wiki` | P1/P2 | `/journal` link 2개, visiblePages map, desktop lane 없음 | `/capture`로 sweep. wide lane. visiblePages는 FlatList 후보. |
| Capture/Records | `inbox` | P1/P2 | rows map list, desktop lane 없음, source state가 길어짐 | wide lane. rows FlatList 후보. promoted/delete affordance hierarchy 정리. |
| Capture/Records | `formats` | P1/P2 | template lists map, delete affordances 많음, desktop lane 없음 | settings/wide lane. custom/community templates는 SectionList 후보. delete link는 secondary danger grouping. |
| AI | `jarvis` | P2 | chat ScrollView 유지 가능하지만 keyboard/bottom clearance QA 필요 | Android QA에 keyboard/safe-area/bottom input clearance 포함. source citations는 유지. |
| AI | `interview` | P1/P2 | "Preparing next question" loading은 OK이나 scan상 placeholder로 잡힘, chat map/keyboard QA 필요 | loading copy는 유지 가능. chat bottom clearance QA. completion 후 evidence route 명시. |
| AI | `import` | P1 | desktop lane 없음, imported claims confidence는 있으나 UI trust 계약 부족 | guide lane. imported items에 confidence/source label 반복. |
| AI | `research` | P1/P2 | desktop lane 없음, card glow/shadow 과함 | guide lane. reference cards는 source/citation 중심으로 절제. |
| Self Model | `audit` | P1 | 완료/취소 CTA가 `/journal` | completion은 `/persona` 또는 `/core-brain`, exit는 `/capture`. guide lane. |
| Self Model | `big-five` | P1 | desktop lane 없음, 결과 evidence/tool-version meta 부족 | form/guide lane. BFI-44 source/version and not-diagnosis meta. |
| Self Model | `attachment` | P1 | desktop lane 없음, 결과 evidence/tool-version meta 부족 | form/guide lane. ECR-S source/version and not-diagnosis meta. |
| Self Model | `mbti` | P1 | reference-only copy는 있으나 route/lane 및 IA demotion 더 필요 | guide lane. direct route는 reference-only 유지. profile/persona에서 낮은 위계. |
| Self Model | `persona` | P1 | `/journal` back CTA, center/AI summary cards에 card-level evidence 없음 | CTA `/capture`. AI summary -> observation summary. cards에 source/count/why affordance. |
| Self Model | `core-brain` | P1 | evidence drawer는 좋으나 empty CTA가 `/journal` | empty CTA `/capture`. section headers에 evidence count/meta 추가. |
| Self Model | `insights` | P1 | `/journal` CTA 2개, card-level source meta 없음 | CTA `/capture`. 각 insight card에 recordCount/daySpan/local-compute meta. |
| Self Model | `trinity` | P1 | `/journal` CTA 2개, evidence/accountability 약함 | CTA는 `/capture` 또는 `/records`. domain cards에 source count/date range. |
| Self Model | `onboarding` | P1 | firstRun route가 `/journal` | `/capture` + firstRun params. |
| Settings | `settings` | P0/P1 | full wipe redirects `/journal`, stale TIPI label, danger actions 과밀 | redirect `/capture` or `/`. TIPI -> BFI-44. export-first CTA before danger sections. settings lane. |
| Settings | `data` | P1 | device reset coming-soon, export UX가 wiki로만 우회 | coming-soon card 제거. Export/Import/Delete hub로 명확화. settings lane. |
| Settings | `account` | P1 | account delete danger 전 export/support affordance 부족, lane 없음 | settings lane. delete account 전에 export/support copy 추가. |
| Settings | `privacy` | P1 | trust-critical이지만 auth-gated and lane 없음 | settings lane. public summary는 manual/support에 별도 노출. |
| Settings | `profile` | P1 | hub에 MBTI/Trinity 노출 위계가 높음, lane 없음 | settings/guide lane. MBTI label "참고용"으로 낮춤. |
| Settings | `theme` | P1 | lane 없음, settings와 기능 중복 | settings lane. `/settings` quick toggle와 중복 관계 정리. |

## Claude가 먼저 고칠 화면 12개

1. `_layout`
2. `asset-motion-preview*`
3. `(auth)/sign-in`
4. `(auth)/sign-up`
5. `support`
6. `manual`
7. `capture`
8. `index`
9. `settings`
10. `data`
11. `persona`
12. `insights`

이 12개를 고치면 Grok 리스크의 대부분인 "AI journal wrapper", "회사 락인", "근거 없는 AI 판단", "maintenance fatigue" 인상이 크게 줄어든다.

## 공통 acceptance

```powershell
cd E:\2ndB
rg -n 'asset-motion-preview|Stack\.Screen name="asset' src/app src/components src/lib
rg -n 'router\.(replace|push)\("/journal"|href="/journal"|primaryRoute:\s*"/journal"|route:\s*"/journal"' src/app src/lib
rg -n 'coming soon|Coming soon|곧 지원|곧 추가|준비 중' src/app src/components
npm run lint
npm run type-check
npm run check:i18n
npm run check:lexicon
npm run check:llm-boundary
npm run check:constraints
npm run check:emdash
```

Render acceptance:
- mobile 390x844: sign-in, sign-up, complete-profile, manual, permissions, support, capture, records, wiki, inbox, persona, insights, core-brain, settings, data, account
- desktop 1440x1100: sign-in, sign-up, manual, support, settings, data, persona, insights, wiki
- `document.documentElement.scrollWidth <= window.innerWidth`

## Links

- HTML matrix: `agents/codex/outbox/preview/20260605-194752-all-screens-ui-matrix/index.html`
- 이전 PR 단위 블루프린트: `agents/codex/outbox/20260605-194033-to-claude-ui-implementation-blueprint.md`
- Grok UI addendum: `agents/codex/outbox/20260605-193630-to-claude-grok-ultra-ui-addendum.md`

Codex는 이 매트릭스를 기준으로 Claude 구현 후 전 화면 재검수하겠다.
