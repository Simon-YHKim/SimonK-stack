#!/usr/bin/env bash
# user-prompt-submit.sh — UserPromptSubmit hook.
# Injects a compact wiki context summary into the LLM's system context so the
# LLM is always aware of accumulated patterns and the session-start policy,
# without the user having to mention them.
#
# Cost: ~300-500 tokens per turn. Kept minimal by emitting only the index
# section + 3 most recent log entries + M/T totals.

set -uo pipefail

# Read & ignore stdin (UserPromptSubmit JSON with the user_prompt etc.)
cat >/dev/null 2>&1 || true

# Locate wiki. Try (in order): env override, SimonK sibling, standard home,
# container default, /home/user fallback. Hook may run under different UIDs
# (root in containers, user locally) so we don't trust $HOME alone.
WIKI=""
PROJ_PARENT=""
[ -n "${CLAUDE_PROJECT_DIR:-}" ] && PROJ_PARENT=$(dirname "$CLAUDE_PROJECT_DIR")
for candidate in \
  "${SIMON_WIKI_DIR:-}" \
  "${SIMON_WIKI_DIR:-}/Simon-LLM-Wiki" \
  "$PROJ_PARENT/Simon-LLM-Wiki" \
  "$HOME/.claude/wiki/Simon-LLM-Wiki" \
  "$HOME/Simon-LLM-Wiki" \
  "/home/user/Simon-LLM-Wiki" \
  "/root/Simon-LLM-Wiki"; do
  [ -z "$candidate" ] && continue
  if [ -d "$candidate" ] && [ -f "$candidate/LESSONS_LEARNED.md" ]; then
    WIKI="$candidate"; break
  fi
done
[ -n "$WIKI" ] || exit 0

LESSONS="$WIKI/LESSONS_LEARNED.md"
LOG="$WIKI/wiki/log.md"
M_FILE="$WIKI/wiki/concepts/recurring-mistakes.md"

# Only emit if wiki actually has content (avoid noise in fresh setups)
[ -f "$LESSONS" ] || exit 0

{
  echo "## 📚 SimonK Wiki — auto-injected context (UserPromptSubmit hook)"
  echo ""
  echo "다음은 누적 학습. **이번 응답에 반영하고, 새 mistake/시행착오 발견 시 wiki 에 append 한 뒤 응답 종료 (Stop hook 이 자동 commit/push).**"
  echo ""

  # 5-second index (top of LESSONS_LEARNED)
  if grep -q '5초 인덱스' "$LESSONS" 2>/dev/null; then
    echo "### 인덱스"
    awk '/^## 📚 5초 인덱스/{flag=1; next} flag && /^---$/{exit} flag' "$LESSONS" | head -15
    echo ""
  fi

  # Recent log
  if [ -f "$LOG" ]; then
    echo "### 최근 wiki 활동"
    grep "^## \[" "$LOG" 2>/dev/null | tail -3
    echo ""
  fi

  # M/T totals
  M_COUNT=0
  [ -f "$M_FILE" ] && M_COUNT=$(grep -c "^## M-[0-9]" "$M_FILE" 2>/dev/null || echo 0)
  T_COUNT=0
  [ -f "$LESSONS" ] && T_COUNT=$(grep -oE "T-[0-9]{3}" "$LESSONS" 2>/dev/null | sort -u | wc -l | tr -d ' ')
  echo "### 누적 코드"
  echo "- M-codes: $M_COUNT (recurring mistakes) — see wiki/concepts/recurring-mistakes.md"
  echo "- T-codes: $T_COUNT (trials/conclusions) — see LESSONS_LEARNED.md"
  echo ""
  echo "**행동 규칙**:"
  echo "1. 사용자 발화에서 _반복되는 mistake_ 또는 _시행착오 + 결론_ 감지 시 wiki 즉시 append (Edit/Write tool)."
  echo "2. M/T code 번호는 연속. 다음 빈 번호 사용."
  echo "3. 응답 끝에 별도 commit 안 해도 됨 — Stop hook 이 자동 처리."
} 2>/dev/null

exit 0
