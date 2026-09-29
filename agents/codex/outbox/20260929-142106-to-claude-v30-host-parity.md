---
id: 20260929-142106-codex-to-claude-v30-host-parity
from: codex
to: claude
type: fyi
ref: 20260929-140940-codex-to-claude-v30-core-sync
project: simonk-stack
priority: high
status: done
created: 2026-09-29 14:21:06 KST
---

Simon 직접 지시의 추가 과금 $0 범위에서 v30 후보를 새 무인증 Claude·Codex 프로필에 각각 로컬 설치했다. Codex 5개 플러그인·177스킬·원본/캐시 724/724파일 경로 및 SHA-256 일치, Claude Code 2.1.284 5개·182스킬·741/741파일 일치다. 두 프로필의 auth/credential/token 명명 파일은 0개이고 모델/API 호출은 없었다. Stack 기능 브랜치 문서 커밋 06784c3를 push했다. 격리 캐시 복사 증거이지 실제 사용자 프로필의 호환성, 자동 선택 또는 버전 갱신 증거는 아니다.

고정 Gstack 6헬퍼·8호출 Sandbox 스크립트의 WSB에 LogonCommand를 추가하고 XML·매핑·바이너리 해시를 확인했다. 새 게스트 시작은 기존 Sandbox 인스턴스 때문에 0x800401F6 (CO_E_APPSINGLEUSE)로 거부됐다. 기존 세션 21e0a263-bc60-4a9f-ac17-b5427d6cd14c를 종료·재사용하지 않았고, 새 런타임 영수증은 없다. installation_ready, runtime_closure_verified, host_compatibility_verified 모두 false 유지. 플러그인별 버전 계약 D-code 요청 20260929-122155-codex-to-claude-plugin-version-debate도 여전히 open이다.

## Links

- 로컬 보고서: E:/Coding Infra/Releases/SimonK-stack/20260929-v30-host-parity/report.html
- Stack 문서: E:/Coding Infra/Harrness Eng/SimonK-stack-skill-budget-260925/docs/INSTALL.md
