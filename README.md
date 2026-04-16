# SimonK-Stack

> Claude Code 가 "새 앱 만들자", "보안 점검", "TDD 시작", "이거 또 틀렸어" 같은 말을 알아듣고
> **자동으로 올바른 작업 절차를 따르게** 만드는 55개 skill 묶음.

**[simonk-stack.pages.dev](https://simonk-stack.pages.dev)** · [![validator](https://img.shields.io/badge/skill--validator-20%2F20%20PASS-brightgreen)]() [![cases](https://img.shields.io/badge/JSON%20cases-14%2F14%20PASS-brightgreen)]() [![license](https://img.shields.io/badge/license-MIT-blue)]()

---

## 목차

1. [이게 뭔가요?](#이게-뭔가요)
2. [설치](#설치--3가지-방법)
3. [사용 예시](#사용-예시)
4. [Skill 카탈로그](#skill-카탈로그)
5. [작동 원리](#작동-원리)
6. [프로젝트 구조](#프로젝트-구조)
7. [테스트](#테스트)
8. [FAQ](#faq)
9. [크레딧·라이선스](#크레딧)

---

## 이게 뭔가요?

**문제**: AI 코딩 어시스턴트는 큰 작업을 시키면 매번 다른 순서로 일하고, 같은 실수를 반복합니다.

**해결**: 55개 skill (작업 매뉴얼)을 미리 준비해 Claude Code 가 **일관된 절차**를 따르게 합니다.

- `"새 앱 만들자"` → `app-dev-orchestrator` 발동 → 21단계 파이프라인
- `"보안 점검"` → `security-orchestrator` 발동 → 5단계 적대적 감사
- `"이거 또 틀렸어"` → `simon-instincts` 발동 → 실수 기록, 다음 세션에서 자동 회피

**Skill = Claude Code 가 읽는 마크다운 매뉴얼** (`SKILL.md`). "IF 조건이 맞으면 THEN 이 절차를 따라라."

| 계층 | 개수 | 역할 |
|---|---|---|
| **simon-stack** | 20 | 방법론 + 오케스트레이션 (TDD, 보안, 리서치, 학습) |
| **Gstack** | 36 | 실행 파이프라인 (ship, QA, deploy, review) |

---

## 설치 — 3가지 방법

### 방법 1: Claude Code 웹 (제일 쉬움)

1. https://claude.ai/code 접속
2. 이 레포 열기
3. 첫 세션 시작 시 자동 설정 (~30초)

### 방법 2: 로컬 CLI / 데스크탑

```bash
git clone https://github.com/learner-thepoorman/Gstack-Ultraplan-superpowers.git
cd Gstack-Ultraplan-superpowers
./scripts/install.sh
```

### 방법 3: 다른 프로젝트에 vendoring

```bash
cd /path/to/your-project
/path/to/Gstack-Ultraplan-superpowers/scripts/setup-repo.sh .
git add .claude/ && git commit -m "chore(claude): add simon-stack"
```

상세: [docs/USING-IN-OTHER-REPOS.md](docs/USING-IN-OTHER-REPOS.md)

---

## 사용 예시

### 새 앱 만들기
```
나: "한국 부동산 매물 검색 웹 앱 만들고 싶어"

Claude: [app-dev-orchestrator 발동]
  → 인터뷰 → /office-hours → simon-research → /plan-ceo-review
  → 디자인 → TDD 구현 → 보안 감사 → 배포 → 회고
```

### 보안 감사
```
나: "배포 전에 전체 보안 점검 해줘"

Claude: [security-orchestrator 발동]
  → RLS 점검 → IDOR 스캔 → 결제 API 방어 → 인프라 감사 → 적대적 리뷰
  → docs/security/<date>-SUMMARY.md 통합 리포트
```

### 실수 반복 방지
```
나: "이거 저번에도 그랬어. grep -c 는 매치 0건일 때 exit 1 이야."

Claude: [simon-instincts 발동]
  → ~/.claude/instincts/tool-quirks.md 에 기록
  → 다음 세션부터 자동 회피
```

---

## Skill 카탈로그

### Simon-stack — Orchestrators (2)

| Skill | 트리거 | 역할 |
|---|---|---|
| `app-dev-orchestrator` | "새 앱 만들자", "MVP 기획" | 21단계 앱 개발 파이프라인 |
| `security-orchestrator` | "보안 점검", "security audit" | 5단계 보안 감사 → 통합 리포트 |

### Simon-stack — Security (3)

| Skill | 트리거 | 역할 |
|---|---|---|
| `security-checklist` | "RLS 확인", "rate limit 점검" | 4대 영역 적대적 테스트 + SQL drop-in |
| `authz-designer` | "권한 시스템 설계", "RBAC" | RBAC/ABAC/ReBAC 선택 + DDL + IDOR 감사 |
| `paid-api-guard` | "Stripe 연동", "결제 API 보안" | 유료 API 6층 방어 체크리스트 |

### Simon-stack — Method (4)

| Skill | 트리거 | 역할 |
|---|---|---|
| `simon-tdd` | "이 기능 구현해줘", "버그 고쳐줘" | RED→GREEN→REFACTOR + 검증 루프 |
| `simon-worktree` | "병렬 작업", "parallel agents" | git worktree 격리 |
| `simon-research` | "리서치 해줘", "기술 비교" | 외부 리서치 의무화 → dated 문서 |
| `simon-instincts` | "이거 또 틀렸어", "기록해둬" | 실수 누적 → 4파일 자동 로드 |

### Simon-stack — Tools (3)

| Skill | 트리거 | 역할 |
|---|---|---|
| `nextjs-optimizer` | "Next.js 최적화", "LCP 개선" | 5대 성능 영역 감사 |
| `stitch-design-flow` | "디자인 시안", "Stitch 프롬프트" | DESIGN.md → Safe/Bold/Wild 프롬프트 |
| `project-context-md` | "CLAUDE.md 만들어줘" | 프로젝트 CLAUDE.md 생성/갱신 |

### Simon-stack — Meta (2)

| Skill | 트리거 | 역할 |
|---|---|---|
| `skill-gen-agent` | "스킬 만들어줘", "validate skill" | Skill 생성·검증·테스트 도구 |
| `context-guardian` | "세션 복구", "context 위험해" | 컨텍스트 고갈 예방/모니터링/복구 |

### Simon-stack — General Dev (6)

| Skill | 트리거 | 산출물 |
|---|---|---|
| `commit` | "커밋해줘" | Conventional Commits |
| `debug` | "버그 고쳐줘" | 근본 원인 진단 + 수정 |
| `explain` | "이 코드 설명해줘" | entry point, 데이터 플로우 |
| `refactor` | "리팩토링" | 동작 보존 구조 개선 |
| `review` | "리뷰해줘" | blocker/major/minor/nit |
| `test-gen` | "테스트 작성" | 골든 패스 + 엣지 + 에러 |

### Gstack (36) — 실행 파이프라인

| 카테고리 | Skills |
|---|---|
| **플래닝** (6) | `/office-hours` `/plan-ceo-review` `/plan-eng-review` `/plan-design-review` `/plan-devex-review` `/autoplan` |
| **디자인** (4) | `/design-consultation` `/design-shotgun` `/design-review` `/design-html` |
| **구현·QA** (6) | `/qa` `/qa-only` `/review` `/benchmark` `/health` `/codex` |
| **배포** (5) | `/ship` `/land-and-deploy` `/canary` `/setup-deploy` `/document-release` |
| **보안·품질** (6) | `/cso` `/careful` `/guard` `/freeze` `/unfreeze` `/retro` |
| **리서치·DX** (4) | `/investigate` `/browse` `/learn` `/devex-review` |
| **기타** (5) | `/checkpoint` `/pair-agent` `/setup-browser-cookies` `/open-gstack-browser` `/gstack-upgrade` |

각 skill 의 상세 알고리즘: **[docs/SKILL-REFERENCE.md](docs/SKILL-REFERENCE.md)**

---

## 작동 원리

### SessionStart Hook

```
세션 시작 → .claude/hooks/session-start.sh 실행
  ├─ Gstack clone + bun install (첫 실행만, ~30초)
  ├─ skills-src/ + .claude/skills/ → ~/.claude/skills/ 복사
  ├─ Instincts 4파일 seed
  └─ ~/.claude/CLAUDE.md 템플릿 설치
  → marker 기록 (재실행 시 skip, <1초)
```

**속성**: Idempotent · Synchronous · Self-healing

### Instincts 학습 시스템

```
세션 1: Claude 실수 → 사용자 지적 → ~/.claude/instincts/ 에 기록
세션 2: 자동 로드 → 같은 실수 회피
세션 N: 수십 개 누적 → Claude 품질 세션마다 향상
```

4파일: `mistakes-learned.md` · `project-patterns.md` · `korean-context.md` · `tool-quirks.md`

### 토큰 최적화 구조 (v1.3)

```
skills-src/     ← 배포용 16개 skill (Claude Code 미로딩)
.claude/skills/ ← 개발용 4개만 (commit, review, skill-gen-agent, context-guardian)
```

`.claude/skills/`에 skill 이 많으면 매 tool call 마다 모든 description 이 system-reminder 로
주입되어 토큰이 폭발합니다. `skills-src/`로 분리하면 개발 중 토큰이 극적으로 줄어듭니다.
설치 시 hook 이 양쪽 모두 `~/.claude/skills/`로 복사.

---

## 프로젝트 구조

```
skills-src/                  ← 배포용 skill 소스 (16개)
├── app-dev-orchestrator/
├── simon-tdd/
├── security-orchestrator/
└── ...

.claude/
├── hooks/session-start.sh   ← 매 세션 bootstrap
├── settings.json
├── instincts/               ← 학습 4파일 seed
└── skills/                  ← 개발용 (4개만)
    ├── commit/
    ├── review/
    ├── skill-gen-agent/     ← validator
    └── context-guardian/

site/                        ← 랜딩 페이지 (simonk-stack.pages.dev)
├── index.html
├── skills.html
└── style.css

docs/                        ← INSTALL, MORNING-START, SKILL-REFERENCE, USING-IN-OTHER-REPOS
scripts/                     ← install.sh, setup-repo.sh
templates/                   ← CLAUDE.md, bootstrap-*.sh
```

---

## 테스트

| 테스트 | 결과 | 도구 |
|---|---|---|
| Static validation | **20/20 PASS** | `validate_skill.py` |
| JSON dry-run | **12/12 PASS** | `test_skill.py --dry-run` |
| Trigger probe | **13/13 PASS** | description 키워드 매칭 |
| Runtime smoke | **24/24 PASS** | Script 실행 + Bash 문법 + JSON 파싱 |
| **총합** | **69/69** | |

재현:
```bash
# 전체 skill 검증
for d in skills-src/*/ .claude/skills/*/; do
  [ -f "${d}SKILL.md" ] || continue
  python3 .claude/skills/skill-gen-agent/scripts/validate_skill.py "${d%/}" 2>&1 | grep Result
done

# Bash 문법
for f in scripts/*.sh .claude/hooks/*.sh skills-src/*/scripts/*.sh; do
  [ -f "$f" ] || continue; bash -n "$f" && echo "OK: $f"
done
```

---

## FAQ

**Q. Gstack 이 뭐예요?**
[garrytan/gstack](https://github.com/garrytan/gstack) — 실행 파이프라인 36 skill. simon-stack 은 방법론만 정의하고 실행은 Gstack 에 위임.

**Q. Skill 이 발동 안 해요**
1. 트리거 키워드 미매칭 → 더 구체적으로 말하거나 skill 이름 명시
2. Hook 미실행 → `.claude/settings.json` 확인, `cat /tmp/simon-stack-*.log`
3. Feature 브랜치 → main 에 병합 필요 (웹은 default branch 로드)

**Q. 다른 repo 에서 쓰려면?**
`scripts/setup-repo.sh /path/to/target` — vendor (기본, 자체 포함) 또는 bootstrap (2파일 drop-in) 모드. 상세: [docs/USING-IN-OTHER-REPOS.md](docs/USING-IN-OTHER-REPOS.md)

**Q. 한국어로만 말해도 되나요?**
네. 모든 skill description 에 한/영 트리거 병기. Instincts 도 한국어.

**Q. 업데이트는?**
```bash
cd Gstack-Ultraplan-superpowers && git pull && ./scripts/install.sh
```

**Q. 제거하려면?**
```bash
rm -rf ~/.claude/skills/{app-dev-orchestrator,security-orchestrator,...}
rm ~/.claude/.simon-stack-installed
```

---

## 크레딧

| 출처 | 기여 |
|---|---|
| [Gstack](https://github.com/garrytan/gstack) — garrytan | 실행 파이프라인 36 skill |
| [Superpowers](https://github.com/obra/superpowers) — obra | TDD, worktree, 검증 루프 |
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) — affaan-m | Instincts 학습, research-first |
| [Skill-Agent](https://github.com/Learner-thepoorman/Skill-Agent) | validate_skill.py 검증 도구 |
| [Impeccable](https://github.com/pbakaus/impeccable) — pbakaus | AI Slop 방지 디자인 원칙 |
| [Supanova Design Skill](https://github.com/uxjoseph/supanova-design-skill) — uxjoseph | 프리미엄 랜딩 페이지 프레임워크 |

**Boris Cherny 5원칙** 전 skill 내장: Plan 모드 기본 · 병렬은 worktree · 검증 루프=도구 제공 · skip-permissions 금지 · CLAUDE.md 팀 체크인

## 라이선스

[MIT](LICENSE). 상업적 사용·수정·배포 자유.

---

**웹사이트**: [simonk-stack.pages.dev](https://simonk-stack.pages.dev) ·
**상세 skill 문서**: [docs/SKILL-REFERENCE.md](docs/SKILL-REFERENCE.md) ·
**설치 가이드**: [docs/INSTALL.md](docs/INSTALL.md) ·
**다른 repo 사용**: [docs/USING-IN-OTHER-REPOS.md](docs/USING-IN-OTHER-REPOS.md)
