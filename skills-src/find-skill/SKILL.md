---
name: find-skill
description: >
  Use when the user wants to find an existing skill for a task instead of writing one — triggers "스킬 찾아", "스킬 검색", "이런 거 하는 스킬 있어?", "X 하는 스킬", "find a skill", "search skills", "is there a skill for", or /find-skill. Searches two catalogs in parallel — the local simon-stack INDEX.md (hardcoded at C:/Users/202502/.claude/skills/INDEX.md) and the external ComposioHQ/awesome-claude-skills GitHub README (64k★, 1000+ skills) — ranks hits by trigger-phrase overlap, and produces a ranked recommendation list (skill name, why it matched, how to invoke). Prefers an already-installed local skill; only surfaces external skills when no local equivalent exists. Different from manual INDEX.md browsing (this is keyword-ranked) and from /skill-gen-agent (which creates new skills — this finds existing ones).
version: 1.1.0
allowed-tools:
  - Read
  - Grep
  - Bash
  - WebFetch
compatibility: [claude-code]
---

# find-skill

사용자가 원하는 기능을 가진 skill 을 **두 카탈로그 동시 검색**으로 찾아 랭킹 추천한다.
로컬 설치본(simon-stack)을 우선 추천하고, 없을 때만 외부 카탈로그를 surface 한다.

## When to use / boundaries

발동:
- Korean: "스킬 찾아", "스킬 검색", "이런 거 하는 스킬 있어?", "PDF 합치는 스킬 있나"
- English: "find a skill", "search skills", "is there a skill for X"
- Slash: `/find-skill <keyword>`

**경계 (사용하지 말 것):**
- 새 skill **생성** → `/skill-gen-agent` (이건 기존 것만 찾음)
- INDEX.md 전체 수동 열람 → 그냥 Read (이건 키워드 랭킹)
- 어떤 skill 을 **실행**할지 이미 안다 → 바로 Skill 툴로 호출

## 두 카탈로그 (하드코딩 경로/URL)

| 카탈로그 | 위치 | 검색 도구 |
|---|---|---|
| **로컬 simon-stack** | `C:/Users/202502/.claude/skills/INDEX.md` | Grep (오프라인, 즉시) |
| **외부 awesome-claude-skills** | `https://raw.githubusercontent.com/ComposioHQ/awesome-claude-skills/master/README.md` | WebFetch (64k★, 1000+ skills) |

외부 README 포맷은 bullet list — 각 줄이 `- 대괄호name소괄호link 대시 description` 꼴 (예: ``- docx - Create, edit Word docs``) — 이며 `## Document Processing`, `## Development & Code Tools`, `## Business & Marketing` 등 카테고리 H2 로 묶임.

## Workflow

### 1. 사용자 의도 → 검색어 추출

자연어 요청에서 2~4개 키워드 + 동의어로 확장한다. 한/영 양쪽 검색어를 만든다.

```
요청: "이메일 자동으로 보내는 스킬 있어?"
검색어: email|이메일|mail|smtp|resend|sendgrid|notification|알림
```

### 2. 로컬 INDEX.md 검색 (먼저, 오프라인)

대소문자 무시 + OR 패턴으로 한 번에 grep 한다.

```bash
grep -niE "email|이메일|mail|smtp|notification|알림|push" \
  "C:/Users/202502/.claude/skills/INDEX.md"
```

매칭 라인이 나오면 해당 skill 폴더의 SKILL.md frontmatter `description` 으로 트리거 문구를 확인한다.

```bash
# 후보 skill 의 실제 트리거/설명 확인
grep -A2 -m1 "^description:" \
  "C:/Users/202502/.claude/skills/growth-engine/SKILL.md"
```

설치 여부는 폴더 존재로 검증한다.

```bash
ls -d "C:/Users/202502/.claude/skills/growth-engine" 2>/dev/null \
  && echo "INSTALLED" || echo "NOT_INSTALLED"
```

### 3. 외부 카탈로그 검색 (병렬, 로컬 미스 보강용)

WebFetch 로 README 를 가져오되 prompt 에 검색어를 박아 모델이 직접 필터하게 한다(1000+ 줄이라 전량 회수는 토큰 낭비).

```
WebFetch(
  url="https://raw.githubusercontent.com/ComposioHQ/awesome-claude-skills/master/README.md",
  prompt="List every skill whose name OR description mentions any of:
          email, mail, smtp, notification, newsletter. For each, output the
          exact bullet line (name, link, and description). If none, say NONE."
)
```

