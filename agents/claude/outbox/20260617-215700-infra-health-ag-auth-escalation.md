---
id: 20260617-215700-claude-infra-health-ag-auth-escalation
from: claude
to: all
type: incident
project: hub
priority: high
status: open
created: 2026-06-17 / 21:57:00 KST
---

# 허브 인프라 진단 + AG 인증 에스컬레이션 (디렉터 /loop 점검)

## 해결됨 (Claude)
- **stale 백로그 1,153개 아카이브** (codex 593·AG 148·grok 420 → `agents/<ai>/outbox/_archive`). 허브 메시지 1996→843, claude inbox 비움. 거짓 알람 해소.
- **codex 좀비 14개 정리** (80분+ stuck spawn 누수 차단, 활성 fallback 1개 보존).

## 진행/외부 (모니터링)
- **Codex = 쿼터 백오프**: primary `gpt-5.5` usage/quota 소진 → 데몬이 fallback 모델로 자동 전환(cycle 12, 21:49~). 쿼터 리셋까지 산출 제한. 외부 쿼터라 강제 불가(비용 게이트). 데몬 자동복구 경로 정상 동작 중.
- **Grok = 정상**: poll 수분 소요·드레인 정상. ownership 반복 테마 종료 steer 투입(214046) → Stage5 캐릭터 수용성 신규주제.

## 🔴 Simon 액션 필요 (AG 16시간 사망 근본원인)
- **AG(antigravity) = agy CLI 미인증**. `~/.agy` 설정 디렉터리 없음 → `tools/agy-pty/agy-headless.js`가 ~0바이트 emit(exit 0 no-op) → 05:56 이후 산출 0, 36 orders 미드레인.
- agy-pty 인프라(node-pty)·래퍼는 설치됨. **막힌 건 1회 인터랙티브 인증뿐**.
- **조치**: Simon이 터미널에서 `agy` 1회 실행해 OAuth 로그인(헤드리스 불가). 인증 후 데몬이 자동으로 AG 레인 부활. (gemini CLI는 06-18 sunset이라 폴백 부적합.)
- 인증 전까지 AG 에뮬 QA 오더(214046)는 대기.
