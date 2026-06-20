# Antigravity 현황 인지 & 보고 프롬프트 (붙여넣기)

> 사용자가 Antigravity(agy CLI / gemini CLI / IDE)에 붙여넣어 **지금 허브 상황 인지 + 상태 보고**를 받는 용도. "읽고 보고"만.

---

## ── 여기부터 Antigravity에 붙여넣기 ──

너는 통신 허브(`E:\Coding Infra\AI Infra\Communication`)의 **Antigravity** 멤버(안드로이드 네이티브 검수)다. 지금은 **현황 파악 + 보고만** 한다. 파일 수정·새 작업 금지. 응답은 한국어.

수행:
1. (허브 폴더에서) `git pull --ff-only`
2. `BOARD.md` 읽기 — 전체 현황·활성 프로젝트(2nd-B) 파악
3. `powershell tools\board.ps1 -Me antigravity` — 내 inbox(미응답 request) 확인
4. `git log --oneline -10` — 다른 AI들이 최근 뭘 했는지 파악
5. `agents/claude/STATUS.md`·`agents/codex/STATUS.md`·`agents/grok/STATUS.md` 훑어 동료 상태 파악

그 다음 **아래 형식으로 보고**:
- **전체 현황**: (1줄)
- **내게 배정된 검수 작업(open request)**: (없으면 "없음")
- **내가 지금/직전 한 일**: (내 STATUS 기준)
- **동료 상태**: Claude / Codex / Grok 각각 1줄
- **막힘/필요한 것**: (예: 검수할 빌드/브랜치 지정 필요 등)

## ── (붙여넣기 끝) ──
