# SimonK-stack 세션 인수인계

## Latest — 2026-10-05 / Sonnet 5.5를 vibe task-fit 정책에서 제외(D-90) · dist 1.806.0

갱신 시각: 2026-10-05 20:3x KST · 갱신자: Claude Code(Opus 5.5). Simon: "소넷 제외 했어? 그것도 같이 봤어야지... 하자" (레지스트리 재확인 때 AA 평가를 관측만 하고 넘긴 것에 대한 지적).

### 어디까지 왔나
- **D-90**(4벤더 quick 토론 FINAL 4/4, 블라인드 심판 Grok 76), #153(5117c38), vibe 2.15.4.
  - task-fit 정책(shadow)에서 `claude-sonnet-5-5`를 네 프로필 모두 제외했다.
  - CODE_SIMPLE 0순위는 gpt-6.1-sol·gpt-6-sol이고, 2순위에 opus-5-5 medium을 넣었다. WRITING 0순위는 opus-5-5다.
  - registry의 Sonnet 5 → 5.5 레인 이전은 `held-until-remeasure`로 멈췄다(재개 조건 기록). D-28 Sonnet 5 A 클래스 폴백 레인은 그대로다.
- **게시**: 같은 PR에 승인 파일 커밋을 넣어 main run이 바로 dist e2b1ccf = **1.806.0**을 게시했다. Claude판·Codex판 모두 Sonnet 항목 0을 확인했다.
- **이 PC**: 후보 `20261005-vibe-2154-5117c38`, problems 0.

### 알게 된 것
- 배포 콘텐츠가 바뀌는 PR은 같은 PR 안에서 승인 파일을 갱신하면 main이 빨간 상태로 남는 구간이 없다.
  1. 내용 커밋을 push한다.
  2. PR 빌드의 RELEASE.json에서 두 digest를 읽는다.
  3. 승인 커밋(source = 내용 커밋)을 더한다.
  4. 머지한다.
- 재진입 조건: AA가 공개판 Sonnet 5.5를 재측정한 뒤, 같은 작업 짝 평가에서 품질을 충족하고 대체 모델보다 쿼터 효율이 좋을 때, 그 프로필에만 되돌린다. 먼저 볼 자리는 CODE_COMPLEX high다.

### 다음 작업 큐
| # | 작업 | 시점 | 단 |
|---|---|---|---|
| A | 레지스트리 재확인 | 2026-10-12 14:17 KST 전 | 1단 |
| B | AA의 Sonnet 5.5 공개판 재측정 확인 → D-90 재진입 판단 | AA 발표 시 | 2단 |

---

## 2026-10-05 17:2x / 남은 일 일괄 처리: 레지스트리 재확인(D-89) · 레거시 폐기(D-87) · Codex 배포(D-88) · dist 1.799.0

갱신 시각: 2026-10-05 17:2x KST · 갱신자: Claude Code(Opus 5.5). Simon: "지금 모두 진행." (남은 일 네 가지를 즉시 처리)

### 어디까지 왔나
- **레지스트리 재확인(D-89)**: #142 vibe 2.15.3. 출처 37개·폐기 페이지 6개를 다시 읽고 CLI 카탈로그와 대조했다. 162필드 중 일치 160, 불일치 0, 확인불가 2(gpt-5.6-terra·luna의 장문 cached_input). 새 만료는 **2026-10-12 14:17 KST**다. 승인 파일 #146 → dist 1.789.0.
  - 함정: #142가 배포 콘텐츠를 바꿨는데 승인 PR이 빠져 14:43~15:42에 main 게시가 거부됐다(공개 dist는 그동안 1.777.0 유지).
- **레거시 경로 폐기(D-87, full 4/4, 심판 Gemini 92)**:
  - PR-A #143: SessionStart 훅 읽기 전용, release.yml·D-33 hold 삭제, fence 테스트 교체.
  - PR-B #145: root skills/·root plugin.json·옛 install.sh·setup-repo·bootstrap 템플릿을 `_archive/`로 git mv. install.sh는 `--offline-package`만 남기고, validate.mjs는 카탈로그를 검사한다.
- **Codex 배포(D-88, full 4/4, 심판 Codex 87)**:
  - 1단계 #144: 빈 `.agents/plugins/marketplace.json`으로 Codex가 Claude 빌드(안전 스킬 포함)를 설치하던 경로를 막았다.
  - 2단계: #147 게이트 schema 2(Claude·Codex 콘텐츠 결속) → #148 승인 → 호스트 실측(설치 177·안전 0, 이전, 롤백 리허설 #149·#150) → #151 카탈로그 전환.
  - Codex 사용자: `codex plugin marketplace add Simon-YHKim/SimonK-stack` 후 `codex plugin add <id>@simonk-stack` × 5로 **Codex판 1.799.0**(177스킬)이 설치된다.
- **브랜치 정리**: 원격은 `main`·`dist`만 남았다. 머지 기록과 맞지 않던 6개는 `archive/branch/*` 태그로 보존했다.
- **이 PC**: 후보 `20261005-vibe-2153-b237fd5`, vibe 2.15.3, update-local current.

### 알게 된 것
- **배포 콘텐츠 판정**: `skills-src/` 변경(레지스트리 갱신 포함)은 항상 배포 콘텐츠다. 머지 뒤 main 빌드의 RELEASE.json digest로 승인 파일 PR을 바로 연다. 승인 파일은 이제 schema 2이고 `content_digest`와 `codex_content_digest`를 둘 다 적는다.
- **Codex 카탈로그 순서**: Codex는 `.agents/plugins/marketplace.json`을 `.claude-plugin/marketplace.json`보다 먼저 읽는다.
- **Codex 갱신 동작**: `marketplace upgrade`만으로는 설치본이 바뀌지 않는다. `codex plugin add`를 다시 실행해야 새 버전 캐시로 교체된다.
- **턴 없는 스킬 확인**: `codex app-server --stdio`의 `skills/list`로 모델 호출 없이 로드된 스킬을 셀 수 있다(스크래치 `codex_skills_probe.py` 방식).

### 다음 작업 큐
| # | 작업 | 시점 | 단 |
|---|---|---|---|
| A | 레지스트리 재확인 | 2026-10-12 14:17 KST 전 | 1단 |
| B | AA의 Sonnet 5.5 비용 프런티어 평가와 CODE_SIMPLE 순위 근거 검토(shadow 정책) | 다음 정책 검토 | 2단 |

---

## 2026-10-05 12:3x / README 사용설명서 재작성 · 안전 훅 안내문 정리(D-86) · 1.777.0 게시

갱신 시각: 2026-10-05 12:3x KST · 갱신자: Claude Code(Opus 5.5). Simon: "깃허브 read me 다시 작성해줘. 소개/사용설명서 느낌으로." + /goal "남은일이 없을때 까지 작업을 계속 진행해."

