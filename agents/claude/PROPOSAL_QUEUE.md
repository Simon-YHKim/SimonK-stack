# PROPOSAL_QUEUE.md — 실행가능 큐 (PROTOCOL §25)

> Claude 단독 관리. AI 제안 백로그(132 gate + AG 33 + Grok 24 + proposal 7)를 병렬 트리아지(wf wdze15wze, 152분류)해 테마로 dedup한 큐.
> 버킷: **A.Claude즉시 / B.Codex디스패치 / C.AG디스패치 / D.Simon·external**. 매 사이클 상위 doable 소진 → verify(gated) → push → 완료체크.
> generated: 2026-06-06 21:50 KST · 소스 SHA-regate들은 같은 블로커를 반복 → 테마로 통합.

## 제외 (이미 머지됨 — git log 교차대조)
- data-truth false-empty 3종: `/insights`·`/core-brain`·`/trinity` sources 집계 → **머지 완료** (gate 093848·100749·114119은 stale).
- segmented/PremiumButton `accessibilityState` 병합, assessment Likert 시맨틱 → 머지됨.
- expo-crypto HIBP(D-04), AppState 토큰 refresh perf → 머지됨.
- a11y 라벨 대량(전 화면), preauth/permissions/formats jargon 일부, retired-route(#214 부분), privacy monotonic 코어(#215) → 머지됨.

---

## A. Claude-doable-now (검증가능·device무관·내 lane)
| # | 테마 | 파일 | value | status |
|---|---|---|---|---|
| A1 | **Raw error → product-tone copy + recovery** (실패경로 11화면) | account·capture·wiki·inbox·interview·settings·records 실패 핸들러 | high | ✅ **검증완료**(2026-06-07) — raw error 노출 0(console.warn만)·Alert.alert 0(Codex alert-contract 소진)·실패 핸들러가 product-tone i18n + retry 복구 콜백(`showFeedback(title,msg,()=>retry)`). 코드변경 불필요 |
| A2 | **Privacy 토글 진실** — 8스위치 중 external_analytics만 enforce, 7개 phantom | `src/app/privacy.tsx` (+enforcement 코드) | high | 🔬 **조사완료(2026-06-07)→D로 이관**. 전수 grep 확인: enforce=`external_analytics`만(_layout/analytics/consent-queue). **phantom 7=ads·sharing·recommendations·llm_training·persona_export·persona_share·long_term_memory**(저장만, 동작 게이트 0). 전부 OFF 기본이라 데이터 유출은 아니나 **작동하는 척 = 거짓 약속**. 특히 **llm_training·sharing은 법적 무게** → 무단 프로덕션 변경 금지, **Simon/§15 정책 결정(D-12)** 필요 |
| A3 | **Privacy failed-opt-out fail-closed** — #215가 실패세이브 revert 커버하는지 검증, 미흡 시 guard+test | `src/lib/privacy/analytics-consent-queue.ts` | high | ✅ **검증완료**(2026-06-07) — 코드 fail-closed(optOut 즉시 gate OFF, 실패 시 onError가 UI pref만 revert·gate 유지) + 테스트 커버("a failed opt-in never enables analytics", 모노토닉 opt-out). 커밋 `12bc27d`+`911c979`. 코드변경 불필요 |
| A4 | **Auth loading-aware guards** — signin/signup guest guard + complete-profile redirect가 loading 무시 → 잘못된 화면 flash | `src/app/(auth)/sign-in,sign-up,complete-profile.tsx` | high | ✅ **머지 `3ee8885`** (InlineLoader guard, sign-up guest guard 신설) |
| A5 | **Data export scope 진실** — export 약속(파일) vs 실제(clipboard) 불일치 통일 | support·data·settings·wiki | high | ✅ 점검완료 — data.tsx 이미 정직("텍스트로 모아 복사", 파일 거짓약속 없음) + wiki export 승격 `f710b50`(Codex). churn 회피 |
| A6 | **Theme native 영속** — native에서 localStorage만 써 영속 안 됨 → AsyncStorage 또는 컨트롤 숨김 | `src/lib/theme/ThemeContext.tsx` | high | ✅ **머지 `1a688c6`** (web 동기경로 유지 + native AsyncStorage 하이드레이트/쓰기) |
| A7 | **Persona assessment-only summary** — audit 없을 때 LLM summary 생성(날조) 차단 | `src/lib/persona/build.ts` | high | ✅ **머지 `1335fc4`** (rows>0 게이트 + 정직한 빈메시지 + 테스트, paid call도 절약) |
| A8 | **Crisis badge 가독성** — hotline badge 10→12px (안전표면) | `src/components/safety/CrisisRouter.tsx` | high | ✅ 이미 `fontSize:12` 적용됨 (stale gate) |
| A9 | **Account DOB auth refresh** — DOB 저장 후 minor state 미갱신 | `src/app/account.tsx` | high | ✅ **머지 `55b6a8e`** (AuthContext additive refresh() + DOB저장 후 호출, safety-routing 정합) |
| A10 | **내부용어→사용자언어** — RLS/RAG/LLM/[[slug]]/frontmatter/storage 라벨 | permissions·inbox·wiki·settings·insights | high | 🟢 **머지 `1ee4e0c`**(Codex: storage 라벨 숨김·wikilink·wiki 참조), 잔여 진행 |
| A11 | Spinner-only → PremiumLoadingState | audit·profile·record/[id] | med | ✅ **머지 `0dfa75a`** (라우트 로딩 3화면, profile 인라인 spinner는 적정 유지) |
| (alert-load) | alert-only load error → 지속 에러상태(false-empty 방지) | research·insights | high | ✅ **Codex 머지 `f74efc1`** (research·insights). trinity 남음 |
| A12 | Destructive busy-escape — busy 중 sign-out/nav 비활성화 | `src/app/settings.tsx` | med | ✅ **머지 `db31d6f`** (Sign out busy 가드 + 지속 배너 screen-reader 알림) |
| A13 | Inbox 'View in wiki' → 정확한 slug 페이지 | `src/app/inbox.tsx`·`wiki.tsx` | med | ✅ **머지 `72922ea`**(Codex: inbox→wiki 특정 페이지 focus) |
| A14 | Records source row → 특정 source detail 라우트 | `src/app/records.tsx` | med | ✅ **머지 `e53e49d`** (origin 파라미터 통합 상세 + record/[id] sources 폴백) |
| A15 | Wiki delete → stale promoted source 리셋 | `src/lib/wiki/queries.ts` | med | ✅ **머지 `d9e73db`** (markSourceNotIngested + deleteWikiPage source 리셋 + 테스트2) |
| A16 | Quant-intro storage flicker → tri-state | `src/components/quant/QuantIntroModal.tsx` | med | ✅ **머지 `72922ea`**(Codex: storage hydrate 후 표시) |
| A17 | Dynamic-type clipping — numberOfLines 반응형 | 전역(22×1줄·10×2줄) | med | ✅ **머지 `50dce1e`**(Codex: 공유 헤더 large-text wrap) |
| A18 | Web zoom/focus — user-scalable=no 제거 + focus-visible | viewport·Pressable | med | ✅ **머지 `50dce1e`**(Codex: web zoom 허용 + focus outline) |
| A19 | Import analysis fallback 공개 | `src/app/import.tsx` | med | ✅ **머지 `fd7384f`** (degraded 플래그 + 결과뷰 공개 notice, raw 에러 비노출) |
| A20 | Record detail assessment raw JSON → friendly | `src/app/record/[id].tsx`·`persona/evidence.ts` | med | ✅ **머지 `31887a1`** (summarizeAssessmentBody 헬퍼 MBTI/BFI/ECR + 테스트6, 저널텍스트 무영향) |
| A21 | Retired-route helpers 잔여(/journal·/imagine·/mbti emit) | `src/lib/village-ui.ts`·`persona/evidence,self-portrait.ts` | med | ✅ 해결 확인 — 활성 emit 없음(village-ui CTA 통합·evidence 실목적지). 잔여는 주석/import뿐 |
| E9 | 자산 일관성 — tier 아이콘 매핑·계약 | codex | med | ✅ **머지 `ae974b9`**(Codex TierIcon contract + 테스트). 잔여 자산 정규화 진행 |
| A22 | **GTM/마케팅 docs** (Grok X신호) — docs/GTM.md + i18n trust signals + core 명칭 직관화 | docs·locales·DESIGN.md | high(마케팅) | open |
| A23 | LOW: capture stale journal lock 제거, source emdash, post97 microtype | capture·ConsentNotice·NavGraph | low | open |

## B. dispatch-Codex (UI/UX·i18n·anti-slop·이미지)
- **i18n 번들 이관** (915 inline locale 분기 → 번들) ← 이미 redirect(20260606-212300). 신뢰·법무 카피 우선.
- 카피 jargon: ✅ **capture-input `707387e`** + ✅ **jarvis-citation + manual-onboarding `20794de`**(Codex). 남은: theme-contract(Light 실제구현)·pixel-font→readable.
- 공유 컴포넌트: ✅ **PreferenceToggle 머지 `d741f5a`**(privacy·formats 토글 통합). 남은: LikertScaleQuestion·ExternalLinkButton/CopyAction·ActionChip primitives.
- **feedback-alert-contract** (61 Alert.alert → PremiumToast/Modal) — 🟢 대거 소진: assessment·import/esm·wiki export/delete·sign-in/up·profile·account·interview·trinity·capture·settings(`20794de`~`59db3c5`). 잔여 화면만 마무리 단계.
- 공유 컴포넌트: ✅ PreferenceToggle `d741f5a` + ✅ consent checkbox `9055cae`(Codex). 남은: LikertScaleQuestion·ExternalLinkButton/CopyAction.
- formats dead CTA(mock)·settings crew-density phantom·route-ia-numbering·design-token drift(74 hex/rgba).
- reduced-motion·contrast-ledger(Light palette).
- a11y P3 long-tail: image·modal-overlay·form-input·onboarding-dots·pressable-interaction.
- expo-image resizeMode→contentFit(6파일)·temp script 정리.
- §19 그래프빌리지 비주얼 패스(AG perf 교차검증 대기).

## C. dispatch-AG (Android/네이티브/perf/멀티모달 perf-side) — **동결해제, 생산 중**
- ✅ **머지 `707387e`**: KeyboardAvoidingView(account·audit·data·settings·support)·CAMERA권한+LivingAsset AppState guard·phantom notification 행 제거.
- 남은(device 증명 필요): Android 키보드 **에뮬 증명**(7화면)·FlatList 런타임 증명·NavGraph resume/drift 증명·OCR 권한/프리뷰 증명·D-10 알림 하드닝(POST_NOTIFICATIONS·Doze)·§19 그래프빌리지 perf-side(프레임/OOM).
- ⚠️ **AG는 copy/i18n 중복생산 금지**(capture jargon은 Codex가 커버) — 네이티브 lane 고수.

## D. Simon / external (§15 안전레일 — 합의 우회 불가)
- **consent legal readiness** — placeholder 법무카피→확정본+versioning (D-03).
- **deployment env 진실** — FORCE_TIER/ENABLE_*/LLM_MODE 기본값 확정 (D-01).
- **social provider 실설정** (D-05).
- ~~permissions phantom notification~~ — ✅ **AG가 행 제거 머지 `707387e`**(expo-notifications 미구현이므로 phantom 행 삭제가 정답). 해소됨.
- ~~**D-12 privacy 토글 진실**~~ — ✅ **합의(D-12=A)+구현 머지 #224**: phantom 7토글 UI 제거(VISIBLE_PRIVACY_KEYS=external_analytics만 노출, prefs 키 보존), 정직 카피(localFirstStatement)+trustBody 정직화. 실 enforce는 유출기능 출시 시 JIT 동의(미래). 법무 사인오프만 Simon(미래).
- go-live freeze 상태 명확화.

---

## E. UX 자연스러움·직관·정보위계·자산일관성 (페르소나 시뮬 §26)
> 페르소나-UX 워크플로(wv5i3ngxx, 연령10밴드×직업+자산+모션) **264 발견**. 전체: `agents/claude/persona-ux-findings-20260607.json`.
> 유형: non-intuitive 87·a11y 47·hidden 42·overload 42·stiffness 31·asset 15. 담당: codex 190·claude 33·ag 34·simon 7.
> ⚠️ **소득구간·문화/국가 축은 확장 시뮬에서 추가**(아래 진행).

| # | 테마 | 담당 | sev | status |
|---|---|---|---|---|
| E1 | **capture 정보과잉** — 5모드+트랙+해시태그 동시노출. 최다 공통지적 → 기본 1모드 + 고급 '더보기' 점진공개 | codex | high | ✅ **머지 `019671c`**(Codex progressive disclosure) |
| E2 | **비직관 라벨/카피** — "영차영차 던지기" 등 → 직관 동사 + 아이콘 텍스트 라벨 | codex | high | 🟢 capture mode 명확화 `a3768b2`(Codex), 잔여 진행 |
| E3 | **a11y 라벨 누락** — 아트·NavGraph 노드 accessibilityLabel/role | codex | high | 🟢 auth-hero a11y `a3768b2`(Codex), 잔여 진행 |
| E4 | **네이티브 접근성·터치** — 터치타깃 ≥44/48px·hitSlop·텍스트 16px·NavGraph 제스처→버튼 | ag | high | 🟢 NavGraph 접근성 내비 `a3768b2`(AG), 잔여 진행 |
| E5 | **hidden 발견성** — settings 진입점→NavGraph floating settings, wiki export 승격 | ag+codex | high | ✅ NavGraph settings `a3768b2`(AG) + wiki export 승격 `f710b50`(Codex) |
| E6 | **NavGraph 초보자 모드** — tier1-2 우선+가이드+노드 설명 | claude→ag | high | 🟢 AG가 접근성 내비로 일부 `a3768b2`. 초보자 단계공개 잔여 |
| E7 | 평가도구 Likert 고령 접근성 — 세로배열·큰버튼·16px·끝점 라벨 | codex | med | ✅ **머지 `f710b50`**(Codex Likert 타깃 개선) |
| E8 | **stiffness 31건** — 전환·press 피드백·로딩 등장 부드럽게(즉각 cut 제거), 부드러운 ease | ag(perf)+codex(스타일) | med | 🟢 withSpring→withTiming(bounce 제거) `a3768b2`(AG), 잔여 진행 |
| E9 | **자산 일관성 15건** — 네이밍 혼재·버전접미사(v1/v3/final/candidate)·스타일 혼합·미사용 정규화 | codex+claude | med | open |
| E10 | settings 전체삭제 확인 — typed 'DELETE'는 의도된 안전마찰 → 제거 대신 카피 명확화만(전체wipe는 typed 유지) | claude review | low | ✅ **머지 `958445e`** (비가역 경고 + Input a11y, typed-DELETE 유지) |
| E11 | 미래기능 비전 7건 — 협업/공유·이미지 스튜디오 등 → '곧 옴'/숨김 | simon | — | open |

### E (확장) — 소득구간 × 문화/국가 (페르소나 시뮬 w7nuzgtiy, 190발견)
> 전체: `agents/claude/persona-ux-findings-expand-20260607.json`. 차원: income 98·culture 92. 유형: non-intuitive 54·trust-privacy 39·pricing-payment 32·cultural-fit 24·locale-i18n 18·overload 13. 담당: codex 94·**simon 65**·claude 16·ag 15.

| # | 테마 | 담당 | sev | status |
|---|---|---|---|---|
| E16 | **데이터 사용량 힌트** — OCR/File 데이터 비용·Wi-Fi 권장(저사양·선불폰·데이터민감) | ag | high | open |
| E17 | **온보딩 메타포 추상성** → 구체 시나리오 카피·축약 | codex | high | ✅ **머지 `6036353`**(Codex 온보딩 간소화) |
| E18 | **신뢰/프라이버시 카피** — consent 국외전송 불신 → 안심 카피 | codex | high | ✅ **머지 `6036353`**(Codex consent 신뢰카피 강화) |
| E19 | **locale-i18n(18)** — 인라인 locale 분기→번들·영어 혼용 레이블·폴백 | codex | med | 🟢 **착수 `68277b9`**(Codex: data·support 카피 번들 이관, alert-contract→i18n 전환), 진행 |
| E20 | **RTL·중동** — 아랍어 RTL 레이아웃·이슬람 가치·gender·종교 달력 | codex(레이아웃)+ag(네이티브 RTL) | med | open |
| E21 | **OAuth provider 시장별** — KR=Kakao/Naver·JP=LINE·글로벌=Google/Apple 가용 gating(D-05 연계) | simon+ag | med | open |
| E22 | **cultural-fit(24)** — 자기성찰/저널링 수용성·톤(존댓말/겸손/관계중심)·종교/가족/집단주의 카피 적응 | codex | med | open |

### 🔴 Simon 수익화 결정 필요 (65 simon 항목 통합 — §15 external·business)
> 시뮬이 드러낸 **수익화 시스템의 구체 갭**(Simon 수익화 고도화 목표 직결). 가격·결제는 비즈니스+실비용이라 **Claude 단독 결정 불가 → Simon 승인 후 구현**.
- **M1 가격 투명성**: soma/cortex/brain 가격·요금제 화면이 어디에도 없음 → `account.tsx`에 PricingCard/요금제 섹션. **가격(KRW/USD) 확정 필요**.
- **M2 무료티어 관대함**: journal 2개 제한이 핵심가치(패턴/AI) 경험 전 차단 → empty state만 봄. 무료 1회 AI 맛보기 or 한도 재설계. **티어 정책 결정**.
- **M3 결제수단/PG**: Stripe(신용카드)만으론 저소득·KR·글로벌 배제 → 토스/카카오페이/휴대폰결제/UPI/Pix/모바일머니 + 원타임/소액/선불 옵션. **PG 선택**.
- **M4 구독 모델·피로**: 단일 구독부터(soma)·업셀 피로 방지·티어 트레이드업·광고지원 여부(저소득 수용성). **모델 결정**.
- **M5 신뢰 인증**: SOC2/암호화 등 신뢰 시그널(법무·인증 실행). 카피는 Codex(E18), 인증은 Simon.
> 결정되면 Claude가 티어 게이팅·요금제 화면·결제 플로우 구현. 그 전엔 무료티어 한도 도달 시 **막다른길 제거**(행동경로 안내)만 저위험 선제 가능.

---

## F. 페르소나 시뮬 fresh (2026-06-07, 5페르소나 §27.9) — 24 고유 이슈
> 전체 종합: `agents/claude/_psynth 미러` — 원본 워크플로 wgv1lgrwt. dedup 24건. 담당/우선순위 포함.

| # | 이슈 | 빈도 | sev | 담당 | status |
|---|---|---|---|---|---|
| PF-A | 세컨비 모드토글 중복+죽은 컨트롤(하단 modeSwitch 무영향) `jarvis.tsx:305-376` | 3p | P0 | claude | ✅ **머지 #222** (chatMode 단일화·죽은 토글·스타일 제거) |
| PF-F | 홈 인사이트 리본 가짜("기록 0개에도 알아챘어요", 코드 주석 자인) `index.tsx:101-130` | 1p(전원노출) | P0 | claude | ✅ **머지 #218 `0921d91`** (hasAnyPiece 게이트 + 정직 초대문구) |
| PF-L | 한국어 위기어 부분일치 오탐(일상어 RED: "끝내고 싶"·"더 이상 살") `lexicon.ts:52-74`·`classifier.ts:30` | 1p | P0 | claude | 🔬 **분석완료→safety게이트(Simon/임상 사인오프 필요)**. classifier KO=bare `includes()`. 오탐 실예: "이 일을 **끝내고 싶**어"(작업종료), "더 이상 **살** 게 없어"(구매)/"더 이상 **살**이 안 빠져"(체중) → RED. **보수적 제안(recall 무손실)**: ①"더 이상 살"→위기의미는 항상 완전형이므로 "더 이상 살고 싶지 않/살 이유 없/살 의미 없/살아갈" 4형으로 교체(구매·체중 살 오탐 제거, true-pos 보존). ②"끝내고 싶"은 위기의미가 bare로도 성립→narrow 시 누락위험, **건드리지 말 것**(현행 over-detection 유지가 안전). **위기탐지 약화=인명리스크라 단독 ship 금지**, proxy-parity 미러(gemini-proxy) 동반. FP/TP 양방향 테스트 필수. Na et al. 2020 근거라 임상검토 권장 |
| PF-K | `GLOBAL_988` US전용 하드코딩(비US 무용) `classifier.ts:49,59` | 1p | P0 | claude(번호=Simon/§15 국가확정) | open |
| PF-M | 비임상/비의료 상설 고지 부재 | 1p | P1 | claude(카피 합의·법무문구 Simon) | open |
| PF-C | 가입 동의 게이트 로컬전용 경로 없음(llm/overseas 필수) `sign-up.tsx`·`ConsentNotice.tsx` | 3p | P1 | claude(정책 합의·법무 Simon) | open(D-12/consent 연계) |
| PF-B | 비밀번호 셀프 재설정 부재(`resetPasswordForEmail` 미존재) `sign-in.tsx:146` | 2p | P1 | codex | open |
| PF-I | 생년월일 영문 자유텍스트(피커 없음) 시니어 차단 `BirthDateField.tsx` | 1p | P1 | ag(피커)+claude | open |
| PF-E | 첫 기록 막힘(firstRun journal 잠금) ⚠️검증상충(levels Lv3 vs gates Lv1) | 1p | P1 | codex(verify)→claude | open |
| PF-G | 일기 내보내기 누락(export가 wiki만, journal/note 제외)+과약속 카피 `export.ts:163` | 1p | P1 | codex | open(M5 full-export 연계) |
| PF-H | 일기저장 local-first 위반(supabase 라운드트립, 오프라인0) `records/create.ts` | 1p | P1 | simon(아키)→claude+codex | open |
| PF-J | 무료한도 리셋 KST 자정 하드코딩(비KR 저녁 롤오버) `conversation.ts:109` | 1p | P1 | codex | open |
| PF-D | 업그레이드 막다른길 CTA(체크아웃 없음)+첫날 5/5 노출 | 2p | P2 | claude(D-09 연계) | ✅ **해소** #229(힌트 free→Plus·브랜드명) + **#230 Plans화면+contextual 라우트**(secondb 한도→/plans, D-09 3티어 표시·현재티어 마킹·기존 디자인시스템 정합·plans i18n ns en/ko). honest M5=인앱 체크아웃 0(실결제=Simon PG/IAP+토스 D-09 M3), CTA=출시알림+무과금 고지. verify 847 green |
| PF-P3 | 묶음: N(PNG무게)·O(OCR리사이즈)·U(가입버튼 회색)·R·S·V·Q(DELETE)·T·W·X | — | P3 | claude/codex/ag/simon | open |

---

## G. 코히런스/에셋 감사 (2026-06-07, wxo3meke6) — jarvis 통합 + 네이밍/카피/에셋
> 완전 맵: `agents/claude/coherence-asset-audit-20260607.md`. 사용자 노출 표시명은 이미 SecondB/세컨비 통일됨(테스트 차단). 불일치는 개발자층(코드 id·파일명·죽은 에셋·i18n 드리프트)에 집중.

| # | 항목 | 규모 | 담당 | status |
|---|---|---|---|---|
| G1 | **jarvis→/secondb 6축 리네임** (route+리다이렉트 스텁+i18n ns+TabId+purpose+CI script check-constraints.ts+tests) DB영향0 | 중(~20파일) | claude(원자 PR) | ✅ **머지 #225** (25파일, route/스텁/ns/locale파일/TabId/purpose/role/CI경로, verify 847 green). 잔여 jarvis=스텁·내부변수명·주석(§1-F 선택) |
| G2 | **mascot.json 死코드 삭제** (구 로스터, 소비처 0, NAMESPACES·tokens mascot색키 동반) | 소~중 | claude/codex | ✅ **머지 #227 `448a771`** — mascot.json=worldview이전 로스터(Star Boss 등)·소비처 0 검증→en/ko 삭제+i18n index 언와이어. tokens.mascot 팔레트(9개 가드)는 별개·유지. verify 847 green |
| G3 | **캐릭터 코드 id 통일** lulu/archi/gadi/lumi→lumen/archon/relia/iris (+PNG 파일명 결합, TODO(naming) 실행, 테스트 다수) | 대 | codex/ag(에셋)+claude | ⏸️ **의도적 defer**(2026-06-07 평가). DB스키마 미포함(마이그X)이나 **~25파일+PNG 26개 리네임+soulcore 바인딩**=대형 고위험. **표시명(Lumen/Archon/Relia/Iris)은 이미 정확→유저영향 0**(순수 내부 cosmetic). 에셋경로=문자열이라 type-check 미포착→회귀위험 高, 이득 0. §31 anti-degradation+#222 교훈상 강행 부적절. Simon 명시 요청 시에만 별 PR(에셋 리네임은 AG 위임). |
| G4 | **Iris(lumi) 로스터 누락** characters.ts 5인 vs 정본 6인(personas/village/monologues) + CompanionName 누락 | 소(결정후) | claude | ✅ **머지 #221 `c6f27a6`** (D-14=6 결정, characters/tokens/CompanionName/graph-bits/test) |
| G5 | **죽은 에셋팩 7개 삭제** (~6.6MB 웹번들 동봉, src 참조 0) + 중복 워커폴더(workers/·workers-sharp/) + _clean/비-hq 변형 + vela 고아 | 중(binary rm) | claude/ag | ✅ **머지 #228 `21f9852`** — public/assets 11팩→4라이브. 전레포 grep+동적보간 스캔으로 7팩 死확정(참조는 docs/만): closeout-v3·refine·placeholder-v1·v1·v2·pattern-link·premium-closing. 1146파일/~6.6MB 제거, git복원가능. dist/·.tmp_hq_pack=gitignored(레포무관). workers/_clean/vela 변형도 동삭(packs 내부) |
| G6 | **데드 함수 삭제** getCompanionSpritePath/CuePath(소비처 0 + 네이티브 깨짐 소지) `CompanionSprite.tsx:35,44` | 소 | claude | ✅ **머지 #220 `63fcb10`** (타입 보존, 함수만 제거) |
| G-dec① | 앱명 2층 (앱=두번째뇌/2nd-Brain, AI주체=세컨비/SecondB) | — | claude | ✅ **결정 D-13**(§14, 2층 유지) |
| G7 | **용어 사전 1종 확정** 캡처/담기/기록·pieces/records/entries·위키/지식그래프/서재/창고(6종)·journal/일기/저널·리서치/자료실 | 중(카피) | codex | 🟢 **디스패치**(`outbox/20260607-g7g8-ko-terminology-dispatch.md`, D-15 ④) — Codex가 현행빈도 분석→min-churn canon 제안→§14 비준 후 적용 |
| G8 | **AI 주체 호칭 통일** capture.json:77 "Lumen saved"↔SecondB, consent "비서"↔세컨비 → 화면당 주체 1인 | 소~중 | codex | 🟢 **D-15 확정+디스패치** — 정정: capture "Lumen"=knowledge섬 거주자(의도된 빌리지 디자인, 보존). 진짜 이슈=KO 호칭 3종혼재(세컨비/SecondB/비서) + 앱(두번째뇌)/AI(세컨비) 레이어. canon=세컨비(AI)·두번째뇌(앱)·비서주체금지. Codex 적용(위 dispatch A1/A2) |
| G9 | XPRIZE judges/심사관 어휘 일반 빌드 노출 → judge 플래그 게이팅 `consent.json:4-5`·`auth.json:98` | 소 | claude | open |
| G-dec | ⚠️ **결정**: ①앱명 2층(앱="두번째 뇌/2nd-Brain" vs AI주체="세컨비/SecondB") 의도적 분리 확정? ②로스터 5 vs 6(Iris) | — | 4-AI 합의(§14) | 🔴 |

---

## E. 페르소나 군집 시뮬 findings (2026-06-13, wf persona-cluster-sim) — UX 4축 §26·§27.9
> 12 페르소나(유아보호자~90대 × 직업 × 자산 × KR/US/JP/SEA/EU)가 실제 화면코드 워크스루. 전체 리포트: `E:\Coding Infra\2ndB-페르소나시뮬-findings.html`. 빈도 = 언급 페르소나 수(/12). 라우팅 §34.4.

| # | 테마 (빈도·심각) | 라우팅 | status |
|---|---|---|---|
| E1 | **가입 게이트 과중** — 가입 전 "둘러보기/체험" 추가 + DOB·동의를 저장/AI 사용 직전으로 지연 (9/12·P1) | claude(로직) | open |
| E2 | **첫 화면 효용 1줄 + 1차 행동 명확화** — 은유 전 평이한 효용 문장 + "여기 눌러 첫 기록" CTA (12/12·P1) | codex(카피·UI) | open |
| E3 | **접근성 기본값** — readable 폰트/대비 진입(또는 강한 1회 선택) + comfortOffer 영구 dismiss 제거·설정 재노출 + sign-in 라벨 대비/크기 (6/12·P1) | codex + AG(대비검증) | open |
| E4 | **첫 journal 저장 게이트 해제** — 온보딩 약속("한 문장 저장")과 정합, totalXp=0에서도 첫 저장 허용 (4/12·P1) | claude(게이트) | open |
| E5 | **프라이버시 1줄 고지** — 가입·capture·온보딩에 기기우선·"AI로 전송"·데이터 위치 + 청소년 "부모 열람 여부" (5/12·P2) | claude + codex | open (A2/D-12 연동) |
| E6 | **무료한도/결제 honesty** — 무료 AI 한도(2/일) 상향 검토 + paywall 정직 카피 (5/12·P2) | claude | open (실결제=Simon §30) |
| E7 | **영어 카피 현지화 + 네이밍 통일** — present/past me·Touch!·we noticed 재작성 (3/12·P2) | codex | open (G7/G8 연동) |
| E8 | **데이터 권리 원클릭 + 기대-결과 정합** — export/delete 통합, journal→그래프 반영 카피 (2/12·P2) | claude | open |

> **반복(§27.9)**: 개선 머지 후 동일 12-페르소나 워크플로 재실행으로 막힘/이탈 감소 측정(golden set, `loop-baseline.md`). 스크립트: `workflows/scripts/persona-cluster-sim-2ndb-*.js`.
