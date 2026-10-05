# First-run 시퀀스 — <product> <date>

## 활성화 정의 (선행 입력)

- Aha 행동: <유저가 처음 가치를 느끼는 단 하나의 행동>
- 임계값: <N회 / M일 이내>
- 활성화 = <조건. 기본값: Aha 행동 1회 완료>
- 플랫폼: <RN/Expo · 웹 · 둘 다>

## 시퀀스 (한 화면 = 한 목적)

각 행은 화면 1개. 마지막 열의 "Aha 거리"는 이 화면이 Aha 행동에서 몇 걸음 떨어졌는지.

| # | 화면 id | 단일 목적 | 단일 CTA | 출구(skip) | activation 이벤트 | Aha 거리 |
|---|---|---|---|---|---|---|
| 1 | welcome | 가치 한 줄 제시 | 시작하기 | 없음(첫 화면) | onboarding_started | 3 |
| 2 | <id> | <목적 하나> | <CTA> | 나중에 하기 | onboarding_step_viewed/completed | 2 |
| 3 | <id> | <목적 하나> | <CTA> | 약한 skip | ... | 1 |
| 4 | aha | <Aha 행동 직접 수행> | <Aha CTA> | 출구 약화 | aha_moment_reached | 0 |
| 5 | account(선택) | 계정 생성(value-first 후행) | 계정 만들기 | 게스트 유지 | user_signed_up | - |

원칙 체크:
- [ ] 화면당 결정 1개 (입력 필드 ≤ 3)
- [ ] 회원가입은 가치 경험 뒤로 (value-first)
- [ ] Aha 직전 스텝만 출구를 약하게, 나머지는 명확한 skip
- [ ] 모든 화면이 Aha 행동에 한 걸음씩 접근

## first-run 1회성 처리

- 플래그 저장: <AsyncStorage key `onboarding_completed_v1` / 서버 user flag>
- 재노출 조건: <없음 / 버전업 시 v2 키로 재실행>
- 큰 상태는 서버로 (AsyncStorage 2MB 한도 주의)

## 화면 구현 인계

화면 컴포넌트·네비게이션은 building-native-ui(expo-router)가 생성.
이 시퀀스 표의 "단일 목적 / CTA / 이벤트"를 그 화면 위에 Edit로 얹는다.
