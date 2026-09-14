# STATE — AI Usage Widget v2
> 덮어쓰기. 네 절만. 갱신 26.09.15 04:10 KST · Claude Code(통합)

## 완료
- v1 전수 분석 → docs/SPEC-v1-baseline.md(V1-01~43), 조사 → docs/RESEARCH-auth-quota.md, 결정 → DECISIONS.md
- 스캐폴딩(a0c72eb): 계약·cli/spawn·보안·빌드 설정
- 모듈 5개 병렬 구현 후 main 병합(충돌 0): shell 2494bee, codex 0a7b992, claude 6d23db9, grok 3c3ab42, renderer c632ece
- 통합: 실제 어댑터 연결(registry → controller → scheduler → renderer), 계약 변경 반영(`loginUrlHosts`, `popup:show`, `cli-unsupported-install`, i18n 7키), 브리지 스크립트 lint 적용, DESIGN.md·DECISIONS.md 갱신(04:06)
- 검증: `pnpm verify` exit 0(47파일·495테스트), `pnpm build` exit 0, `pnpm dist:dir` exit 0, 퓨즈 7개 설정값 일치, 배포본 `release\win-unpacked\ai-usage-widget.exe --smoke` exit 0(ok:true, CSP 헤더 일치, IPC 23/23, koffi loaded, CLI 탐지 claude 2.1.270·codex 0.154.0·grok 1.0.30)

## 진행중
- 없음

## 다음
- 사용자와 실측: T1 Codex device code 로그인·버킷·인증 페이지 호스트 / T2 Claude 파이프 로그인 / T3 statusline rate_limits 기록 / T4 Grok `_x.ai/billing` 응답·device-auth 출력 / T8 GUI(팝업 blur·topmost·전체화면·재질·테마 이벤트·자동 시작 배포본)

## 막힌 것
- CLI 설치 안내 URL(`EXTERNAL_LINKS`) 비어 있음: 공식 문서에서 확인한 https 주소가 필요(설치 안내 버튼은 not-found)
- 실측 전 추정: codex 오류 문구 판정, grok billing 응답 형태·plan, claude needs-paste 타이밍
