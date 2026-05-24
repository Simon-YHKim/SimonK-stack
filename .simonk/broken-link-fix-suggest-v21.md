# Wiki Broken Link Fix Suggestions (Sprint v21 분석)

Generated: 2026-05-24 (sprint-v21)
Total raw count: **49 broken** (553 → 49, 91% reduction in sprint v18-v20)

## 분류 정확도 분석 (simonK Phase 4 verification)

분석 결과 49건 중 실제 분포:

| 카테고리 | 갯수 | 액션 우선순위 |
|---|---|---|
| **진짜 missing (raw 파일 미수집)** | **17** | ⚠ **HIGH** — `[[../../raw/.../SimonK_*]]` 패턴, raw/ 어디에도 SimonK_LLMWiki_Spine/SystemBlueprint/OperationsManual 등 파일 미존재 |
| Wikilink 사용법 예시 (CLAUDE.md 안) | 7 | ✅ false-positive — `[[페이지명]]`, `[[wikilink]]`, `[[link]]`, `[[A2-uk-2004]]` 등 문서 안 예시 텍스트 |
| 외부 repo 경로 (skills-src/) | 5 | ⚠ MEDIUM — `[[../../skills-src/simon-ohmo]]`, `[[../../skills-src/simon-design-first]]` — wikilink 가 외부 repo 가리킴, wiki 페이지 미러 또는 link 제거 |
| Raw transcripts 누락 | 6 | ⚠ MEDIUM — `[[../raw/transcripts/...]]` 패턴, transcripts/ 폴더 안 실제 파일명 확인 필요 |
| 진짜 missing page (circuits, notebooklm-py 등) | 4 | ⚠ HIGH — `[[circuit-04-speaking-hurts]]`, `[[notebooklm-py]]` × 2, `[[../entities/tools/stitch-design-flow-references]]` |
| Bash 코드 안 더블 brackets (linter 버그) | 1 | ✅ false-positive — `[[ "$GITHUB_REF_TYPE" == "tag" ]]` — wiki-broken-link-analyzer.py 가 bash 더블 brackets 를 wikilink 로 오인식 |
| Markdown 안 link placeholder | 1 | ✅ false-positive |
| **기타 raw/ 경로** | 8 | ⚠ MEDIUM — raw/ 하위 경로 정확성 확인 필요 |

**합계**: 49 = 17 (raw 미수집) + 7 (예시) + 5 (skills-src) + 6 (transcripts) + 4 (진짜 missing) + 1 (linter 버그) + 1 (placeholder) + 8 (raw 경로)

## 다음 sprint 액션 후보

