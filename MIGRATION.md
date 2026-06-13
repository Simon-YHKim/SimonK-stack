# SimonK-stack — 모놀리식 → 플러그인 전환 (진행 중)

이 레포는 전환기 동안 **두 형태를 동시에** 보유합니다.

## 신규: SimonKStack 플러그인 (canonical)
- `.claude-plugin/plugin.json` + `skills/` (빌드 도메인 스킬 + `/skstack` 오케스트레이터)
- 설치: `/plugin marketplace add Simon-YHKim/SimonK-stack` → `/plugin install simonk-stack`
- SimonK 플러그인 스위트의 빌드 도메인. 짝 플러그인: SimonKCore / SimonKDesign / SimonKMarket / SimonKAIHub (각 별도 레포).

## 레거시: 모놀리식 부트스트랩 (여전히 활성)
- `skills-src/` + `scripts/install.sh` + `external/` — session-start 부트스트랩(`.simon-stack-src`)이 사용.
- **이번 전환에서 건드리지 않음** — 기존 환경 무손상.

## 남은 컷오버 (TODO)
부트스트랩을 5개 플러그인 기반으로 완전 전환(install.sh가 플러그인 마켓플레이스/clone 사용)은 라이브 세션 검증이 필요해 별도로 진행한다. 그때까지 레거시 부트스트랩을 유지한다.
