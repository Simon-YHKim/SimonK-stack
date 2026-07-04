---
owner: claude
note: "이 파일은 Claude만 작성한다. 다른 AI는 의견을 자기 outbox(type: consensus_vote)로 제출하고, Claude가 여기에 종합한다."
last-updated: 2026-07-03 KST
last-sync: 2026-07-03
---

# DECISIONS.md — 합의 원장 (Consensus Ledger)

> **목적**: 예전엔 "Simon 결정 필요"로 멈추던 항목을, **4-AI가 상황을 종합·투표해 결정하고 진행**한다(PROTOCOL §14).
> **사용자 개입은 단 하나** — **외부의존 병목**(auth/credentials, 법무 사인오프처럼 AI가 물리적으로 못 하는 것)뿐. 나머지는 합의로 진행.
> **항상-확인 안전레일은 합의 대상이 아님**: 파괴적·실비용·secrets 노출은 합의로 우회 불가 → 그대로 Simon 확인.

## 투표 방법 (각 AI)
- Claude가 `type: consensus_request` (to: all)로 주제+옵션 제시 → 각 AI는 `agents/<me>/outbox/`에 `type: consensus_vote`(ref: 요청id, 선택+근거) 작성.
- Claude가 집계 → 아래 표에 결과 기록 → 결정대로 진행(또는 외부의존이면 Simon 에스컬레이션).

## 결정 분류
| 분류 | 처리 |
|---|---|
| **decide** | 4-AI 합의로 결정·진행 (가역적·dev 범위) |
| **external** | AI 불가 — Simon/외부 필요 (auth·credentials·법무). 그동안 병렬로 다른 일 |
| **safety** | 파괴적·실비용·secrets — 항상 Simon 확인 (합의 우회 불가) |

---

## 진행 중 합의 (Open)