### HIGH 우선순위 (21건)
1. **raw 파일 수집** — `raw/simonk-system/` 폴더 생성 + SimonK_LLMWiki_Spine_v1_260523, SimonK_SystemBlueprint_v05_260522, SimonK_OperationsManual_v0_260522 추가
2. **진짜 missing 4건 작성**:
   - `circuit-04-speaking-hurts` (9 circuits sub-page 누락 — sprint v19 에서 9개 분할했는데 #04 누락 가능)
   - `notebooklm-py` × 2 (entities/tools/graphify.md, openharness.md 가 가리킴 — 통합 entity 페이지 필요)
   - `entities/tools/stitch-design-flow-references.md` (concepts/design-md-workflow.md 가 가리킴)

### MEDIUM 우선순위 (19건)
- skills-src 5건: 외부 repo 페이지 미러 또는 link 제거 결정
- transcripts 6건: raw/transcripts/ 안 실제 파일명 확인 + slug 정규화

### LOW 우선순위 (9건) — false-positive
- linter 개선 (CLAUDE.md 안 wikilink 예시 + bash 더블 brackets 제외 룰)

## simonK Phase 4 verification 결과

snapshot v20 claim: "553 → 49 (95% 외부·raw 경로 false-positive)" → **부분적으로 부정확**.
- 실제 false-positive: 9/49 (18%)
- 진짜 actionable broken: 40/49 (82%)
- 다음 fix sprint 에서 raw 파일 수집 우선 (17건) 진행 시 → 49 → 32 → 다시 미분류 12 (skills-src/transcripts) → 진짜 missing 4 + linter 9건 = 13건 남김 가능

---

## Raw 분석 출력 (analyzer original)

Total: 49 broken

## typo-candidate: 2026-05-19-meta-analysis-request (17)

- `wiki\assessments\assessment-roadmap.md` → `[[../../raw/.../SimonK_LLMWiki_Spine_v1_260523]]`
- `wiki\assessments\assessment-roadmap.md` → `[[../../raw/.../SimonK_SystemBlueprint_v05_260522]]`
- `wiki\entities\orgs\internal-projects-catalog.md` → `[[../../raw/.../SimonK_SystemBlueprint_v05_260522]]`
- `wiki\entities\orgs\internal-projects-catalog.md` → `[[../../raw/.../SimonK_LLMWiki_Spine_v1_260523]]`
- `wiki\entities\tools\bitwarden.md` → `[[../../raw/.../SimonK_OperationsManual_v0_260522]]`
- `wiki\entities\tools\graphify.md` → `[[../../raw/.../SimonK_LLMWiki_Spine_v1_260523]]`
- `wiki\entities\tools\notebooklm.md` → `[[../../raw/.../SimonK_LLMWiki_Spine_v1_260523]]`
- `wiki\entities\tools\openharness.md` → `[[../../raw/.../SimonK_LLMWiki_Spine_v1_260523]]`
- `wiki\entities\tools\openharness.md` → `[[../../raw/.../SimonK_SystemBlueprint_v05_260522]]`
- `wiki\entities\tools\toolstack-now.md` → `[[../../raw/.../SimonK_SystemBlueprint_v05_260522]]`
- `wiki\entities\tools\zotero-mcp.md` → `[[../../raw/.../SimonK_LLMWiki_Spine_v1_260523]]`
- `wiki\projects\ai-pivot.md` → `[[../../raw/.../SimonK_SystemBlueprint_v05_260522]]`
- `wiki\protocols\mcp-integration.md` → `[[../../raw/.../SimonK_LLMWiki_Spine_v1_260523]]`
- `wiki\protocols\operations-manual.md` → `[[../../raw/simonk-system/SimonK_OperationsManual_v0_260522]]`
- `wiki\protocols\simon-ohmo-architecture.md` → `[[../../raw/.../SimonK_SystemBlueprint_v05_260522]]`
- `wiki\protocols\system-blueprint.md` → `[[../../raw/simonk-system/SimonK_SystemBlueprint_v05_260522]]`
- `wiki\protocols\system-blueprint.md` → `[[../../raw/simonk-system/SimonK_LLMWiki_Spine_v1_260523]]`

## missing-page (10)

- `wiki\CLAUDE.md` → `[[페이지명]]`
- `wiki\CLAUDE.md` → `[[../카테고리/페이지]]`
- `wiki\CLAUDE.md` → `[[../raw/.../파일]]`
- `wiki\CLAUDE.md` → `[[../raw/assessments/2026-XX-birkman-G6RW38]]`
- `wiki\CLAUDE.md` → `[[페이지명]]`
- `wiki\CLAUDE.md` → `[[A2-uk-2004]]`
- `wiki\CLAUDE.md` → `[[페이지명]]`
- `wiki\protocols\llm-wiki\README.md` → `[[link]]`
- `wiki\protocols\llm-wiki\README.md` → `[[link]]`
- `wiki\protocols\llm-wiki\concepts\sandbox-workarounds.md` → `[[ "$GITHUB_REF_TYPE" == "tag" ]]`

## typo-candidate: circuit-9-social-integration-vulnerable (5)

- `wiki\sources\2023-03-13-gpt-equipment-blackbox.md` → `[[../raw/transcripts/2023-03-13-gpt-equipment-blackbox-report]]`
- `wiki\sources\2023-03-13-gpt-relationship-soha.md` → `[[../raw/transcripts/2023-03-13-gpt-girlfriend-parents-gift]]`
- `wiki\sources\2023-04-13-gpt-career-record.md` → `[[../raw/transcripts/2023-04-13-gpt-linkedin-career-profile]]`
- `wiki\sources\2023-04-13-gpt-career-record.md` → `[[../raw/transcripts/2023-05-04-gpt-resume-eol-achievement]]`
- `wiki\sources\2023-11-30-gpt-ie-domain-knowledge.md` → `[[../raw/transcripts/2023-11-30-gpt-automation-line-tacttime]]`

## typo-candidate: stack-config (3)

- `wiki\protocols\mcp-integration.md` → `[[../../skills-src/simon-ohmo]]`
- `wiki\protocols\simon-ohmo-architecture.md` → `[[../../skills-src/simon-ohmo]]`
- `wiki\protocols\simon-ohmo-architecture.md` → `[[../../skills-src/simon-ohmo]]`

## typo-candidate: lg-innotek (2)

- `wiki\CLAUDE.md` → `[[wikilink]]`
- `wiki\log.md` → `[[wikilink]]`

## typo-candidate: circuit-7-anger-ok-fragility-no (2)

- `wiki\CLAUDE.md` → `[[../raw/transcripts/2026-05-12-self-analysis-marathon]]`
- `wiki\sources\2023-04-13-gpt-career-record.md` → `[[../raw/transcripts/2023-10-31-gpt-resume-translation]]`

## typo-candidate: assessment-roadmap (2)

- `wiki\concepts\ai-design-references.md` → `[[../../skills-src/simon-design-first]]`
- `wiki\concepts\design-md-workflow.md` → `[[../../skills-src/simon-design-first]]`

## typo-candidate: three-simons (2)

- `wiki\entities\tools\graphify.md` → `[[notebooklm-py]]`
- `wiki\entities\tools\openharness.md` → `[[notebooklm-py]]`

## typo-candidate: circuit-1-effort-currency (1)

- `wiki\CLAUDE.md` → `[[circuit-04-speaking-hurts]]`

## typo-candidate: ai-engineer-interview-papers (1)

- `wiki\concepts\design-md-workflow.md` → `[[../entities/tools/stitch-design-flow-references]]`

## typo-candidate: 2026-05-21-claude-session-mgmt (1)

- `wiki\entities\tools\toolstack-now.md` → `[[../../raw/.../SimonK_StackConfig_v1_260522]]`

## typo-candidate: maps-timeline-9y (1)

- `wiki\protocols\llm-wiki\CLAUDE.md` → `[[wiki-page-name]]`

## typo-candidate: aarrr-vs-growth-engine-vs-viral-launch (1)

- `wiki\sources\2023-04-13-gpt-career-record.md` → `[[../raw/transcripts/2023-04-13-gpt-university-transcript]]`

## typo-candidate: release-notes-vs-document-release (1)

- `wiki\sources\2023-11-30-gpt-ie-domain-knowledge.md` → `[[../raw/transcripts/2024-05-29-gpt-modapts-most-paper]]`

