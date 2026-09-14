# CLAUDE.md — AI Usage Widget v2 (프로젝트 고유 규칙)

## 세션 시작 시 읽는 파일 (고정 목록)
1. `CLAUDE.md` (이 파일)
2. `DECISIONS.md`
3. `STATE.md`
4. `docs/HANDOFF.md`
- 서비스 조회 코드(`src/main/providers/*`)를 건드리기 전에 `docs/SPEC-v1-baseline.md`의 "v1 문제 목록"과 `docs/RESEARCH-auth-quota.md`를 읽는다.

## 무엇인가
Windows 작업표시줄 옆에 뜨는 AI 구독 사용량 위젯. v1(C:\AI.Usage.Widget-1.0.2-win, 소스 없음)을 재구성한 v2.

## 절대 규칙
- **가짜 수치 금지.** 조회 실패는 `error`/`unknown` 상태로 표시한다. 0%로 간주하지 않는다. 개발용 mock은 테스트 코드에만 둔다.
- **사칭 금지.** 공식 클라이언트 User-Agent·ideType·client ID를 흉내 내지 않는다.
- **다른 도구의 자격증명 파일에 직접 쓰지 않는다.** 로그인·갱신은 해당 공식 CLI가 한다. 위젯은 계정별 격리 폴더를 만들고 CLI를 그 폴더로 실행할 뿐이다.
- **토큰을 렌더러로 보내지 않는다.** 렌더러 DTO는 id·이름·provider·email·사용량만. 로그에 토큰·이메일 원문 금지(마스킹).
- 위젯이 직접 보관해야 하는 비밀은 `safeStorage`로 암호화한다.
- 렌더러는 `innerHTML`에 외부 문자열을 넣지 않는다(이스케이프 또는 textContent). CSP 필수.
- 원본 v1 폴더(C:\AI.Usage.Widget-1.0.2-win)는 읽기 전용 참고 자료다. 수정 금지.

## 환경
- Windows 11, PowerShell 5.1, Node v24.14.1, pnpm 11.7, git 2.53
- 설정 파일은 BOM 없는 UTF-8

## 검증 게이트
- 단일 명령 `pnpm verify` (typecheck + lint + test)의 종료코드로 판정한다. (스캐폴딩 시 정의)
