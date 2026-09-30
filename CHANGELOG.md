# Changelog

모든 중요한 변경은 이 파일에 기록합니다.
형식: [Keep a Changelog](https://keepachangelog.com/), 버전: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- **`/vibe` 2.12.22 Antigravity 1.2.14 메타데이터 관측** — 현재 호스트에서 `/usage`가 성공·0턴·0토큰으로 끝나는 것을 확인하고 정확한 CLI 버전만 수집기 허용 목록에 추가했다. 계정·구독 포함 모델·AI 크레딧 초과 사용 차단·실행 어댑터는 확인되지 않았으므로 AGY 생성 라우트는 여전히 차단한다.
- **`/vibe` 2.12.21 Claude 실토론 후속 노드** — 단발 구독 CLI 어댑터가 검증·비용 정산된 양측 실제 답변을 해시로 묶어 Claude 반박과 별도 심판 호출에 전달하도록 확장했다. 다른 벤더 결과는 검증된 UTF-8 아티팩트와 별도 교차 전달 증거가 있어야 하며, 누락·변조·미검증·전달 미승인은 호출 전 차단한다. 다섯 노드 자동 실행, Codex/AGY/xAI 어댑터, 실제 청구/사용량·D-code·설치는 여전히 별도 게이트다.
- **`/vibe` 2.12.20 Claude 구독 CLI 단발 실행 경로** — 독립·읽기 전용·도구 없는 LLM 노드(토론 첫 입장 포함)에 한해 등록 계획/Store 새 claim, 고정 실행 파일·프로필·계정·모델·effort·쿼터 증거를 묶은 `execute_cli.py`를 추가했다. 같은 격리 환경의 `claude.ai` 인증 재확인, API/대체 공급자 환경 제거, 결과 파일의 배타적 생성과 재진입 조회 전용을 테스트한다. 응답은 자동 비용 정산·검증/후속 노드 허가가 아니며, 반박·심판과 Codex/AGY/xAI 직접 경로·실제 과금/실효 effort 검증은 미완료다. 사용자 설치와 `main`은 변경하지 않는다.
- **`/vibe` 2.12.19 실제 모델 토론 계획 계약** — 선택적 `debate` 입력을 서로 다른 벤더의 두 입장, 각 입장별 반박, 별도 심판의 다섯 고유 LLM 노드로 검증한다. 반박은 두 입장, 심판은 두 반박의 검증된 결과에 종속되며 반박의 표면·계정 변경과 단일 벤더 토론을 차단한다. 토론 구조는 실행·구독 청구·D-code의 증거가 아니며 직접 CLI/AGY/xAI/Bot 실호출은 별도 실행 게이트를 유지한다.
- **`/vibe` 2.12.17 자연어 메인 진입 경계** — 메인 오케스트레이터 요청에서 엉뚱한 절차를 고른 반례에 맞춰 첫 노출 설명을 명확히 하고 평가 사례를 추가했다. 같은 읽기 전용 Claude Sonnet 5.5 요청의 실제 `Skill` 호출이 이전 후보 `simonk-stack:skstack`에서 새 후보 `simonk-core:vibe`로 바뀌었다. GUI 진입 키워드 누락은 후보 내부 회귀 테스트가 잡아 복원했다. Codex 전체 subset 노출은 스킬 설명 예산을 초과했고 3스킬 시험의 본문 읽기는 정책에 막혔다. 따라서 한 사례의 Claude 선택 개선이며 Codex 본문 실행·선택률·실효 effort·구독 청구·사용자 설치를 인증하지 않는다.
- **`/vibe` 2.12.16 새 격리 후보** — 고정 원본 5플러그인으로 Claude 182스킬·Codex 일반 subset 177스킬을 재조립했다. 네 영수증, 공통 본문 176개·payload 612개 정적 패리티, 일회용 오프라인 실행 4단계와 네트워크 차단 Sandbox의 양호스트 적재/등록을 확인했다. 모델 생성·자동 선택·실효 effort·사용자 설치·구독 청구·전체 Gstack 런타임은 검증하지 않았다.
- **Gstack 로컬 기록·팀 초기화 활성 경로 격리 실측** — 고정 원본을 새 무인증·네트워크 차단 Windows Sandbox의 임시 저장소에 복제해 `learnings-log` 정상/거부 입력, `timeline-log`, `team-init` optional/required 5회 호출의 종료 코드와 예상 파일만 생성됨을 확인했다. 실패한 앞선 하네스 시도도 영수증으로 보존했다. 원본 사용자 저장소·설치본은 건드리지 않았으며 동기화/삭제 분기, 전체 전이 폐쇄성, Claude·Codex 호스트 동작 및 설치 준비는 인증하지 않는다.
- **Gstack 격리 런타임 안전 분기 실측** — 네트워크·클립보드가 꺼진 두 Windows Sandbox에서 고정 독립 원본의 6개 helper 비활성/읽기 분기 8회와 `spawned` 스킬 시작 프리앰블 1회를 실행해 기대 출력·게스트 상태·자격증명 부재를 확인했다. 사용자 홈·모델·API·Bot은 사용하지 않았으며 전체 Gstack 전이 폐쇄성이나 호스트 성능·설치 준비를 주장하지 않는다.
- **Claude·Codex 후보 정적 본문 패리티 게이트** — 5플러그인 Claude 후보와 출처가 검증된 Codex 일반 subset의 스킬 파일을 비교한다. 공통 176개는 완전 동일, `zoom-out` 1개는 수동 호출 정책에 필요한 정확한 frontmatter 투영만 허용하며, D-29 안전 스킬 5개 제외를 강제한다. 불일치·추가·누락은 실패한다. 정적 PASS를 실제 선택 품질·안전 훅 동등성 또는 설치 준비로 승격하지 않는다.
- **후보 경로 감사의 Markdown 링크 폐쇄성 확장** — 검증된 5플러그인 후보의 `SKILL.md`에서 백틱 경로 외에 단순 상대 Markdown 링크·이미지 자산도 중복 없이 검사한다. 현재 후보 182스킬의 명시 경로 검사는 144→176개로 확대됐고 미해결 0·비이식 명령 0이다. Gstack 전이 참조 31스킬·646건과 동적 import·서비스는 여전히 런타임 미검증으로 남긴다.
- **`app-dev-orchestrator` 1.1.1 호스트별 라우팅 경계** — 새 앱 21단계 절차가 고정 Opus 4.6·최고 effort를 강제하지 않고 `/vibe`의 최신 검증된 중앙 계획·품질·구독 게이트에 위임한다. Codex D-29 일반 후보의 제외된 안전 스킬 5개와 Claude hook 신뢰 여부를 구분하고, 누락된 안전 제어·별도 배포 권한을 조용히 생략하지 않도록 한다. 소스·오프라인 검증이며 실제 호스트 행동 동등성은 별도 실측이 필요하다.
- **`model-router` 0.2.5 소스·중앙 계획기 계약 수렴** — `/vibe`가 새로 지원하는 기획·복잡 코딩·간단 코딩·글쓰기 4개 유형을 기존 11개와 함께 문서·통합 테스트에 반영하고, 코딩 effort와 품질 하한(tier 2/3)을 별도로 검증한다. Core 원본의 2026-09-29 제조사·Artificial Analysis·X 근거 스냅샷을 소스 오버레이에 포함해 후보 조립의 누락 파일을 해소한다. Claude/Codex는 동일한 과제·수용 기준을 쓰되 실제 모델·스킬 로드·effort·산출의 동등성은 별도 호스트 실측까지 주장하지 않는다. 사용량 복구는 재검증 계기이지 유료 API·Bot 발주 허가가 아니다.
- **`vibe-bot` 0.9.4 현재 권한 우선 게이트** — 과거 Grok·모델 실호출 보류 문구를 현재 사용자 지시로 대체한다. 복구된 사용량은 구독 포함 경로의 조건부 사용 가능성을 뜻할 뿐, Bot/Relay 계정·쿼터·전송 승인·전체 비용 증거가 아니므로 실제 발주는 별도 게이트를 거친다. 추가 과금 $0, 초과 사용·자동 충전·유료 API 폴백 금지는 유지한다. 회귀 평가 사례는 이 둘을 분리하며 실제 Bot 전송이나 Claude/Codex 행동 동등성을 인증하지 않는다.
- **`/vibe` 2.12.7 과제별 라우팅 프로필** — 기획, 어려운 코딩, 간단한 코딩, 글쓰기를 기존 중앙 계획기의 별도 typed task로 분리해 최소 역량과 routine/reasoning 수요를 검증한다. 코딩의 노력 수준과 품질 하한을 분리해 단순 작업도 tier 2, 어려운 작업은 tier 3 이상만 후보로 허용한다. 제조사 발표와 Artificial Analysis의 2026-09-29 근거는 실행 허가가 아닌 후보 해석으로만 사용하고, 직접 확인할 수 없었던 X 의견은 규칙으로 승격하지 않는다. 이미지 생성은 검증된 전용 도구가 없으면 미해결로 남기며 텍스트 모델·Bot 또는 유료 API로 우회하지 않는다. Claude/Codex 실효 effort·실제 품질 동등성은 별도 관측이 필요하다.
- **Claude·Codex 기록 선택 교차 평가** — 호스트별 namespace를 유지한 두 평가 입력의 동일 과제·관측 모드를 확인하고, 양쪽 선택 정확도·한쪽만 실패한 사례·회귀를 오프라인으로 비교한다. 테스트용 관측이 없는 상태에서 실제 호스트 실행·스킬 본문 로딩·결과 품질 또는 구독 과금 안전을 인증하지 않는다.
- **`setup-deploy` 원본 평가 계약 통합** — 기존 플랫폼 감지 사례 2건을
  유지하며, 운영 플랫폼·URL 신호 충돌과 선택 CLI/헬스체크 실패·시크릿
  비노출 사례 2건을 추가했다. 장문 참조에 목차를 넣어 validator 경고를
  해소했다. 평가 dry-run은 실제 배포·호스트 행동·운영 주소 검증이 아니다.
- **`codex` 원본 평가 계약 통합** — 원본 Stack의 구독 전용 검토·리뷰와 머지/배포 승인 분리 사례 2건을 기존 리뷰·적대적 챌린지 사례에 더했다. 기존 사례의 무조건 실호출·검증 결과 단정은 비용·실행 증거 게이트에 맞춰 수정했다. 이는 평가 스키마 추가이며 자동 생성 Gstack 실행 본문의 비용 안전성, 모델 행동 또는 구독 과금 경로를 증명하지 않는다.
- **후보 간 플러그인 버전 충돌 감사** — 두 검증된 후보의 플러그인별 전체 파일(생성 manifest는 버전 필드만 정규화)과 버전을 대조해 내용 변경·동일 버전을 실패로 판정한다. v26→v28 AIHub 충돌을 재현하고 v28→v30의 불필요한 네 플러그인 버전 변경을 경고로 구분한다. 버전 계약 수정·사용자 설치·호스트 동작 검증은 아니다.
- **v30 flat 스킬 전체 파일 감사** — 검증된 후보 영수증과 같은 이름의 운영 스킬 직접 디렉터리만 읽어 상대 경로·바이트 해시를 비교한다. 링크·제외 경로·무관 스킬은 따라 읽거나 변경하지 않으며 7개 회귀 테스트를 추가했다. 현재 홈의 직접 디렉터리 133개는 전부 후보와 상이하고 세 경로 합계 링크 항목 143개는 보존·미검사다. 이는 설치 이관이나 행동 검증이 아니다.
- **`simonk-report` 브라우저 회귀** — 격리된 로컬 Chrome에서 값이 채워진 HTML 템플릿의 모바일 탭·키보드·메모 저장/복원·복사 실패 대체·다크 모드·인쇄/PDF·페이지 외부 요청 없음을 18개 검사로 재현한다. Chrome/Node 부재 환경에서는 건너뛰며 실제 보고 생성·파일 발송·타 브라우저 동작이나 설치 준비를 인증하지 않는다.
- **Gstack 직접 helper 격리 실행** — 고정 원본의 9개 Bash helper를 네트워크 차단·무인증 Windows Sandbox의 임시 프로젝트에서 지정 설정으로 9/9 실행했다. 게스트 프로젝트 변경은 `CLAUDE.md` 하나였고 동기화 큐·텔레메트리는 0이다. 기본 설정·삭제 분기·전이 의존성 및 사용자 설치 준비를 인증하지 않는다.
- **고정 Gstack 원본 감사** — 읽기 전용 Git/tree/index·작업 파일 영수증 검사가 mode `120000`의 `connect-chrome`을 패키징 차단 항목으로 확인한다. 원본 크기와 해시를 재현 가능하게 기록하지만 helper 전이 폐쇄·호스트 동작·설치 준비는 입증하지 않는다.
- **Gstack 대표 종료 경로 격리 증거** — 고정 원본의 qa·retro·ship 시작→종료 3/3과 동기화 호출 6/6을 네트워크 차단 Sandbox에서 확인했다. 설정 OFF에서 로컬 텔레메트리·큐 0이며, 전체 Gstack 런타임 폐쇄나 사용자 설치 증거는 아니다.
- **v20 Claude 초기화 검증** — 무인증·네트워크 차단 Sandbox에서 Claude Code 2.1.283의 대조군과 5플러그인 후보 `--init-only`가 모두 종료 0이었다. 후보 로그는 5플러그인·182스킬·5명령 로딩, 오류 0을 확인했다. 기존 사용자 프로필 호환성, 실제 스킬 동작, 모델·구독 과금 검증은 아니다.
- **v20 격리 설치·철회 증거** — 네트워크 차단 Windows Sandbox의 새 무인증 Claude·Codex 프로필에서 5플러그인 설치·활성, 각각 734/740파일의 영수증 바이트 일치와 철회를 확인했다. Gstack 시작 절차 55개도 별도 격리 시험에서 통과했다. 이는 사용자 프로필 전환, 전체 스킬 실행, 외부 런타임 폐쇄 또는 구독 과금 검증이 아니다.
- **Guarded `/vibe` Claude preview** — `scripts/preview-vibe-candidate.ps1` verifies the immutable five-plugin receipt by default without a model call. An explicit, subscription-confirmed `-Run` offers a Core-inline, plan-mode, Skill-only routing preview, blocks API/alternate-provider environment routes, and requests claude.ai MCP connector suppression only in that child process. This preview does not install plugins or certify billing, connector suppression, other host paths, actual tasks, or context savings.

### Changed
- **v28 AIHub 제품 모델 선택 핀** — 원본 기능 브랜치에서 구형 정적 모델 ID와 제품 API/대화형 구독 과금 혼동을 교정한 SimonKAIHub를 고정했다. 새 5플러그인 후보·Codex 오버레이·일반 subset은 바이트 영수증을 재검증했고 저장소 회귀 341건은 338통과·3건너뜀이다. v26과 v28의 AIHub 표시 버전이 같아 설치 갱신 위험이 추가로 확인됐으며, Gstack 외부 런타임과 실제 호스트·계정 검증도 남아 있어 설치 준비는 false다. 사용자 설치본·main·과금 설정은 변경하지 않았다.
- **`/vibe` 공개 Claude Sonnet 5.5 사실 갱신** — 2026-09-28 출시 모델·API effort·Claude Code 최소 버전·직접 API 표준 가격을 레지스트리에 추가했다. `sonnet` 별칭을 이전 Sonnet 5의 확정 별칭으로 취급하지 않고 새 모델 후보로 옮겼으며, 이전 라인의 전환은 transport·canary 검증 대기로 유지한다. 구독 포함 여부·실제 모델 접근·호스트 라우팅·과금 안전은 확인하지 않았고 실호출도 하지 않았다.
- **`/vibe` 2.11.16 progressive disclosure** — moved the generated historical Orca lane table into a directly linked reference and retargeted its drift checker. Normal skill loading omits the legacy table; the generator, safety guards and frontier runtime routing are unchanged. This does not reduce the initial five-plugin description footprint or prove model/host behavior.

### Fixed
- **이미지 생성 라우팅 경계와 독립 설치 fixture** — `IMAGE_GENERATION`을 텍스트 `VISION`과 구별되는 차단 계획 단계로 보존하고, 독립 설치 테스트 두 곳에 필수 `task-fit-policy.json`을 포함했다. 저장소 테스트 387건은 3건 조건부 skip 외 통과했다. 전용 구독 포함 이미지 도구나 실제 생성 기능을 추가한 것은 아니다.
- **`ship` 1.0.1 출시·과금·호스트 경계 교정** — 원본의 최신 재검증·추가 과금 $0 평가 사례를 보존하고, 자동 base 머지·모든 미커밋 파일 포함·유료 judge 필수 실행·Codex/Claude 무료 단정·무조건 push/PR·`git add -A` 문서 동기화를 사용자/저장소 권한과 구독 포함 증거에 종속시켰다. Claude 도구명을 Codex 호스트 기능에 대응시키되 동일 출시 게이트를 유지하는 사례를 추가하고 장문 참고문서에 목차를 넣었다. 정적 평가·저장소 회귀만 수행하며 실제 모델 행동, 유료 평가, 배포, 사용자 설치, 양 호스트 성능 동등성을 인증하지 않는다.
- **`security-checklist` 1.0.1 보안 판단 교정** — 원본의 사용자/IP 제한·3계층 예산 누락 사례를 소스 평가에 복원하고, RLS 정책 존재와 활성화의 혼동, 행 정책의 열 보호 오인, 모든 TossPayments 웹훅 서명 가정, OpenAI soft budget을 hard cap으로 간주한 지침을 바로잡았다. SQL 예시는 운영 변형 실행을 금지하고 권한별 결과를 구분한다. 평가는 스키마 dry-run이며 운영 DB·실결제·유료 API·모델 행동 검증은 아니다.
- **`paid-api-guard` 1.0.1 유료 API 감사·비용 경계 교정** — 원본의 Twilio SMS 유출 의심/비용 폭증 감사 사례를 소스 평가에 복원하고, Stripe 공개 키 `pk_` 오탐, 처리 전 웹훅 완료 표시, 브라우저 HMAC·BFF·고정 비율·실결제 중복 시험 강제 등 위험한 단정을 제거했다. 공급자 알림은 하드 지출 차단이 아님을 명시하고 추가 과금 $0 사례를 추가했다. 평가는 스키마 dry-run이며 모델 행동·운영 결제·문자 발송을 검증하지 않았다.
- **`authz-designer` 1.0.1 설계·감사 경계 교정** — 원본의 교차 테넌트 IDOR 감사 사례를 소스 평가에 복원하고, 단순 소유자 비교를 무조건 취약점으로 판정하거나 감사 요청에 DDL·운영 변경을 요구하던 지침을 바로잡았다. 선택적 SQL 예시의 Supabase·PostgreSQL 15+ 전제를 표시하고 nullable UNIQUE 중복 위험을 줄였다. 평가 3건은 스키마 dry-run이며 실제 보안 감사·운영 DB 테스트·모델 행동 검증은 아니다.
- **`vue-best-practices` 2.0.1 원본 계약 통합** — 기존 Options API·상태 소유권·실측 성능 작업을 보존하고, Pinia 직접 상태 변경 및 Vue 3.5+ props 구조분해에 대한 잘못된 오류 판정을 바로잡았다. 원본 라우팅·동작 사례 5건과 새 공식 동작 회귀 2건을 소스 평가에 포함했다. 모델 행동, 사용자 설치, 브라우저 성능은 아직 검증하지 않았다.
- **`vercel-react` 0.1.3 라우터·캐시 모델·배포 경계 교정** — 원본의 React/Next.js 기존 프로젝트·실측 우선 원칙을 반영하고 Pages Router/React 단독 앱에 App Router 지침을 강제하지 않는다. Cache Components와 이전 캐시 모델을 분리하고 `updateTag`·Proxy/런타임·Suspense·Server Action 예시의 단정을 바로잡았다. 원본 트리거 3건과 새 회귀 3건을 소스 평가에 추가했으나 모델 행동·브라우저·운영 배포를 검증한 것은 아니다.
- **`building-native-ui` 2.0.1 프로젝트 우선·빌드 경계 교정** — 고정 Expo 56·RN 버전과 FlashList/NativeWind/Expo Router 강제를 제거하고 원본의 기존 앱·Android APK/Studio·iOS 증거·EAS Submit 게이트를 반영했다. Expo Babel 자동 구성, Metro exports 전역 폴백, Windows EAS 로컬 빌드 제약도 공식 문서에 맞춰 조건부로 수정했다. 원본 5개 회귀 사례를 소스 평가에 이식했으나 모델 라우팅·실제 APK/스토어 동작을 검증한 것은 아니다.
- **`stack-architect` 1.0.1 고정 배포비·인프라 단정 제거** — 사용자 수별 공급자·월 비용·Kubernetes 도입표를 요구량 기반 검토로 바꾸고, 기존 스택·실측 부하·공식 가격·초과 과금 조건을 먼저 확인한다. 로컬 AI·관리형 실시간 등 대안을 열어 두고, 아키텍처 문서를 배포 승인으로 취급하지 않는다. 원본 회귀 2건과 교정한 기존 사례 2건을 포함하되 모델 선택 행동·실제 배포를 검증한 것은 아니다.
- **`db-selector` 1.0.1 무료 한도·비용 단정 제거** — 오래된 서비스별 무료 용량과 사용자 수별 고정 월 비용을 후보 검토 항목으로 바꾸고, 기존 DB·마이그레이션·실측 사용량·공식 가격 확인일을 요구한다. 추가 과금 $0 조건에서는 유료 DB 생성·초과 사용·자동충전을 실행하지 않으며 원본의 회귀 사례 2건을 더했다. 모델 선택 행동이나 실제 서비스 생성은 검증하지 않았다.
- **`phase4-game-orchestrator` 0.1.1 과거 상태 제거** — 지난 Phase 4 일정·Godot 설치·Suno 가격·Android 출시·42morrow 자료 수를 현재 사실로 취급하던 문구를 관측 조건으로 바꿨다. 게임 구현 요청은 `/vibe`의 실제 빌드·검증으로 연결하고, 원본의 비용·라이선스 평가 2건과 교정한 기존 사례 2건을 유지한다. 모델 행동·에셋 생성·스토어 게시가 검증됐다는 뜻은 아니다.
- **`app-platform-selector` 1.0.1 심사 단정 제거** — Apple 공식 §4.2의 최소 기능 요건에 맞춰 PWA·WKWebView의 승인·거절을 보장하던 문구를 위험 기반 검토로 교정하고, 기존·원본 평가 사례를 함께 유지했다. 플랫폼 비교와 유료 개발자 등록·스토어 제출을 분리한다. 실제 심사 승인이나 모델 행동 검증은 아니다.
- **`/vibe` 2.12.6 레거시 실행 안내 정정** — 과거 함정·Astra effort 참고문서의 raw worker 재시도·종료·터미널 전송, 직접 Codex 실행, 무료라고 단정한 effort 탐침을 사고 기록으로 분리했다. 현재 중앙 계획·구독 포함·비용·조회 전용 복구 계약을 명시했으며 실행 어댑터, 사용자 설치본, 결제 설정은 변경하지 않았다.
- **원본 플러그인 Windows CI 로캘** — AIHub·Core·Design·Market의 Python 품질 게이트가 기본 CP949 콘솔에서 UTF-8 자식 출력을 읽다가 실패하던 경로를 고쳤다. 각 원본의 회귀 검사 4/4와 품질 게이트 7/57/19/32를 통과한 커밋을 고정 입력에 반영했고 v24 격리 후보의 바이트 영수증을 재검증했다. Codex 기본 catalog·Gstack 전이 런타임·사용자 설치 준비는 아직 미해결이다.
- **프로필 계획 회귀 fixture** — 기존 무료 로컬 도구 사례에 필수 `nonmetered`·전이 효과 감사 선언을 추가해 강화된 비용 가드와 일치시켰다. 실제 판정 로직이나 사용자 과금 설정은 변경하지 않았다.
- **`/vibe` 2.11.14–2.11.15 immutable-bundle CLI safety** — plain Python entrypoints now disable bytecode before their first local import; the six legacy/user CLIs have isolated subprocess regressions. Parent `-B` does not cover child Python, so bundle tests also set `PYTHONDONTWRITEBYTECODE=1` and reverify the receipt. v14 source and five-plugin candidate passed offline tests without digest drift. This does not verify actual host routing, subscription billing, live dispatch or installation readiness.
- **`vibe-bot` 0.9.3 natural GUI over-trigger** — a bounded v10 Claude Max skill-name probe still selected `vibe-bot` for a fresh Play Console request without loading `Skill`. The adapter description now contains only explicit Bot requests or a verified internal `/vibe` handoff; the regression case uses the observed prompt. This changes discovery metadata only and needs a fresh host-selection measurement; no Bot work was dispatched.
- **`vibe-bot` 0.9.2 implicit GUI routing boundary** — a single Claude Max Play Console skill-name probe answered `vibe-bot` without invoking `Skill`, although ordinary GUI requests should enter `/vibe`. The adapter description now reserves `vibe-bot` for explicit Bot requests or a GUI-only step already verified by `/vibe`; an evaluation case records the expected boundary. Offline validators and fixtures do not prove improved live selection, and no Bot task was sent.
- **`/vibe` 2.11.13 GUI discovery** — a bounded Claude Max subscription probe with tools disabled named a nonexistent Play Console specialist instead of the installed `/vibe`/`vibe-bot` pair. The main skill description now includes natural-language Play Console/GUI requests, the CLI/API/MCP-first boundary and the real adapter name; a regression and evaluation case cover the text contract. This does not prove live model selection or authorize Bot delivery. Claude CLI reported a USD cost-equivalent field for the probe; no second generation was attempted and account billing was not independently verified.
- **`/vibe` 2.11.12 Antigravity metadata compatibility** — locally verified CLI 1.2.12 `/usage` returns zero turns and zero tokens, then added only that exact version to the read-only collector allowlist. The observation does not establish account billing, model inclusion, generation availability or permission to use a direct CLI fallback.
- **Packaged `/vibe` self-test layout** — the catalog test now verifies the receipt-bound five-plugin candidate instead of assuming a source checkout, and the TDD guard regression reads the packaged Stack resource when present. Its CLI round-trip disables bytecode writes so the immutable candidate receipt remains valid after testing. Both source and packaged 82-case runs pass without weakening candidate discovery or the guard.
- **Discovery trigger follow-up** — restored the Korean phrases "오르카로 돌려", "하이드레이션 에러" and "스크린리더 테스트" in the compact `vibe` 2.11.6, `vercel-react` 0.1.2 and `accessibility-audit` 0.1.2 descriptions, without changing their bodies. Codex invocation guidance now uses the actual registered namespace. Added 30 controlled primary-skill selection cases and an offline scorer; missing observations remain pending, not a model-accuracy pass.
- **`/vibe` 2.11.4 / `vibe-bot` 0.9.0 user-test update** — applies Simon's 2026-09-24 Grok Bot organization snapshot (19 bots, six teams). New tasks/results use Relay only while preserving specialist identity; both Relay and specialist status gate publication. Analytics, AdMob and QA are distinct owners; `web-qa` remains unresolved Relay triage. Explicit free/reversible draft saves retain payment/publication/delete/credential hard stops. Previous specialist plans require their preserved original adapter; no automatic migration or resend. Offline tests cover the new routing; no live model/Bot validation is claimed.
- **`/vibe` 2.11.3 / `vibe-bot` 0.8.1 contract alignment** — the main runbook now consumes the durable Bot hub adapter and pinned result checks introduced in 0.8.0. Legacy unbound verification and collect exit codes cannot establish central completion. Bot evals cover observable draft, routing, recovery, acceptance and cost outcomes rather than manual paste or retired hub/webhook delivery. Source/fixture validation is not live Relay/account proof, model-mode measurement or installation.
- **Benchmark freshness truthfulness** — raw collection never edits Wiki timestamps/content/logs or the routing registry. Empty, failed, unimplemented, malformed or partial collections return `2` without replacing a prior cache; `--dry-run` writes no files. Successful snapshots remain explicitly unverified with an attempt timestamp and unknown data-as-of date. Cache replacement is atomic, and offline fixture regressions are included in skills CI. The external Wiki cron still needs separate exit-code integration; this is not a completed live benchmark refresh.

### Added
- **Relay 양방향 핸드셰이크** — 승인된 협업 루프에서 저장 상태 기반 읽기 전용 bus 감시, 코딩 과제·답변 우선 처리, 중복 운영 쓰기 확인 및 1회 알림 규칙을 연결했습니다. 기존 추가 과금·작업 발송·운영 변경 승인 게이트는 유지합니다.
- **`/vibe` 2.9.0 guarded Orca adapter** — registers native Task/spec, runtime, executable and exact workspace bindings with the durable plan; fresh account/billing evidence and an internal atomic claim gate one start. Lookup-only recovery, bounded CLI output and metadata-only result reporting preserve unknown costs without automatic retry, cleanup or acceptance. Local Claude/Codex flag-effort lanes only; Grok generation remains held, live billing/E2E and installed-version parity are not established.
- **`apps/ai-usage-widget/`** — Windows 작업 표시줄 AI 사용량 위젯 v2(Electron 44)를 이력 포함(git subtree)으로 통합. 공식 CLI 경로만 사용(Claude statusline 브리지, `codex app-server`, grok ACP billing, `agy -p "/usage"`), 가짜 수치·클라이언트 사칭 금지. 자체 `CLAUDE.md`·`DECISIONS.md`·`STATE.md`·`docs/` 포함.
- **`/ai-usage-widget-install`** (skills-src) — 위 위젯을 소스에서 빌드·검증(`pnpm verify`)해 사용자 전용 NSIS로 설치, `-Status` 점검, Claude 브리지가 남아 있으면 거절하는 `-Uninstall`. PowerShell 5.1 호환 스크립트 포함.
- `NOTICE` Trademarks 절 — 위젯에 쓰인 타사 마크는 MIT 범위 밖임을 명시.

### Changed
- **Skill discovery context** — compacted 12 routing/long descriptions while preserving skill bodies and safety controls; removed the 400-character authoring minimum. Codex duplicate exposure can be disabled by exact path without uninstalling skills. This is metadata optimization, not a claim of measured model routing accuracy or elimination of every host budget warning.
- **HTML 보고서 규칙 정렬 (지침 v8.1.1 · `html-default-output` 1.1.0 · `simonk-report` 1.1.0)** — 단일본 §6 'S 필수' 줄에 "스킬·템플릿과 다르면 바닥선이 이긴다"를 보강하고, §1 시각 명령을 `TZ=KST-9 date` 로 바꿨다(Git Bash 에서 `TZ=Asia/Seoul` 은 UTC 반환). `html-default-output` 은 길이 기준(100줄)을 버리고 §2 의 6개 목적을 따르며, 인터랙션 깊이를 L1~L4 → Lv1~Lv4 로 바꿔 §6 등급 S/M/L 과 구분했다. `simonk-report` 템플릿을 §6 S 등급으로 다시 썼다: 라이트/다크 자동 · 3색 · 한국어 절 이름 · 요약/상세 탭 · 메모 사이드바(localStorage→메모리, 복사 3단 폴백) · 다운로드 배너 · JS 가 꺼져도 본문 표시. 134개 스킬의 '완료 보고' 블록에 남은 "무JS" 문구는 이번에 고치지 않았다 — §6 우선 규칙으로 해소되며, 일괄 수정은 별도 결정.
- `CLAUDE.md` — "앱 코드 없음" 규칙에 `apps/ai-usage-widget` 예외와 그 폴더의 검증 방법을 추가.

## [1.7.0] — 2026-06-16

Sprint v38 — HTML 완료 보고 표준. 137 skill 일괄 적용. validator 0 error.

### Added
- **HTML completion-report standard appended to all 137 skills (skills-src + dev)** — every skill emits a self-contained HTML report with progressive-disclosure `[자세히]` buttons on completion. 단순 한눈 요약 + 직관적 inline-SVG 차트/이미지, 각 항목은 `[자세히]` 버튼 뒤 progressive disclosure.

## [1.6.0] — 2026-06-07

Sprint v37 — 디자인 시스템 영속화. 1 신규 skill. validator 130/130 pass / 0 error.

### Added — 1 new skill

차용·종합 출처: `anthropics/claude-code` frontend-design skill + `Dammyjay93/interface-design` 플러그인.

Product & Design (1):
- `/design-system-keeper` — 디자인 시스템을 세션 너머 영속·강제. 6 방향(Precision/Warmth/Sophistication/Boldness/Utility/Data) 선택 → `.design-system/system.md` 토큰 캡처·자동로드 → 기존 코드서 토큰 extract → 컴포넌트 drift audit. frontend-design의 distinctiveness(비-제네릭 방향성·분위기)와 interface-design의 persistence(system.md·audit)를 통합하고, Simon의 anti-slop 규칙(≤3색·no-gradient·Pretendard, 2nd-B DESIGN.md)과 조화(충돌 시 프로젝트 규칙 우선). `references/direction-and-aesthetics.md` 포함, `evals/cases.json` 3 케이스.

### Note
- simon-design-first(인테이크)·consistency-guard(데이터 일관성)·design-system-page(1회성 카탈로그)와 중복 회피 — design-system-keeper는 영속 system.md + audit 루프 담당.

## [1.5.0] — 2026-05-28

Sprint v36 — 외부 카탈로그 흡수. 11 신규 skill + 3 기존 skill 보강. validator 132/132 pass / 0 fail.

PR 머지: SimonK-stack #22.

### Added — 11 new skills

차용 출처: `zarazhangrui/frontend-slides`, `robonuggets/{design-system, html-it}`, `OpenSenseNova/SenseNova-Skills`, Claude Skills 2026 slide deck.

Engineering domain (5):
- `/vercel-react` — Next.js + Vercel best practices (Server vs Client Components, Edge runtime, ISR/SSR/SSG, hydration debugging)
- `/vue-best-practices` — Vue 3 Composition API + Pinia state management
- `/building-native-ui` — React Native + Expo (expo-router, FlashList, Reanimated, EAS)
- `/remotion-best-practices` — programmatic video (TypeScript + React composition/sequences)
- `/scientific-paper` — LaTeX + BibTeX + matplotlib/plotly + IEEE/ACM/Nature format (renamed from `claude-scientific` due to reserved-word rule)

Product & Design (2):
- `/slides` — zero-dep HTML 16:9 slides, 3 visual preview → pick pattern
- `/design-system-page` — design.md → design-system.html + A4 brand-book PDF

Knowledge & Memory (1):
- `/notebooklm-import` — YouTube transcripts + PDF + web → SimonKWiki pages

Skill DevOps / utilities (3):
- `/find-skill` — search awesome-claude-skills (26k★) + internal INDEX
- `/office-docs` — Docx/Xlsx/Pptx/PDF generation (Anthropic Big Four)
- `/web-publisher` — automated login + form fill + upload (browse + auth)

### Changed — 3 existing-skill boosts (no new skills)

- `html-default-output` — 4-level complexity classification 추가 (L1 Static / L2 Visual / L3 Interactive / L4 Throwaway tool). 차용 출처 `robonuggets/html-it`.
- `simonk` — Phase 1.4 Doctor Check 추가 (env health: git/network/disk/auth) — Boundary Check 직전, 기존 `gcloud-helper` skill 통합. 차용 출처 OpenSenseNova SenseNova-Skills.
- `simonk-report` — Optional VLM 품질 자체 검증 (chromium screenshot → vision 5-axis 점수 → <7/10 시 1회 auto-fix). opt-in `SIMONK_REPORT_VLM=on` env. default OFF, ~$0.05/회.

### Changed — catalog

- `.claude/skills/INDEX.md`: 8 신규 entry 를 Design / Implementation / Learning&Memory / Utilities 섹션에 추가
- `README.md`: 8 부서 표에 신규 skill 매핑 (Product&Design +2, Engineering +1 row, Knowledge&Memory +1, Skill DevOps +4), badge 120+ → 132+
- `README.en.md`: badge 107 → 132, sprint v36 absorption section 추가

### Notes

- 사용자가 본 흡수 결정에서 14 항목 전부 도입을 선택 (assistant 의 4 항목 권장과 반대). 토큰 비용 + 정체성 drift 우려는 commit body 에 기록. 실제 사용 빈도를 다음 세션부터 모니터링; 저사용 skill 은 향후 polish sprint 의 deprecation 후보.

## [1.4.0] — 2026-05-27

Sprint D — 전체 스킬 chain audit, Wiki 정합성, 설치 ease, 100% functional perfection.

PR 머지: SimonK-stack #9 #10 #11 #12 #13 + SimonKWiki #4 + 2nd-B #18.

### Fixed — Install & hook critical
- **B1** `scripts/install.sh`: 수동 install 시 `skills-src/` 90+ 스킬 누락 (이전엔 `.claude/skills/` 만 sync). (#9)
- **B2** `scripts/install.sh` + `.claude/hooks/session-start.sh`: "existing → skip" 정책으로 글로벌 영구 stale → `git pull` 가 반영 안 되던 문제. install.sh `--force` flag. session-start.sh SHA-aware 선택적 overwrite (installed-SHA ↔ current-SHA git diff 로 changed-skill set 만 force overwrite) + `SIMON_STACK_FORCE_SYNC=1` env. (#9)
- **B2-bis** `.claude/hooks/session-start.sh`: SHA-diff sed 명령이 separator `|` 와 ERE alternation `|` 충돌 → CHANGED_SET 추출 silently fail → B2 fix 가 사실상 작동 안 함. separator `#` 으로 교체. (#10)
- **C1** `connect-chrome` 폴더가 `open-gstack-browser` 와 동일 `name:` field → Claude Code dedupe → zombie. install/hook 의 sync loop 에 명시적 skip. Gstack auto-generated SKILL.md 라 직접 수정 금지. (#13)

### Fixed — Skill chain orchestration
- 5 SKILL.md self-reference 슬래시 alias 가 frontmatter `name` 과 불일치 → 정확한 이름으로 변경: `/ohmo` → `/simon-ohmo`, `/phase4-game` → `/phase4-game-orchestrator`, `/session-export` → `/session-context-export`, `/keepass` → `/keepass-helper`, `/gcloud` → `/gcloud-helper` (`docs/CURATED-SKILLS.md` 포함). (#9)
- `simon-design-first` Step 5: 4 → 7 design skill 전체 chain 으로 확장. `/plan-design-review` + `/design-review` 가 위임 분기에서 빠져있던 문제 해결. (#11)
- `app-dev-orchestrator` 단계 3.5 (`simon-design-first` proxy) 신규 — description 이 명시한 "mandatory proxy before /design-consultation 등" 계약을 본문 chain 에 반영. (#11)
- `simon-design-first` Step 5.5: 5 시나리오 decision matrix (zero-to-one / existing refactor / live polish / variant only / external Stitch only) — chain bloat 방지 + LLM 가지치기 가능. (#12)
- `simon-research` description: orchestrator coverage 를 `app-dev-orchestrator` 에서 `dev-orchestrator` + `security-orchestrator` 까지 확장. (#13)
- `payment-integrator` Related Skills: `subscription-manager-selector` back-ref 추가 (asymmetric link graph 해소). (#13)
- `test-gen` Related skills trailer 추가 (canonical 4-skill cross-ref). (#13)
- `wiki-ingest` / `wiki-query` / `wiki-lint`: bidirectional cross-refs 추가 (3 skill 이 같은 vault 다루는데 서로 무링크였음). (#13)

### Fixed — Docs / Wiki
- `templates/CLAUDE.md`: simon-stack "13개" 표기 → "100+개" + 카테고리 재정리 (Orchestrator / 방법론 / 보안 / 그로스·수익화 / 도구·헬퍼). (#9)
- `docs/USING-IN-OTHER-REPOS.md`: stale 카운트 (24개 / 28+ / 55+ / 60+) → 100+ 통일. (#9)
- `README.md` / `README.en.md`: "0 errors / 0 warnings" → "0 errors / 56 minor warnings" (실측, description score 등 비차단). (#10)
- `docs/INSTALL.md`: 36 Gstack / 24 simon-stack → 38+ / 100+ + `~/.claude/.simon-stack-installed` marker 안내 추가. (#13 follow-up)
- **SimonKWiki PR #4**: `wiki/entities/tools/getdesign-md.md` 의 broken `[[design-consultation]]` / `[[design-shotgun]]` / `[[simon-design-first]]` → backtick (skill names, not wiki pages). `wiki/index.md`: last-updated 2026-05-25 → 2026-05-27, 페이지 카운트 메인 89→129, total 115→155.

### Fixed — Downstream (2nd-B repo, PR #18)
- `.claude/settings.json`: inline-bash hook → `templates/bootstrap-session-start.sh` 정식 위임 형식.
- `.claude/hooks/session-start.sh` (신규): bootstrap script + `SIMON_STACK_REPO` default 를 `Simon-YHKim/SimonK-stack` 로 명시 (transferred URL redirect 의존 제거).
- `CLAUDE.md`: ghost slash commands `/context-save` / `/context-restore` → `/checkpoint` + `/context-guardian`.

### Added
- `scripts/install.sh`: `--force`, `--no-backup`, `--help` flags. install 후 `~/.claude/.simon-stack-installed` 에 SHA 기록.
- `.claude/hooks/session-start.sh`: SHA-aware selective overwrite + `SIMON_STACK_FORCE_SYNC=1` env var.
- 2nd-B 같은 다운스트림 repo 의 정식 bootstrap hook 패턴 (templates/bootstrap-session-start.sh + bootstrap-settings.json) 검증·문서화.

### Verified
- 108 SKILL.md 모두 `validate_skill.py` 0 errors (56 minor warnings — W013 long ref no-TOC 33 / W009 path resolve 15 / W006/W007/W004 8 — 모두 비차단, cosmetic).
- 106 unique invocable skills (connect-chrome dedupe 후).
- 6 orchestrator chain + 7 design skill chain + 6 chain category 전수 audit (Planning / Implementation / Security / Ship & Deploy / Growth & Monetization / Korean & Helper / Wiki & Memory) — chain integrity strong.
- Wiki health: lint-report v4 후 mostly-healthy (E3→E0 after fix, W2 user-judgment 잔존).
- End-to-end: 2nd-B bootstrap hook → `~/.simon-stack-src` clone → upstream session-start.sh delegate → global `~/.claude/skills` sync 정상 동작.

### Follow-ups
- gstack upstream 99 commits behind (`~/.claude/skills/gstack/` 38 modified files) → 사용자 직접 `/gstack-upgrade` 호출 권장 (destructive 변경 위험 — 자동 처리 안 함).
- W009 false-positive 다수 (`scripts/X.ps1` 가 repo-root 기준인데 validate_skill.py 가 skill-folder 기준 resolve) → upstream Skill-Agent (`Learner-thepoorman/Skill-Agent`) PR 별도.
- W013 (reference 파일 > 400 lines + no `## Contents`) → 33 references TOC 추가 별도 작업.
- Windows-native `install.ps1` (bash 의존 제거) — 다른 머신용 nice-to-have.

## [1.3.0] — 2026-04-16

### Changed — Token optimization + README rewrite
- **구조 분리**: `.claude/skills/` 20개 → `skills-src/` 16개 + `.claude/skills/` 4개 (commit, review, skill-gen-agent, context-guardian)
  - 매 tool call 마다 55+ skill description 이 system-reminder 로 주입되던 토큰 폭발 해결
  - `skills-src/` 는 Claude Code 가 무시 → 개발 중 토큰 사용량 극감
  - 설치 시 hook 이 양쪽 모두 `~/.claude/skills/` 로 복사 (기존 동작 유지)
- **session-start.sh** — `skills-src/` + `.claude/skills/` 양쪽에서 복사하도록 수정
- **setup-repo.sh** — vendor mode 소스 복사 + embedded hook 동일 수정
- **CLAUDE.md** — 디렉토리 구조, 검증 명령, 금기 경로 업데이트

### Docs
- **README.md** — 1,675줄 → 308줄 (81% 축소). 카탈로그 테이블 + 간결한 구조로 리라이트
- **docs/SKILL-REFERENCE.md** — (신규) 상세 skill 알고리즘 문서 (README 에서 분리)

## [1.2.0] — 2026-04-14

### Added — Meta + session management
- **`skill-gen-agent`** — vendored from `github.com/Learner-thepoorman/Skill-Agent`.
  Provides `validate_skill.py`, `test_skill.py`, `refactor_skill.py`,
  `version_log.py`, `install_skill.py` scripts + references + templates
  for creating and improving Claude Code skills from within the repo.
- **`context-guardian`** — 3-mode skill for Claude Code session health:
  - Prevention: inserts `<!-- context-guardian-rules:v1 -->` block into
    CLAUDE.md + generates `.claudeignore` (idempotent)
  - Monitoring: `context_limit_log.json` with measured-not-hardcoded
    token limits, `--load` / `--record` / `--check` subcommands,
    80% / 90% threshold warnings
  - Recovery: `SESSION_RECOVERY.md` generator with git state auto-fill,
    secret-pattern abort, ready-to-copy next-session prompt
- 3 bundled scripts: `install-rules.sh`, `create-recovery.sh`,
  `update-context-log.sh`
- `references/templates.md` documenting all 4 output artifacts
- `evals/cases.json` with 4 test cases per skill

### Validated
- All 20 skills pass `validate_skill.py` with 0 errors / 0 warnings
- Both new skills pass `test_skill.py --dry-run`
## [1.1.0] — 2026-04-13

### Added — Repo hygiene + cross-repo distribution
- `.gitignore` — `.claude/settings.local.json`, `.bak`, OS artifacts, editor files, node/bun
- `LICENSE` — MIT + upstream credits (Gstack, Superpowers, ECC)
- `CHANGELOG.md` — this file
- `scripts/setup-repo.sh` — 다른 레포에 simon-stack 설치 (vendor / bootstrap 모드)
- `templates/bootstrap-session-start.sh` — 얇은 drop-in hook
- `templates/bootstrap-settings.json` — settings.json 템플릿
- `docs/USING-IN-OTHER-REPOS.md` — 4-시나리오 결정 트리 가이드

### Fixed
- `scripts/session-start-instincts.sh` — `grep -c` dual-output 버그 (`0\n0` 줄바꿈) + 템플릿 placeholder 가 "최근 실수"에 끼어드는 문제 해결

### Docs
- README 에 cross-repo 섹션 링크 추가
- `.claude/skills/README.md` 를 INDEX.md 포인터로 갱신

## [1.0.0] — 2026-04-12

### Added — simon-stack 통합 스택
- **Orchestrators**: `app-dev-orchestrator` (21단계 마스터 파이프라인),
  `security-orchestrator` (5단계 보안 감사 메타)
- **Security**: `security-checklist` (RLS/구독/RateLimit/예산),
  `authz-designer` (RBAC/ABAC/ReBAC + IDOR 감사),
  `paid-api-guard` (유료 API 6층 방어 + API 설계)
- **Method (simon-\*)**: `simon-tdd` (RED-GREEN-REFACTOR),
  `simon-worktree` (병렬 세션 격리), `simon-research` (리서치 우선),
  `simon-instincts` (누적 학습)
- **Tools**: `nextjs-optimizer` (Next.js 5대 최적화),
  `stitch-design-flow` (Stitch 프롬프트 생성기),
  `project-context-md` (프로젝트별 CLAUDE.md 템플릿)
- **Instincts**: 4 seed 파일 (`mistakes-learned`, `project-patterns`,
  `korean-context`, `tool-quirks`)
- **Templates**: `templates/CLAUDE.md` (글로벌 CLAUDE.md, Boris 원칙 + skill 맵)
- **Scripts**:
  - `scripts/install.sh` — 로컬 데스크탑 설치
  - `scripts/session-start-instincts.sh` — user-level instincts 요약 hook
- **Hook**: `.claude/hooks/session-start.sh` — Claude Code 웹 매 세션 bootstrap
- **Config**: `.claude/settings.json` — SessionStart hook + Skill permission
- **Docs**: `README.md`, `docs/INSTALL.md`, `docs/MORNING-START.md`

### Infra
- Gstack 풀 런타임 (36 skills + bin/scripts/lib + bun install)
- 매 세션 idempotent 재설치 (marker 파일 기반)

## [0.1.0] — 2026-04-12

### Added — Base
- `commit`, `review`, `debug`, `refactor`, `test-gen`, `explain` —
  6 일반 개발 skill
- `.claude/skills/README.md` — 최초 skill 안내
