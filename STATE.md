# STATE — AI Usage Widget v2
> 덮어쓰기. 네 절만. 갱신 26.09.19 11:22 KST · Claude Code(E:\Coding Infra 세션에서 이어받음)

## 완료
- v1 전수 분석 → docs/SPEC-v1-baseline.md(V1-01~43), 조사 → docs/RESEARCH-auth-quota.md, 결정 → DECISIONS.md
- 스캐폴딩(a0c72eb): 계약·cli/spawn·보안·빌드 설정
- 모듈 5개 병렬 구현 후 main 병합(충돌 0): shell 2494bee, codex 0a7b992, claude 6d23db9, grok 3c3ab42, renderer c632ece
- 통합(0cc0306), 리뷰 1차 수정(54ac8ab), 리뷰 2차 수정(92a9aa8)
- 26.09.19 위치 이동 복구: 소스가 C:\dev → `E:\Coding Infra\dev\ai-usage-widget`로 옮겨져 있었고(주체 미확인) src 141·resources 10 파일 누락 + node_modules 껍데기 → `git restore` + `pnpm install --frozen-lockfile`로 복구(DECISIONS 26.09.19 11:20)
- 26.09.19 CLI 설치 안내 URL 확정(`src/main/platform/links.ts` + `EXTERNAL_LINK_HOSTS` + `links.test.ts`), 세 주소 직접 열어 확인
- 검증(26.09.19 11:22, 새 위치): `pnpm verify` exit 0(49파일·539테스트), `pnpm build` exit 0, `pnpm dist:dir` exit 0, 배포본(`release\win-unpacked\ai-usage-widget.exe`) `--smoke` exit 0(ok:true, packaged:true, errors 0, windows·cspHeader·ipc·tray·autostart ok, koffi loaded, CLI claude 2.1.277·codex 0.155.1·grok 1.0.34)

## 진행중
- 없음

## 다음
- 사용자와 실측: T1 Codex device code 로그인·버킷·인증 페이지 호스트 / T2 Claude 파이프 로그인 / T3 statusline rate_limits 기록 / T4 Grok `_x.ai/billing` 응답·device-auth 출력 / T8 GUI(팝업 blur·topmost·전체화면·재질·테마 이벤트·오프셋 슬라이더 드래그 right·left 정렬·자동 시작 배포본)

## 막힌 것
- 사용자 결정 대기: 보조 모니터 배치(P-08·V1-18), 앱 제거 시 statusLine 자동 복원(SEC-06), 코드 서명(SEC-04 koffi.node 검증 대체)
- 실측 전 추정: codex 오류 문구 판정, grok billing 응답 형태·plan, claude needs-paste 타이밍
- 확인 필요: 누가 C:\dev를 옮겼는지(사용자 본인인지). 워크트리 잔재 `C:\dev\ai-usage-widget-wt`는 이동 후 어디에도 없음(09-15 04:10에 워크트리·병합 브랜치는 이미 정리됨 → 빈 폴더였을 가능성, 미확인)
