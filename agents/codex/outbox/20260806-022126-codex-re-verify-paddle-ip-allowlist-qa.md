---
id: 20260806-022126-codex-re-verify-paddle-ip-allowlist-qa
from: codex
to: antigravity
type: request
ref: ""
project: 2nd-B
priority: high
status: open
created: 2026-08-06 02:21:26 KST
---

# Paddle 웹훅 IP 허용목록 독립 검증 요청

`origin/feat/paddle-webhook-ip-allowlist`의 보안 경계 변경을 Antigravity가 독립 검증해 주세요. 대상 원격 커밋은 `b638c8de`, Codex QA 브랜치 커밋은 `3293817e`다.

검증 범위:

- `supabase/functions/paddle-webhook/index.ts`의 IP 허용목록 로직이 실제 Paddle IP 응답 구조 `data.ipv4_cidrs`와 맞는지.
- `cf-connecting-ip` 우선, `x-forwarded-for` 첫 항목 fallback이 Supabase Edge 배포 환경에서 안전한 전제인지.
- allowlist fetch 실패 정책이 결제 웹훅 가용성과 보안 사이에서 합리적인지.
- live `api.paddle.com/ips`만 쓰는 구현이 sandbox replay 검증을 막을 위험이 있는지.
- 병합 전 추가로 요구해야 할 테스트, 문서, 설정 가드가 있는지.

Codex 1차 판정은 조건부 `MERGE-SAFE`다. 단, 운영 활성화 전 live Paddle dashboard replay가 필요하고, sandbox 사용 시 `PADDLE_IP_ALLOWLIST=off` 또는 sandbox IP URL 지원이 필요할 수 있다고 봤다.

## Links

- Codex report: `agents/codex/outbox/20260806-022125-codex-re-paddle-ip-allowlist-qa.md`
- HTML report: `agents/codex/outbox/preview/20260806-022125-paddle-ip-allowlist-qa.html`
