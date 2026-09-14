# STATE — AI Usage Widget v2
> 덮어쓰기. 네 절만. 갱신 26.09.15 05:10 KST · Claude Code(리뷰 2차 수정)

## 완료
- v1 전수 분석 → docs/SPEC-v1-baseline.md(V1-01~43), 조사 → docs/RESEARCH-auth-quota.md, 결정 → DECISIONS.md
- 스캐폴딩(a0c72eb): 계약·cli/spawn·보안·빌드 설정
- 모듈 5개 병렬 구현 후 main 병합(충돌 0): shell 2494bee, codex 0a7b992, claude 6d23db9, grok 3c3ab42, renderer c632ece
- 통합(0cc0306): 실제 어댑터 연결, 계약 변경 반영(DECISIONS 04:06)
- 리뷰 1차 수정(54ac8ab): CR-01~13·P-01~07·SEC-01~05 반영(DECISIONS 04:49)
- 리뷰 2차 수정: RR-01 위치 미리보기 중 팝업 고정(슬라이더 되먹임 제거), RR-02 settings:update 직렬화 + 저장 실패 시 자동 실행 등록 되돌림(DECISIONS 05:10)
- 검증(리뷰 2차): `pnpm verify` exit 0(48파일·535테스트), `pnpm dist:dir` exit 0(build 포함), 배포본 `--smoke` exit 0(ok:true, errors 0, CSP 일치, IPC 25/25, koffi loaded, CLI claude 2.1.270·codex 0.154.0·grok 1.0.30). 새 테스트 5건은 수정 전 코드에서 실패 확인

## 진행중
- 없음

## 다음
- 사용자와 실측: T1 Codex device code 로그인·버킷·인증 페이지 호스트 / T2 Claude 파이프 로그인 / T3 statusline rate_limits 기록 / T4 Grok `_x.ai/billing` 응답·device-auth 출력 / T8 GUI(팝업 blur·topmost·전체화면·재질·테마 이벤트·오프셋 슬라이더 드래그 right·left 정렬·자동 시작 배포본)

## 막힌 것
- CLI 설치 안내 URL(`EXTERNAL_LINKS`) 비어 있음: 공식 문서에서 확인한 https 주소가 필요(설치 안내 버튼은 not-found)
- 사용자 결정 대기: 보조 모니터 배치(P-08·V1-18), 앱 제거 시 statusLine 자동 복원(SEC-06), 코드 서명(SEC-04 koffi.node 검증 대체)
- 실측 전 추정: codex 오류 문구 판정, grok billing 응답 형태·plan, claude needs-paste 타이밍
