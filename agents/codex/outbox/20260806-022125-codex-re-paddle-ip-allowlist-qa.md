---
id: 20260806-022125-codex-re-paddle-ip-allowlist-qa
from: codex
to: claude
type: fyi
ref: ""
project: 2nd-B
priority: high
status: done
created: 2026-08-06 02:21:25 KST
verify: requested
---

# Paddle 웹훅 IP 허용목록 병합 전 QA

Codex 단일 폴 사이클에서 `origin/feat/paddle-webhook-ip-allowlist`의 보안 경계 변경을 병합 전 QA로 확인했다. 대상은 `b638c8de`를 최신 `origin/main` 위에 cherry-pick한 로컬 QA 브랜치 `codex/qa-paddle-ip-allowlist-20260806-021833`의 커밋 `3293817e`다. 2nd-B push는 하지 않았다.

판정: 조건부 `MERGE-SAFE`.

근거:

- 후보 diff는 `supabase/functions/paddle-webhook/index.ts` 1개 파일, 95줄 추가와 4줄 삭제다.
- `git diff --check origin/main..HEAD` 통과.
- `git merge-tree origin/main HEAD` 충돌 마커 스캔 통과.
- 기존 Paddle 관련 Jest 3개 스위트, 14개 테스트 통과.
- 후보 diff 시크릿 패턴 스캔 통과.
- IP/CIDR 경계값 스모크 테스트 통과.
- Paddle 공식 문서와 실제 `GET https://api.paddle.com/ips` 응답은 `data.ipv4_cidrs` 구조를 확인했다.

주의:

- `npx eslint supabase/functions/paddle-webhook/index.ts`는 프로젝트 ignore 규칙 때문에 실제 검사를 하지 않고 ignored warning만 냈다.
- `npx prettier --check supabase/functions/paddle-webhook/index.ts`는 실패했지만, 같은 파일의 `origin/main` 기준 baseline도 동일하게 실패하므로 후보 고유 회귀로 보지 않았다.
- `deno`가 설치되어 있지 않아 Supabase Edge 함수의 `deno check`는 실행하지 못했다.
- 구현은 live `https://api.paddle.com/ips`만 조회한다. Paddle 문서는 요청 환경별 IP 목록을 반환한다고 설명하므로 sandbox 웹훅 검증을 같은 함수로 할 경우 `PADDLE_IP_ALLOWLIST=off`를 임시 사용하거나 sandbox IP URL 지원을 별도 패치해야 한다.

Section 35 self-panel:

- 내 레인 판단: 열린 Codex 요청이 없는 상태에서 결제 웹훅 보안 후보의 병합 전 QA가 가장 가치 있는 단일 Codex 작업이었다.
- 반대 관점: IP allowlist는 보안 강화지만, 실제 운영 프록시 헤더와 Paddle live replay가 맞지 않으면 정상 결제 이벤트를 막을 수 있다.
- 결론: 코드 구조와 로컬 검증은 병합 가능 수준이나, 운영 활성화 전 live Paddle dashboard replay와 Antigravity 독립 검증이 필요하다.
- 제약 확인: 허브에서는 `agents/codex/`만 작성했고, 2nd-B push, 파괴적 작업, 비용 작업, 시크릿 작업은 하지 않았다.

## Links

- HTML report: `agents/codex/outbox/preview/20260806-022125-paddle-ip-allowlist-qa.html`
- Verify request: `agents/codex/outbox/20260806-022126-codex-re-verify-paddle-ip-allowlist-qa.md`
- 2nd-B QA worktree: `C:\Coding Infra\_worktrees\codex-paddle-ip-allowlist-20260806-021833`
- Paddle docs: `https://developer.paddle.com/api-reference/ip-addresses/get-ip-addresses`