WebFetch 가 막히면(네트워크/404) gh API 폴백:

```bash
gh api repos/ComposioHQ/awesome-claude-skills/contents --jq '.[].name' \
  | grep -iE "email|mail|comm|notif"
```

### 4. 랭킹 (trigger-match 휴리스틱)

각 후보에 점수를 매겨 내림차순 정렬한다. **로컬 설치본에 +2 가산** (이미 있으니 즉시 사용 가능).

| 신호 | 점수 |
|---|---|
| 검색어가 skill **이름**에 등장 | +3 |
| 검색어가 frontmatter `description`/트리거 문구에 등장 | +2 (당 1회) |
| 로컬에 **이미 설치됨** | +2 |
| 카테고리(H2)만 일치, 직접 언급 없음 | +1 |
| 사용자 도메인(제조/IE·앱) 인접 | +1 |

동점이면 로컬 > 외부, 좁은 범위 > 광범위 순.

### 5. 출력 포맷 (랭킹된 추천)

상위 3~5개만. 각 항목 3요소 고정: **이름 · 왜 매칭(근거) · 호출법**.

```
1. growth-engine  [로컬·설치됨·score 7]
   왜: description 에 "이메일 시스템(Resend/SendGrid)" + "푸시 알림(OneSignal/FCM)" 명시 — 요청과 직격.
   호출: Skill 툴 growth-engine  또는  대화에 "이메일 시스템 세팅"

2. analytics-integrator  [로컬·설치됨·score 4]
   왜: 알림/이벤트 추적 인접. 직접 메일 발송은 아님.
   호출: Skill 툴 analytics-integrator

— 외부 (로컬 미설치 기능) —
3. [Slack Automation](https://github.com/ComposioHQ/awesome-claude-skills/tree/master/...) [외부·score 5]
   왜: 메시지/스케줄링 자동화. 로컬 등가물 없음.
   호출: 미설치 → 설치하려면 /skill-gen-agent 로 포팅하거나 repo 에서 clone.
```

로컬 등가물이 있으면 외부는 **참고로만** 보이고 로컬 사용을 권한다.

### 6. 결과 없음 처리

양쪽 모두 미스면 추측으로 지어내지 말고 명시한다.

```
"email 자동발송" 매칭 skill 없음 (로컬·외부 둘 다 0건).
→ 신규 생성: /skill-gen-agent 로 만들 수 있음.
→ 또는 인접: growth-engine 이 메일 인프라를 다룸 — 그걸로 충분한지 확인 필요.
```

## 검증

추천이 환각이 아님을 사용자가 직접 확인할 수 있게 한다.

```bash
# 1. 추천한 로컬 skill 이 실제 존재하는가
for s in growth-engine analytics-integrator; do
  ls -d "C:/Users/202502/.claude/skills/$s" >/dev/null 2>&1 \
    && echo "OK  $s" || echo "MISSING  $s (추천에서 제거)"
done

# 2. INDEX.md 에 카탈로그돼 있는가
grep -c "growth-engine" "C:/Users/202502/.claude/skills/INDEX.md"

# 3. 외부 링크가 살아있는가 (HTTP 200)
gh api repos/ComposioHQ/awesome-claude-skills >/dev/null 2>&1 \
  && echo "external repo reachable"
```

MISSING 으로 찍힌 항목은 출력에서 즉시 뺀다.

## Anti-patterns

- ❌ INDEX.md 안 읽고 기억으로 skill 이름 추천 → 환각·오타. **항상 grep 으로 실재 확인.**
- ❌ 외부 README 전문을 WebFetch 로 통째 회수 → 1000+ 줄 토큰 폭발. **prompt 에 필터를 박아라.**
- ❌ 외부 skill 을 "설치됨"인 양 호출 안내 → 로컬에 없으면 Skill 툴로 안 불림. 설치 경로 명시.
- ❌ 로컬 등가물 있는데 외부부터 추천 → 로컬 +2 가산 원칙 위반.
- ❌ 동의어 확장 생략(한글만/영어만) → 절반 누락. 한·영 양쪽 검색.
- ❌ score 0건인데 억지 추천 → "없음 + 신규 생성 경로"로 정직하게.

## Related skills

- `/skill-gen-agent` — 매칭 없을 때 새 skill 생성
- `/stack-update` — INDEX.md·skill 카탈로그 최신화
- `app-dev-orchestrator` · `dev-orchestrator` — 찾은 skill 들을 파이프라인으로 엮음