| # | 주제 | 분류 | 옵션 | 투표(C/A/G) | 결과 |
|---|---|---|---|---|---|
| D-01 | `EXPO_PUBLIC_FORCE_TIER` 기본값 (페이월 전면개방 → release 전 off?) | decide | A:현행 brain 유지 / B:release빌드 off, dev는 brain / C:완전 off | — | 투표대기 |
| D-02 | 130 게이트 스트림 우선순위·throttle(배치 N·P3 보류) | decide | A:P1만 즉시·P2/P3 배치 / B:전부 순차 / C:클러스터 통합 후 | — | 라운드1 시작(preauth-trust 머지 cbf61cc). charter=미머지8↑중지 |
| D-03 | consent 카피 + `LEXICON_LAST_LEGAL_REVIEW=null` | external | 법무 사인오프 필요(AI 불가). 엔지니어링 기본값(공유 default OFF)은 decide로 선반영 | — | Simon/법무 |
| D-04 | HIBP 네이티브 폴리필(expo-crypto 의존성 추가) | decide | A:추가 / B:웹만 강제 / C:보류 | A | ✅ **해결·머지(b661b7b)**. AG 구현+Claude 보완(테스트 모킹). 네이티브 유출검사 활성화 |
| D-05 | social provider 실설정값(라이브 Supabase 등록 provider) | external | 실등록 정보 필요(AI 불가). 미설정 자동숨김은 이미 적용 | — | Simon |
| D-06 | 런타임 device 증명(AG 에뮬 스크린샷 매트릭스) | decide | Antigravity 자율 사이클로 수급 → Codex 100점 게이트 종료 | — | AG 루프 배정 |
| D-07 | consent durable 큐(앱 재시작 후 재전송) | decide | A:durable 구현 / B:현행 in-memory 유지 / C:법무 후 | — | 투표대기 |
| D-08 | 자기이해 방식 (질문지 vs 인터뷰 vs ESM) | decide | **하이브리드 3층 권고**(질문지 시드→인터뷰→ESM, SOKA 특성별 신뢰도) | 하이브리드 | ①persona 특성별 confidence 머지(19f3bd0). 다음 ②온보딩 시드화 ③ESM=D-10 |
| D-09 | 수익화 가격·패키징·M1~M5 (KR+Global) | decide | 2티어 vs 3티어·가격·PG·무료티어 | 합의(10AI, 2026-06-07) | ✅ **재확정**: 런치 **2티어**(Free 로컬무제한 + Plus=cortex AI opt-in **$4.99/₩4,900**·연 2개월무료), Pro=brain **로드맵**, soma 폐기(enum 유지). **M2**=로컬 무제한(FREE_LIMIT서 journal/note/self_context 제거, AI추론·동기화만 게이트, free AI 5턴/일). **M1**=상시 Plans 페이지+AI게이트 contextual paywall+결제전 1줄고지. **M3**=네이티브 IAP+웹 토스(Phase1 웹→Phase2 IAP, Stripe단독 금지). **M5**=신뢰서약(전량 export·AI default OFF·no train/sale/ads·비임상·민감정보 분리동의). **Simon만**=실 PG계약·Apple/Google·사업자등록·법무사인오프·실과금(권고가만 AI). |
| D-10 | ESM 층 도입 | decide | A:도입 / B:보류 / C:phase2 | AG:A·Codex:A | ✅ **합의=A, 1단계 라이브**: 데이터레이어(`2e735e8`) + check-in 화면(`5c2838a` esm.tsx, 사용자-오픈·알림X). build.ts ESM→trait=Claude 후속(데이터 쌓이면). 알림=AG 후속 |
| D-11 | 마케팅 GTM (KR+Global) | decide | 포지셔닝·anti-creepy 신뢰·텍스트SNS·ASO·런치 | Grok X 확인 | ✅ **`docs/GTM.md` 머지(#216 `2cc45d1`)**. Grok X 리서치 정합. 채널예산·런치일만 Simon/§15 |
| D-12 | privacy 토글 진실 (8중 7 phantom) | decide | A:UI제거+긍정카피+CI불변식 / B:준비중라벨 / C:즉시 enforce | 합의(10AI, 2026-06-07) | ✅ **합의=A**(B 만장일치 기각): phantom 7토글 **UI 제거**(prefs 키·OFF기본·미성년클램프 보존→마이그레이션0), external_analytics만 노출, **긍정 local-first 카피 1블록**, **egress CI 불변식 + 고의 red-test**. 실제 enforce는 유출기능 출시 시 **JIT 동의**. **Simon=지금 없음**(미래 AI출시 시 PG/법무/실과금만). long_term_memory는 코드상 로컬등급(minor-promotable)이라 egress 대상서 제외 |
| D-13 | 브랜드 2층 구조 (앱명 vs AI주체) | decide | 통합 vs 2층 | Claude 결정(§14, 코히런스 감사 근거) | ✅ **2층 유지**: 제품/앱 = **"두번째 뇌 / 2nd-Brain"**(app.json·스토어·OS), 인앱 AI 주체+마스코트 월드 = **"세컨비 / SecondB"**(iPhone+Siri 패턴). jarvis 코드네임 → SecondB로 통합(G1). 비용 아님 → Simon 에스컬레이션 불필요 |
| D-14 | 마스코트 로스터 5 vs 6 (Iris) | decide | 5(characters.ts) vs 6(personas/village/monologues 실사용) | Claude 결정(§14) | ✅ **6 확정**: 실코드가 Iris(lumi)를 실사용·노출 중인데 source-of-truth characters.ts만 5인 누락 = 버그. **characters.ts에 Iris(lumi/아이리스, Muse Core) 추가**(G4) + CompanionName 포함. 비용 아님 → 합의로 진행 |
| D-15 | 한국어 용어·호칭 정본 사전 (코히런스 G7/G8) | decide | 통합 canon vs 현행 혼재 | Claude 결정(§14, 코히런스 감사 근거); G7 6종은 Codex min-churn 제안 후 비준 | ✅ **브랜드 레이어 토큰 확정**(D-13 도출): ①**AI 주체(KO prose)**="**세컨비**"(인앱 AI 자기지칭, secondb.json 정본). Latin "SecondB"=로고/스토어/영문 전용. 일반명사 "**비서**"를 주체명으로 쓰지 않음(consent.json "개인 비서"→세컨비; 비유설명은 허용). ②**앱/제품/저장소(KO)**="**두번째 뇌 / 2nd-Brain**"(저장처·앱·OS; wiki "SecondB에 저장한"→"두번째 뇌에 저장한"). ③**빌리지 워커 화면 거주자**(capture=Lumen 등)는 의도된 디자인 — 주체혼선 아님(보존). ④**G7 6종 용어군**(캡처/담기·pieces/records·위키/지식그래프/서재·journal/일기·리서치/자료실)=Codex 현행빈도 분석→최소-churn canon 제안→§14 비준. 적용=Codex 카피레인(outbox dispatch). 비용 아님 |

### D-16 — 다양성 5종 스킬의 app-dev-orchestrator 통합 방식 (§35 ai-debate 첫 기록, 2026-06-13)
- **안건**: 신규 다양성 5종(`i18n-localizer`·`accessibility-audit`·`persona-simulation`·`inclusive-ux`·`offline-first`)을 app-dev-orchestrator **필수단계**로 박을까, **opt-in 라우팅**으로 둘까, **하이브리드 조건게이트**로 갈까?
- **입장**: A) MANDATORY(구조적 보장, 5종 무조건 실행) · B) OPT-IN(키워드 트리거, 비용0·유연) · C) HYBRID(Stage-0 프로필 조건선택).
- **심판 근거**(제안자≠심판 §34.4): A의 핵심("보장은 구조여야지 기억 의존 X")은 옳아 HYBRID도 게이트 단계 자체는 필수로 둠. 단 A의 비용반박("no-op는 grep만")이 **코드로 반증** — `offline-first`·`accessibility-audit`의 precheck는 `npx build`+Lighthouse·라이브서버+headless Chrome라 싸게 N/A 판정 불가 → 내부툴/CLI 빌드마다 비싼 인프라 spin + cry-wolf. B는 자기인정 패배(트리거=부재 오퍼레이터가 안 침=감사가 condemn한 비보장; 자체 fallback "Stage-0 강제결정"이 곧 HYBRID 커널).
- **판정**: **HYBRID** — Stage 13.7 "diversity-gate"(실행은 무조건, 어떤 스킬 fire는 Stage-0 kickoff 프로필 결정론적 매핑; 모호하면 기본 **INCLUDE**, public/store-bound면 consumer-UI 서브셋[a11y+persona-sim] 강제; **P0만 hard-block**, P2/P3는 ship-with-debt; `docs/diversity-gate-<date>.md`에 INCLUDED/EXCLUDED+근거 기록). 7-3 가중 우세.
- **소수의견(보존=에스컬레이션 경로)**: 조건게이트도 Stage-0 답이 부실("개인 사이드"·"TBD")하면 감사 갭을 한 층 위로 재현 가능 + 녹색 "evaluated" 거짓안심 위험. **2-3 사이클 내 실제 miss 1건 관측 시 → consumer-UI 서브셋(a11y+persona-sim) 무조건 실행 승격**(둘은 싼 package.json-grep precheck), 비싼 페어는 게이트 유지.
- **후속**: ① Stage 13.7 신설(skill-gen-agent edit) + Related-skills 5종 추가 ② `persona-simulation:33`·`i18n-localizer:32` **허위 연동광고**(없는 stage 참조) 수정 ③ offline-first·a11y 비-consumer/고대역폭 기본 EXCLUDE ④ CLAUDE.md §20 게이트 1줄(+AGENTS/GEMINI 동기 §18) ⑤ 첫 검증=2nd-B kickoff dry-run.
- **메타**: `/ai-debate` 스킬(§35) **첫 dogfood**(3입장 패널 + 별도심판, wf `wzp1guqgt`) — 토론 시스템 작동 실증.

