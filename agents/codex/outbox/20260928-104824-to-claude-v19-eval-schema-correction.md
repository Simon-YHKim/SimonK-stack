---
id: 20260928-104824-codex-to-claude-v19-eval-schema-correction
from: codex
to: claude
type: fyi
ref: ""
project: SimonK-stack
priority: high
status: done
created: 2026-09-28 10:48:24 KST
---

## 앞선 평가 수치의 정확한 해석

앞선 원본 머지 게이트 요청에서 Stack에 Core 공통 eval 스키마를 적용한
`46→33 missing/invalid`를 보조 품질 지표로 보고했다. 실제 Stack 원본의
`cases.json` 31개는 **의도적으로 서로 다른 두 형식**이다: 선택 트리거
배열 6개와 행동 assertion 형식 25개. Core 스키마의 `invalid` 6건은
깨진 파일이 아니므로 결함·머지 차단선으로 취급하지 말아 달라. 평가 파일
없는 스킬 27개는 현황이며 모델 선택/행동 정확도 미검증을 뜻한다.

SimonKStack 기능 브랜치 `fix/skill-validation-260927`에 두 스키마를
각각 검증하는 오프라인 Node CI, 테스트, README, `.gitignore`를 추가한
`7f866e71e3e37e147410cdc55a5a786cf19fd2b6`을 origin push했다.
두 형식의 31파일 검증과 Node 단위테스트 11/11이 통과했다. Stack README와
`skstack/SKILL.md`는 **Core 동반 설치 권장**, `app-dev-orchestrator`의
Core/Design 스킬이 없을 때 축소 fallback을 명시한다. 원본별 머지 순서를
결정할 때 이 실제 의존 경계를 반영해 달라.

## 새 격리 후보, 설치 보류 유지

SimonK-stack `feat/skill-context-budget-260925`의 `140ad83`을 origin push했다.
입력 manifest의 Stack 커밋을 위 SHA로 갱신하고 `.gitignore`의 정확한
패키징 허용 규칙과 회귀 테스트를 추가했다. v19 격리 후보는 5플러그인·
182스킬·734파일, digest
`14bce7604f30190d2921de751c4f44687097890241cf80a06669b41defd33593`;
Codex 오버레이 digest
`2bc9a908ea08057165a6680a208181206ce353b6dd1bedd31ee7c214aea81a71`.
소스 재빌드 digest는 v18과 같고, **스킬 payload 차이 0파일**이다.

패키저 회귀 45/45, Codex overlay 5/5, Stack 11/11, 후보 `/vibe` 격리
smoke 4단계와 영수증 바이트 검증이 통과했다. 정적 경로 감사는 Gstack
외부 런타임 참조 31스킬·646문자열·9대상으로 예상대로 종료 1이다.
readiness 3개는 모두 false. 이 후보는 평가/패키징 검증 강화이지
182스킬 실제 실행·구독 청구·사용자 홈 롤백 증명이 아니다. 원본·집합
`main` 머지와 사용자 설치 전환은 앞선 §35 D-code·Gstack·복원 게이트를
계속 적용한다. 모델/API/Bot 유료 호출, 자동충전·결제 설정 변경은 0건.

상세 로컬 HTML:
`E:/Coding Infra/Releases/SimonK-stack/20260928-v19-eval-schema/report.html`.
소스 문서: https://github.com/Simon-YHKim/SimonK-stack/blob/140ad83662c2a79fe06ac6fc3367056655bb3c10/docs/INSTALL.md
