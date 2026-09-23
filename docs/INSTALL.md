# Install — simon-stack

이 레포는 Claude Code 를 위한 통합 skill 스택(Gstack + simon-stack + Superpowers 철학)이다.

## 검증된 소스 오버레이 — 격리·오프라인 경로

`/vibe` 이관의 새 배포 경로는 **source-owned overlay**입니다. 아래 명령은 실제
사용자 설치나 공식 5-plugin release를 교체하지 않습니다. 기존 기본 설치기와
SessionStart 자동 복사 경로는 아직 아래 계약으로 전환되지 않았습니다.

`distribution/skills-release.v1.json`이 배포용 소스 137개의 단일 plugin home을
명시합니다. 개발용 4개는 제외 범위로 기록하고, 공식 plugin에만 있는 45개도
포함하거나 삭제하지 않습니다. 숫자는 이 manifest 기준이며 새 스킬을 추가하면
소유권도 함께 갱신해야 합니다. 미배정 source는 빌드가 실패합니다.

Windows의 Python 3.10+와 Git으로, 존재하는 격리 부모 폴더 아래 **새 절대 경로**를 지정합니다.
예시 경로는 실제 환경의 임시 경로로 바꾸세요. 출력 위치가 이미 있으면 빌드는
덮어쓰지 않고 실패합니다.

```text
python -B scripts/skill_release.py build --repo E:/reviewed/SimonK-stack --ownership E:/reviewed/SimonK-stack/distribution/skills-release.v1.json --output E:/staging/release-a
python -B scripts/skill_release.py verify --package E:/staging/release-a --expected-digest <build가 반환한 release_digest>
```

빌드는 Git 추적 중인 `skills-src/<name>/` 전체 파일과 LICENSE/NOTICE,
`skills-src/VENDORED.md`의 upstream attribution을 복사합니다.
`release.json`에는 source/package/flat-install 상대경로, 바이트 수, SHA-256,
Git 실행 비트가 들어갑니다. 캐시·`.env`·백업·symlink/reparse·hardlink·충돌·경로 탈출은
포장하지 않습니다. 파일은 읽기 전에 열린 핸들의 hardlink 수까지 검사합니다.
미추적 파일은 배포물에 포함되지 않으므로 필요한 새 helper/assets는 먼저 Git에
추가하세요. SKILL.md가 있는 미추적 새 스킬 자체는 소유권 검사에서 차단됩니다.

`release_digest`는 검토한 빌드 결과에서 별도로 보관해야 합니다. 공격자가 package와
동시에 바꿀 수 있는 manifest의 자체 hash를 신뢰하는 서명/인증 체계가 아닙니다.
이 artifact는 명시한 tracked working-tree bytes의 snapshot이며 Git commit 전체나
공급망 출처를 인증하지 않습니다. 소스 snapshot과 임시 staging의 단독 작성이
전제입니다. 빌드·materialize 중 다른 작성자가 해당 트리를 수정하지 않아야 합니다.

기존 `install.sh`를 통해 격리된 flat skill root로 연결합니다. 이 명시적 모드는
backup/clone/의존성 설치/환경변경/marker 기록보다 먼저 끝납니다. `--force` 등
legacy 옵션 혼용은 실패하고, 옛 설치 경로로 자동 fallback하지 않습니다.

```bash
# 기본 preview: target 생성·설정 변경 없음
bash scripts/install.sh --offline-package E:/staging/release-a --target E:/staging/skills-a --expected-digest <digest>
# 전체 검증 후 새 격리 target에만 공개
bash scripts/install.sh --offline-package E:/staging/release-a --target E:/staging/skills-a --expected-digest <digest> --apply
```

Git Bash의 Python 경로가 다르면 이 명령에만 `SIMONK_PYTHON`을 지정할 수 있습니다.
검증·읽기·쓰기·publish는 현재 Windows 고정 로컬 드라이브 전용이며,
UNC/장치 경로·네트워크 드라이브·다른 플랫폼은 실패로 차단합니다.
보호 경로와 입력/출력 중복 검사는 핸들에서 얻은 정규 경로를 비교하므로
Windows 8.3 짧은 경로 별칭으로 우회할 수 없습니다.
부모/파일/stage의 native handle을 고정하여 reparse 경로 바꿔치기와 stage 교체를
막고, 같은 부모 안에서 no-replace 원자적 directory publish를 수행합니다.
publish 전후 owned 파일을 검증하지만 같은 사용자에 의한 동시 child 추가를
OS 권한으로 봉쇄하는 기능은 아닙니다. 위 단독 작성 전제와 구분하세요.
Windows는 Git의 portable 실행 비트를 기록하지만 실제 POSIX executable 권한 검증은
할 수 없어 `mode_verified=false`입니다. bytes 검증과 이를 구분하세요.