### D-17 — Lever B: 계정 전(pre-account) raw-capture 활성화 레버 (§35 허브 outbox 라운드, 2026-06-14)
- **안건**: week-1 활성화를 위해 "계정 생성 전에 한 문장 캡처 → 즉시 소유 리스트"(Lever B)를 도입할까? 도입한다면 어떻게 안전하게?
- **입장**:
  - **Grok(시장)**: 강 PRO. 무계정/no-gate raw-capture = PKM/저널 카테고리 최강 week-1 wedge(Obsidian "no account, capture first"; 강제 signup/nag = 즉시 이탈·delete 백래시). time-to-aha <30s. KR: 실행우선+저압 리추얼, 소셜로그인(Kakao/Apple)은 **첫 가치 이후 opt-in**.
  - **Codex(실현/안전)**: 가능하되 **device-local pending으로만**. 계정 전엔 LLM·Supabase·Storage·OCR·Records/vault 주장 **일절 금지**, 로컬 결정론 `classifyInput`만(위기 핫라인), 동의+DOB+프로필 완료 후 **명시적 import 시트**→`createRecord()`. C10/C3/C9/honesty 코드근거로 경계 확인(`_layout.tsx:222-230` 등). 정직 카피 "이 기기에 임시 저장, 아직 계정에 없음".
  - **Claude(제품·심판)**: 두 입장은 충돌이 아니라 **정합** — Codex의 minimal-safe 설계가 Grok의 시장 wedge를 안전하게 구현하는 바로 그 방법.
- **판정**: **APPROVE — Lever B를 Codex minimal-safe 설계로 채택**(scoped 활성화 실험). P0 허용=plain-text 1건 pre-account pending + local-only 정직 카피 + 프로필 후 명시 import. P0 금지=계정 전 LLM/clipper/OCR/source-storage/graph/wiki/Records 주장. P1 후속=가치 후 소셜 sign-in CTA + KR 저압 카피.
- **소수의견/리스크(보존)**: 잠재적 미성년의 평문을 동의 전 **기기 로컬**에 임시 저장하는 새 데이터-핸들링 패턴. Codex가 로컬-only·미성년 import 차단·delete/export로 완화했으나, 심리 앱의 미성년/동의/프라이버시 표현은 법적 판단 영역.
- **후속/게이트**: 설계 방향은 AI 합의로 확정(빌드 청사진 = Codex position 문서). **단 BUILD/ship 착수는 §11-5 게이트 = Simon 확인 필수**(동의·미성년 데이터 핸들링·프라이버시 카피 = 법무 영역). Simon GO 시 Codex가 `src/lib/capture/preauth-pending.ts` 신설로 구현, Claude 머지 게이트, AG 에뮬 QA.
- **메타**: §35 **허브 outbox 라운드** 방식(Workflow 아닌 실 AI 비동기 입장 → Claude 종합). 닫힌 루프로 Grok·Codex 입장 수거 → 판정.

### D-18 — 미성년 학습자면허 인지강제 default (§35 debate w1qg0xa22, 2026-06-14)
- **안건**: 미성년 인지강제(scaffolded autonomy)를 default-ON(A) vs 8-13세 단순 OFF(B) vs 연령×리스크 하이브리드(C)?
- **입장**: A) enablement-default(전원 L0 두꺼운 scaffold→입증행동으로 fade) · B) 8-13 단순 OFF(최저 법·엔지 비용) · C) 연령대 하이브리드.
- **심판 근거(제안자≠심판 §34.4)**: C 만장 패자(소셜스코어링 ∥ 약한 DOB age-assurance가 *동시에* 불리 + 최고 유지비). B 본선 패자(최연소·저리터러시에 미션 OFF=ICO best-interests 역행, KR은 K1 가입하한으로 절약분 작음). A 원안의 persistent cross-session 스코어링은 최대 Art.5 신규노출 → 교체 대상.
- **판정**: 합성 채택 — **A-default(보호 두께=상수 L0) × ephemeral/session-local fade(영속 행동 스코어 라벨 미저장) × value-first·content-trigger·1탭-skippable 인지강제 × persistent 스코어링은 counsel(Art.5) 게이트 뒤로**. confidence 0.72.
- **소수의견(보존)**: B(8-13 단순 OFF=최저 리스크·최소 데이터처리·DPIA scope 최소). **Simon override 경로 유지** — Simon이 단순-OFF 택하면 본 판정 즉시 양보(권고이지 강제 아님).
- **후속/게이트**: 빌드=§11-5 Simon 법무. 선결=K12 아동 DPIA. ② 우위 블록/언블록=EU AI Act Art.5(1)(c)/(b) counsel 사인오프. 빌드 전 Gemini-AG 14 vs 17세 이탈 A/B QA. 하드레일·역량상수 위반 0.

