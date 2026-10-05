# 다른 레포·세션에서 simon-stack 사용하기

> **은퇴한 설치 안내 (허브 D-87, 2026-10-05).** 이 문서가 설명하던 네 방법은 모두 은퇴했다. 예전 본문은 git 이력에 있다.

| 예전 방법 | 지금 |
| --- | --- |
| §1 로컬 글로벌 설치 `./scripts/install.sh` | `scripts/install.sh`에는 `--offline-package` 진입점만 남았다. 다른 인자는 은퇴 안내를 출력하고 exit 2로 끝난다. |
| §2 이 레포를 열면 SessionStart 훅이 자동 bootstrap | 훅은 읽기 전용 안내만 출력하고 아무것도 쓰지 않는다. |
| §3 Bootstrap 모드 `setup-repo.sh --mode bootstrap` (curl 스트림 포함) | `setup-repo.sh`와 bootstrap 템플릿 2개는 [`_archive/legacy-install/`](../_archive/legacy-install/README.md)에 보관했다. |
| §4 Vendor 모드 `setup-repo.sh <target>` | 같은 곳에 보관했다. |

## 지금 쓰는 법

- **사용자**: 다른 레포에 파일을 심지 않는다. Claude Code에 마켓플레이스 다섯 플러그인을 설치한다 — [README 3절 설치](../README.md#3-설치).
- **이 PC(flat 설치)**: `pwsh -File scripts/windows/update-local.ps1`(미리보기, `-Apply`로 설치) — [README 11절 개발자 안내](../README.md#11-개발자-안내).
- **개발(스킬 추가·수정, 릴리스 경로)**: [README 11절](../README.md#11-개발자-안내).

플러그인과 flat 설치를 한 PC에서 함께 켜지 않는다(README 3절).

## 관련 문서

- [INSTALL.md](INSTALL.md) — 설치·배포 절차와 검증 기록
- [옛 설치 스크립트 보관](../_archive/legacy-install/README.md)
