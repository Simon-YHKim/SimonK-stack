# 레거시 루트 플러그인 `simonk-stack` 0.1.0 (보관)

허브 결정 D-87(2026-10-05) PR-B에서 저장소 루트에서 이 폴더로 `git mv`했다. 지우지 않았으므로 이력과 내용은 그대로다.

## 무엇이었나

- 2026-10-05 전까지 마켓플레이스 `simonk-stack`이 제공하던 단일 플러그인 `simonk-stack` 0.1.0이다.
- `plugin.json`(원래 `.claude-plugin/plugin.json`)이 `./skills/` 아래 스킬 68개를 나열했다. `skills/`는 원래 저장소 루트에 있었다.
- 마지막 변경은 `4b02423`(2026-09-20)이다.

## 왜 보관했나

- 카탈로그 `.claude-plugin/marketplace.json`은 2026-10-05 D-82 마지막 단계부터 다섯 `dist` 플러그인만 가리킨다. 이 플러그인을 가리키는 곳은 없다.
- D-87은 D-33 source-only hold와 그 hold가 막던 옛 배포·설치 경로를 은퇴시켰다. PR-A(#143)는 SessionStart 훅을 읽기 전용 안내로 줄이고 `release.yml`과 hold 파일을 지웠다. PR-B는 이 폴더와 옛 설치 스크립트([`_archive/legacy-install/`](../legacy-install/README.md))를 보관했다.
- 이 폴더는 dist 빌드 입력이 아니다. 다섯 플러그인은 `skills-src/`와 플러그인별 원본 저장소(`distribution/plugin-inputs.v1.json`에 커밋 고정)로 빌드한다.
- `scripts/dist_release.py`는 이 `plugin.json`을 읽지 않고 상수 `LEGACY_FLOOR = "0.1.0"`을 쓴다. 릴리스 버전 `1.<N>.0`은 지금도 이 값보다 커야 한다.

## 지금 제품을 받는 법

- 사용자: [README 3절 설치](../../README.md#3-설치) — `/plugin marketplace add Simon-YHKim/SimonK-stack` 뒤 다섯 플러그인을 설치한다.
- 0.1.0을 쓰던 사용자: [README 8절](../../README.md#8-예전-simonk-stack-010에서-옮기기)의 네 줄.
- 이 PC(flat 설치): `pwsh -File scripts/windows/update-local.ps1`(미리보기, `-Apply`로 설치). [README 11절](../../README.md#11-개발자-안내) 참고.

## 되돌리기

PR-B 커밋을 `git revert`하면 이 파일들과 검증기(`.github/validate.mjs`)·버전 하한(`scripts/dist_release.py`) 변경이 함께 돌아온다. 파일만 필요하면 `git mv`로 `skills/`와 `.claude-plugin/plugin.json`에 되돌린다.
