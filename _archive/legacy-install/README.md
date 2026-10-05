# 은퇴한 설치 경로 (보관)

허브 결정 D-87(2026-10-05) PR-B에서 이 폴더로 `git mv`했다. 지우지 않았으므로 이력과 내용은 그대로다.

| 파일 | 원래 위치 | 하던 일 |
| --- | --- | --- |
| `install.sh` | `scripts/` | git clone 전역 설치. 다섯 플러그인 저장소를 `~/.simon-stack/plugins/`에 clone·pull 해서(모두 실패하면 `skills-src/` 폴백) 스킬을 `~/.claude/skills`로 복사했다. `~/.claude` 백업, Gstack, instincts 시드, `~/.claude/CLAUDE.md`, instincts 요약 훅 스크립트 복사도 했다. |
| `setup-repo.sh` | `scripts/` | 다른 레포에 simon-stack을 심었다. vendor 모드는 스킬·instincts·훅을 대상 레포에 복사했고, bootstrap 모드는 매 세션 이 저장소를 clone하는 훅 파일 2개를 넣었다. |
| `bootstrap-session-start.sh` | `templates/` | bootstrap 모드가 넣던 SessionStart 훅. 이 저장소를 `~/.simon-stack-src`에 clone·갱신한 뒤 그 저장소의 `.claude/hooks/session-start.sh`로 넘겼다. |
| `bootstrap-settings.json` | `templates/` | 위 훅을 등록하던 `.claude/settings.json` 템플릿. |
| `tests/test_no_install_marker.py` | `scripts/tests/` | D-68 `.simonk-no-install` 표식 테스트. `install.sh`·`setup-repo.sh`와 옛 SessionStart 복사 루프를 임시 폴더에서 실행했다. CI에는 들어 있지 않았다. |

## 왜 은퇴했나

D-87은 D-33 source-only hold와 그 hold가 막던 옛 배포·설치 경로를 은퇴시켰다. PR-A(#143)에서 SessionStart 훅은 읽기 전용 안내만 출력하고 아무것도 쓰지 않는다. 위 파일들은 그 옛 부트스트랩과 git clone 설치를 전제로 했다.

`scripts/install.sh`는 남아 있지만 `--offline-package` 진입점(`scripts/skill_release.py materialize`)과 `--help`만 한다. 그 밖의 인자는 은퇴 안내 한 줄을 stderr에 쓰고 exit 2로 끝난다.

## 지금 설치하는 법

- 사용자: [README 3절 설치](../../README.md#3-설치).
- 이 PC(flat 설치): `pwsh -File scripts/windows/update-local.ps1`(미리보기, `-Apply`로 설치). [README 11절](../../README.md#11-개발자-안내) 참고.

## 되돌리기

PR-B 커밋을 `git revert`하거나, 파일을 `git mv`로 원래 위치에 되돌린다. 테스트는 원래 위치(`scripts/tests/`)에서만 저장소 루트를 찾는다. 테스트 하나는 `.claude/hooks/session-start.sh`에서 옛 복사 루프(`count_new=0`부터)를 잘라 실행하는데, 그 루프는 PR-A에서 없어졌다. 그 테스트까지 살리려면 PR-A도 되돌려야 한다.