같은 artifact로 다시 실행하면 이미 설치된 **실제 owned 파일**을 다시 검증할 뿐
쓰지 않습니다. 다른 release, 수정/추가/누락된 owned 파일, 기존 unmanaged target은
보존하고 실패합니다. 별개의 unowned 최상위 폴더는 읽거나 바꾸지 않습니다.
실제 `.claude/.codex/.agents`, 공식 `SimonK-Plugins`, gstack 및 reparse target은
이 경로의 적용 대상이 아닙니다. 실제 운영 이관은 별도 검토·승인 단계입니다.
중단 시 완성 전 임시 `.simonk-build-*`/`.simonk-materialize-*`는 부모에 남을 수
있지만 기존 destination을 삭제하거나 교체하지 않습니다. 자동 정리/롤백은 없습니다.

이 검증은 **포장된 파일 전체의 무결성**입니다. repo-root PowerShell wrapper,
`~/.claude/scripts/upgrade-vendor.sh`, 외부 vendor/runtime/CLI/API/MCP/인증/과금,
호스트별 SKILL frontmatter 호환성 및 스킬 행동 평가까지 닫힌 의존성 검증이 아닙니다.
빠진 외부 의존은 manifest에 명시하며, 모델·Bot을 실행하거나 설치하지 않습니다.
공식 plugin의 extras/manifest 및 자동 설치기의 정합성, 실제 재설치·main 통합은
후속 배포 게이트로 남습니다.

회귀 테스트: `python -B -m unittest discover -s scripts/tests -p test_skill_release.py`
(임시 Git repo·격리 target, 실제 사용자 홈/공식 plugin/모델 호출 없음).

### Manifest 계약과 새 체크아웃 재현성

`schema_version`은 정수 1만 허용하며 bool/실수는 거부합니다. `source_state`는
`tracked-working-tree-bytes`만 허용하고, 외부 의존 선언은 정확한 `name/status`
문자열 두 필드·필드당 1~4096자·고유한 이름으로 제한합니다. 선언 순서는 보존합니다.
NaN/Infinity/overflow·중복 JSON 키·비정규 release.json은 검증에서 거부합니다.
release.json은 builder의 UTF-8/sorted-key/2-space/trailing-newline 형식이어야 합니다.
이는 형식 검사이지 의존 상태 문자열의 진실성이나 공급망 출처를 인증하는 기능은 아닙니다.

`.gitattributes`는 **새 체크아웃**의 배포 텍스트 확장자(md/json/py/sh/ps1/sql/html),
LICENSE/NOTICE 및 scripts/install.sh에만 LF를 지정합니다. 알려지지 않은 packaged
asset은 `-text`로 바이트를 보존합니다. 기존 작업 폴더를 일괄 renormalize하지 마세요.
일반 build는 dirty 상태도 가능한 현재 raw snapshot이며 clean commit attestation이 아닙니다.
같은 commit이어도 기존 CRLF 작업 폴더와 새 LF 체크아웃은 서로 다른 **정상 digest**를
만들 수 있습니다. 이전 패키지를 무효화하거나 기존 checkout과 같다고 주장하지 않습니다.

테스트는 두 개의 독립 임시 Git checkout에 checkout **전** `core.autocrlf=true/false`를
각각 적용하여 전체 package bytes/digest 일치, binary 원본 보존, 실제 Git Bash
installer의 preview/apply/재검증을 확인합니다. fixture만 설치하며 실제 홈은 건드리지 않습니다.