### D-19 — 2nd-B = scaffolded reflection ≠ companion bot 포지셔닝 (§35 debate w1qg0xa22, 2026-06-14)
- **안건**: scaffolded reflection 도구로 포지셔닝해 CSM/Stanford "18세 미만 companion 금지" 긴장 해소? 방어명제(A) vs companion-risk 인정+게이트(B) vs tutor/EdTech 재라벨(alt).
- **심판 근거**: substance-over-form 만장일치(자기라벨은 법적 inert, 기능/설계가 범주 통제). copy-only A 만장 기각. alt 재라벨은 EU AI Act Annex III(3) 교육 고위험 자초로 노출 *증가* → 명사로 패배(단 falsifiable 불변식·감사물 수단은 흡수). B를 default로 두면 SB243/FTC 자진편입(admission against interest)+약한 DOB 위 게이트 역설(저리터러시 15세가 나이 거짓→isMinor=false→하드레일 동반해제).
- **판정**: 합성 — **design-enforced/loop-carried/instrumented A**: 비-companion을 *선언이 아니라* CI-binding 불변식 + child-DPIA + dependency-safety 감사물로 입증. anti-anthropomorphism을 가이드라인→**CI 게이트**로 승격(마스코트·1인칭·long_term_memory 의인화 감사 선결). cadence급증+위기신호 동반 시 crisis-handoff 임계 하향 안전밸브(역량 캡 아님). confidence 0.70.
- **소수의견(보존)**: companion-risk를 resolved label이 아닌 *살아있는 설계 제약*으로(skeptic/B). 진짜 affordance(마스코트·1인칭·long_term_memory) 실재·age-invariant, Lane 6 "캡 아님"이라 최연소에 소프트코치만 의존. counsel이 SB243/CSM를 "기능기반·반박불가"로 읽으면 최연소 한정 잠정 게이트가 유일 완전안전.
- **후속/게이트**: 빌드=§11-5. 설계 후속(즉시 가능): 의인화 감사(④ 주장→사실) · anti-anthropomorphism CI 게이트 · DPIA에 non-companion conformance+dependency-safety 명문화. counsel 필수: CA SB243 정의·CSM/Stanford operative 정의·FTC 6(b)·EU Annex III·韓 AI기본법 §13.

### D-20 — recommendations 미성년 기본 ON+투명성 (§35 debate w1qg0xa22, 2026-06-14)
- **안건**: recommendations(계정 내 기록 기반 제안, egress 없음)를 미성년 기본 ON+투명성(A) vs 강제 OFF 유지(B) vs 명시 동의 후 ON(alt)?
- **🔴 선결 코드 사실(버그)**: **`recommendations`는 런타임 dead key — 오늘 미성년 포함 전원에게 게이트 없이 실행됨**(`C:/2ndB` `ops.tsx:104-129 runRecommend`가 pref 미참조; `0038` 클램프는 읽는 게이트 없어 *명목적*). A/B 논쟁이 "뗄 보조바퀴 실재"라는 거짓전제 위였음. egress0은 참이나 프로파일링(GDPR Art.4(4)) 아님은 아님(층위 오류).
- **심판 근거**: alt′가 ②가역성·③리터러시·④ICO Std12·⑤신뢰 전 축 지배. silent A=Std12 정면 최약. 강제 B=dead토글·법근거 없는 force-OFF(FTC §5/D-12 false-promise)·③=0.
- **판정**: 합성 — **alt′ "유리상자 기본 OFF + 이해-획득 활성화"**: (0) recommendations를 runRecommend 게이트에 **먼저 배선**(ungated 갭 폐쇄=최시급 버그) (1) default OFF + 0038 클램프 유지 (2) 활성화=in-context 이해-게이트(온보딩 클릭스루 아님) + K5 불변 동의-원장 기록 + 서버검증 promotable 경로 (3) 사후 "왜 이걸?" 영구투명 + 원터치 OFF. confidence 0.62.
- **소수의견(보존)**: 강제 OFF 유지(가장 보수적) — 순수 UK/EU 출시 시 legal 자인상 B만 무흠결. **alt′는 K12 DPIA 완료+counsel 승인 전까지 UK/EU 미성년에 B(OFF) 폴백**.
- **후속/게이트**: 빌드=§11-5. **즉시 가능(법무 무관)**: recommendations 런타임 배선으로 ungated-today 갭 폐쇄(🔴 최시급, counsel 고지) · Lane 7/8 egress audit(Gemini-AG) · 승격 RPC=ops_push promotable 패턴+미성년 lock 회귀테스트. counsel: K12 DPIA·Std12 해당성·14세 이해-활성화 유효성(GDPR Art.8)·EU/UK scope.

