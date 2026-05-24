# Tool Quirks — 하네스·CLI 함정 모음

> **목적**: Claude Code, Cursor, Codex, Opencode 등 각 에이전트 하네스와 주변 CLI 도구의 알려진 함정을 누적한다.
> **갱신 규칙**: 같은 함정에 두 번 걸리면 이 파일에 기록.

---

## Claude Code

### 2026-04-12 — Plan 파일에 시크릿 substring 포함 금지
- **상황**: 플랜 파일에 "시크릿 누출 검사" 의 grep 패턴을 그대로 기록했는데, 패턴 자체가 실제 API 키의 prefix 였음
- **증상**: `grep -r AQ.Ab8RN6... ~/.claude/` 로 자체 검증 실행 → 플랜 파일 자신이 LEAK 판정
- **회피법**: 검증용 grep 패턴은 placeholder 사용 (`AQ\.[A-Za-z0-9_-]{20,}` 같은 정규식만)
- **근본 해결**: 검증 스크립트는 패턴을 arg 로 받아 플랜 본문에 값이 남지 않도록

### 2026-04-12 — Gstack skill 은 SKILL.md 만으로는 작동 안 함
- **상황**: Gstack 레포 clone 후 skill 디렉토리(`SKILL.md`)만 복사
- **증상**: 스킬 자체는 YAML 파싱 OK, description 에 노출되지만, 실행하면 `~/.claude/skills/gstack/bin/gstack-*` 를 찾아 호출 → 파일 없음 → `|| true` 로 silent degradation, 핵심 기능(learnings·telemetry·config) 미작동
- **회피법**: Gstack 레포 전체를 `~/.claude/skills/gstack/` 에 복사 + `bun install`
- **근본 해결**: Gstack 공식 설치 스크립트 사용 (있을 경우). 현재는 수동 복사 + bun install 로 해결

- **Plan 모드**: 편집 불가. 계획 파일 하나만 쓸 수 있음. ExitPlanMode 로만 탈출
- **`--dangerously-skip-permissions`**: 사용 금지. `/permissions` allowlist 사용
- **병렬 세션**: 반드시 `git worktree`로 격리. 동일 브랜치 병렬 작업 금지
- **CLAUDE.md 체크인**: 팀 git에 포함, PR 마다 갱신
- **Stop hook**: `~/.claude/stop-hook-git-check.sh` — 커밋 누락 감지용. 우회 금지
- **Skill 트리거**: description의 키워드가 발동 조건. 한국어·영어 병기 권장
- **컨텍스트 자동 압축**: 긴 세션에서 초기 메시지가 요약됨 — 중요한 메타데이터는 답변 본문에 재명시

## Cursor / Cline

- Agent 모드: 파일 단위 diff 리뷰. 큰 edit 은 여러 턴으로 쪼개야 적용률 높음

## OpenAI Codex CLI

- `codex review` / `codex challenge` — Gstack `/codex` 스킬이 래핑
- 세션 연속성: `--session-id` 로 유지

## Git

### 2026-04-13 — `git clone` 이 GitHub default branch 를 복제, main 아님
- **상황**: 레포를 public 으로 전환하고 main 에 푸시 했는데, 외부에서 `git clone https://github.com/<user>/<repo>` 하면 옛 base commit 만 나옴
- **증상**: `git log` 에 1 개 commit 만. 최근 작업 내용이 안 보임
- **원인**: GitHub default branch 가 아직 main 이 아님. `git clone` 은 서버의 default branch 를 복제
- **회피법**: hook 스크립트는 `git clone --depth 1 --branch main` 으로 명시
- **근본 해결**: GitHub `Settings → Branches → Default branch` → `main` 으로 전환, 옛 브랜치 삭제

- `--no-verify`: 사용 금지 (pre-commit hook 우회). 사용자 명시 허가 시에만
- `git reset --hard`, `git clean -f`, force push — confirm 없이 금지
- `git worktree` 종료 시 `git worktree remove` 필수 (고아 브랜치 방지)
- Conventional Commits: `feat/fix/docs/chore/refactor/test/perf/ci/build/style` 외 금지
- **원격 브랜치 삭제 차단**: Claude Code 웹 sandbox 의 로컬 git proxy 는 `git push origin --delete <branch>` 를 HTTP 403 으로 막음. 원격 브랜치 정리는 GitHub UI 로만 가능

## Node / npm / pnpm

- `npm install` vs `npm ci`: CI 에서는 `ci` 필수 (lockfile 존중)
- 글로벌 설치 피함: npx 우선
- Node 22 LTS — `--experimental-vm-modules` 관련 플래그 변경 주의

## Supabase

- `service_role` 키: **서버 전용**. 클라이언트 번들에 노출 금지
- RLS: `ENABLE` 만으로는 부족 — `FORCE ROW LEVEL SECURITY` 도 적용해야 테이블 owner 우회 차단
- migrations 순서 충돌: 동시 작업 시 타임스탬프 prefix 충돌 주의

## Playwright / Puppeteer

- 한국어 폰트 렌더링: 이미지 비교 테스트 시 OS 기본 폰트 차이로 false-negative
- `waitForSelector` 보다 `waitForLoadState('networkidle')` 선호

## NotebookLM CLI (notebooklm-py)

- **`notebooklm doctor` false-positive**: `storage_state.json` 의 SID cookie 존재만 검사. cookie 가 stale 이어도 ✓ pass. 진짜 검증은 `notebooklm list` Title 컬럼 ("Warning: Authentication expired..." vs 실제 워크스페이스 제목).
- **`notebooklm login` press-ENTER 트랩**: 브라우저 OAuth 완료 후 **터미널로 돌아가 ENTER 키 1회 누르지 않으면 `storage_state.json` 미저장**. Chromium 내장 `Network/Cookies` SQLite 만 갱신, CLI 가 읽는 storage_state 는 그대로 stale. "Authentication saved to ..." 메시지 확인 필수.
- **Windows Chrome/Edge app-bound encryption (v127+)**: `notebooklm login --browser-cookies chrome` 또는 `edge` 가 "Could not decrypt" 로 실패. rookiepy 우회 불가. Firefox/Brave 가 fallback. 없으면 `--fresh` + 수동 OAuth + 터미널 ENTER 정공법.
- **`--fresh` 부작용**: `browser_profile/` 청소 후 Playwright 로 새 세션 만들려 함. `pip install "notebooklm-py[browser]"` + `playwright install chromium` 선설치 안 됐으면 cleanup 직후 "Playwright not installed" 종료 (storage_state.json 자체는 별도 파일이라 보존).
- **stale lock 잔재**: 비정상 종료 시 `~/.notebooklm/profiles/default/.storage_state.json.lock`, `.rotate.lock` 0-byte 파일 잔재 가능. 다음 login 차단 가능성. `Remove-Item ...lock -Force` 로 정리.
- **`notebooklm delete` 는 `-n` 필수**: positional 인자 거부. `notebooklm delete -n <id> --yes` (use 는 positional OK — 일관성 X).

---

## 템플릿

```
### <tool> — <한 줄 제목>
- **상황**: 언제 발생
- **증상**: 겉으로 드러나는 모습
- **원인**: 실제 원인
- **회피법**: 즉시 적용 가능한 우회
- **근본 해결**: 있다면
```
