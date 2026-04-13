# 다른 레포·세션에서 simon-stack 사용하기

4 가지 시나리오를 커버합니다. 상황에 맞는 섹션으로 바로 이동하세요.

## 시나리오 결정 트리

```
Claude Code 어디서 쓰고 있나요?
├── 💻 데스크탑 / CLI (로컬 PC)
│   └── → §1. 로컬 글로벌 설치 (한 번만 하면 평생)
│
└── ☁️ 웹 (claude.ai/code)
    │
    ├── 이 레포(Gstack-Ultraplan-superpowers)에서 작업
    │   └── → §2. 자동 동작 (아무것도 안 해도 됨)
    │
    └── 다른 레포에서 simon-stack 을 쓰고 싶음
        │
        ├── 이 simon-stack 레포가 public?
        │   ├── YES → §3. Bootstrap 모드 (2-file drop-in, 가벼움)
        │   └── NO  → §4. Vendor 모드 (파일 embed, 권장)
```

---

## §1. 로컬 데스크탑 / CLI (일회성 설치)

Claude Code 데스크탑 앱, VSCode extension, 또는 CLI (`claude` 명령어) 를 쓰는 경우. `~/.claude/` 가 **영구 저장**이므로 한 번 설치하면 모든 프로젝트에서 쓸 수 있습니다.

```bash
# 1. 레포 clone
git clone https://github.com/Learner-thepoorman/Gstack-Ultraplan-superpowers.git
cd Gstack-Ultraplan-superpowers

# 2. 글로벌 설치
./scripts/install.sh

# 3. Claude Code 재시작 → 끝
```

이후 어느 프로젝트에서 Claude Code 를 열든 49+ skill 자동 사용 가능. 제거는 `~/.claude.bak-*` 백업에서 복원.

**업데이트**: 새 버전이 나오면 `cd <this-repo> && git pull && ./scripts/install.sh` 재실행 (idempotent, 안전).

---

## §2. Claude Code 웹에서 이 레포 (자동)

https://claude.ai/code → `learner-thepoorman/Gstack-Ultraplan-superpowers` 열기 → **끝**.

매 세션 시작 시 `.claude/hooks/session-start.sh` 가 자동 실행돼서 simon-stack + Gstack 을 `~/.claude/` 에 bootstrap 합니다 (첫 세션 30초~1분, 이후 marker 로 skip).

아무것도 안 해도 됩니다. 세션 시작 후 바로 `"새 앱 만들고 싶어"` 같은 요청을 보내면 `app-dev-orchestrator` 가 발동합니다.

---

## §3. Claude Code 웹 / 다른 레포 / Bootstrap 모드

**상태**: ✅ **이 레포가 public 으로 전환돼 즉시 사용 가능** (2026-04-13 검증됨)

Claude Code 웹 sandbox 가 `git clone -b main https://github.com/Learner-thepoorman/Gstack-Ultraplan-superpowers` 을 auth 없이 성공.

### 설치

target 레포에서 (simon-stack 을 쓰고 싶은 프로젝트):

```bash
# Option A: simon-stack repo 가 로컬에 있는 경우
cd /path/to/target-repo
/path/to/Gstack-Ultraplan-superpowers/scripts/setup-repo.sh --mode bootstrap .

# Option B: curl 스트림
curl -sSL https://raw.githubusercontent.com/Learner-thepoorman/Gstack-Ultraplan-superpowers/main/scripts/setup-repo.sh | bash -s -- --mode bootstrap
```

생성되는 파일 2개:
```
<target-repo>/
├── .claude/
│   ├── hooks/
│   │   └── session-start.sh     ← simon-stack 를 매 세션 clone 하는 bootstrap
│   └── settings.json            ← hook 등록
```

### 커밋 + 사용
```bash
git add .claude/
git commit -m "chore(claude): add simon-stack bootstrap"
git push
```

### 커스텀 fork 사용
```bash
# Env var 로 override
SIMON_STACK_REPO=https://github.com/you/your-fork \
SIMON_STACK_REF=main \
./scripts/setup-repo.sh --mode bootstrap /path/to/target
```

또는 hook 스크립트 상단의 default 값 직접 편집.

### 장단점
| 장점 | 단점 |
|---|---|
| Target 레포가 **2 파일만** 추가 (깔끔) | simon-stack 레포가 **public** 이어야 함 |
| simon-stack 업데이트 자동 흡수 | 매 세션 git clone 네트워크 호출 (~5s) |
| 여러 target repo 에서 한 simon-stack 공유 | simon-stack breaking change 시 예고 없이 깨짐 |

---

## §4. Claude Code 웹 / 다른 레포 / Vendor 모드 (권장 기본값)

simon-stack 레포가 private 이거나, 네트워크 의존성 없이 self-contained 하고 싶을 때. **19개 skill 파일을 target 레포에 직접 copy**.

### 설치

```bash
cd /path/to/Gstack-Ultraplan-superpowers
./scripts/setup-repo.sh /path/to/target-repo
# (default 가 --mode vendor)
```