`.github/workflows/skill-release-windows-manual.yml`은 같은 정확 HEAD의 **실제 소스**를
두 새 로컬 clone으로 검증할 수 있는 Windows workflow 정의입니다. `workflow_dispatch`
전용·contents:read·credential persistence 없음·artifact upload/배포 없음입니다.
이 정의를 추가했다고 원격 CI가 통과한 것은 아닙니다. 과금 조건 확인과 별도 실행 권한
없이는 실행하지 마세요. 결과는 같은 SHA·선언된 checkout 정책 아래의 재현성만 증명합니다.
배포 전에는 commit과 artifact를 결합하는 별도 provenance receipt/승인도 필요합니다.

## One-shot 설치

아래는 기존 경로입니다. 소스 오버레이의 parity 증거를 대신하지 않으며,
네트워크·환경변경을 포함합니다. `--dry`만으로 모든 legacy 부작용의 안전성이
검증됐다고 가정하지 마세요. 새 `/vibe` 운영 이관을 위해 자동 실행하지 않습니다.

```bash
git clone https://github.com/Simon-YHKim/SimonK-stack.git
cd SimonK-stack
./scripts/install.sh
```

설치되는 것 (2026-05-27 기준):
- `~/.claude/skills/gstack/` — Gstack 풀 트리 (38+ skill + bin/scripts/lib + bun deps, garrytan/gstack upstream)
- `~/.claude/skills/<gstack-skill>/` — 38+ Gstack skill 개별 노출
- `~/.claude/skills/<simon-stack>/` — 100+ simon-stack skill (skills-src/ + .claude/skills/, connect-chrome zombie auto-skip)
- `~/.claude/instincts/` — 4 seed 파일 (mistakes / patterns / korean / quirks)
- `~/.claude/session-start-instincts.sh` — SessionStart hook 스크립트
- `~/.claude/CLAUDE.md` — 글로벌 지침 (instincts auto-load + Boris 원칙 + 100+ skill 카테고리 맵)
- `~/.claude/.simon-stack-installed` — installed SHA marker (session-start.sh selective-update logic 입력)

**기존 파일은 덮어쓰지 않음** — `cp -n` 로직. 재실행 안전.

## 사전 요구사항

- `git`
- `bun` (Gstack 런타임. 없어도 SKILL.md 만 동작하지만 헬퍼 스크립트는 실패)
- `node` ≥ 20 (Claude Code 자체)
- `claude` CLI 설치됨

## 수동 단계 (자동화 불가)

1. **SessionStart hook 등록** — `~/.claude/settings.json` 에 직접 추가:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "~/.claude/session-start-instincts.sh" }
        ]
      }
    ]
  },
  "permissions": {
    "allow": ["Skill"]
  }
}
```

2. **Claude Code 재시작** — 새 skill 로드를 위해.

3. **트리거 테스트**:
   - "새 앱 만들고 싶어" → `app-dev-orchestrator` 발동
   - "기능 구현해줘" → `dev-orchestrator`
   - "보안 점검" → `security-orchestrator`
   - "권한 시스템 설계" → `authz-designer`
   - "TDD 시작" → `simon-tdd`

## 구성

- **Gstack** (garrytan/gstack): 실행 파이프라인 36개. `/ship`, `/qa`, `/cso`, `/retro`, ...
- **simon-stack** (이 레포): 방법론·보안·학습 24개
  - Orchestrators: `app-dev-orchestrator`, `dev-orchestrator`, `security-orchestrator`
  - Security: `security-checklist`, `authz-designer`, `paid-api-guard`
  - Method: `simon-tdd`, `simon-worktree`, `simon-research`, `simon-instincts`, `agent-delegate`
  - Tools: `code-health-guard`, `simon-design-first`, `nextjs-optimizer`, `stitch-design-flow`, `project-context-md`
  - Meta: `skill-gen-agent`, `context-guardian`
  - General Dev: `commit`, `debug`, `explain`, `refactor`, `review`, `test-gen`

자세한 카테고리 맵: `.claude/skills/INDEX.md`

## 제거

```bash
rm -rf ~/.claude/skills/gstack
# 개별 simon-stack skill 은 수동 제거
# 백업에서 복구:
ls ~/.claude.bak-*  # 설치 시 자동 백업됨
```

## 참고

- [Gstack](https://github.com/garrytan/gstack) — 실행 파이프라인 원본
- [Superpowers](https://github.com/obra/superpowers) — TDD·worktree 철학 원본
- [everything-claude-code](https://github.com/affaan-m/everything-claude-code) — instincts·research-first 원본
