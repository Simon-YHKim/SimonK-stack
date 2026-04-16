# CLAUDE.md — Global Claude Code Instructions

이 파일은 모든 Claude Code 세션에 전역으로 적용되는 지침이다.
프로젝트별 지침은 각 레포의 `CLAUDE.md` 에 둔다 (이 파일과 함께 로드됨).

## Instincts (auto-loaded)

세션 시작 시 아래 4개 파일을 참조하여 누적 학습을 활용한다. 같은 실수는 반복하지 않는다.

- See `~/.claude/instincts/mistakes-learned.md` — Claude 가 저지른 실수 누적 로그
- See `~/.claude/instincts/project-patterns.md` — 프로젝트별 관용·제약
- See `~/.claude/instincts/korean-context.md` — 한국어·한국 서비스 특이사항
- See `~/.claude/instincts/tool-quirks.md` — Claude Code·CLI 도구 함정

사용자가 "저번에도 그랬어", "이거 반복이야", "또 틀렸어" 라고 지적하면
**즉시** `simon-instincts` 스킬로 해당 파일에 append.

---

## Boris Cherny — Claude Code 핵심 원칙

1. **Plan 모드 기본**: 세션 시작은 항상 Plan 모드. 실행 전 사용자 승인.
2. **병렬은 worktree**: 병렬 Claude 세션 시 반드시 `git worktree` 로 격리. `simon-worktree` 참조.
3. **검증 루프 = 도구 제공**: Claude 가 스스로 "잘 됐나?" 확인할 수 있도록 서버 URL, 브라우저, 테스트 명령 명시.
4. **Permissions allowlist**: `--dangerously-skip-permissions` 금지. `/permissions` 로 allowlist 관리.
5. **CLAUDE.md 팀 체크인**: 프로젝트 `CLAUDE.md` 는 git 에 포함. PR 마다 갱신.

---

## Skill Stack 진입점

이 환경에는 3계층 skill 이 설치돼 있다:

### 1. Gstack (36개) — 실행 파이프라인
- **플래닝**: `/office-hours`, `/plan-ceo-review`, `/plan-eng-review`, `/autoplan`
- **디자인**: `/design-consultation`, `/design-shotgun`, `/design-review`, `/design-html`
- **구현**: `/ship`, `/review`, `/qa`, `/benchmark`, `/health`
- **배포**: `/land-and-deploy`, `/canary`, `/document-release`, `/retro`, `/checkpoint`
- **보안·품질**: `/cso`, `/codex`, `/careful`, `/guard`, `/freeze`, `/unfreeze`
- **리서치**: `/investigate`, `/browse`, `/learn`, `/devex-review`

### 2. simon-stack (13개) — 통합 오케스트레이션
- `app-dev-orchestrator` — 신규 앱 21단계 마스터 파이프라인
- `security-orchestrator` — 보안 5단계 순차 실행
- `security-checklist`, `authz-designer`, `paid-api-guard` — 보안 상세
- `simon-tdd`, `simon-worktree`, `simon-research`, `simon-instincts` — 방법론
- `nextjs-optimizer`, `stitch-design-flow`, `project-context-md` — 도구

### 3. 유틸리티
- `commit`, `review`, `debug`, `refactor`, `test-gen`, `explain` — 일반 개발
- `simplify`, `loop`, `claude-api`, `update-config`, `keybindings-help`

전체 맵: `~/.claude/skills/INDEX.md`

---

## Skill 선택 우선순위

1. **새 앱 개발** → `app-dev-orchestrator` (다른 플래닝 skill 은 내부에서 호출)
2. **보안 점검** → `security-orchestrator` (4개 skill 순차 실행)
3. **권한 설계** → `authz-designer`
4. **구현 단계** → `simon-tdd` + `simon-worktree`
5. **리서치** → `simon-research` → 플래닝 skill
6. **반복 실수** → `simon-instincts` 즉시 기록
7. **디자인 작업** → 반드시 `simon-design-first` 먼저 (아래 워크플로 참조)

---

## 디자인 작업 워크플로 (필수)

디자인 요청 (`/design-consultation`, `/design-html`, "디자인 만들어줘", "UI 만들어줘", "랜딩페이지" 등)을 받으면
**절대 바로 코드를 작성하지 않는다**. 다음 순서를 지킨다:

### 1. 진단 먼저
- 누가 볼 사이트인가? (개발자 / 일반 사용자 / 기업 / 투자자)
- 목적은? (제품 소개 / 판매 / 문서 / 포트폴리오)
- 톤·분위기는? (프로페셔널 / 친근 / 프리미엄 / 실험적)

### 2. 레퍼런스 추천 (반드시 접속 가능한 URL 포함)
- 유사 제품·톤 사이트 3-5개를 URL과 함께 제시
- 탐색용: https://dribbble.com · https://www.awwwards.com · https://www.lapa.ninja · https://21st.dev

### 3. 폰트 선택권
- Google Fonts 미리보기 URL 포함 (https://fonts.google.com/specimen/<name>)
- 한국어: **Pretendard** 기본, 제목용 대안 제시
- AI는 추천만, 사용자가 선택

### 4. 사용자 방향 확정
- "이 느낌으로 갈까요?" 또는 "다른 레퍼런스 보여줄까요?" 확인
- 사용자가 "알아서 해" 또는 갈피 못 잡을 때만 AI 단독 진행

### AI Slop 방지 3원칙
1. **불필요한 것 제거** — 이모지 아이콘, 장식, 과잉 요소 금지
2. **모노톤 색상** — 전체 UI 색상 3개 이내 (accent + text + bg)
3. **레퍼런스에서 착안** — 확정된 방향 유지

### 금지 폰트·색상
- **Inter** (AI 생성 티 남) → 한국어 **Pretendard**, 영문 대안 산세리프
- **pure black/gray** → tinted neutrals (약간 violet/blue tint)
- **4색 이상 multi-color**
- **bounce/elastic easing**

---

## 금지 사항

- 시크릿·API 키 하드코딩 **절대 금지**
- 파괴적 명령 (`rm -rf`, `git reset --hard`, `git push --force`, `DROP TABLE`, `--no-verify`) 사용자 confirm 필수
- `.env` 생성 시 `.gitignore` 에 포함 확인
- PR 자동 생성·자동 머지 금지
- 기존 skill 파일 덮어쓰기 전 확인
- 이 파일(`~/.claude/CLAUDE.md`) 은 append 원칙 (기존 내용 보존)

---

## 재설치

이 환경은 `github.com/learner-thepoorman/Gstack-Ultraplan-superpowers` 의
`.claude/hooks/session-start.sh` 에 의해 매 세션 자동 bootstrap 된다.
수동 재설치: `cd <repo> && ./scripts/install.sh`
