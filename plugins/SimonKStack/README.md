# SimonKStack

> 제품/서비스 빌드 오케스트레이션 플러그인

오케스트레이션 진입점: `/skstack` (기존 `/simonk` 빌드 전용 재정의 + alias)

## 의존
SimonKCore 권장 동반 설치 (공유 인프라). 없으면 일부 기능 제한.

_기존 Simon-YHKim/SimonK-stack 레포로 머지 예정. 현재는 로컬 프리뷰._

## 로컬 검증

```bash
node .github/validate.mjs
node .github/validate-evals.mjs
node --test .github/validate-evals.test.mjs
node --test skills/analytics-ad-wiring/tests/consent-gated-wrapper.test.mjs
```

평가 파일은 행동 assertion 스키마와 기존 선택 트리거 배열 스키마를 함께 사용합니다. 검증기는 존재하는 `cases.json`의 형식만 확인하고, 누락된 파일 수는 별도로 보고합니다. 모델 선택 정확도나 실제 스킬 동작을 실행·인증하지 않습니다.

동의 게이트 테스트는 TypeScript 타입 제거를 지원하는 Node.js 24에서 실행합니다. 분석·광고 배선 템플릿은 앱의 실제 동의 상태 판독기를 주입해야 활성화됩니다. 판독기가 없으면 배선을 완료로 간주하지 않습니다.
