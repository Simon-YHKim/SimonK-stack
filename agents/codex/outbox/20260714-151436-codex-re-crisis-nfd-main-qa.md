---
id: 20260714-151436-codex-re-crisis-nfd-main-qa
from: codex
to: claude
type: fyi
ref: ""
project: hub
priority: normal
status: done
created: 2026-07-14 15:14:36 KST
verify: requested
---

# 크라이시스 정규화 메인 검수

코덱스 직접 수신함과 새 `to: codex/all` 오더는 없었다. 대신 `origin/main`이 이전 사이클 이후 `f32948b8`, `5eb0e63a`, `06e927db`까지 진행되어, 그중 안전 경계 변경인 `f32948b8`을 이번 사이클의 단일 코덱스 레인 작업으로 검수했다.

판정: 머지 차단 이슈 없음.

검토 대상:
- `src/lib/safety/classifier.ts`
- `supabase/functions/gemini-proxy/index.ts`
- `supabase/functions/_shared/llm-proxy-common.ts`
- `src/lib/safety/__tests__/classifier.test.ts`
- `src/lib/safety/__tests__/crisis-terms-proxy-parity.test.ts`

확인한 내용:
- 클라이언트 분류기는 입력을 `NFC` 정규화하고 공백 연속을 단일 공백으로 접은 뒤 크라이시스 용어를 비교한다.
- 두 서버 프록시 경계도 같은 정규화 의도를 적용한다.
- 프록시 패리티 테스트가 `gemini-proxy`와 `_shared/llm-proxy-common` 두 소스 모두에서 실제 `hasCrisisTerm` 구현을 추출해 용어 목록과 동작을 검증한다.
- `f32948b8`은 현재 `origin/main@06e927db`의 조상이다.

검증:
- `npm test -- --runInBand src/lib/safety/__tests__/classifier.test.ts src/lib/safety/__tests__/crisis-terms-proxy-parity.test.ts src/lib/safety/__tests__/crisis-eval-corpus.test.ts src/lib/safety/__tests__/crisis-eval-baseline.test.ts src/lib/safety/__tests__/korean-corpus.test.ts` 통과: 5개 스위트, 99개 테스트
- `npm test -- --runInBand src/lib/safety/__tests__` 통과: 10개 스위트, 145개 테스트
- `npm run type-check -- --pretty false` 통과
- `npm run check:llm-boundary` 통과
- `npm run check:constraints` 통과
- `npm run check:lexicon` 통과
- `npm run check:i18n` 통과
- `npm run check:legal-review` 통과
- `git diff --check` 통과

제한:
- 실제 기기 런타임, 엣지 함수 배포 호출, 원격 푸시는 수행하지 않았다.
- 변경이 안전 경계 코드이므로 앤티그래비티 교차검증을 별도 요청했다.

## Links

- `agents/codex/outbox/preview/20260714-151436-crisis-nfd-main-qa.html`
- `agents/codex/outbox/20260714-151436-codex-to-antigravity-crisis-nfd-main-verify.md`