target 레포에 복사되는 것:

```
<target-repo>/
├── .claude/
│   ├── hooks/
│   │   └── session-start.sh      ← vendored hook (simon-stack 을 target 내부에서 읽음)
│   ├── settings.json
│   ├── skills/                   ← 19개 simon-stack skill 전체
│   │   ├── INDEX.md
│   │   ├── app-dev-orchestrator/
│   │   ├── security-orchestrator/
│   │   ├── security-checklist/
│   │   ├── authz-designer/
│   │   ├── paid-api-guard/
│   │   ├── simon-tdd/
│   │   ├── simon-worktree/
│   │   ├── simon-instincts/
│   │   ├── simon-research/
│   │   ├── nextjs-optimizer/
│   │   ├── stitch-design-flow/
│   │   ├── project-claude-md/
│   │   └── (기존 6: commit, review, debug, refactor, test-gen, explain)
│   ├── instincts/                ← 4 seed 파일
│   └── CLAUDE.md.template        ← 글로벌 CLAUDE.md 템플릿
```

### 세션 시작 동작
매 세션 hook 이 실행되면:
1. Gstack 을 `github.com/garrytan/gstack` 에서 clone (public 레포라 auth 불필요)
2. `bun install` 실행
3. target 레포의 `.claude/skills/*` 를 `~/.claude/skills/` 로 복사
4. 56+ skill 사용 가능

### 커밋 + 사용
```bash
cd /path/to/target-repo
git status
# .claude/hooks/session-start.sh
# .claude/settings.json
# .claude/skills/ (19 dirs)
# .claude/instincts/ (4 files)
# .claude/CLAUDE.md.template

git add .claude/
git commit -m "chore(claude): add simon-stack (vendor)"
git push
```

### 업데이트
새 simon-stack 버전이 나오면 target repo 에서:
```bash
cd /path/to/Gstack-Ultraplan-superpowers && git pull
cd /path/to/target-repo
/path/to/Gstack-Ultraplan-superpowers/scripts/setup-repo.sh .
# 기존 파일 skip, 새 파일만 추가됨
```

수정된 skill 을 덮어쓰려면 해당 디렉토리 삭제 후 재실행.

### 장단점
| 장점 | 단점 |
|---|---|
| **네트워크 독립** — simon-stack repo private 여도 OK | Target 레포 size 증가 (~19 SKILL.md 파일) |
| 예측 가능한 버전 (lockfile 역할) | 수동 업데이트 필요 |
| simon-stack breaking change 로부터 격리 | 여러 repo 에서 공유 시 중복 저장 |

---

## §5. Troubleshooting

### Hook 이 안 돌아요
```bash
# 1. Hook 실행 권한 확인
ls -la .claude/hooks/session-start.sh

# 2. 수동 실행
CLAUDE_CODE_REMOTE=true CLAUDE_PROJECT_DIR=$PWD bash .claude/hooks/session-start.sh

# 3. settings.json 검증
cat .claude/settings.json | python3 -m json.tool

# 4. Default branch 에 커밋·푸시됐는지 확인
git log origin/$(git symbolic-ref --short HEAD) -1 -- .claude/
```

### Hook 은 돌아가는데 skill 발동 안 해요
```bash
# 1. Global skill 디렉토리 확인
ls ~/.claude/skills/ | wc -l   # 50+ 기대

# 2. Marker 확인
cat ~/.claude/.simon-stack-installed

# 3. 강제 재설치
rm ~/.claude/.simon-stack-installed
bash .claude/hooks/session-start.sh
```

### simon-stack 업데이트를 받고 싶어요
- **Bootstrap 모드**: 자동 (매 세션 `git pull` 됨)
- **Vendor 모드**: 수동 (`setup-repo.sh` 재실행)
- **로컬 글로벌**: `cd <simon-stack-repo> && git pull && ./scripts/install.sh`

### 두 모드를 섞어 쓰면?
target repo 에 bootstrap + vendor 둘 다 설치되면 hook 충돌. 하나만 사용.

---

## 요약 표

| 환경 | 방법 | 네트워크 | 파일 수 | 업데이트 |
|---|---|---|---|---|
| Desktop / CLI (로컬) | `install.sh` | 첫 설치만 | 전역 `~/.claude/` | 수동 `git pull` |
| 웹, 이 레포 | 자동 (이미 됨) | 매 세션 (Gstack) | N/A | 자동 |
| 웹, 타 레포, public fork | §3 Bootstrap | 매 세션 x2 | 2 | 자동 |
| 웹, 타 레포, 일반 (권장) | §4 Vendor | 매 세션 (Gstack) | 24+ | 수동 |

---

## 관련 문서

- [INSTALL.md](INSTALL.md) — 로컬 데스크탑 설치 상세
- [MORNING-START.md](MORNING-START.md) — 빠른 시작 가이드
- [.claude/skills/INDEX.md](../.claude/skills/INDEX.md) — skill 카테고리 맵