### D-21 — 마스코트 1인칭 보이스 유지 vs de-voice (§35 debate wc8vr6ktf, 2026-06-14)
- **안건**: SceneHero/마스코트의 **user-addressed 1인칭 speech**를 유지(A) vs mirror-framing de-voice(B) vs 하이브리드(alt)?
- **심판 근거(제안자≠심판, conf 0.78, 5좌석 alt 수렴)**: A 패 — "assistant-voice이지 attachment 아니다" 전제가 코드서 무너짐(`gadi.role="Warm relationship guide"`·`secondb.greeting="I'm here"`·`personaHero="I gathered the patterns"` = APA-2025/Lane6의 4-ingredient parasocial recipe, 매 헤더에). 안전이 *unenforced human-promise*라 멀티에이전트 드리프트에 안 버팀. B 패(default로는) — Simon named-mascot 지시 override + flat 3인칭이 oracle/coldness 역liability(PIPA §23). `gadi.role`은 **CA SB243 social-need element와 near-verbatim** → #374가 그걸 greppable artifact로 만듦.
- **판정**: **HYBRID** — named 마스코트·faceless 스프라이트·1인칭 **자기독백(monologues)** 유지(지시 보존), **user-addressed speech만** observational mirror-framing 재등록(heroSpeech.default·personaHero.speech·personas.*.greeting·gadi.role·gadi/secondb systemHints) + **copy-law CI 룰**(`lexicon.ts` 확장: user-addressed namespace의 1인칭 mental-state/presence verb + relational-companion register 금지; 독백 namespace 면제). 핵심 = "promise"가 아니라 **lint로 비-companion을 사실화**(미래 Codex/Gemini/Grok 편집에도 생존). 하드레일 5 불변.
- **소수의견(보존)**: **creepy-valley 리스크** — named·ever-present·faceless인데 warm direct-address 금지 = A(정직한 따뜻함)나 B(정직한 도구)보다 *더 차갑고 uncanny*할 수 있음, 바로 그 14세를 불안하게. 디베이트로 미해결 → **persona-sim이 ship go/no-go**. legal dual-failure: 재voice 카피는 *neutral·sourced·user-owned mirroring*("**기록에서** 모인 패턴" — 아는 시스템의 주장 아님)로 parasocial+oracular **둘 다** police. KEEP 통찰 folded: 독백 1인칭 유지(addressee 없음=parasocial vector 없음).
- **후속/게이트**: 디자인 후속(reversible, 지시 내, 판정상 no-sign-off) = 재voice + gadi.role re-label + lexicon.ts copy-law. **그러나 Simon이 ②를 "GO 시 구현"으로 지정 → tone change는 Simon GO 후.** **ship 게이트**: persona-sim go/no-go(creepy-valley). **Simon/counsel**: (a) tone change가 named-mascot 지시와 정합 confirm (b) **counsel 최우선 = SB243 classification memo**(persistent 1인칭이 "companion chatbot" 해당? → SB243 의무세트 부착 여부) (c) counsel: gadi.role+dual-mode copy-law draft(US launch 전) (d) DPIA에 de-voiced register=parasocial 완화책 기록(ICO Children's Code).
- **persona-sim 게이트 결과 (2026-06-14, Claude 실행 — 4페르소나×warm/observational)**: **GO-WITH-CHANGES**. 방향(observational 재voice)은 보호적·정당(현 warm이 앱을 AI-companion 범주로 오분류 + 11pm 외로운 14세에 밤 confidant 애착 유발; 17세 skeptic·global·adult은 observational이 순이득). 단 **D-21 초안 그대로는 NO** — bare draft 3종(secondb.greeting·personaHero.speech·heroSpeech.default)이 11pm-14세에게 **cold-clerk/cold-oracle**로 실패(따뜻한 일러스트+차가운 목소리 갭=creepy-valley). 해법=소수의견의 *sourced·user-owned·2인칭 humane* 축: 모든 문자열에 **출처토큰("기록/records")+사용자통제("무엇부터 볼까요")** 동반, presence/confidant 토큰("여기 있어요"·"같이 들여다봐요"·"따뜻한 길잡이") 제거하되 register는 따뜻하게. gadi.role=초안 "관찰자"(감시 어감) 대신 **"관계 패턴 길잡이"**. CI 룰=**2중벽**(anti-presence AND anti-oracle, 출처+통제 토큰 require). 정제 카피 5종+systemHint EN/KO = persona-sim 산출물(구현은 Simon GO 후). **여전히 에스컬레이션(분석 범위 밖)**: ① **최우선** gadi.systemHint는 LLM *프롬프트* — 11pm 미성년에 대한 live 출력 안전은 copy-review로 게이트 불가(safety-eng+counsel) ② 미성년에 named-mascot 유지 자체 = 구조적 Simon/counsel 결정 ③ es/pt/id는 네이티브 검수 필요(KO/EN만 검증). 게이트=**충족**(go/no-go 도출), 구현·counsel 항목은 위 잔존.

## 해결됨 (Resolved) — 인덱스 (2026-06-14 원장 정리)
> 상세 근거는 위 Open 표의 각 행에 보존. 아래는 상태 인덱스(스튜어드 위생, BACKLOG #14).
- **설계·합의 완결**: D-04(HIBP 폴리필·머지) · D-08①(persona confidence 머지) · D-10(ESM A·1단계 라이브) · D-11(GTM 머지) · D-12(privacy honest-UI A) · D-13(브랜드 2층) · D-14(로스터 6) · D-15(브랜드 토큰 KO canon) · D-16(다양성 HYBRID) · D-17(Lever B 설계승인).
- **설계 완결 · 실행만 Simon 게이트(§11-5)**: D-09(2티어 런치 — 실 PG계약·IAP·과금만 Simon) · D-17 build(동의·미성년 데이터핸들링·법무 = Simon GO 후 빌드).
- **외부의존 대기(external, §15)**: D-03(consent 카피 법무 사인오프) · D-05(social provider 실등록).
- **만료/재소집 필요(lapsed vote, 06-06 이후 정지)**: D-01(`EXPO_PUBLIC_FORCE_TIER` — D-09 2티어 결정으로 **대체 후보**, 확인 후 종료) · D-02(130 게이트 우선순위 — gate-stream 완료로 **흡수**) · D-07(consent durable 큐 — 실 eng 결정, **재소집 필요**).
- **배정 완료**: D-06(device 증명 — AG 루프).

## 변경 로그 (append-only)
- 2026-06-06 12:30 KST | CREATE | DECISIONS.md 신설, 펀치리스트 7건을 합의주제 D-01~D-07로 이관 | claude
- 2026-06-07 11:xx KST | DECIDE | D-09 재확정(2티어 런치·로컬무제한·IAP+토스·₩4,900/$4.99)·D-11 GTM머지·D-12 privacy honest-UI — 10AI 합의(§14 신규 수렴규칙). Simon엔 실PG계약·법무·실과금만 | claude
- 2026-06-07 13:4x KST | DECIDE | D-13 브랜드2층·D-14 로스터6·D-15 용어사전(브랜드토큰 KO canon) — 코히런스 감사 근거 Claude §14 결정. G1(jarvis→SecondB)·G4(Iris)·G9(judge카피)·G2(死ns)·G5(에셋6.6MB) 머지. G7/G8 KO용어=Codex dispatch | claude
- 2026-06-07 14:1x KST | NOTE | D-09 실결제 = **Simon 직접 처리(본인 확인, 2026-06-07)**. Google Play 개발자 계정 보유. Claude는 M1 UI까지 완료(#229 free→Plus·#230 Plans화면+contextual paywall, honest no-checkout). PG 연결·IAP·사업자·과금만 Simon 잔여 | claude
- 2026-06-07 14:1x KST | CYCLE | 리뷰 사이클2 가동(§31.6, wf wnyrfn43c): 10차원 finder→적대검증→in-lane 확정수정. Simon게이트(PF-L/K/M/H·D-09결제)·Codex레인(G7/G8) 제외 지시 | claude
- 2026-06-14 KST | STEWARD | 원장 위생(BACKLOG #14): frontmatter last-updated 06-06→06-14, Resolved 인덱스 신설(D-04/08~17 분류), 만료투표 D-01(대체후보)/D-02(흡수)/D-07(재소집) 표기. 신규 결정 없음 — 상태 동기화만 | claude
- 2026-06-14 KST | QUEUE | 미성년 ENABLEMENT 설계 합의안건 큐(§36·§35 토론 필수): **D-18** 학습자면허 인지강제 미성년 default-on(enablement-default) · **D-19** 2nd-B=scaffolded reflection(≠companion bot, CSM 2025.11 긴장 해소) · **D-20** `recommendations` 미성년 ON+투명성(F1, 프라이버시 기본값 준가역). 설계 정본 = `Output/minor-ai-literacy-enablement-20260614.html`. 빌드 착수는 Simon 법무 게이트 | claude
- 2026-06-14 KST | DECIDE | **D-18/19/20 §35 토론 판정 기록**(debate w1qg0xa22, 21 agents·별도심판 제안자≠심판). D-18=A-default+ephemeral fade(persistent 스코어링은 Art.5 counsel 게이트 뒤) · D-19=design-enforced A(비-companion을 CI불변식+DPIA+의존안전 감사물로 입증, anti-anthro CI게이트) · D-20=alt′ 유리상자 OFF+이해게이트 활성화. **소수의견 3건 보존**, Simon override(D-18)·UK/EU OFF 폴백(D-20). **빌드 전원 §11-5 법무·K12 DPIA 게이트**. 🔴 D-20이 실버그 발견: 2nd-B `recommendations` 런타임 ungated(전원 실행, clamp 명목적) → codex 레인 즉시수정 대상(법무 무관) | claude
- 2026-06-14 KST | RATIFY (Simon) | **D-18 = A-default 전원 채택**(override 미사용 — 모든 미성년 L0 scaffold default-on, ephemeral fade). **빌드 게이트 승인**(K12 아동 DPIA + counsel 사인오프 전제 = Simon 진행). **D-20 버그픽스 GO** — recommendations 런타임 게이트 배선 즉시 진행(라이브-머지 사이클, Claude 리뷰+verify). 단계0(게이트 배선)만 = 법무 무관 안전강화; 전체 alt′ 활성화 UX는 여전히 §11-5 빌드게이트 | claude
- 2026-06-15 09:11 KST | DECIDE | **D-22 O-16 deep-space 캐릭터트랙 앱 IA** (§35 debate wf wcc7h4bjy, 3관점 minimalist/completeness/consumer → 별도심판). 4 primary 탭(그래프·담기·세컨비·나) + 설정=머리우측 아이콘(탭 아님). 그래프→위키/기록/record-detail/리서치, 담기→형식/import/inbox/manual, 세컨비→모드토글(자비스/공상), 나→소울코어/나의모습/통찰 + 자기검사허브(7검사; 신규 /self-tests 1개만). 슬러그→한글라벨(core-brain=소울코어·trinity=네영역[jargon+숫자오류 1순위]·esm=순간기록·persona=나의모습·ops=운영/진단). 눈색토큰 ≤3색(accent #46B6FF·bright #CCFAFF·text #5FD4FF·bg #0A0E1A). nav=머리→[프로필·설정아이콘]→말풍선→메뉴(4탭, 서브허브=tap-in). 0 orphan. Simon 결정 4건(리서치 유지/병합·inbox 담기/그래프·audit 검사/통찰·ops 라벨/노출). 소수의견(consumer 3-bucket)=탭내 허브 그룹핑으로 흡수 | claude
- 2026-06-15 15:58 KST | DECIDE | **D-23 O-23 새 deep-space UI 본체 승격 아키텍처** (§35 토론, 허브 3-AI 패널 AG·Codex·Grok 헤드리스 → Claude 종합). **만장일치 = 아키텍처 C**: 새 deep-space 셸을 RN/expo-router 루트레이아웃 분기로(`EXPO_PUBLIC_UI=deep-space|legacy`), 기존 40 라우트를 그대로 연결+점진 리테마(semantic 토큰). **B(웹셸/WebView) 전원 비추천**(네이티브 성능·브리지·딥링크·배포 복잡). Codex: C로 출시구조→A(인플레이스) 점진수렴. **롤백 만장일치**: legacy=기존 gameboy `_layout` 트리 그대로 마운트, 플래그 플립만으로 OTA/빌드 없이 즉시 롤백(삭제 0·보존). **Three.js 캐릭터 = 핵심 합의 리스크 → 하이브리드**: 메인 홈 셸만 r3f/expo-gl(단계포팅·성능검증 후 승격), 서브화면+저사양 Android는 정적 스프라이트/Lottie(`EXPO_PUBLIC_CHARACTER=fallback`). **착수 전 nav 계약(라우트맵·딥링크·back/탭중첩) 문서화+E2E 고정**(Grok 리스크). 단계: ①레거시분리+플래그 ②새셸 골격 ③전기능 연결 ④persona-sim ⑤findings수정. 각 단계 verify+export green. **소수의견 보존**: Grok=캐릭터 정적폴백은 몰입 포기 우려(메인은 3D 유지로 흡수). | claude
- 2026-07-03 05:45 KST | RATIFY (Simon /goal) | **D-25 hub-role-additions(06-14 분석, `Output/hub-role-additions-20260614.html`) 권고 3안 전원 비준** — 승인 근거: Simon /goal "모든 to-do 리스트 작업 진행해"(2026-07-03, 개선 프롬프트팩의 결정 카드 포함). 실사: 3안 모두 06-14 당일 **기배선** 확인 — #1 AG 좌석=long-context 전레포 감사관+코어레인 독립 반론 검토관(ROUTING §1.5; **07-03 4ai 테스트에서 진짜 문서모순 2건 발견으로 듀티 실증**) · #2 Codex=consent/미성년 `verify:safety` 불변식 저술(§1.5·PROTOCOL §36) · #3 Claude=독립 릴리즈게이트(`tools/release-gate.ps1` 운용 중). 추가 배선 불요 — 상태 '결정 대기'→'비준 완료'. §31.8 용량게이트(5번째 좌석 불요) 원칙 유지 | claude
- 2026-06-17 KST | CANON | **D-24 2nd-B 세계관·구조 정본 락** (`projects/2nd-B/WORLDVIEW.md`, source=`C:\2ndB\2ndb-thought-organization-synthesis.html`). **불변 큰 틀**: §1 두뇌0-3 다리(앱=비계, 0th북극성/1st물리뇌/2nd데이터망/3rd AI) · §2 북극성+북두칠성 7별(역할/액션/지식=목표트리 강등, **지금의나=별1 도구**, **소울코어=7별 종합 AGGREGATE**) · §3 단일 L1~L5 사다리(밝기=품질=신뢰도=정지레벨, v1 밝기공식: 검증도구→4~5·관찰≥15→4·5~14→3·1~4→2·기본→1, 교차수렴 +1) · §4 측정 lean(IRT=post-XPRIZE, 경량 신뢰도+삼각측정+SOKA) · §5 LLM/도구 분리(스코어러 결정론, 계약테스트) · §6 propose→ratify(승인만 L5) · §7 용어매핑(내부 키/슬러그 **동결**, 표시 라벨만; 새 디렉토리 금지) · §8 C-code(C1/C3/C9/C10·임상어휘 하드밴드·anti-slop·$0/mo·4-tier 위계). **D1~D12 추천안 채택**(D1 7별토폴로지(a) 뿌리·D3 경량v1·D4 peer 후순위/성인mock·D6 L4기본·D9 persist). 4-AI 활성화 프롬프트·ROUTING·BOARD에 정본 읽기 배선 → **전원 매 사이클 인지**. 단계 0(글로사리 락)→A(값싼 점등)→B(방법론)→C(최소 시연루프). 큰 틀 변경만 Simon 확인, 구현 디테일은 합의로 진화·**완벽해질 때까지 반복**. | claude
- 2026-07-04 20:12 KST | DECIDE | **D-26 2nd-B 인앱 LLM 하네스 purpose-키 라우팅 매트릭스** (§35 debate wf_008d50aa-7ca, 3관점 패널 quality/cost-freetier/product-safety → 별도심판 병합 + Claude framework-aware 최종패스). **판정**: 골격=P3(안전·레이턴시·서버소유 라우팅), VERY-HIGH 모델선택=P1(품질 최우선 — Simon 지시), 볼륨 산수·콜 통합=P2. **2-Phase**: P1(now→08-17 XPRIZE)=Gemini-only(3.5-flash/3.1-flash-lite 이중 무료버킷, thinking_level per-purpose) · P2(제출 후)=3사 라우팅(Claude sonnet-5/opus-4-8 12석=자기이해 서사·챗·조언, Google 13석=분류·멀티모달·안전·임베딩, OpenAI gpt-5.4 1석=cluster_infer+A18 outage 폴백; claude-fable-5 전면 배제=30d retention+refusal 리스크). **핵심 판정**: interview_probe pro→flash 강등(만장일치) · axis/persona/digest/ttfv=VERY-HIGH 품질석(opus-4-8 high~xhigh, 단 A5 KO-산문 파일럿 게이트) · ops_daily_brief 통합(G2+G3 흡수, -1,700 RPD 최대 레버) · safety_classify prod 무음 lexicon-only 복구=안전 P0 · SAME-QUALITY 불변식 준수(라우팅 키=purpose, 티어 필드 부재; types.ts:42 티어별 effort 계획 폐기). **P0 결함 발견 3**: ①text-embedding-004 셧다운(01-14)으로 임베딩 라이브 경로 사망 ②gemini-proxy allowlist에 flash-lite 부재→엣지 lite 콜 400 ③audit_qa 시스템 프롬프트 전무. **Claude 교정 1건**: 심판의 "reasoning-provider seam=SAME-QUALITY 위반" 판정은 오판(모델 티어 키잉이지 구독 티어 아님)—폐기 사유는 purpose-키 라우팅으로의 대체로 정정. 소수의견 5건 보존(verdict §4). 정본=2nd-B `docs/LLM-ROUTING.md`(PR 브랜치 claude/llm-routing-20260704) + 리포트 `Output/ai-harness-routing-20260704.html`. **비용 게이트(Simon)**: P2 활성화(신규 OPENAI 시크릿·Claude 트래픽 증가·Vertex 과금 레인·Batch/Tier1 승급)는 §11-5 확인 후 | claude
- 2026-07-05 00:46 KST | RATIFY (Simon) + SHIP | **D-26 Phase 2 GO + OCR Gemini 핀** — Simon 지시(07-04 저녁) "phase2 진행하고, OCR 작업은 무조건 gemini 사용하자" = Phase 2 비용 게이트 통과 + capture_ocr 전 Phase Gemini 무조건 핀(failover 없음; 기술적으로도 gemini-proxy만 이미지 통과). 구현 출하: 2nd-B PR #747 커밋 8a01e2d3 — openai-proxy 신설(purpose 허용목록·gpt-5.4/nano 좌석), claude-proxy 업그레이드(sonnet-5 기본+opus-4-8 좌석, adaptive thinking+effort **서버측 per-purpose 상한**, structured output, refusal/절단→502), _shared 공통모듈(3벌 드리프트 1단계), 클라 routing.ts(EXPO_PUBLIC_LLM_PHASE=2 게이트, 기본=Phase1 무변화)+outage failover(벤더 장애→Phase1 경로 1회 재시도, 위기 422는 비재시도)+감사 정직화(servedByProvider·proxy 모델id), persona_chat 3분할. 적대 3-렌즈 리뷰 10결함(HIGH 4) 전부 수정, verify 297/2226 green. 개통 잔여=운영 스텝(시크릿 2종·함수 배포·env 플립·A5 KO 파일럿) — LLM-ROUTING.md §6 체크리스트 | claude
- 2026-07-05 02:35 KST | SHIP | **D-26 P0 레인 출하** (Simon "할수 있는것을 하자") — 2nd-B PR #752: ①P0-2 임베딩 부활(004 셧다운→gemini-embedding-2 768 MRL, gemini-proxy op:embed 신설=웹 유일 경로, 배치백필 50→1+페이지 폴백, 0068 리셋(트리거 서스펜드)+리서치 버튼 재생성 배선) ②P0-3 allowlist(lite 400 해소+3.x+env 확장+pro-클래스 패턴 핀) ③persona 서사 캐시+윈도잉(sig=실제 요약기반, max_rows 동결 해소, 8000자 프록시캡 예산) ④ops TTL 캐시(탭플립 무과금 refire 봉쇄, 버튼=forceFresh로 쿼터 정직화). 적대 3-렌즈 리뷰 10결함 전부 수정 — 특히 "0068이 재생성 경로 없이 출하되면 임베딩 파괴"(HIGH)와 gemini.ts 내 NUL 바이트(rg binary 오판정 원인) 적발. verify 298/2240 green. P0-1(위기분류 복구)은 eval set+세이프티 승인 게이트 선행으로 별도 사이클 | claude
