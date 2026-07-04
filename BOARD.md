---
owner: claude
note: "이 파일은 Claude(오케스트레이터)만 작성한다. Codex·Antigravity·Grok은 읽기 전용."
last-updated: 2026-07-03 08:17 KST
run_mode: RUNNING (CONTROL.md 정본 — 2026-07-02 재개, 07-03 감사·정비 완료. 데몬=codex+AG 레인, grok=요청전용, 원격오더 채널=watchdog 감시)
live_head: 2nd-B 라이브 상태는 2nd-B 레포(github.com/Simon-YHKim/2nd-B main)와 ORDERS.md가 정본 — BOARD frontmatter에 SHA 복제 금지(06-17 스냅샷이 16일 stale로 남던 관행 폐기, 2026-07-03).
---

# BOARD.md — 마스터 상태판 (always-latest)

> 전체 작업의 단일 진실 소스(single source of truth). Claude가 갱신.
> Codex·Antigravity·Grok은 세션 시작 시 이 파일로 현재 상황을 파악한다.
> **런-스테이트는 `CONTROL.md`, 합의는 `DECISIONS.md`.** 운용 모델 = B(자율, PROTOCOL §11).

## 🎯 현재 포커스 (2026-07-03 08:17 — 2nd-B 개선 루프 · 4-AI 디렉티드 배정, Claude)
> **2nd-B 3세션 완결 직후** (rev2 15PR+#726 / fable5 게이트해소+#727 / runtime 0.0.7 EAS 빌드 FINISHED, OTA 그룹 40033b66). Claude QA 세션이 상시 감시(main/PR/OTA/허브/inbox) + 머지·OTA 보장 중.
> **디렉티드 오더 3건 발행 (닫힌 루프 — 산출 수거→Claude 검증·머지→피드백)**:
> - **AG**: `007-emu-qa` — 0.0.7 APK 에뮬 설치 + 신기능 캡처 세트(소셜버튼/Seen gap/통화회고/plans). 판정은 Claude 픽셀 직독.
> - **Codex**: `ko-spotcheck` — share/capture/ops/imagine/star KO 카피 vs 글로사리·em-dash·하드코딩 점검, `codex/ko-spotcheck-0703` 브랜치. 머지는 Claude.
> - **Grok**: `consumer-advisory` — 통화회고·세컨비의추정 KR 수용성/프라이버시/클리니컬 카피 리스크, ≤10줄.
> 게이트 불변: 파괴/비용/secrets/임상/법무 + 수익화(plans 3티어)=Simon.

## 이전 포커스 아카이브 (2026-07-03 — 허브 전수 감사·정비 사이클, Claude)
> **허브 재정비 완료.** Simon 지시(트랜스크립트 4종+Fugu 적용 확인·레거시 정리·라우팅·원격·에러·머지)에 따른 전수 감사 — 10-agent 워크플로 + Claude 통합. 상세 `Output/hub-audit-20260703.html`.

**고쳐진 것 (r1, 2026-07-03)**:
- **git**: codex 브랜치 하이재킹 복구(206커밋 master ff-머지, stray 삭제) + **3중 브랜치 가드**(commit.ps1 non-master 차단 · 데몬 BRANCH-HEAL · watchdog 알림). 오프머신 백업(HubBackup→comm-hub) 정상화.
- **오더 위생**: stale open 89→0 (84 batch-stale + 5 응답 클로즈, PROTOCOL §3 TTL 신설). codex "stale queue hold" 공회전·커밋 스팸 근절(no-op 무커밋 규칙).
- **AG 좌석 부활**: 하드페일 진범 = ConPTY가 Start-Job(콘솔 없음)에서 사망 — `AGY_USE_CONPTY=0`(winpty) 픽스, Start-Job 재현 테스트 PONG 검증. (agy 인증 유효 확인.)
- **모델**: claude `claude-fable-5`@max 재핀(재가용) · HubModelBenchmarkRefresh 예약작업 재등록(09:00, pwsh 런처).
- **원격 오더 채널**: 06-21 이후 **12일 무소비 발견**(소비자=/loop 세션 SPOF) → watchdog `orders-unconsumed` 감시 + 소비자 하트비트(`-Heartbeat`) + 픽업 원장(`-Ack`) 도입.
- **라우팅 정합**: grok 데몬 기본레인 제외(§4 요청전용) · AG 레인 "직접 코딩+QA, 푸시는 Claude 게이트"로 §1↔§4↔데몬 일치 · MoA 교차검증 런타임 훅(데몬 프롬프트, ROUTING-MOA §5).
- **문서**: PROTOCOL 3-AI→4-AI·gemini sunset 과거형·§33 현행화, README 재작성, STATUS running 동기화, CONTROL 변경로그 소급, 레거시 `Legacy-` 정리(EMERGENCY_ANDROID·루트 inbox·AG QA 잔해 83파일·prompts sync 3종·Output 9종 등).

**남은 것 / 게이트**: 원격 오더 디렉터 세션은 Simon /loop 재가동 시 부활(프롬프트 = report-4ai-postfix RUN 카드).

**프롬프트팩 전량 소화 (2026-07-03 05:45 — Simon /goal "모든 to-do")**: frontmatter 9키 계약을 데몬+프롬프트 7종에 배선 · grok 분량 가드 · `tools/dispatch-oneshot.ps1` 신설(RUNBOOK §8) · hub-health WARN 9→0(활성 3건 키 보충 + _archive 집계 제외) · **D-25 비준**(hub-role-additions 3안 — 06-14 기배선 확인, AG 감사관 듀티는 4ai 테스트로 실증) · AG 실작업 커밋-완주 실증 진행 중(agfix-doc-audit 오더, 신규 타임아웃 하에 첫 실작업).

**4-AI 라운드트립 테스트 (2026-07-03 05:15 — 3/3 응답 수집, 문제 6건 발견·4건 즉시 수정)**:
- 왕복: Grok 87초(옵트인 원샷) · AG 4분52초(drain 21초 픽업, 단 래퍼 킬로 미커밋→회수) · Codex 6분14초(사이클 정렬 지연 포함). 품질: AG가 진짜 문서모순 2건 발견(§0 푸시 문구·3.5-flash 자기모순 — 반영됨), Codex a11y 실발견 2건(v2 리포트 반영됨), Grok 실링크 포함 시장신호(정직).
- 수정: agy 90초 킬 P1(→300s/900s) · Count-OpenOrders ref-blind P1(→ref-인지) · MoA "자기 도메인 스킵" 금지 명문화 · 테스트 오더 3건 클로즈.
- 관찰(비수정): self-report 신뢰불가(codex "high" 주장 vs 배너 medium 실증, grok "4.3" vs spawn build — **계측은 배너/로그 1차 근거로만**) · AG frontmatter 부분누락(created/project) · grok 분량제한 위반(10줄→48줄, over-delivery 성향).

---

## 이전 포커스 아카이브 (2026-06-17 21:46 KST · /loop 디렉터 실행자 사이클 — Claude)
> **라이브 origin/main `0e3ef45c`** — 이번 세션 deep-space O-31 패치 **7건** 머지(#437~#442·#444): a11y·토큰·/profile밀도·설정SVG·authBack·**#442 auth-bypass게이팅+탭바겹침**·**#444 가시 back+브랜드공존(Codex)**. 모두 독립 release-gate GO. **Stage7 export GREEN.** Stage3(Back단일화·노드모달無·가시back·auth게이팅) = 사실상 완료.
> **⚠️ grok 자동루프 over-produce**: 데몬이 600s마다 반복 advisory 생산(누적 291 아카이브, 알람 진실화). ROUTING §4는 grok=요청전용 — **Simon: grok 데몬 레인 throttle/정지 권고**(value 소진). AG=stale 브랜치 리셋 요청됨.
> **AI 상태(22:06)**: Codex 쿼터 백오프 ~80분(자동복구) · Grok request-wait(Stage5 advisory 소비됨) · **AG=agy 미인증으로 16h 정지(Simon 1회 `agy` 인증 필요)**.
> **AI 가치 재배치(21:40)**: AG=deep-space 신규빌드 에뮬 QA(유휴 해소) · Codex=O-31 서브화면 테마/밀도(fresh 브랜치 a656a1f4+) · Grok=ownership 테마 종료·인사이트 소비→Stage5 캐릭터 수용성 신규주제.
> Simon /loop 원격오더 실행자(디렉터) 세션 가동. CONTROL=running. 매 사이클 orders-poll → 분배/통합 → verify·release-gate → 머지·라이브 → DONE/BOARD 갱신. 게이트(파괴·실비용·secrets·임상·법무·미성년DPIA)만 Simon 확인.

**폴(orders-poll.ps1 · origin/main 기준)**: 미처리 = **O-30 · O-31** 둘뿐(O-0~29 전부 DONE).
- **O-31 (P0 · deep-space 단일 본체화)**: origin/main `f6489ba2`에 Stage1·2·4 이미 머지(#434 라우트연결 · #435 synthesis · #436 deep-space default). **잔여 = Stage3(Back 별자리홈 단일화) · Stage5(Three.js 캐릭터 본체 포팅/하이브리드) · Stage6(정보밀도) · Stage7(nav-contract E2E + persona-sim + verify/export green)**.
- **통합 대기 머지후보 2건(Codex · deep-space)**: `codex/deepspace-a11y-labels-i18n` **601415d5**(a11y 라벨 KO/EN + 가드 · type-check/i18n/lexicon/emdash/lint/merge-tree green · Tier0 무게이트) · `codex/deepspace-token-spacing` **7dc0e8ab**(pressed 토큰화 + letterSpacing + 가드 · bounded green). → 다음 사이클 **독립 통합 워크트리(origin/main 기준)에서 release-gate → 머지·라이브** (Codex 활성 워크트리 비침범 §18).
- **O-30 (4-AI 풀분배 · Codex tty)**: 사실상 완료 — 워크트리(2ndB-codex/antigravity/ds-nav-stage2/ds-theme-stage3) 존재, Codex가 데몬 대신 **포그라운드 5분 루프**로 가동(tty-block 해소 · 21:03 FYI). 분배로그 정리 후 DONE 이동.

**허브 LIVE**: Codex(deep-space a11y/token 산출 중) · Grok(KR X 35패널 소비자 advisory 산출 중) 활발 / AG 프로세스 가동(최근 산출 오전 · 에뮬 QA 재급양 대상) / HubWatchdog Ready.
**⚠️ 주의**: `C:\2ndB` 로컬 클론 stale(origin/main 대비 behind 91 · ahead 1 · dirty=기머지 중복 잔여) → **머지 vehicle 아님**. `docs/legal/DPIA-2ndB-minors-draft.md` 등 게이트 파일 라이브 푸시 금지.
**lane**: 구현·머지·online-git=Claude / UI·캐릭터에셋=Codex / 네이티브·에뮬QA=AG / 소비자검증=Grok.

## 이전 포커스 아카이브 (2026-06-14 루프) — 2nd-B 기능/에뮬 점검 + 디벨롭 (Simon /loop "AIs decide")
> 허브 가동(CONTROL running, §34/§35·라우팅·가드). 각 AI 자기 레인 directed. **디자인·아키텍처·네이밍 결정 = §35 `ai-debate` 경유**(혼자 결정 X). **UI = design-first**. **머지·온라인git·iOS = Claude 단독**(§11).

**🧭 2nd-B 세계관 정본 정렬 (2026-06-17 · D-24 · `projects/2nd-B/WORLDVIEW.md`)**: 모든 2nd-B 디벨롭은 **불변 큰 틀**에 정렬 — 북극성+북두칠성7별(역할/액션/지식=목표트리 강등, 지금의나=별1, 소울코어=종합)·**L1~L5 단일 사다리(밝기=품질=신뢰도)**·두뇌0-3 다리·propose→ratify·용어매핑(내부 키/슬러그 동결·표시 라벨만)·C-code 하드제약. 단계 **0**(2nd-B `CONTEXT.md` 글로사리 3블록 락 + `worldview-naming.test.ts`, DOCS-ONLY)→**A**(7렌즈 재구조+ECR-S→별5+결정론 밝기함수)→**B**(경량 신뢰도 정지규칙+LLM/도구 분리 계약테스트+C3/C9 배선)→**C**(최소 시연루프: 밝기②+propose-ratify⑤). lane: 구현·머지=**Claude** / UI·라벨·신규화면=**Codex**(anti-slop) / 네이티브·콜드스타트(전부 L1)·SVG OOM QA=**AG** / XPRIZE 프레이밍·임상어휘 advisory=**Grok**. **완벽해질 때까지 반복 개선.**

**라이브 (origin/main 3381cd9, 11:57 KST · verify 142 suites/1188 tests 전부 PASS) — 닫힌 루프로 이번 세션 2nd-B 27건+ 머지**:
**r33(12:44 허브 인프라 — Simon ultracode)**: ① **HUB-STARTUP.html 정리**(모드A 데몬/모드B 인-윈도우 루프 분리, 붙여넣기 대상 AI 아이콘, 대비/죽은CSS/아이콘일관성/복사레이스 리뷰픽스, 수동원샷 제거) ② **hub-health.ps1 신설**(허브 기능 셀프테스트: 구문·commit가드·상태파일·models.json최고모델·git/UTF-8·데몬생존, read-only, 19 PASS/0 FAIL) ③ **최고모델+effort 강제**(`MODELS.md`+`tools/models.json` 정본, 데몬이 spawn시 자동주입: claude-fable-5/gpt-5.5 xhigh/grok-4.3 high/gemini-3.1-pro-preview HIGH; activate 4종·codex RULES 반영; 웹검증 workflow 10에이전트) ④ **일일 벤치 갱신**(`refresh-models.ps1`+Windows예약작업 `HubModelBenchmarkRefresh` 09:00, 제안+Claude게이트 — 환각id가 spawn깨는 것 차단). 정본=MODELS.md.
**r32(11:57)**: **boot-profile isMinor-preserve 안전 P2 머지·라이브**(`3381cd9`=세션복원 시 프로필행 missing이어도 같은 userId면 직전 isMinor 보존→미성년 consent/youth hotline 라우팅 1프레임 깜빡임 차단). **구조 수정 즉효**: 직전 사이클에 박은 PROTOCOL §241 "실 SHA 강제"로 Codex가 placeholder 대신 실 SHA(`bc8e81a`)로 재제출→머지 가능해짐. cherry-pick(staleness-immune)으로 통합. AG 데몬 다운 지속(신규 산출 0, 복구 대기).
**r31(11:43)**: Codex persona mbti shape guard 통합·라이브(`b8ef8d2`=비정규 MBTI 레코드(type 4글자/scores object-shape)를 identity-truth로 오인 차단, 8 score키 finite+canonical [EI][NS][TF][JP]만 surface). **boot-profile isMinor-preserve P2(미성년 consent 라우팅 깜빡임=안전관련)는 HOLD** — Codex 브랜치 `auth-session-sweep-1124`가 미커밋/미네이밍이라 접근불가, commit+네이밍 요청함. **AG 데몬 다운**(`critical error [object Object]`, no-daemon 1h) — 복구 후 reset-플로우 에뮬 재검증 inbox 배치. codex 데몬 중복(PID41444+AG기동) 모니터링.
**r29(11:26)**: Codex auth 스윕 통합·라이브(`39f9592` judge profile mode·`0399f06` impossible DOB reject·**`35a040c` reset email state 누수 P2**=재설정 이메일 수정 시 stale 확인카피 클리어). AG 에뮬 스모크 PASS(dfd83bb)·auth-elevation Codex 956a2a24 기확인. **AG idle-state ERROR 규명=버그 아님**(CharacterPathLayer withRepeat 의도된 무한 애니메이션; animator scale 0이면 dump SUCCESS·UI 회귀 0). 재배정: AG=reset 플로우 에뮬 재검증·Codex=persona-records 스윕·Grok=로컬소유권 카피 advisory(§35 전 직접반영 X).
first-glimpse 정직카피 · pre-auth 가드 · PremiumButton a11y · home CTA · profile chips · data-shape 계약테스트 · tab-contrast · capture-abort · **P0 홈 sources.created_at→captured_at**(AG 에뮬 QA가 잡음) + sources-orderby 가드 · **audit-write crisis UX/ledger split**(임상안전 HOLD→재설계→머지) · **stale-screens P1**(NavGraph stable-ref+memo+focus-refetch) · core-brain evidence-refresh(Gemini 재과금 회귀 차단) · T1 first-save comfort/grace · first-run graph records · **chat 쿼터 export 버그**(TOCTOU+red-zone 보존) · persona BFI 부분행 가드 ×2 · audit crisis-fallback · import field caps · **capture-file size guard 다층**(picker/content-length/byteLength). + AG graph-perf(58b5e2b).
**r28(09:41)**: 새 머지코드 없음(triage: `62505c1` T4 v10 asset=이미 main서 pattern_data 제거됨·stale 중복 / `aaaa3e4` poll-native=동일테스트 이미 main 존재·redundant). **AG 에뮬 QA 3건 수령**(드릴다운#252 PASS·FlatList PASS·elevation 리뷰) + logcat_crash/freeze=앱 FATAL 없음(skia AGTM 양성). main 정책가드 3/3 PASS.
**닫힌 루프**: AI 산출 수거→framework-aware 검토→머지/HOLD→피드백+재배정. merge-gate 진가 2회(AG가 실P0 / 내가 임상안전 회귀 HOLD). [[feedback_closed_loop_orchestration]] [[feedback_web_ci_green_not_runtime_safe]].
**🔴 Simon 게이트 1건 = D-17 Lever B(계정 전 캡처) 빌드** — 설계는 AI 합의 확정(Codex minimal-safe device-local-pending), 빌드 착수만 §11-5 법무/동의/미성년 GO 대기.
**가동 중(r28 재배정)**: Codex=persona-records 스윕 진행→완료시 auth/session 스윕 · AG=최신 main(dfd83bb) 에뮬 기능 스모크(런치/캡처/챗/persona)+경계 auth-elevation만(40파일 sweep 금지=hard-shadow 의도) · Grok=feature-gap #1만(T1 recap 반복 단호히 중단).
**하우스키핑**: 머지된 codex 브랜치 worktree-pinned sprawl(~13, daemon idle시 GC) · BOARD single-writer = Claude 전용(commit.ps1 lane-guard 가동중).

| Thread | 내용 | 레인 |
|---|---|---|
| **T1 페르소나 P1** | 첫화면 "이 앱 뭐지" 효용 1줄+1차행동(12/12) · 가입게이트 경량화/둘러보기 · 첫 journal 저장 게이트 해제 · 프라이버시 1줄(가입·capture). #367 comfort-offer 후속. 디자인결정=§35 토론, 수익화/법무=Simon | Codex(UI worktree) + Claude(로직·결정·머지) |
| **T2 iOS 라이브** | 로컬 main 미푸시 iOS 픽스 6커밋 `npm run verify`→push(라이브). Appetize 업로드=토큰 게이트(별도) | Claude(온라인git) |
| **T3 그래프 트리 P11** | 모션 + narrative 재틴트 — 하단뿌리 상향 크리스탈 테서랙트 트리 마감(v10 아트 유지) | Codex(모션UI) + AG(device QA) |
| **T4 에셋 v3 통일** | 상태-에셋 레이어(feedback.tsx 동일사각형 보완) · 세대난립→v3 SVG 통일 · 마스코트 네이밍 일치. 정본 DESIGN.md+V3_ASSET_BRIEF | Codex(이미지·에셋 레인) |
| (advisory) Grok | 4 thread 시장/소비자 신호(경쟁앱 반응·바이럴훅·획득채널·표현민감도) — 이미 active | Grok |

charter(§12.2): 미머지 8건 초과 시 발견중지·머지대기. P3 통합 1건. baseline 갱신 후 재평가. **결정지점은 §35 토론으로 수렴, 발견형 thrashing 금지.**

## 🔄 자율 루프 상태 (Autonomous Loops, PROTOCOL §12)
| AI | 루프 | 상태 | charter |
|---|---|---|---|
| Claude | 통합(구현·머지·온라인git) + **제안 큐(§25)** | running | 백로그 트리아지 → PROPOSAL_QUEUE 소진 → verify → merge |
| Codex | anti-slop 발견 | running | 미머지 8건 초과 시 발견중지·P3 통합 |
| Antigravity | 네이티브 픽스·QA | running(**Device QA 완료**) | **E4(터치증명), E16(데이터힌트), E20(RTL), §19(graph perf) 디바이스/에뮬레이터 검증 및 픽스 완벽히 완료**. 리포트 전달 완료. Codex/Claude PR 지속 QA 리뷰 중 |
| Grok | 트렌드·결정입력 | running | **X/소셜 GTM 리서치로 재배치(20260607-0322)** — 경쟁앱 소셜반응·바이럴훅·획득채널·표현민감도. advisory(검증 전 직접반영 X) |

## 🔐 외부의존 블로커 (Simon 개입 필요 — §15)
- (DECISIONS.md `external` 항목 참조: D-03 consent 법무, D-05 social provider 실설정)
- **🔴 수익화 결정 5건 (페르소나 시뮬 65 simon 항목)** — PROPOSAL_QUEUE 'Simon 수익화 결정' 블록: M1 가격투명성(요금제화면+가격확정)·M2 무료티어 관대함·M3 결제수단/PG(Stripe만으론 KR/저소득 배제)·M4 구독모델/피로·M5 신뢰인증. 승인 후 Claude가 티어게이팅·요금제·결제 구현. (권고안 HTML: `agents/claude/outbox/preview/20260607-0149-monetization-recommendation.html`, deep-research wuz03uq9o로 실증 보강 중)
- **🟢 AG device-native 고유 작업 완료** — AG가 에뮬레이터에서 E4(터치 증명), E16(데이터힌트), E20(RTL) 렌더링/동작 확인 완료 및 §19(graph perf) 메타데이터 스트립 픽스 처리 완료. (상세 내역은 inbox 리포트 참조). 이어서 루프 지속 중.

## 🤝 합의 진행 (Consensus — DECISIONS.md)
- D-01~D-07 투표 대기 (펀치리스트 이관). 각 AI는 `type: consensus_vote`로 참여.

## 🔥 진행 중 (In Progress)
| ID | 작업 | 담당 | 상태 | 비고 |
|---|---|---|---|---|
| cycle-5 | 2nd-B privacy opt-out monotonicity P1 — 동의 게이트가 stale/실패 완료로 재활성화되던 회귀 | claude | ✅ **머지+라이브** | PR #215 main `911c979`, Codex MERGE-SAFE+closes_p1(2라운드: stale완료·실패revert 둘 다). cycle-3 직렬화 수정의 잔여 consent 무결성 버그 |
| cycle-4 | 2nd-B 은퇴라우트 slop 수정 — /journal·/imagine·/mbti를 실제 목적지로 emit + 재유입방지 테스트 | claude | ✅ **머지+라이브** | PR #214 main `ee9f80b`, Codex MERGE-SAFE(retired-route gate 종료). 리다이렉트는 deep-link 호환 유지 |
| cycle-3 | 2nd-B **적대적 버그헌트 + 수정** — 42발견→P0:0/P1:3/P2:11/P3:13, 18+4수정 | claude | ✅ **머지+라이브** | PR #213 main `ada9bd2`, Codex 8.5 MERGE-SAFE(2 HIGH 블로커 잡고 수정). HTML `agents/claude/outbox/preview/20260606-overnight-summary.html` |
| cycle-2 | 2nd-B UX 완벽화 — **머지+라이브** (PR #212, main `d8ba4a0`) | claude | ✅ done | Codex 97. FlatList·NavGraph LOD·raw에러·trust(persona/social/consent) |
| cycle-1 | 2nd-B 완성형 사이클 — **머지 완료** (PR #211, main `0bfbfa3`) | claude | ✅ done | 보안·trust·route·Android네이티브·a11y |
| research-2 | deep-research: 사람을 정확히 파악하는 구조(SOKA·informant·표현적글쓰기·ESM·LLM) | claude | 실행중 | → "구조" 설계 culminating 산출 |
| gate-stream | Codex 100점 UX 게이트 스트림 — 130 발견. 신뢰카피·a11y·파괴UX·i18n 4클러스터 | codex+claude | 🟢 소비중 | **머지 6건**: preauth-trust`cbf61cc`·PremiumButton-a11y`c2a7e6c`·settings-selected`f7004c1`·permissions+formats`3569ae6`·insights-false-empty`3153de4`(+4테스트, 834 green). Codex=capture/research selected, settings/account+로직게이트=claude |
| pipeline-test | 4-AI 풀파이프라인 + 피드백 round-trip 실증 | claude | ✅ 검증 | 헤드리스 codex/grok/gemini 라운드트립 OK(기여자별 커밋). Grok 검증 PASS. AG D-06 제안. 레거시 48 분류(38삭제/10keep). 함정=헤드리스 긴 한글 프롬프트는 stdin UTF-8 |
| false-empty | source-only false-empty 데이터진실 게이트(insights·core-brain·trinity 형제) | claude | ✅ 3/3 완결 | insights`3153de4`·core-brain`3becd09`·trinity`34c7da5` 머지(records+sources 집계). 데이터-진실 family 완결 |
| hub-v2 | 4-AI 허브 자율화 개편(B모델) — CONTROL·DECISIONS·PROTOCOL §11~18·board.ps1·commit.ps1·4 activate 프롬프트·기여자표기 | claude | ✅ 구현완료 | 5갈래 조사 워크플로 기반. Simon이 4 프롬프트 각 터미널 입력 예정 |

## 📥 분배됨 / 대기 (Assigned / Waiting)
| ID | 작업 | 요청→담당 | 상태 | 메시지 |
|---|---|---|---|---|
| disp-codex2 | MBTI 강등 스펙 + DESIGN 판정 + 모바일 오버플로우 스펙 | claude→codex | ✅ done | 회수 완료, 구현 반영중 |
| user-grok | 나이대별·국가별 X 선호/유입/트렌드 10+cycle 딥다이브 | **user**→grok | 진행/완료 | §10.4 user-direct (`85d1322`) |
| user-android | Android 10+ 심층 검사 리포트 (part 1·2) | **user**→? | 진행 | §10.4 user-direct (`1582810`,`e4722b5`) |

## 👥 멤버 온보딩 상태
| AI | 역할 | 상태 | 런타임 |
|---|---|---|---|
| Claude | 오케스트레이터 + 코딩 | ✅ active | Claude Code |
| Codex | 이미지 · UI/UX | ✅ onboarded | codex CLI (헤드리스 OK) |
| Antigravity | Android/Google 네이티브 **개발+검수** | ✅ onboarded | **gemini CLI**(헤드리스 작동) / agy CLI(헤드리스 hang—첫 인증 필요) / IDE(수동) |
| Grok | X(소셜) 트렌드·소비자 리서치 | ✅ onboarded | grok CLI (`--prompt-file` UTF-8, 헤드리스 작동) |

## ✅ 완료 (Done) — 최근 10건
| ID | 작업 | 담당 | 완료 |
|---|---|---|---|
| disp-codex | 화면 인벤토리·IA 감사: 43라우트 분류 + Phase6 화면맵 + DESIGN 위반 후보 | codex | 2026-06-05 |
| disp-grok | 소비자·경쟁 리서치(7제품 감정 + Barnum + portable hook + 권고5) | grok | 2026-06-05 |
| disp-antig | 네이티브 QA 준비도: 조건부 가능(Reanimated v4/RN0.85 리스크) + QA 체크리스트 | antigravity | 2026-06-05 |
| audit-wf | 7차원 코드감사 → 8건 확정(0C/0H/5M/3L): knowledge_sources RLS 인젝션·DDL drift·wiki export PII·마스코트 canon | claude | 2026-06-05 |
| deepres-wf | 심리토대 문헌(Big5/SDT/Attach/VIA) 24 claim 수집(검증레이어 장애→C8 인간검증 대상) | claude | 2026-06-05 |
| status-check | 4-AI 허브 라이브 점검(3-AI 헤드리스 핑 OK: Codex/GPT-5·Gemini·Grok4.3) + 2ndB ff-only 동기화 | claude | 2026-06-05 |
| protocol-v10 | PROTOCOL §10(실행모드·자동승인·Claude단독대화·병렬·직접지시/현황) + `*-activate.md` 3종 추가 | claude | 2026-06-05 |
| onboard-codex | Codex 허브 온보딩 + self-commit 실증 | codex | 2026-06-05 |
| onboard-antig | Antigravity(gemini) 허브 온보딩 + self-commit 실증 | antigravity | 2026-06-05 |
| boot-0 | 3-AI 통신 프로토콜·구조 생성 | claude | 2026-06-05 |

## 🧱 결정 대기 → DECISIONS.md로 이관 (PROTOCOL §14 합의)
> 예전 "Simon 결정 펀치리스트"는 **합의 원장 `DECISIONS.md` D-01~D-07**로 옮겼다.
> 대부분은 **4-AI 합의로 결정·진행**(decide), 진짜 외부의존만 Simon(external): D-03 consent 법무·D-05 social provider 실설정.
> 안전레일(파괴·실비용·secrets)은 합의 우회 불가 — 그대로 Simon 확인.

## 📌 활성 프로젝트
| 프로젝트 | 레포 | 경로 | 단계 |
|---|---|---|---|
| **2nd-B** | github.com/Simon-YHKim/2nd-B (main, 138 br) | `projects/2nd-B/` | build |
| _TEMPLATE | — | `projects/_TEMPLATE/` | 템플릿 |
