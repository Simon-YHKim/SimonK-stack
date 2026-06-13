# SimonK-stack — 모놀리식 → 플러그인 전환 (완료)

부트스트랩 설치가 **5-플러그인 suite 기반**으로 전환되었습니다.

## 설치 소스 (scripts/install.sh)
- **주 소스**: 5-플러그인 — 이 레포 `skills/`(SimonKStack) + `SimonKCore`/`SimonKDesign`/`SimonKMarket`/`SimonKAIHub`(install.sh가 `~/.simon-stack/plugins/`로 클론·풀 후 각 `skills/` 수집). 약 171 스킬.
- **폴백**: 플러그인 클론이 모두 실패(오프라인 등)할 때만 레거시 `skills-src/` 사용 → 사용자가 스킬 없이 남지 않음.
- **안전장치**: `~/.claude` 백업(`~/.claude.bak-*`), idempotent, 그리고 `SIMONK_SKILLS_TARGET=<temp>`로 ~/.claude 무접촉 로컬 테스트(TEST_MODE).

## 레거시 (폴백 전용)
`skills-src/`(129) + 모놀리식 구조는 더 이상 주 설치 소스가 아니라 **오프라인 폴백 + 이력 보존용**으로만 유지. 플러그인 경로가 충분히 안정화되면 제거 가능.

## 검증
`SIMONK_SKILLS_TARGET=/tmp/t SIMONK_PLUGIN_CACHE=/tmp/c bash scripts/install.sh --force --no-backup` → 5 소스에서 171 스킬 수집, ~/.claude 무변경 확인됨.
