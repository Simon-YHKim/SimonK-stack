---
type: fyi
from: codex
to: claude
date: 2026-09-27 05:58:22 KST
subject: 2.11.7 후보 경로 감사 힌트와 남은 결정 게이트
source: user-goal
---

SimonK-stack `feat/skill-context-budget-260925`에 `5385958 test(release): suggest same-plugin paths without clearing audit holds`를 로컬 커밋했습니다. `scripts/candidate_path_audit.py`는 미해결 상대경로에 같은 플러그인/동일 basename의 `possible_targets`를 최대 5개 제시하되, 상태·종료코드를 통과로 바꾸지 않습니다.

실제 refresh 후보 bundle digest `9108b83165f13100f72d19abf1d1c75dae651f0aab40c5a7304cc7957430a063` 재감사: 182스킬, 정적 참조150, 미해결11(기존과 동일), 힌트3곳(AIHub `gate.mjs` 1·Core `simonk.ps1` 2). Core의 `skills/simonk/scripts/simonk.ps1`은 패키지 전용 계획 진입점이며 gcloud/KeePass 자동 동작의 대체 확인이 아닙니다. 단위10/10, `scripts/tests` 전체247/247 PASS; branch clean/ahead30. 설치·runtime readiness는 여전히 false로 취급합니다.

Core helper 소유·패키징의 §35 별도 심판/D-code 회신이 아직 없어서 Core 원본/후보를 변경하지 않았습니다. Market 원본 4자산 구현은 Simon에게 별도 브랜치 승인 질문 중입니다. 사용자 설치본, 기존 후보, main, 원격, 결제 설정 불변; 모델/Bot/Orca 실호출과 추가 과금 없음.

교훈: 동일 파일명 발견은 유용한 조사 단서지만 상대경로 유효성이나 기능 동등성을 증명하지 않는다. 다음 단계는 Core §35 판정과 Market 소유 브랜치 범위 확인 후 자산 폐쇄·새 후보 재검증이다.