### 어디까지 왔나
- **README 재작성**(#138, 308afad): 날짜별 기록이 쌓였던 README를 소개·사용설명서 12절로 다시 썼다(설치·확인, 처음 써 보기, 일별 스킬 표·전체 목록, 안전 모드, 업데이트·롤백·제거, 레거시 이전, 문제 해결, 위젯, 개발자 안내). README.en.md도 같은 구조. 상대 링크 58개 깨짐 0.
- **안전 훅 안내문 flat 경로 정리**(#139, 04c06c8, 허브 D-86): 플러그인 `.simonk-runtime`에 그대로 실리는 check-careful.sh·check-freeze.sh 차단 안내문 3곳이 `~/.claude/skills/...`를 가리켰다. 경로 없는 문장으로 바꾸고 SKILL.md 본문은 flat·플러그인을 나눠 적었다. careful 0.2.6 · freeze 0.2.7 · unfreeze 0.2.1. 재발 방지 테스트 2개.
- **게시**(#140, 218c5cb): 승인 파일 D-86 → dist a63f5b0 = **1.777.0**. 다섯 플러그인 모두 1.777.0.
- **이 PC 설치**: 후보 `20261005-vibe-2152-218c5cb`, update-local status current, selftest vibe 188/0 · vibe-bot 97/0.
- **원격 브랜치 정리**: 머지된 PR head와 끝 커밋이 같은 82개를 이름 지정으로 삭제. 머지 기록과 맞지 않는 17개는 보존(docs/html-report-rules-260927, feat/aiuw-*-2609xx, feat/vibe-main-orchestrator-260923, plugin/simonk-stack 등 — 내용 확인 전 삭제 금지).

### 알게 된 것
- careful leaf 테스트는 이 PC에서 36개 약 20분 걸린다. 다른 무거운 명령과 동시에 돌리면 느려진다. 절반씩 나눠 포그라운드로 돌리면 10분 제한 안에 끝난다.
- 안내 문구를 바꿀 때는 옛 문구의 짧은 부분(예: "fix the hook")으로도 테스트를 검색한다. assertIn이 부분 문자열을 검사한다.
- 승인 파일 PR 전에는 main 빌드 게시 job이 content-not-approved로 실패한다(설계대로). 승인 PR 머지 뒤 main run이 초록이 된다.

### 다음 작업 큐(지금 할 일 없음, 날짜·결정 대기)
| # | 작업 | 시점 | 단 |
|---|---|---|---|
| A | 레지스트리 재갱신(알림 10-10 09:00) | 2026-10-11 21:46 KST 전 | 1단 |
| B | Codex 배포(D-76이 2단계로 미룸) | 별도 결정 | 2·3단 |
| C | D-33 hold와 레거시 경로 정리 | 별도 안건 | 3단 |
| D | 보존한 원격 브랜치 17개 내용 확인 후 정리 | 별도 | 1단(내용 확인 뒤) |

---

## 2026-10-05 04:5x / GitHub 마켓플레이스가 다섯 dist 플러그인을 제공(D-76·D-82 완료)

갱신 시각: 2026-10-05 04:5x KST · 갱신자: Claude Code(Opus 5.5). Simon: "남은 작업 모두 완료하고 머지 한뒤 깃허브 머지까지 완료해" → /goal "남은일이 없을때 까지 작업을 계속 진행해."

### 어디까지 왔나
- **GitHub 배포 완료**: `.claude-plugin/marketplace.json`이 `git-subdir`·ref `dist` 다섯 항목을 가리킨다(PR #135). `/plugin marketplace add Simon-YHKim/SimonK-stack` 후 다섯 개를 설치하면 1.768.0이 된다(실측).
- **게시 게이트**(#129): `SIMONK_DIST_PUBLISH`(설정됨)와 커밋된 `distribution/dist-publish.allow`(D-코드·source·content digest). 새 내용은 승인 파일을 고치는 PR로만 나간다. D-33 hold는 release.yml과 SessionStart만 막는다.
- **실측 증거**(허브 D-76·D-82·D-84):
  - 4단계: 격리 설치·업데이트·롤백·줄끝 확인
  - 차단 해소: #127(비Windows 인터프리터 가드, 레거시 이전 문서), #128(시간 초과 시 Job Object로 트리 종료)
  - 세션 실측: `--plugin-dir`로 띄워 careful·freeze·unfreeze 확인
  - HTTPS 4A: 깨끗한 설치, 레거시 이전, 원격 세션 스모크
  - HTTPS B: 내용 변경 업데이트, 고버전 롤백, 다시 적용, 늦은 옛 빌드 거부
- **같이 고친 것**:
  - #129~#131 dist CI(숨김 폴더 artifact)
  - #132·#134 플러그인 `/unfreeze`의 `FREEZE_CLEARED` 출력(freeze 0.2.6)
  - #125 핀 태그
  - #126 레지스트리 2차 갱신(만료 2026-10-11 21:46 KST)
  - #136 테스트 timeout flaky
  - SimonKCore main fast-forward(D-80)
- **이 PC 설치**(D-85): 후보 `20261005-vibe-2152-286494e`, vibe 2.15.2, freeze 0.2.6, `status: current`.

### 운영 규칙(새로 생긴 것)
- main의 카탈로그 커밋은 되돌리지 않는다(설치된 플러그인이 not found가 됨).
- 롤백은 main에서 원인 커밋을 revert하는 것이다. 이전 내용이 더 높은 버전으로 재출하되고, 승인 파일도 함께 되돌아간다.
- 호스트는 버전이 다르면 낮아도 받는다. 늦은 옛 빌드를 막는 것은 게시 쪽 `decide`(not-newer-than-dist)다.
- PR 빌드의 버전은 병합 커밋 때문에 main보다 1 높게 보인다.

### 다음 작업 큐(지금 할 일 없음, 날짜·결정 대기)
| # | 작업 | 시점 | 단 |
|---|---|---|---|
| A | 레지스트리 재갱신(알림 10-10 09:00) | 2026-10-11 21:46 KST 전 | 1단 |
| B | Codex 배포(D-76이 2단계로 미룸) | 별도 결정 | 2·3단 |
| C | D-33 hold와 레거시 경로 정리 | 별도 안건 | 3단 |

---

## 2026-10-04 19:4x / 2026-10-04 / 권장안 기본 실행(D-73) · 배포 경로 결정(D-76) · 1~3단계 이행 · main 396aeae 설치

갱신 시각: 2026-10-04 19:4x KST · 갱신자: Claude Code(Opus 5.5). Simon: "권장하는 안건을 모두 반영해. 앞으로 변동사항이 있으면 권장하는 바가 항상 실행되게 하고, 바로 사용할수 있는 상태로 업데이트 하게 하자."

### 어디까지 왔나
- **규칙(D-73, 허브 PROTOCOL §35.9)**: 권장안은 되묻지 않고 실행한다. 완료는 PR → CI 녹색 → 머지 → 이 PC 설치 → GitHub 배포 경로 갱신 → 기록까지다. 루트 CLAUDE/AGENTS/GEMINI §10을 같은 뜻으로 맞췄다.
- **설치 파이프라인 레포화**(PR #120): `pwsh -NoProfile -NonInteractive -File scripts/windows/update-local.ps1 [-Apply] [-Selftest]`. 기본은 미리보기다. 후보 입력과 설치 바이트로 최신 여부를 판정하고, 실패하면 되돌린다. 메모리가 부족하면(<3GB) 시작하지 않는다.
  - 메모리 회수 대응: 전체 실행이 10분을 넘으면 백그라운드에서 끊길 수 있다. 그럴 때는 `build-candidate.ps1` → `install-junctions.ps1` → `install-physical.ps1`을 단계별로 포그라운드에서 돌리고, 끝에 미리보기로 `status: current`를 확인한다.
- **오래된 PR #57·#54·#49**: 모두 대체됐다. 근거를 달아 닫았다(D-75). 열린 PR은 0이다.
- **vibe 2.15.0**(다른 세션 D-74): 포함 사용량으로만 판정하고 85%에서 막는다. 크레딧 잔액은 판정에 쓰지 않는다. 설치는 D-77, 두 세션이 함께 확인했다.
- **GitHub 배포 경로(D-76, full 4/4, 심판 Codex 85)**: 검증된 5플러그인 빌드를 `dist`로 배포한다. 실제 설치·업데이트·롤백을 증명하기 전까지는 D-33 펜스를 유지한다.
  - 1단계(PR #122): 경로 감사 5건을 소스에서 고치고, 절대경로 게이트를 넣었다. 예외 4곳은 `scripts/shipped_path_exceptions.json`에 문서화했다.
  - 2·3단계(PR #121): 릴리스 버전을 `1.<main 커밋 수>.0`으로 정했다. 콘텐츠 digest는 `bundle.json`에 따로 남긴다. `five-plugin-dist.yml`이 main에 push될 때마다 Windows에서 재빌드·검증한다(약 2.5분). 게시 job은 `vars.SIMONK_DIST_PUBLISH`가 없어서 꺼져 있다. 경로 감사는 상태로 판정하고, external_runtime_pending은 통과시킨다.
- **이 PC 설치(D-78)**: 후보 `20261004-vibe-2151-396aeae`. 설치된 버전은 vibe 2.15.1, vibe-bot 0.9.7, ai-debate 0.2.6, careful 0.2.4, freeze 0.2.3, guard 0.2.2다. update-local 미리보기 결과는 `current`, problems 0이다.

### 다음 작업 큐
| # | 작업 | 크기 | 단 |
|---|---|---|---|
| A | D-76 4단계 호스트 증거. 깨끗한 설치, 레거시 68→Stack 60 이전, 5플러그인 설치·충돌, 업데이트 감지, 이전 콘텐츠를 더 높은 버전으로 재출하해 롤백, 비Windows 안내·복구, dist `.gitattributes` 준수를 확인한다. 격리된 Claude Code 호스트(별도 설정 디렉터리)가 필요하다 | 큼 | 2단 |
| B | D-76 5단계: 별도 릴리스 승인 → `marketplace.json` 전환, D-33 펜스·hold 교체, `SIMONK_DIST_PUBLISH` 설정, 첫 dist 게시 | 중간 | 3단 |
| C | 플러그인 pin을 기능 브랜치에서 태그로 고정. SimonKCore `semantic_index.py` 절대경로를 고치고 pin을 상향 | 작음 | 1단 |
| D | `docs/INSTALL.md` 기간 분할(약 395KB, 400KB 직전) | 작음 | 1단 |
| E | 레지스트리 재갱신, 2026-10-11 13:05 KST 전 | 중간 | 1단 |

---

## 2026-10-04 14:5x / 지침 v8.1.2: claude.ai 일반 대화·Cowork 통합

갱신 시각: 2026-10-04 14:5x KST · 갱신자: Claude Code(Opus 5.5). Simon: "클로드 일반 대화와 코워크는 통합됐어. 지침을 통합/수정 진행해."

### 어디까지 왔나
- 단일본 v8.1.2:
  - 붙이는 곳을 3곳에서 2곳으로 줄였다(claude.ai 프로필 지침이 일반 대화·Cowork 공통, 그리고 `~/.claude/CLAUDE.md`).
  - §8 적용 판정을 'Cowork 앱'에서 '승인 폴더의 파일을 다루는 Cowork 작업'으로 바꿨다.
  - §0-1 표와 §3·§6의 Cowork 언급을 같은 뜻으로 맞췄다. 규칙 수 변화는 0이다.
- `split.py`: 사본 `profile_§0-6`과 `cowork_§0-6+§8`을 `claude-ai_§0-6+§8` 하나로 합치고 옛 사본 2개는 저장소에서 지웠다. `--verify` 통과(sha 일치, 절 구성 OK, 끊긴 참조는 기준선 그대로 2건).
- `~/.claude/CLAUDE.md`를 새 판으로 교체했다(백업 `~/.claude/CLAUDE.md.bak_261004_1445`, 생성본과 바이트 일치).
- 붙여넣기 카드 v2: https://claude.ai/artifact/YKXcXAEnu1rXTet14cpLB2
  - 카드 1: 프로필에 붙이기(9,114자, 칸의 글자 수 제한은 미확인)
  - 카드 2: Cowork 작업에서 '📌 채팅 제목' 규칙 개수 확인. 1이면 정상, 2면 중복, 0이면 프로필이 Cowork에 닿지 않는 것이다.

### 다음 작업 큐
| # | 작업 | 크기 | 단 |
|---|---|---|---|
| A | Simon: 카드 1 붙여넣기 → 카드 2 확인 결과를 알려 줌. 0이 나오면 `split.py` 배정을 다시 판정 | 작음 | 사람 단계 |
| B | 레지스트리 재갱신, 2026-10-11 13:05 KST 전 | 중간 | 1단 |

---

## 2026-10-04 14:33 / 레지스트리 갱신 · Orca canary PASS · 안전 런타임 20초 예산 · 후보 2142 설치(D-71)

갱신 시각: 2026-10-04 14:33 KST · 갱신자: Claude Code(Opus 5.5). Simon: "남은일 마저 진행해줘" → (메모리 부족 중단 뒤) "다시 진행해봐".

### 어디까지 왔나
- **레지스트리 갱신**(PR #114, vibe 2.14.1): 모델 턴 없이 갱신했다. 출처 28개와 task-fit 9개, CLI 카탈로그를 다시 읽었고 제거·개명된 모델은 없다. 새 만료는 **2026-10-11 13:05 KST**다. 같은 PR에서 적대 평가 `VENDOR_OF`와 `probes.json`에 D-67 새 레인을 추가했다.
- **D-67 Orca canary PASS**(PR #115, vibe 2.14.2): `claude-opus-5-5`@high와 `gpt-6.1-sol`@xhigh 모두 requested와 effective가 같았다. 워커는 레인마다 1개였고, 정지 뒤 PID가 사라진 것을 확인했다. 상태는 `pending-transport-and-certificate`다. native send 보류와 인증서 부재가 그대로라 아직 **동작하지 않는다**.
  - 관찰 1: Orca 워커는 전권 모드로 뜬다. 그래서 읽기 전용은 과제문으로만 지켜진다.
  - 관찰 2: Codex 워커는 priority tier를 물려받는다. 사용량 배수는 확인하지 못했다.
- **안전 런타임**(PR #116, freeze 0.2.2): 프로세스마다 5초이던 제한을 검사 한 번 전체 20초 예산으로 바꿨다. 실측 최대는 평상시 leaf 4.42초, 무거운 테스트 6개를 동시에 돌렸을 때 14.70초였다. 시간 초과 deny 사유에 "다시 시도해도 안전"을 적는다. `codex_guarded_policy.py`는 leaf deny를 그 사유 그대로 넘긴다.
- **후보 `20261004-vibe-2142` 설치**(D-71): 정션 8개와 freeze 실폴더를 바꿨다. 설치본 selftest는 vibe 188/0, vibe-bot 97/0이다.
- **claude.ai·Cowork 지침 붙여넣기 카드**: https://claude.ai/artifact/YKXcXAEnu1rXTet14cpLB2 — Simon 작업이다. 화면과 링크는 ⚠ 미확인이다.

### 다음 작업 큐
| # | 작업 | 크기 | 단 |
|---|---|---|---|
| A | 레지스트리 재갱신, 2026-10-11 13:05 KST 전(알림 작업은 10-10 09:00 그대로) | 중간 | 1단 |
| B | D-67 레인 인증서: 모델 포함·extra usage OFF·폴백 OFF 증거. Codex는 크레딧 사용 허용 상태라 조건을 채울 수 없다(묻지 않는다) | - | Simon |
| C | sonnet-5-5·6-luna 레인 여부, `exec_plan`이 opus-5-5 effort를 싣지 않음(격리 경로) | 작음 | 2단 |
| D | Codex 쪽 leaf 시간 제한 8초 재측정 | 작음 | 1단 |
| E | Cursor Share Data(Simon 판단) · 지침 카드 붙여넣기(Simon) · `docs/INSTALL.md` 기간 분할(400KB 도달 시, 지금 약 383KB) | - | - |

---

## 2026-10-04 04:35 / D-60 PASS · quick 토론 2건(D-67·D-68) · 후보 2140 설치(D-70)

갱신 시각: 2026-10-04 04:35 KST · 갱신자: Claude Code(Opus 5.5). Simon: "debate.py 실행중이고, heavy 로그인 했고, 그록봇은 시간이 됐으니 다음 작업 진행해줘" → "작업 완료 하면 머지 하자".

### 어디까지 왔나
- **Grok Bot D-60 PASS**(D-64 이행, 1단): `vb-c594b4d8`·`vb-0f14a5a0` 모두 succeeded·verified·0원. 자동 충전 컨트롤은 없고 On-Demand·월 한도는 Disabled. run 2건은 `run_state.py complete`로 닫았다. Cursor Settings에 `Share Data: Active`가 보였다(바꾸지 않았고 Simon에게 보고).
- **vibe-bot 0.9.6**(PR #109): G6가 콘솔 과제의 메뉴 범위("확인한 메뉴 경로", `Dashboard > Spending` 같은 경로)를 범위로 인정한다.
- **Grok catch-up 9건(D-56~D-64)**: 다른 세션이 끝냈고 모두 FINAL(허브 37a7ffb7). D-58의 Grok OBJECT는 D-60 판정을 근거로 호스트가 타이브레이크했다.
- **quick 토론 2건**(각 약 10분, 4/4):
  - D-67 Orca 레인: ADD_ALONGSIDE_KEEP_LEGACY(PR #110, vibe 2.14.0). `claude-opus-5-5`·`gpt-6.1-sol`은 **등록만** 됐고, canary 전에는 '동작'으로 보지 않는다.
  - D-68 investigate: SimonK 소스를 설치 대상에서 뺐다(PR #111, 표식 파일과 설치 가드). freeze·guard 0.2.1에 Windows 경고를 넣었다.
- **안전 런타임**(PR #112, careful 0.2.3, D-62 후속 5): 플러그인 런타임이 deny를 ask로 낮추지 않는다. 런타임 자체 실패도 deny다.
- **후보 `20261004-vibe-2140` 설치**(D-70, 1단): 정션 8개와 실폴더 careful·freeze·guard. 설치본 selftest는 vibe 188/0, vibe-bot 97/0. careful 훅 스모크 3/3.

### 다음 작업 큐
| # | 작업 | 크기 | 단 |
|---|---|---|---|
| A | 레지스트리 재갱신, 2026-10-10 21:42 KST 전 | 중간 | 1단(절차 반복) |
| B | Orca canary(읽기 전용 1회, launch.requested와 effective 대조) + 계정/과금 인증서 → D-67 레인 '동작' 판정 | 중간 | 2단 |
| C | `adversarial_eval.py` VENDOR_OF·`eval/probes.json`의 옛 레인명 정리, sonnet-5-5·6-luna 레인 여부 | 작음 | 2단 |
| D | 안전 런타임 5초 제한(부하가 걸리면 deny), `codex_guarded_policy.py`가 ask만 받음 | 작음 | 2단 |
| E | Cursor Share Data 설정(Simon 판단) · claude.ai/Cowork 400KB 지시 · `docs/INSTALL.md` 기간 분할(400KB 도달 시) | - | - |

---

## 2026-10-04 01:55 / 결정 3단 도입(PROTOCOL §35.8) · ai-debate 0.2.5

갱신 시각: 2026-10-04 01:55 KST · 갱신자: Claude Code(Opus 5.5). Simon: "이거 왜 이렇게 오래 걸리지? 결정 주체의 권한이 약한가? 의견 합치가 안 될 때는?" → 진단 보고 후 "제안하는대로 진행하자".

### 어디까지 왔나
- **진단**: 판정권은 약하지 않았다(블라인드 심판 1회로 매번 결정, 비준 18/18 동의). 느린 원인은 토론을 너무 자주·무겁게 연 것(9건 중 full 6건, 토론만 약 102분). 보고: https://claude.ai/artifact/7qTM85ez1JGyLapvHcoTMM
- **결정 3단(허브 D-65, PROTOCOL §35.8)**: 1단 오케스트레이터 단독(되돌릴 수 있는 운영 판단, 기계적 근거 + DECISIONS 한 줄, 이의 시 승격) · 2단 quick(설계·머지·설치, R1 + 블라인드 심판) · 3단 full(삭제·결제·보안·프로덕션·스키마) · 심판 확신도 70 미만만 Simon 질문. 루트 CLAUDE/AGENTS/GEMINI §21 동기화.
- **ai-debate 0.2.5**(PR #107, main 8afa150, 홈 설치 = D-66 첫 1단 단독 기록): SKILL.md에 3단 표, `status`가 확신도 70 미만이면 `ASK SIMON`, 기록에 경고. 테스트 112/112.
- **D-64 이행(1단)**: Grok Bot 첫 발행 비용 0 정산 + 자동 충전 확인용 Settings 화면 캡처 2차 과제 진행 중(결과 오면 check-result·정산, 통과 시 D-60 PASS AMEND).

### 다음 작업 큐
| # | 작업 | 크기 | 단 |
|---|---|---|---|
| A | Grok Bot 2차 과제 결과 회수·check-result·정산 → D-60 PASS AMEND | 작음 | 1단 |
| B | Grok catch-up D-56~D-64(9건): CLI를 Heavy 계정으로 다시 로그인(Simon `! grok login`)하거나 10-08 16:51 KST 이후 | 작음 | - |
| C | investigate 스킬(gstack 판), careful PS 미판정 형태, 플러그인 `safety_runtime.py` deny→ask | 중간 | 2단 |
| D | 레지스트리 재갱신 2026-10-10 21:42 KST 전 | 중간 | 1단(절차 반복) |
| E | Orca 레인 현행 세대 이전 · claude.ai/Cowork 지시사항 400KB 반영 · `docs/INSTALL.md` 기간 분할 | 중간 | 2단 |

---

## 2026-10-04 01:17 / 토론 4건 이행: 안전 훅 Windows·PowerShell · 위젯 D-54 재토론 · Grok Bot 첫 과제

갱신 시각: 2026-10-04 01:17 KST · 갱신자: Claude Code(Opus 5.5). Simon 요청: "6분 뒤 grok 작업 마저, D-54는 너가 다시, 토론할 것이 있으면 멈추지 말고 진행, cursor 초과 과금은 꺼져 있고 양방향으로 승인 중, 승인 기록은 봐도 됨."

### 어디까지 왔나
- **결정(모두 PROVISIONAL 3/4, Grok CLI 결석)**: D-60(Grok Bot 레인 조건부 단계 개통, 자문 불허), D-61(D-54 재토론: 조건부 KEEP_AND_LAND), D-62(안전 스킬 2단계: A1 → 실측 D → A2·최소 B), D-63(위젯 REINSTALL_THEN_FIX). D-58에 Simon 게이트 증언 AMEND.
- **안전 훅(D-62)**: PR #103 freeze·guard·unfreeze 0.2.0(Windows 경로 정규화, cwd 대체 판정 제거), #104 careful 0.2.2(Windows 루트·홈 HIGH 52형, PowerShell 매처 deny 전용). 후보 `20261004-vibe-21310b` 설치(정션 8 + 실폴더 4). **새 대화형 세션 종단 6/6 PASS**(Bash·PowerShell force-push deny, freeze 경계 밖 Write deny).
- **실측 결론**: PowerShell 매처 발화, deny는 bypass에서도 차단, **ask도 bypass에서 확인창**, Edit 경로는 `C:\...`, 새 세션은 PowerShell 도구에 `CLAUDE_CODE_USE_POWERSHELL_TOOL=1` 필요.
- **위젯(D-61·D-63)**: 데이터 백업(`~/.claude/flat-link-archive/aiuw-backup-261003`, 7,683파일·210.6MB, ACL 좁힘)·사본 복원 리허설 일치. d767272 경고는 일반·모션 감소에서 구분 불가(FAIL) → PR #102로 2c21eec만 main, PR #105로 경고를 모양 단서(삼각형·밑줄)로 고쳐 세 모드 PASS, `094da97` 고정 소스로 최종 재설치(계정·인증 파일 해시 불변).
- **Grok Bot(D-60)**: PR #101로 Relay만 `active`. 첫 과제(Cursor 초과 과금·자동 충전 화면 확인, 읽기 전용) `vb-c594b4d8`를 /vibe 정식 경로(Store USD 0 init·register·인증서·`execute_bot.py dispatch`)로 01:07:51 발행. 할당량 근거 = 위젯 Bot 행 자동 관측(96% 남음). 결과 대기(Relay 마지막 점검 00:38).
- **Grok 계정**: Simon이 말한 리셋은 SuperGrok **Heavy** 계정(위젯 첫 Grok 칸, 10-03 23:12 KST 리셋, WK 89% 남음). Grok CLI는 10-01부터 다른 계정(10-08 16:51 리셋)이라 xai 좌석은 계속 결석.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | Grok catch-up D-56~D-63(8건). CLI를 Heavy 계정으로 다시 로그인하면 바로 가능(Simon이 `! grok login`), 아니면 10-08 16:51 KST 이후 | 작음 | 감시 스크립트가 READY 시 자동 실행 |
| B | Grok Bot `vb-c594b4d8` 결과 회수 → `execute_bot.py check-result` → 스크린샷 직접 확인. PASS 전에는 다른 Bot 과제 금지(D-60) | 작음 | |
| C | investigate 스킬(아직 gstack) 처리, careful PS 미판정 형태(변수·splatting·EncodedCommand), 플러그인 `safety_runtime.py` deny→ask 강등 수정 | 중간 | §35 |
| D | 레지스트리 재갱신 2026-10-10 21:42 KST 전(알림 10-10 09:00) | 중간 | |
| E | Orca 레인 현행 세대 이전(§35) · claude.ai/Cowork 지시사항 400KB 반영 · `docs/INSTALL.md` 400KB 근접 → 기간 분할 | 중간 | |

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup --orchestrator anthropic
```

---

## 2026-10-03 22:53 / 남은 일 전부 처리: vibe 2.13.1 · ai-debate 0.2.4 · careful 0.2.0 · Grok Bot 증거 레인

갱신 시각: 2026-10-03 22:53 KST · 갱신자: Claude Code(Opus 5.5). Simon 요청: "남은 일 모두 진행해줘. 토론에 그록 봇도 포함시키자. 그록은 2시간 뒤 리셋될꺼야. 그록은 한번 테스트 하지 않았나? 꼭 필요한가?"

### 어디까지 왔나
- **main `baafc70`**: PR #96(vibe 2.13.0·qa 2.1.0 — 야간 QA 브랜치를 main에 합침), #98(vibe 2.13.1, 레지스트리 37건 재확인·변경 0, 만료 **2026-10-10 21:42 KST**), #97(ai-debate 0.2.4, Codex 좌석 실시간 `account/rateLimits/read`), #99(careful 0.2.0, gstack 1.91.9 위 재구성·내부 실패 deny). 머지 커밋 넷 모두 CI 성공.
- **홈 설치(D-59 조건부 ALL)**: 후보 `20261003-vibe-21310-candidate` 영수증 4/4, 정션 8개 + Codex config 한 줄 전환, 설치본 selftest 180/0. ai-debate 0.2.4 사본 교체(110/110). careful 0.2.0 교체 후 **새 대화형 Claude Code 세션에서 실측**: force-push가 `[careful][HIGH] … blocked` deny, 원격 ref 불변, echo 통과. agy는 qa 정션을 못 봐서 심링크 추가 → 4개 CLI 182/182.
- **실측(2026-10-03)**: 스킬 frontmatter 훅에서 `${CLAUDE_SKILL_DIR}`는 비어 있고 그 경로 훅은 실행되지 않음(시작 실패 훅은 fail-open). 훅 deny는 bypassPermissions에서도 막음. ask는 미측정.
- **결정**: D-56(안전 스킬 REBASE), D-57(0.2.3), D-58(Grok Bot = 좌석 아님, 비투표·비차단 증거 레인), D-59(머지·설치) — 모두 PROVISIONAL 3/4(Grok 결석). D-53·D-55 FINAL via catch-up. **D-54는 Codex OBJECT로 차단**(Orca 대화형 Codex가 `--host-session`으로 직접 제출 — Codex 호스트 E2E 실증).

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | Grok catch-up D-56·D-57·D-58·D-59. 실시간 billing은 주간 리셋 **2026-10-08 16:51 KST**(Simon은 10-03 23시대 리셋이라 함). 감시 스크립트가 READY 되면 자동 실행 — 이 세션이 끝나면 `debate.py catchup --orchestrator <호스트>` | 작음 | |
| B | D-54 타이브레이크: 호스트(Codex)가 결정. 그 전엔 AI Usage Widget 갱신 금지 | 작음 | Codex 세션에서 |
| C | D-56 다음 단계: guard·freeze·unfreeze 훅도 `${CLAUDE_SKILL_DIR}` → `$HOME` 고정 + freeze 공용 작성기 보존. careful HIGH에 `/c/`·`C:/`·`$HOME/*` 추가 여부. PowerShell 도구 감시 공백. 플러그인 `safety_runtime.py`가 deny를 ask로 바꾸는 문제 | 중간 | §35 토론 |
| D | Grok Bot 증거 레인 실사용: Cursor 계정 초과 과금 꺼짐 화면 증거 + Simon `approval_ref` 확보. 소수의견("xAI 관점 자문")은 Simon 결정 | 작음 | |
| E | 레지스트리 재갱신 2026-10-10 21:42 KST 전(알림 10-10 09:00) | 중간 | |
| F | Orca 레인 현행 세대 이전(§35) · claude.ai/Cowork 지시사항 400KB 반영 · `docs/INSTALL.md` 400KB 근접 시 기간 분할 | 중간 | |

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup --orchestrator anthropic
```

---

## 2026-10-03 21:10 / 4벤더 토론 실전 테스트 · ai-debate 0.2.3

갱신 시각: 2026-10-03 21:10 KST · 갱신자: Claude Code(Opus 5.5). Simon 요청: "코덱스, 그록, 제미나이 사용량 차있어. 한번 테스트 해볼래?"

### 어디까지 왔나
- **Codex catch-up 완료**: D-53·D-55의 Codex 좌석을 실호출(gpt-6.1-sol xhigh, 84초·100초) → 둘 다 ACCEPT. 두 결정 모두 **FINAL via catch-up**, 허브 AMEND 기록. D-54(Codex가 연 토론)의 Codex 좌석은 살아 있는 대화형 Codex 세션만 채울 수 있어 남겨 둠.
- **새 full 토론 D-56**(`dbt-261003-204651`, 안전 스킬 5개 gstack 원본 vs SimonK 판): R1·R2·블라인드 심판(Codex)·비준 3/3 ACCEPT → **REBASE**(확신도 84), PROVISIONAL 3/4.
- **테스트에서 결함 발견 → ai-debate 0.2.3**: `seats`가 Grok을 READY(78%)로 냈다. 근거는 이틀 전 로그 줄이었고, 실제 계정은 100%라 R1이 402로 거절됐다(과금 0, on-demand·선불 0). [PR #93](https://github.com/Simon-YHKim/SimonK-stack/pull/93)으로 고침.
  - Grok 좌석이 `grok agent --no-leader stdio` → `_x.ai/billing`으로 실시간 조회를 먼저 한다(모델 턴 없음, 약 0.4초).
  - 오래된 로그는 여유 근거로 쓰지 않는다.
  - D-57 토론에서 Codex·Claude 좌석이 따로 찾은 "기간 종료 + 오래된 로그 = READY" 빈틈도 같은 PR에서 막았다.
  - 머지 `5e4cae8`, 홈 설치 완료(`docs/INSTALL.md` 첫 절).
- 허브 `DECISIONS.md`: D-53·D-55 AMEND, D-56, D-57(+조건 이행 AMEND). 로컬 커밋 `0db9c2da`.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | **2026-10-08 중**(만료 10-09 00:39 KST 전) /vibe 레지스트리 재확인·갱신. 홈 /vibe는 지금 2.13.0(야간 QA 브랜치 후보)이라 갱신은 2.13.0 기준 소스에서 할 것 | 중간 | 놓치면 /vibe 라우팅 정지 |
| B | Grok catch-up: D-56·D-57(그리고 같은 계정이 리셋되는 **2026-10-08 16:51 KST** 이후). `debate.py catchup --orchestrator <호스트>` | 작음 | Grok CLI 계정은 지금 주간 100% |
| C | D-56 이행: careful부터 REBASE. `${CLAUDE_SKILL_DIR}`가 스킬 훅에서 전개되는지 로컬 실측이 먼저다(gstack 주석 #2469는 안 된다고 함 → SimonK 판 훅이 아예 안 돌 수 있음). freeze는 gstack 공용 작성기 보존 | 중간 | |
| D | Codex 좌석도 실시간 조회(`codex app-server` `account/rateLimits/read`) — D-57 소수의견 | 작음 | |
| E | `feat/qa-evidence-261003`(/vibe 2.13.0) PR·머지 여부 — 홈에는 이미 설치됨, main에는 없음 | 작음 | |
| F | Orca 레인 현행 세대 이전(§35 토론) · claude.ai/Cowork 지시사항 400KB 반영 | 중간 | 이전 블록 C·E |

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup --orchestrator anthropic
```

---

## 2026-10-03 03:43 / QA 2.1.0 + vibe 2.13.0 설치

Simon 요청: AI 코딩 QA 강화안을 `/vibe`까지 연동해 최종 개선하고 PC 종료.

- 소스: `feat/qa-evidence-261003`, QA `32efde8`, vibe `f607bff`, 설치 경로 회귀 보완 `cf139c3` push 완료. main 병합·PR 생성·운영 배포 없음.
- QA는 독립 계약/대상 핀, 필수 positive/negative/boundary/recovery 검사, 실제 증거 해시, 고위험 사람 검토를 대조한다. 누락·미실행·실패·오래된 증거를 차단한다.
- vibe `Store.complete`는 변경/coding/qa 노드가 있으면 `bind-qa`와 실제 게이트 통과가 필수다. 완료 직전 재검사하며 기존 LLM 리뷰·비용 정산 조건도 유지한다. node `verify`는 리뷰용 출력 준비 상태다.
- **실제 설치**: Claude vibe·Codex vibe·공용 Claude QA 세 경로만 새 후보로 전환. `.agents`는 기존 연결로 갱신. 다른 Core 링크는 이전 후보이므로 설치 루트가 혼합돼 있다. [설치 기록·영수증·백업](INSTALL.md) 첫 절을 기준으로 한다.
- 검증: 설치된 Codex 전체410 / Claude 상태관리67 / 공용QA33 PASS, 소스 selftest180 / Skill-Gen24 / 141 skill gate PASS. 네 패키지 영수증도 PASS. 원격 feature push는 GitHub `skills-ci` 트리거가 아니다. 기능 커밋 `cf139c3`의 Cloudflare Pages 체크는 success이며, 실제 앱 E2E·모델 비용·전체 호스트 행동은 증명하지 않는다.
- 결정: 앞선 사용자 정족수 예외를 유지. Claude/Codex 쿼터와 Grok 실제 잔액 거절 때문에 Google advisory만 참여했다. 최종 재검토에서 즉시 차단 결함 없음. 4벤더 합의나 새 D번호를 주장하지 않는다.
- 보고서: `E:/Coding Infra/reports/simonk-vibe-qa-completion-20261003.html`. 종료 전 작업/검증 기록을 저장한다. 예약된 종료의 실제 실행 여부는 후보 루트의 `shutdown-status.json`을 확인한다.
- 남은 경계: 계약의 완전성·테스트 실행자·사람 신원은 해시로 인증되지 않는다. 신뢰하는 coordinator/CI가 기준과 immutable build를 관리해야 한다. 레지스트리 만료 갱신 등 이전 후속 큐는 유지한다.

---

## 2026-10-02 / 4개 CLI 동일 사용: /vibe 2.12.43 · ai-debate 0.2.2

갱신 시각: 2026-10-02 02:25 KST · 갱신자: Claude Code(Opus 5.5). Simon 요청: "codex, claude, grok, agy 모두 이 스킬을 동일하게 사용하게, ai-debate·오케스트레이션·모델/effort 라우팅 모두 최신화. 나보고 시키지 말고 직접."

### 어디까지 왔나
- main `9e88140`: [PR #90](https://github.com/Simon-YHKim/SimonK-stack/pull/90) ai-debate 0.2.2(호스트 중립: `--orchestrator` 필수, 호스트 자기 좌석 세션 내, 다른 벤더 라이브 세션의 `--host-session` 증명·결합, Grok·agy 겐세이 감지), [PR #91](https://github.com/Simon-YHKim/SimonK-stack/pull/91) /vibe 2.12.43(레지스트리 만료 10-06 → **10-09 00:39 KST**, grok-4.5 legacy, legacy 동점 보정).
- **설치 완료**: /vibe 2.12.43(정션 7개), ai-debate 0.2.2(리플레이 게이트 4벤더 18건 통과 후). 상세·영수증·되돌리기는 `docs/INSTALL.md` 첫 절.
- **4개 CLI 동일**: Claude Code·Codex·Grok·agy가 같은 스킬 파일을 읽는다. agy는 `~/.gemini/config/skills.json` + Core 5개 심링크로 182/182(이번에 신설).
- SimonK 자체 스킬 31개를 main과 동기화. 허브 `tools/models.json`·`hub-health.ps1`·`hub-daemon.ps1` 기본값·`MODELS.md`를 현재 모델로 재핀(로컬 커밋 `351c0828`). ModelWatch 예약 작업은 설치 경로를 실행.
- 결정: D-55(4벤더 토론, PROVISIONAL 3/4, Codex 결석). D-54(Codex가 연 토론)의 Claude 좌석을 이 세션이 `--host-session`으로 실제 catch-up(대화형 증명 `entrypoint cli`, `bound_by fingerprint`) — 교차 호스트 경로 실증.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | **2026-10-08 중**(만료 10-09 00:39 KST 전) /vibe 레지스트리 사실 재확인·갱신 → PR → 후보 → 정션 전환. 알림 = 예약 작업 `\SimonK-Vibe-RegistryRefresh-Reminder` | 중간 | 놓치면 /vibe 라우팅 전부 정지 |
| B | 2026-10-07 09:03 KST 이후 Codex catch-up: `debate.py catchup --orchestrator <호스트>` → D-53·D-55 Codex 좌석, 그리고 Codex 호스트 라이브 E2E 1회. 알림 = `\SimonK-AiDebate-CodexCatchup-Reminder` | 작음 | Codex 쿼터 95% 미만 먼저 확인 |
| C | Orca 레인(routing.LANES 등)을 현행 세대로 이전 — Orca로 claude-opus-5-5·gpt-6.1-sol·grok-4.7 보내면 지금은 거부 | 중간 | 별도 §35 토론 |
| D | gstack 원본으로 덮인 34개 중 안전 계열 5개(careful·freeze·guard·unfreeze·investigate)의 SimonK 강화판 복원 여부 결정 | 작음 | |
| E | claude.ai 개인 프로필·Cowork 지시사항에 `instructions/out/` 사본 반영(400KB) — 브라우저 제어 도구가 연결된 세션에서 | 작음 | |

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup --orchestrator anthropic
```

---

## 2026-10-02 / Grok catch-up 완료 · 파일 상한 400KB · ai-debate 0.2.1

갱신 시각: 2026-10-02 00:05 KST · 갱신자: Claude Code(Opus 5.5).

### 어디까지 왔나
- Simon이 Grok을 다른 계정으로 다시 로그인했다. 무모델 ACP billing 조회(`runtime_collect.py --surface grok`): SuperGrok, 주간 78%(2026-10-08 16:51 KST 리셋), on-demand 한도 0·사용 0·선불 0.
- D-53 Grok catch-up 실호출 성공: grok-4.7 xhigh, 166초, **ACCEPT**(독립 입장 조건부 선택지 1, 확신도 76). 허브 `DECISIONS.md`에 AMEND 줄 추가. D-53은 PROVISIONAL 유지, **남은 의무는 Codex catch-up 하나**(2026-10-07 09:03 KST 이후).
- [PR #87](https://github.com/Simon-YHKim/SimonK-stack/pull/87) ai-debate 0.2.1: `status`가 catch-up을 마친 좌석을 "catch-up done"으로 표시(78/78).
- [PR #88](https://github.com/Simon-YHKim/SimonK-stack/pull/88) Simon 지시로 단일 파일 상한 100KB → **400KB**(지침 단일본 5곳, `split.py` 재생성·`--apply`, simon-handoff 1.0.1 굴리기 예산 320KB·상한 400KB). 100KB 넘는 파일은 offset/limit·tail·grep으로 읽는다.
- 설치본 갱신: `~/.claude/skills/ai-debate` 0.2.1, `~/.claude/skills/simon-handoff` 1.0.1(main `10a6cfb`와 바이트 동일, 이전 사본은 `~/.claude/flat-link-archive/skills-261002/`).

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | 2026-10-07 09:03 KST 이후 Codex catch-up: `debate.py catchup` → `call --round catchup --vendor openai` → `record --id dbt-261001-201826 --amend` | 작음 | 남은 유일한 D-53 의무 |
| B | claude.ai 개인 프로필 지침·Cowork 상시 지시사항에 `instructions/out/` 사본 붙여 넣기(400KB 반영) | 작음 | 사람 단계 |
| C | ai-debate `seats`의 Grok 근거를 로그 마지막 줄 대신 ACP billing 조회로(계정 전환 직후 옛 수치 방지) | 작음 | |
| D | 2.12.42 첫 실제 `/vibe` 실행 결과를 기준점으로 기록 · `\SimonK-Vibe-ModelWatch` 예약 작업 갱신 | 작음 | 이전 블록 B·D |

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup
```

---

## 2026-10-01 / `/vibe` 2.12.42·`ai-debate` 0.2.0 설치 완료와 4벤더 토론

갱신 시각: 2026-10-01 20:40 KST · 갱신자: Claude Code(Opus 5.5). Simon이 Codex의 장시간 작업을 넘기며 "스킬 업데이트 완료"와 "ai-debate를 항상 4개 벤더(Claude·Codex·Grok·Gemini)로, 오래 걸리면 중간에 겐세이"를 지시했다.

### 어디까지 왔나
- `origin/main` `bfee665`: [PR #84](https://github.com/Simon-YHKim/SimonK-stack/pull/84)(ai-debate 0.2.0) → `9c11992`, [PR #85](https://github.com/Simon-YHKim/SimonK-stack/pull/85)(/vibe 2.12.42) → `bfee665`. 두 PR 모두 정확 HEAD 검사 4/4, main 머지 커밋의 skills-ci·release·validate-plugin 성공, 새 태그 없음(source-only hold 유지).
- **사용자 홈 설치 완료**: `/vibe` 2.12.24 → 2.12.41 → 2.12.42(정션 7개 + Codex config 한 줄), `ai-debate` 0.1.0 → 0.2.0(물리 폴더 교체). 후보·영수증·검증·되돌리기는 `docs/INSTALL.md` 첫 절.
- **ai-debate 0.2.0**: `scripts/debate.py`(4벤더 좌석 러너, 무모델 쿼터 증거로 착석 판정, 결석 기록, 블라인드 심판·비준·catch-up, append-only 허브 기록)와 `scripts/interject_scan.py`(T1~T6 겐세이 감지, 읽기 전용). 적대적 검토 P0 4건·P1 다수 수정, 테스트 77/77.
- **/vibe 2.12.42**: Simon이 고른 Gstack 실행별 상태 폴더(telemetry off·update_check false, 개인 설정 불변). 호스트 격리는 지시 수준, Orca는 best-effort라고 문서에 명시.
- **첫 실제 4벤더 토론 D-53**(`dbt-261001-201826`, full): Claude ✓ · Codex ✗(주간 100%, 구매 크레딧 과금 위험) · Grok ✗(402) · Gemini ✓(실호출). 블라인드 심판(Gemini) 조건부 GO 90, 비준 ACCEPT 2/2, **PROVISIONAL 2/4**. 허브 `DECISIONS.md`에 append.
- 루트 `CLAUDE.md`·`AGENTS.md`·`GEMINI.md` §21과 허브 `PROTOCOL.md` §35.2·§35.7을 4벤더·겐세이 규칙으로 갱신(허브는 로컬 커밋).

### 안전 경계
- 추가 과금 $0: Codex·Grok 호출 0회. Gemini는 agy 무턴 `/usage`로 100% 남음 확인 후 4회 호출, Claude 좌석은 세션 내 서브에이전트.
- 관찰: 다른 Codex 세션들이 주간 한도 소진 뒤 구매 크레딧을 실제로 차감 중이었다(18:07→18:38 KST 55,940→55,741). 설정은 건드리지 않았다.
- 이미 열린 세션은 이전 스킬 목록을 캐시한다. 로컬 기본 체크아웃(오래된 main)을 프로젝트로 열지 말 것 — 구 SessionStart 훅이 스킬을 실폴더로 덮을 수 있다.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | Grok(2026-10-03 23:12 KST 이후)·Codex(2026-10-07 09:03 KST 이후) 복귀 시 `debate.py catchup` → `call --round catchup` → `record --id dbt-261001-201826 --amend` | 작음 | 일정에 박기 |
| B | 2.12.42 설치 뒤 첫 실제 `/vibe` 실행 결과를 기준점으로 기록, 실패 시 41로 되돌려 원인 분리 | 작음 | D-53 소수의견 |
| C | `debate.py` 106KB 모듈 분할(100KB 지침) · 허브 `DECISIONS.md` 170KB 기간 분할 | 중간 | 지침 위반 해소 |
| D | 예약 작업 `\SimonK-Vibe-ModelWatch`가 pr67 후보의 구 `model_watch.py`를 실행 — 새 후보로 갱신 | 작음 | |

### 핵심 파일과 검증
```text
skills-src/ai-debate/SKILL.md                     4벤더·결석·겐세이 계약 (0.2.0)
skills-src/ai-debate/scripts/debate.py            좌석 러너
skills-src/ai-debate/scripts/interject_scan.py    겐세이 감지
skills-src/ai-debate/references/seats.md          벤더별 호출·쿼터 증거
skills-src/vibe/scripts/run_state.py              gstack-env
docs/INSTALL.md                                   2.12.42 후보 영수증·설치·되돌리기
```
```powershell
python -B -m unittest discover -s skills-src/ai-debate/scripts -p "test_*.py"
python -B skills-src/ai-debate/scripts/debate.py seats --orchestrator anthropic
python -B skills-src/ai-debate/scripts/debate.py catchup
python -B .github/skill-ci/run_ci.py
```

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B "$env:USERPROFILE\.claude\skills\ai-debate\scripts\debate.py" catchup
```

---

## 2026-10-01 / `/vibe` 2.12.41 소스 머지와 실행별 Gstack 정책

갱신 시각: 2026-10-01 18:11:33 KST. Simon은 PR 머지 뒤 작업을 멈추고 `/simon-handoff`를 요청했다. 이 블록은 후속 구현이 아니라 다음 세션을 위한 상태 기록이다.

### 어디까지 왔나
- `origin/main`: `ccad7423a48b7d63e6826d074bd147fb9a45f5d4` — [PR #82 `/vibe` 설명 축약 대응](https://github.com/Simon-YHKim/SimonK-stack/pull/82) 소스 전용 일반 머지. 변경 5파일(스킬 설명·CI 회귀 테스트·README/INSTALL/CHANGELOG). 정확한 PR HEAD `fb79284870654eea5a8f759c6c332fa4dad3fe25`의 4/4 검사가 통과했고, main의 Cloudflare Pages·skills-quality·Windows path audit·validate·tag-release 5/5도 성공했다.
- `/vibe` 소스 2.12.41은 Codex가 설명을 48자로 축약해도 `/vibe`·SimonKStack·라우팅 목적을 앞에 남긴다. 품질 게이트 141/141, 오케스트레이션 회귀 131/131, 최종 격리 후보 네 SHA-256 영수증 및 오프라인 runtime probe 4/4가 통과했다. 후보는 `E:/Coding Infra/Releases/SimonK-stack/20261001-vibe-21241-quality-candidate/`; 정확한 digest는 `docs/INSTALL.md` 첫 절에 있다.
- Claude·Codex·`.agents` 사용자 flat `/vibe` 세 경로의 SHA-256은 모두 `3b1cc7b001ecc432a9fb300ef0083d7162de536ef3eb9cf122167264a4f08e08`로 불변이고 버전은 2.12.24다. 앞선 격리 Codex 프로필의 무모델 입력에서는 namespaced `simonk-core:vibe`·`simonk-core:vibe-bot`가 각 1회 노출됐지만 새 최종 후보의 자연어 자동 선택·실호출 품질은 미검증이다.
- 현재 전용 소스 브랜치 `fix/vibe-description-routing-261001`와 기존 기본 체크아웃은 정리·삭제하지 않았다. 허브의 D-52 결정은 기존 dirty/diverged 저장소에 로컬 기록했고 원격 push하지 않았다.

### 안전 경계와 사용자 결정
- D-52는 소스 전용 main 머지와 운영 Cloudflare Pages 자동 배포만 허용했다. `distribution/main-source-only.hold`, SessionStart/Release 차단, marketplace `313c04b` pin 및 D-39/D-50 사용자 홈 설치 HOLD를 유지한다. 이번 작업에서 모델·이미지·Grok Bot 호출, 결제 설정·자동충전 변경, 추가 과금은 없었다.
- Simon은 구매 크레딧 잔액/사용 허용 설정을 더 묻거나 조회하지 말라고 했다. 사용 가능하다고 답했더라도 구매 크레딧을 사용해도 된다는 승인이 아니다. 추가 과금 $0, 구독 포함 usage만 사용하며 후속 실호출은 하지 않는다.
- Simon은 Gstack 개인 설정을 바꾸지 않고 **각 `/vibe` 실행별 별도 상태 폴더에서 telemetry와 업데이트 확인을 OFF**로 하기를 선택했다. 이 실행별 격리는 **아직 구현하지 않았다**. 개인 Gstack 설정·시작/종료 telemetry 절차는 실행하지 않았다.
- Simon은 약 5GB 로컬 이미지 모델 설치가 불필요하다고 했다. D: 다운로드·ComfyUI 모델 설치는 하지 않는다. 검증된 구독 포함 이미지 도구가 없으면 이미지 실생성 경로는 차단한다.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | Gstack의 `GSTACK_HOME`·업데이트 검사 경로를 읽기 전용으로 확인하고, 개인 설정을 보존하는 `/vibe` 실행별 telemetry/update OFF 격리 구현·오프라인 테스트 | 중간 | Simon이 선택한 다음 구현. 새 브랜치·별도 검증 후 결정 |
| B | 실제 사용자 홈에 2.12.41을 설치할지 D-39/D-50의 자산 보존·명령 수락·롤백 게이트로 재판정 | 큼 | 소스 머지를 설치 완료로 오인 금지 |
| C | 자연어 자동 선택·모델/effort·Grok Bot·이미지 경로의 실제 사용자 품질 검증 | 큼 | 구독 포함과 구매 크레딧 폴백 차단이 검증되지 않으면 실호출 금지 |

### 핵심 파일과 검증
```text
skills-src/vibe/SKILL.md                         2.12.41 메인 스킬 설명·안전 경계
skills-src/vibe/scripts/test_orchestrate.py       CI가 실행하는 48자 발견성 회귀
docs/INSTALL.md                                   최종 후보 SHA-256과 설치 HOLD
distribution/main-source-only.hold               자동 설치·릴리스 차단
E:/Coding Infra/AI Infra/Communication/DECISIONS.md  D-52(로컬 기록)
```
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
python -B .github/skill-ci/run_ci.py
python -B skills-src/vibe/scripts/test_orchestrate.py
```

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
# A부터 진행하되, Simon의 중단 요청 이후 자동 실호출·설치·결제 설정 변경은 하지 않는다.
```

---

## 2026-10-01 / Claude·Codex CLI 계약 수정과 PR #78 인계

갱신 시각: 2026-10-01 15:41:53 KST. Simon이 컨텍스트 부담을 이유로 `/simon-handoff`를 요청했다. 문서 작성 중 별도 작업 흐름에서 코드 PR #78이 머지되어 아래 상태를 다시 반영했다.

### 어디까지 왔나
- `origin/main`: `669da9fe33c585cd685526637309b83d06b71612` (PR #78 머지). 이번 흐름에서 #76·#77·#78이 main에 머지됐다.
- [PR #78 — 직접 CLI의 허위 `ready` 차단](https://github.com/Simon-YHKim/SimonK-stack/pull/78)은 **머지됨**. 최종 HEAD `b8a26a76fa88ad5cccdde670f077f91c16ca4539`, merge SHA `669da9fe33c585cd685526637309b83d06b71612`, 6파일(플래너·테스트·계약 문서·Claude CLI 가짜 전송 테스트의 원격 CI 추가). PR 검사 4/4 성공. 다음 세션에서 최신 main 상태를 재조회한다.
- 로컬 전체 `/vibe` unittest 361/361, selftest 180/180, skill quality gate 141/141, `git diff --check` 통과. Git Bash의 TDD guard는 통과했으나 WSL 실행은 Windows worktree `.git` 경로를 해석하지 못해 실패했다. 모델·Bot 실호출은 없었다.
- 이 인수인계는 별도 `handoff/20261001-1539` 브랜치에서 문서만 작성한다. 기존 `fix/vibe-cli-node-contract-261001` 작업 트리는 깨끗했다. 공유 기본 체크아웃의 로컬 `main`은 원격과 크게 분기되고 다른 미커밋 파일 4개가 있어 이동·정리하지 않았다.

### 판단·안전 경계
- 독립 `ai-debate` 심판의 #78 판정은 **조건부 소스 전용 GO**였다. 별도 흐름에서 D-47과 소수의견을 허브에 로컬 기록하고 PR 본문에 연결한 뒤 머지했다. D-47 기록상 main의 quality·Windows path audit·validate·Cloudflare Pages·tag-release 5/5 성공, 태그/릴리스 차단 유지, 사용자 flat 설치 불변이다. 완전 CLI 5노드 양성 통합 계획·Store/전송 경로는 여전히 미검증이다.
- 허브 `E:/Coding Infra/AI Infra/Communication/`는 dirty/diverged 상태다. D44–D47은 로컬 기록이며 원격 반영으로 간주하지 않는다. 허브 전체를 무차별 stage/push하지 않는다.
- `distribution/main-source-only.hold`, SessionStart/Release 차단 및 marketplace `313c04b` pin은 현재 유지됐다. **소스 머지는 설치·릴리스·실호출 허가가 아니다.** 사용자 flat `/vibe` 설치는 마지막 확인 시 2.12.24이고, 최신 소스 변경을 설치하지 않았다.
- 사용자 정책: 추가 과금 **$0**, 구독 포함 usage만 사용, 자동충전·초과 과금·결제 설정 변경 금지. Grok CLI/Bot과 모든 모델의 실호출은 정확한 계정·구독 버킷·차단 상태를 검증하기 전에는 하지 않는다. Bot은 GUI-only, CLI/API/MCP로 가능한 작업은 `/vibe`가 직접 맡는다.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | 완전 Claude/Codex 직접 CLI 5노드 debate의 양성 통합 계획·Store/전송 경로를 오프라인 테스트로 검증한다 | 중간 | D-47 소수의견의 첫 후속 |
| B | AGY·Grok CLI에 구독 전용 `claim → send once → lookup → verify` 어댑터를 오프라인 구현·검증한다 | 큼 | 별도 브랜치 |
| C | Claude/Codex 사용자 설치 후보의 자산 보존·호스트 명령·구독 청구를 별도 검증한 뒤 설치 게이트를 다시 판단한다 | 큼 | 소스 머지와 분리 |
| D | 허브 D44–D47 기록의 소유권과 dirty/diverged 이력을 안전하게 조정한다 | 중간 | 허브 전체 push 금지 |

### 핵심 파일과 검증
```text
skills-src/vibe/scripts/orchestrate.py               직접 CLI 후보의 구조 사전검사
skills-src/vibe/scripts/execute_cli.py                Claude CLI 전송 전 검사
skills-src/vibe/scripts/execute_codex_cli.py          Codex CLI 전송 전 검사
skills-src/vibe/scripts/test_orchestrate.py           플래너 회귀 테스트
.github/workflows/skills-ci.yml                       Claude CLI 가짜 전송 CI 추가
skills-src/vibe/references/orchestration.md            운영 계약
distribution/main-source-only.hold                    설치·릴리스 경계
E:/Coding Infra/AI Infra/Communication/DECISIONS.md  D-code (별도 저장소)
```
```powershell
python -B -m unittest discover -s skills-src/vibe/scripts -p test_*.py -q
python -B skills-src/vibe/scripts/selftest.py
python -B .github/skill-ci/run_ci.py
gh pr checks 78 --watch=false
```

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
gh pr view 78 --json number,state,headRefOid,baseRefOid,statusCheckRollup,body
```

---

## 2026-10-01 / `/vibe` 구독 전용 실행 경로와 핸드오프

### 어디까지 왔나
- 작업 시작 기준 `origin/main`: `357a42136b691951a3869169c86d5d5726b75f88` (PR #75 Orca 동시성 수정 머지). 최종 main SHA는 `git rev-parse origin/main`으로 다시 확인한다.
- 이번 세션 PR: [#76 — unsupported provider route 차단](https://github.com/Simon-YHKim/SimonK-stack/pull/76). 코드 커밋 `1733560d853ceeaf0ca2872ff152b661e7613a30`; 문서 추가 전 4/4 원격 검사가 통과했다. 이 문서 커밋 후 CI와 머지 상태를 다시 확인한다.
- `/vibe` 소스 2.12.38에서 AGY·Grok의 `cli`/`orca` 실행 어댑터가 없으면 합성된 런타임·과금 증거로도 `ready`가 되지 않는다. Antigravity는 구매 크레딧 폴백 차단과 정확한 계정·전송 경로별 쿼터 증거도 요구한다.
- 검증: `/vibe` 오프라인 unittest 351/351, `selftest.py` 180/180, skill validator 오류·경고 0, eval 26건 dry-run 입력 확인, `git diff --check` 통과. 실제 구독 청구·모델 품질·실제 Bot 전달의 증명은 아니다.
- 기존 Claude·Codex·`.agents` 사용자 flat `/vibe`는 마지막 관측에서 2.12.24였다. 이 변경은 소스 전용이며 사용자 설치를 수행하지 않았다.

### 활성 인프라·안전 경계
- `distribution/main-source-only.hold`, SessionStart의 source-only 보호, marketplace `313c04b` pin 및 GitHub Release hold를 유지한다. `main` Pages 자동 배포만 Simon이 이번 작업에 허용했다.
- 추가 API 과금 $0, 구독 포함 usage만 사용한다. 자동충전·초과 과금·결제 설정을 변경하지 않는다. 사용자 보고상 xAI 사용량이 소진되어 Grok CLI·Grok Bot 실호출을 하지 않았다.
- Grok Bot은 `/vibe` 내부 GUI-only Relay 어댑터이고 직접 `/vibe-bot` 호출과 호환된다. CLI/API/MCP로 가능한 작업을 Bot으로 보내지 않는다. 실제 활성 roster·Relay·비용/결과 증거 없이는 발송·완료 판정을 하지 않는다.
- 허브 `E:/Coding Infra/AI Infra/Communication/DECISIONS.md`의 D-44는 로컬 기록이다. 허브 저장소는 별도의 dirty/diverged 상태이므로 원격 반영으로 간주하지 않는다.

### 다음 작업 큐
| # | 작업 | 크기 | 권장 |
|---|---|---|---|
| A | PR #76의 최종 main/CI·source-only hold·Pages·이 문서의 도달을 확인하고 다음 개발 브랜치를 정한다 | 작음 | 먼저 |
| B | Claude/Codex CLI의 planner `ready`와 실행 어댑터의 no-skill/node 제한을 일치시킨다. 현재 합성 `step(skills=["explain"])`는 planner를 통과하지만 실제 CLI adapter는 거부한다 | 중간 | 허위 준비 상태의 남은 사례 |
| C | AGY와 Grok CLI에 각각 구독 전용 `claim → send once → lookup → verify` 보호 어댑터를 기존 Store에 연결; 계정·모델·effort·쿼터·credit fallback을 전송 직전 재검증 | 큼 | 한도 복구와 무관하게 오프라인 구현 가능 |
| D | 사용량 복구 후 각 xAI 표면을 새로 관측하되, 정확 계정/버킷·구독 포함·초과 과금 차단이 증명될 때만 실호출; Bot과 CLI의 쿼터를 서로 대체하지 않음 | 중간 | 비용 증거가 없으면 계속 차단 |
| E | Claude/Codex 사용자 설치 후보의 자산 보존·Gstack 런타임·호스트 명령 선택·구독 청구를 별도 검증하고 설치 게이트 재판정 | 큼 | 소스 머지를 설치 준비로 오인 금지 |

### 결정 요약
- D-44 독립 토론 판정: 먼저 허위 `ready` 차단, 이후 AGY/Grok 보호 어댑터를 오프라인 구현. 새 중앙 registry 신설은 기존 planner/Store와 중복되어 보류. 소수 의견은 한도 복구 직후 사용성을 위해 어댑터를 선구현하자는 것과 장기적으로 명시적 준비 상태가 유리하다는 것이다.
- D-45 별도 심판은 #76의 코드·이 문서를 같은 최종 HEAD에서 소스 전용 머지하되, 새 CI/hold·기존 CLI planner/adapter 불일치의 인수 기록을 조건으로 했다. 소수 의견은 CLI의 노드별 실행 제한을 먼저 고치자는 것이다. 사용자 설치·실호출·결제 변경은 이 문서로 승인되지 않는다.

### 핵심 파일 위치
```text
skills-src/vibe/SKILL.md                         메인 스킬 계약·비용 경계
skills-src/vibe/scripts/orchestrate.py            실행 경로·과금·쿼터 planner
skills-src/vibe/scripts/test_orchestrate.py       허위 ready 회귀 테스트
skills-src/vibe/references/orchestration.md       런타임·어댑터 운영 계약
skills-src/vibe/scripts/execute_bot.py            GUI 전용 Bot Relay 어댑터
docs/INSTALL.md                                   후보·사용자 설치 게이트
```

### 다음 세션 시작하는 법
```powershell
git fetch origin main
git show origin/main:docs/HANDOFF.md
gh pr view 76 --json state,headRefOid,baseRefOid,statusCheckRollup
```

`docs/HANDOFF.md`가 아직 `origin/main`에 없으면 PR [#76](https://github.com/Simon-YHKim/SimonK-stack/pull/76)의 본문·변경 파일 또는 아래 브랜치에서 읽는다.

```powershell
git fetch origin fix/vibe-provider-readiness-261001
git show origin/fix/vibe-provider-readiness-261001:docs/HANDOFF.md
```

---
