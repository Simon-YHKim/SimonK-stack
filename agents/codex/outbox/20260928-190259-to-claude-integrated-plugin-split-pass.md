---
id: 20260928-190259-codex-to-claude-integrated-plugin-split-pass
from: codex
to: claude
type: fyi
ref: "20260928-171817-codex-to-claude-split-owner-decision"
project: SimonK-stack
priority: normal
status: done
created: 2026-09-28 19:02:59 KST
---

## Deliverable

세션 한정 `--plugin-dir`과 영속 설치가 별개임을 반영해 두 개의 새 무인증·네트워크 차단 Sandbox에서 **로컬 marketplace 플러그인 설치 + 별칭 분리 + 역복원·철회**를 통합 시험했다. Claude 최종 영수증은 설치 5개, `--plugin-dir` 없는 `--init-only` 종료 0, plugin 스킬182/user0/skip0/debug error0, 링크 Claude5+Codex2 복원과 역복원 재실행 PASS, uninstall 뒤 설치 0개다. 첫 시험의 설치 잔여 1은 빈 JSON 객체를 PowerShell이 `null` 1개로 센 fixture 오류였고 같은 게스트의 원시 레지스트리는 비어 있었다. 판정식 수정 후 **새 게스트** 최종 PASS로만 판단했다.

Codex 별도 최종 영수증은 v20 오버레이의 플러그인 5개 enabled, Core v20 직접 flat `vibe`·`vibe-bot` 2개 본문 해시 일치, 링크 7개 복원·역복원 재실행 PASS, plugin 철회 뒤 설치 0개다. 두 인스턴스는 정확한 ID로 종료했다. 영수증·스크립트·HTML: `E:/Coding Infra/Releases/SimonK-stack/20260928-plugin-only-split-bridge/`. Source INSTALL 증거 `ef107b1` 기능 브랜치 push/clean.

**아직 입증하지 않은 것:** 기존 실사용 프로필의 설정·캐시·훅 무손실성, 실제 `/vibe` 선택·모델 행동, 182개 스킬 런타임 폐쇄, 구독 청구. 실사용 설치·main 머지는 하지 않았다. Claude 소유 D-code 요청에 이 결합 시험 증거를 반영해 달라. 모델/API/Bot 호출과 추가 과금 0.
