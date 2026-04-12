# Gstack-Ultraplan-Superpowers

**Claude Code 통합 skill 스택** — Gstack 실행 파이프라인 + simon-stack 방법론·보안·학습 + Superpowers TDD/worktree 철학 + UltraPlan 대형 플래닝을 한 환경에 결합한 skill 라이브러리.

**총 19개 skill 제공** (13 simon-stack + 6 일반 개발 skill). `scripts/install.sh` 한 방으로 Gstack 36 skill 도 자동 설치.

## 한 줄 요약

```
"새 앱 만들고 싶어" → app-dev-orchestrator 가 21단계 파이프라인 자동 진행
"보안 점검"        → security-orchestrator 가 5단계 감사 순차 실행
"TDD 시작"         → simon-tdd 가 RED-GREEN-REFACTOR 강제
"또 틀렸어"        → simon-instincts 가 실수 누적 학습
```

## 설치

### ☁️ Claude Code 웹 (권장 — 자동)

1. https://claude.ai/code 접속
2. 이 레포 열기 (default branch `main`)
3. 세션 시작 시 `.claude/hooks/session-start.sh` 가 자동 실행
4. 30초~1분 뒤 56개 skill 준비 완료

**PC 변경 무관** — 어느 PC에서 Claude Code 웹을 열든 동일한 환경이 재구성됩니다. 집→회사→카페 모두 동일.

자세한 가이드: [docs/MORNING-START.md](docs/MORNING-START.md)

### 💻 로컬 CLI / 데스크탑 (수동)

```bash
git clone https://github.com/learner-thepoorman/Gstack-Ultraplan-superpowers.git
cd Gstack-Ultraplan-superpowers
./scripts/install.sh
```

요구사항: `git`, `bun`, `node ≥ 20`. 자세한 단계는 [docs/INSTALL.md](docs/INSTALL.md)

### 🔁 강제 재설치 (모든 환경)

```bash
rm ~/.claude/.simon-stack-installed
bash <repo>/.claude/hooks/session-start.sh
```

## Skill 카테고리

### 🧭 Orchestrators
- **app-dev-orchestrator** — 신규 앱 21단계 마스터 파이프라인 (office-hours → research → plan → design → TDD → security → ship → deploy → retro → instincts)
- **security-orchestrator** — security-checklist + authz-designer + paid-api-guard + /cso + /codex 순차 실행

### 🔒 Security
- **security-checklist** — RLS / 구독상태 / 이중 RateLimit / 예산한도 4대 감사, 적대적 테스트 5종
- **authz-designer** — RBAC/ABAC/ReBAC 모델 선택 + DDL 템플릿 + IDOR·권한상승 감사
- **paid-api-guard** — 결제·SMS·지도 등 유료 API 6층 방어 + API 설계 리뷰

### 🛠️ Method (방법론)
- **simon-tdd** — RED-GREEN-REFACTOR 강제 + Boris Cherny "검증 도구 제공" 원칙
- **simon-worktree** — 병렬 Claude 세션용 git worktree 격리
- **simon-research** — 플래닝 전 외부 리서치 의무화
- **simon-instincts** — Claude 실수·패턴 누적 학습 시스템

### 🧰 Tools
- **nextjs-optimizer** — Next.js 5대 성능 영역 (이미지·렌더링·분할·스크립트·캐싱)
- **stitch-design-flow** — Google Stitch 웹 UI용 프롬프트 생성기
- **project-claude-md** — 프로젝트별 CLAUDE.md 템플릿 생성

### 📝 일반 개발 (original)
- **commit** · **review** · **debug** · **refactor** · **test-gen** · **explain**

전체 맵 (Gstack 36 포함): [.claude/skills/INDEX.md](.claude/skills/INDEX.md)

## 철학

이 레포는 4가지 오픈소스 아이디어를 하나로 엮는다:

| 출처 | 기여 |
|---|---|
| [Gstack](https://github.com/garrytan/gstack) | 실행 파이프라인 36개 (ship·qa·cso·retro·checkpoint 등) |
| [Superpowers](https://github.com/obra/superpowers) | TDD 사이클 강제, git worktree 격리, 검증 루프 |
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) | instincts 누적 학습, research-first |
| [UltraPlan](https://code.claude.com/docs/en/ultraplan) | Claude Code 대형 플래닝 (CLI 내장 기능) |

**Boris Cherny 원칙** (Claude Code PM) 5가지를 모든 skill 에 내장:
1. Plan 모드 기본
2. 병렬은 worktree 격리
3. 검증 루프 = Claude 가 스스로 확인할 수 있도록 도구 제공
4. `--dangerously-skip-permissions` 금지
5. CLAUDE.md 팀 git 체크인

## 구조

```
.
├── .claude/
│   ├── skills/             # 19개 skill (simon-stack 13 + general 6)
│   │   ├── INDEX.md        # 전체 카테고리 맵
│   │   ├── app-dev-orchestrator/
│   │   ├── security-*/
│   │   ├── simon-*/
│   │   └── ...
│   └── instincts/          # 4개 seed 파일
├── docs/
│   └── INSTALL.md          # 설치 가이드
├── scripts/
│   ├── install.sh          # 설치 스크립트
│   └── session-start-instincts.sh  # SessionStart hook
└── README.md
```

## 라이선스

MIT (이 레포)  · Gstack / Superpowers / ECC 는 각자의 라이선스 준수

## 기여

- 새 skill 추가 시 `.claude/skills/<name>/SKILL.md` + `.claude/skills/INDEX.md` 업데이트
- 실수 발견 시 `.claude/instincts/mistakes-learned.md` 에 append
- PR 은 `main` 대상, Conventional Commits (`feat:`, `fix:`, ...)
