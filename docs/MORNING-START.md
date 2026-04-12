# Morning Start — 4시간 뒤 출근해서 읽을 것

이 환경은 **자동 설치** 되도록 세팅돼 있다. 따라가야 할 단계는 3개뿐.

---

## 🚀 Quick Start (3단계)

### 1. Claude Code 웹 접속
https://claude.ai/code 로 이동

### 2. 이 레포 열기
- `learner-thepoorman/Gstack-Ultraplan-superpowers` (또는 URL 로 직접)
- **default branch 는 `main`** — 이게 최신 상태

### 3. 첫 메시지 보내기
세션 시작 시 `.claude/hooks/session-start.sh` 가 자동 실행돼서:
- Gstack 레포 clone (`~/.claude/skills/gstack/`)
- `bun install` 실행 (Gstack 의존성)
- 36 Gstack skill 을 `~/.claude/skills/` 에 노출
- 13 simon-stack skill 을 `~/.claude/skills/` 에 복사
- 4 instincts seed 파일 설치
- 글로벌 `~/.claude/CLAUDE.md` 설치 (template 기반)

첫 세션 한정 약 30초~1분 소요. 이후 세션은 marker 파일로 즉시 skip.

세션 준비 완료 후 아무 메시지나 보내면 됩니다. 예시:
- `새 앱 만들고 싶어` → `app-dev-orchestrator` 발동 → 21단계 파이프라인 시작
- `보안 감사 해줘` → `security-orchestrator` → 5단계 순차 실행
- `TDD 시작` → `simon-tdd` → RED-GREEN-REFACTOR

---

## ⚠️ 출근 전 한 번만 할 일 (2분)

### (a) GitHub default branch 를 `main` 으로 전환
현재 원격 default 는 `claude/create-claude-skill-Jt63X` 또는 다른 옛 브랜치일 수 있음.

1. https://github.com/Learner-thepoorman/Gstack-Ultraplan-superpowers/settings/branches 열기
2. **Default branch** 섹션에서 드롭다운 → `main` 선택 → `Update`
3. 경고 창 확인 → 진행

왜 필요한가: Claude Code 웹이 default branch 기준으로 레포를 체크아웃하기 때문. `main` 이 default 가 아니면 새 simon-stack skill 과 hook 이 로드되지 않습니다.

### (b) 스테일 브랜치 삭제 (옵션, 청소용)
동일 페이지에서:
- `claude/create-skill-set-BZBaN` — 쓰레기통 아이콘 클릭 (로컬은 이미 삭제됨. 원격은 프록시 403 때문에 CLI 로 못 지웠음)
- `claude/create-claude-skill-Jt63X` — 이미 CLI 로 삭제됨 (로컬/원격 둘 다)

### (c) 노출된 Stitch API 키 로테이션
이전 세션 transcript 에 키가 평문으로 남아있음. Google Stitch 대시보드에서 해당 키 revoke + 신규 발급.

---

## 🎯 사용 시나리오 예시

### 시나리오 1: 새 앱 프로젝트 시작
```
나: "카카오톡 로그인 기반 한국 부동산 매물 크롤링 앱 만들고 싶어"

Claude: [app-dev-orchestrator 발동]
  단계 0. 인터뷰: 플랫폼? 타깃? 레포? 예산?
  단계 1. /office-hours 로 YC 6문 진행
  단계 2. simon-research 로 경쟁 제품 3종 비교
  ...
```

### 시나리오 2: 보안 감사
```
나: "배포 전에 보안 점검 싹 해줘"

Claude: [security-orchestrator 발동]
  Step 1. security-checklist: RLS / 구독 / RateLimit / 예산 4대 감사
  Step 2. authz-designer: IDOR 스캔, 권한 상승 테스트
  Step 3. paid-api-guard: 결제·SMS API 6층 방어 점검
  Step 4. /cso comprehensive: 인프라·시크릿·공급망 감사
  Step 5. /codex challenge: 적대적 리뷰
  → docs/security/<date>-SUMMARY.md 통합 리포트
```

