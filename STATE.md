# STATE — AI Usage Widget v2
> 덮어쓰기. 네 절만. 갱신 26.09.20 11:00 KST · Claude Code(E:\Coding Infra 세션)

## 완료
- v1 전수 분석 → docs/SPEC-v1-baseline.md(V1-01~43), 조사 → docs/RESEARCH-auth-quota.md, 결정 → DECISIONS.md
- 뼈대·모듈 5개·통합·리뷰 1·2차(09.15, 92a9aa8까지)
- 09.19 소스 위치 이동 복구(C:\dev → `E:\Coding Infra\dev\ai-usage-widget`, 주체 미확인), CLI 설치 안내 URL 확정, **Antigravity 공급자 추가**(공식 `agy -p "/usage"`, 계정 1개·위젯 로그인 없음, 요청 소모 차단기), Grok Bot 조사 → 카드 미추가
- 09.19~20 **실사용 실측 통과**: 사용자가 계정 4개(claude Max20·codex Pro20·grok Super grok Heavy·antigravity AI Pro) 추가·로그인, 기본 `~/.claude`에 브리지 설치(Orca statusLine을 감쌈, 09.20 10:48에도 유지·기록 갱신 중) → Claude 5H·WK, Codex 주간, Grok 주간, Antigravity 5H·WK 표시 확인(T1·T2·T3·T4·T6b)
- 09.20 Grok 파서 수정: 주간 리셋 직후 `creditUsagePercent`(=0) 생략 → 온전한 주간 config일 때만 0%. **확증됨**(10:49 재조회에서 29% 등장, DECISIONS 10:51)
- 09.20 Codex 실측: 서버가 주간 창만 줌(`secondary:null`) → 주간 한 줄이 정상. 첫 로그인 `protocol-error` 원인(취소된 신원 조회의 app-server가 죽기 전에 로그인이 같은 CODEX_HOME에서 새 app-server 시작) 수정 + 재현 테스트(7062332)
- 09.20 아이콘: Codex·Grok = 공식 SVG 경로를 투명 배경·테마 본문 색 벡터로(사용자 확인 완료), 단색 모드 + 밝은 테마 PNG 필터 수정
- 09.20 자동 조회 공급자별 최소 간격(claude 15·codex 60·grok 60·antigravity 120초) + 설정 탭 안내(619bdee). 계기: 사용자 설정이 15초라 `agy`가 거의 연속 실행되고 있었음
- 검증(26.09.20 10:57): `pnpm verify` exit 0(52파일·571테스트), `pnpm dist:dir` exit 0, 배포본 `--smoke` exit 0(ok:true, errors 0), 위젯 재실행. NSIS 설치 파일 빌드 exit 0(`ai-usage-widget-setup-2.0.0-alpha.0.exe` 106.9MB, oneClick·사용자 전용, 서명 없음) — **빌드만 확인, 실행·설치 안 함**
- T8 부분 실측(user32 조회, 화면 캡처 없음): 위젯 창 730×39 at (94,1397) = 작업 표시줄(0,1392~3440,1440) 안, visible·topmost. 팝업 380×440 hidden·topmost. Run 키에 위젯 항목 없음(`openAtLogin:false`와 일치)

## 진행중
- 없음

## 다음
- T8 나머지(사람 눈 필요): 팝업 blur 닫힘·깜빡임, 전체화면 앱에서 위젯 숨김, Mica/Acrylic 재질, 시스템 테마 전환 시 즉시 반영, 오프셋 슬라이더 드래그(right·left 정렬), 자동 시작 켜고 재부팅
- NSIS 설치 → v1 폴더·자동 실행 정리: 둘 다 사용자 확인 후 진행(DECISIONS 09.15 01:36)
- 원격 저장소 없음(로컬 커밋만). GitHub에 올릴지 사용자 결정 필요(만들면 private 권장)

## 막힌 것
- 사용자 결정 대기: 보조 모니터 배치(P-08), 앱 제거 시 statusLine 자동 복원(SEC-06, **NSIS 설치 전에 정하는 게 좋음**), 코드 서명(비용), Antigravity 위젯 막대 그룹(현재 첫 그룹 = Gemini Models)
- 미확인: Codex 2번째 로그인 시도의 `login-failed` 원인(로그만으로 불명, 미재현). `agy` 1회 실패(09.20 08:12 exit 1, status 비정상 — 1건뿐, 재발 시 조사). agy 로그아웃 출력 문구(정규식은 추정). Orca가 나중에 `~/.claude` statusLine을 덮어쓰는지(현재까지는 유지). C:\dev를 누가 옮겼는지