### 시나리오 3: 같은 실수 반복 방지
```
나: "이거 저번에도 그랬잖아"

Claude: [simon-instincts 발동]
  ~/.claude/instincts/mistakes-learned.md 에 즉시 append
  - 날짜 / 증상 / 원인 / 예방책
  다음 세션부터 자동 로드
```

---

## 🧪 동작 확인 (선택)

세션 시작 후 다음으로 설치 성공 여부를 빠르게 확인:

```bash
# Hook 로그
cat /tmp/simon-stack-session-start-*.log

# 설치된 skill 수 (56+ 개여야 함)
ls ~/.claude/skills/ | wc -l

# Gstack 런타임 확인
~/.claude/skills/gstack/bin/gstack-config get telemetry
~/.claude/skills/gstack/bin/gstack-repo-mode

# Instincts 확인
ls ~/.claude/instincts/

# Marker 파일
cat ~/.claude/.simon-stack-installed
```

`simon-` 또는 `app-dev-orchestrator` 같은 키워드를 시스템 reminder 에 포함시키면 발동 준비 완료.

---

## 🔧 문제 해결

### 문제: "skill 이 발동 안 해요"
1. `~/.claude/skills/<skill-name>/SKILL.md` 존재 확인
2. Claude Code 세션 재시작 (hook 재실행)
3. description 에 트리거 키워드가 사용자 메시지와 매칭되는지 확인
4. `permissions.allow` 에 `Skill` 포함됐는지 확인

### 문제: "Gstack 명령어 (`/ship`, `/cso`) 가 작동 안 해요"
1. `~/.claude/skills/gstack/` 디렉토리 존재 확인
2. `~/.claude/skills/gstack/node_modules/` 존재 확인 (bun install 성공)
3. `bun --version` 으로 bun 설치 여부 확인
4. Hook 로그 (`/tmp/simon-stack-session-start-*.log`) 에서 에러 확인

### 문제: "Hook 이 실행 안 해요"
1. `.claude/settings.json` 의 `hooks.SessionStart` 존재 확인
2. `.claude/hooks/session-start.sh` 실행 권한 (`chmod +x`)
3. `.claude/hooks/session-start.sh` 를 수동 실행: `CLAUDE_CODE_REMOTE=true CLAUDE_PROJECT_DIR=$PWD bash .claude/hooks/session-start.sh`
4. Default branch 가 main 인지 확인 (상단 (a) 참조)

### 문제: "강제 재설치 하고 싶어요"
```bash
rm ~/.claude/.simon-stack-installed
bash .claude/hooks/session-start.sh
```

### 문제: "설치 전 상태로 되돌리고 싶어요"
```bash
ls ~/.claude.bak-*    # 백업 디렉토리 목록
rm -rf ~/.claude
mv ~/.claude.bak-<timestamp> ~/.claude
```

---

## 📚 추가 자료

- `README.md` — 레포 overview
- `docs/INSTALL.md` — 수동 설치 가이드 (non-web 환경)
- `.claude/skills/INDEX.md` — 51개 skill 카테고리 맵
- `.claude/instincts/` — 4개 누적 학습 파일
- `templates/CLAUDE.md` — 글로벌 CLAUDE.md 템플릿
- `~/.claude.bak-*` — 설치 전 백업

---

## 🎁 4시간 동안 Claude 가 한 일 요약

- ✅ Gstack 36 skill 런타임 설치 + `bun install`
- ✅ simon-stack 13 skill 생성 (orchestrator · security · method · tools)
- ✅ 4 instincts seed (mistakes · patterns · korean · tool-quirks)
- ✅ `~/.claude/CLAUDE.md` 템플릿 (Boris 원칙 + skill stack 맵)
- ✅ SessionStart hook 2개 — 레포 bootstrap + user instincts 요약
- ✅ `.claude/settings.json` 에 hook 등록
- ✅ `main` 브랜치 생성 + 푸시 + 로컬 stale 브랜치 정리
- ✅ `scripts/install.sh` 수동 설치 스크립트
- ✅ `docs/INSTALL.md`, `README.md`, 이 문서
- ✅ 빈 HOME 에서 end-to-end 설치 시뮬레이션 통과 (56 skills)

**주무시는 동안 수고하셨습니다. 좋은 출근 되세요.** 🌅
