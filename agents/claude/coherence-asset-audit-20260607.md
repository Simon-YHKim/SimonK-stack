##### naming

조사 완료. 실제 파일 근거로 정리한 네이밍 정합성 맵입니다.

---

# 1. jarvis → SecondB 완전 맵

## 1-A. 라우트 리네임 (핵심 결정)

[라우트 파일] · `src/app/jarvis.tsx` (파일명 + `export default function Jarvis()` line 86) · 현재: URL/파일/컴포넌트가 모두 `jarvis` 인데 화면 표시명은 "세컨비/SecondB" (line 1 주석 "세컨비 chat screen (formerly Jarvis)") · 수정안: 파일을 `src/app/secondb.tsx` 로 리네임, 컴포넌트 `function SecondBChat()`. 라우트는 `/secondb` 권장(브랜드=SecondB와 1:1). 대안 `/chat`(기능 서술형)이나 브랜드 정합 우선이면 `/secondb`.

[리다이렉트 필요여부] · 신규 `src/app/jarvis.tsx` (스텁) · 현재: `/jarvis` 가 라이브 1차 탭 + 웹 baseUrl `/2nd-B/jarvis` (app.json line 80) + 딥링크 `secondbrain://` 대상 · 수정안: **리다이렉트 필요**. 이 레포의 확립된 관행(`imagine.tsx`→`/jarvis`, `mbti.tsx`→`/persona`, journal→capture)과 동일하게 `<Redirect href={{pathname:"/secondb", params}}/>` 스텁을 `jarvis.tsx` 에 남겨 저장/공유된 딥링크·웹URL 404 방지. `typedRoutes:true`(app.json line 78)라 스텁을 남기면 기존 `/jarvis` 타입도 유효.

## 1-B. `/jarvis` 문자열 호출처 전수 (리네임 시 전부 `/secondb`)

[router 호출] · `src/app/core-brain.tsx:159, 190, 223, 309, 317` · `router.push("/jarvis")` / `{pathname:"/jarvis", params}` · → `/secondb`
[redirect 타깃] · `src/app/imagine.tsx:10` · `pathname:"/jarvis"` · → `/secondb`
[router 호출] · `src/app/wiki.tsx:376` · `pathname:"/jarvis"` · → `/secondb`
[router 호출] · `src/app/record/[id].tsx:202` · `pathname:"/jarvis"` · → `/secondb`
[router 호출] · `src/components/graph/NavGraph.tsx:1270, 1280` · `pathname:"/jarvis"` / `"/jarvis"` · → `/secondb` (주석 6, 27-28, 808, 1275도 함께)
[탭 단일 진실원] · `src/lib/nav/tabs.ts:9` · `PRIMARY_TAB_PATHS = [..., "/jarvis", ...]` · → `"/secondb"`
[캐릭터 라우트맵] · `src/lib/characters.ts:38` · `secondb.routes: ["/jarvis","/"]` · → `["/secondb","/"]`
[persona 라우트] · `src/lib/persona/evidence.ts:38` · `"/jarvis?mode=divergent"` · → `/secondb?...`
[persona 라우트] · `src/lib/persona/self-portrait.ts:75` · `goal:"/jarvis?mode=divergent"` · → `/secondb?...`
[BackArrow 라벨] · `src/components/ui/BackArrow.tsx:47` · `"/jarvis": {en:"SecondB", ko:"세컨비"}` · → 키를 `"/secondb"` 로
[테스트] · `src/lib/__tests__/characters.test.ts:63-64`, `src/lib/persona/__tests__/evidence.test.ts:38`, `src/lib/persona/__tests__/self-portrait.test.ts:70` · `/jarvis` 기대값 · → `/secondb`
[주석만] · `src/lib/motion/useSignatureMotion.ts:82`, `src/app/mbti.tsx:10` · "lives in /jarvis" · → /secondb

## 1-C. 탭 식별자 / TabId

[TabId 타입] · `src/components/premium/tab-bar.tsx:22` · `type TabId = "graph"|"capture"|"jarvis"|"profile"` · → `"secondb"`
[TABS 항목] · `tab-bar.tsx:34` · `{ id:"jarvis", href:"/jarvis", ko:"세컨비", en:"SecondB" }` · → `id:"secondb", href:"/secondb"` (라벨 ko/en은 이미 정합)
[switch case] · `tab-bar.tsx:80` · `case "jarvis":` (아이콘) · → `case "secondb":`

## 1-D. i18n 네임스페이스 "jarvis" 리네임 영향

[네임스페이스 정의] · `src/lib/i18n/index.ts:50` · `NAMESPACES = [...,"jarvis",...]` · → `"secondb"`
[import] · `i18n/index.ts:14, 36` · `import enJarvis from ".../jarvis.json"` / `koJarvis` · → `enSecondb`/`koSecondb`, 경로 `secondb.json`
[resources 매핑] · `i18n/index.ts:54, 55` · `jarvis: enJarvis` / `jarvis: koJarvis` · → `secondb: enSecondb` 등
[훅 호출] · `src/app/jarvis.tsx:87` · `useTranslation("jarvis")` · → `useTranslation("secondb")`
[로케일 파일] · `locales/en/jarvis.json`, `locales/ko/jarvis.json` · 파일명 자체 · → `secondb.json` (내용은 이미 "세컨비"로 정합, line 1-11)
영향: 네임스페이스 키는 코드에서만 참조되어 서버/DB 무관, 위 5곳 동기 변경으로 닫힘.

## 1-E. `jarvis_chat` purpose 값 (분석/모킹 레이블)

[purpose 유니온] · `src/lib/llm/types.ts:11` · `| "jarvis_chat"` · → `"secondb_chat"`
[mock 테이블 키] · `src/lib/llm/gemini.ts:86, 105` · `"jarvis_chat"` mock 응답 · → `"secondb_chat"`
[호출] · `src/lib/chat/conversation.ts:178` · `purpose:"jarvis_chat"` · → `"secondb_chat"`
[테스트] · `src/lib/chat/__tests__/conversation.test.ts:112` · `expect(...).toBe("jarvis_chat")` · → 동기 변경
근거: `db/migrations/**` 및 `supabase/functions/**` grep 결과 `jarvis` 0건, `0004_ai_audit_log.sql` 에 `purpose` 컬럼 없음 → **DB CHECK·영속화 없음, 코드 전용 저위험**. (단 분석 이벤트로 흘러가면 과거 라벨 연속성만 고려.)

## 1-F. 내부 식별자 / 코드네임 잔재 (사용자 비노출이지만 정합성)

[ChatTurn role] · `src/app/jarvis.tsx:50, 138, 209, 216, 229, 402, 417, 443, 482` · `role:"user"|"jarvis"` · → `"assistant"` 또는 `"secondb"`
[스타일명] · `jarvis.tsx:705, 787` · `jarvisRow`, `jarvisBubble` · → `secondbRow`/`assistantBubble`
[console 태그] · `jarvis.tsx:157, 230` · `"[jarvis] ..."` · → `"[secondb]"`
[NavGraph bubbleAction] · `src/components/graph/NavGraph.tsx:151` · `bubbleAction?: "jarvis"|"upload"` · → `"secondb"|"upload"`
[주석 코드네임] · `src/lib/chat/limits.ts:1`, `src/lib/chat/conversation.ts:1` · "Jarvis daily..."/"Jarvis chat orchestrator" · → "SecondB ..."

## 1-G. CI 스크립트 하드코딩 (리네임 시 깨짐 — 필수 동기)

[검증 스크립트] · `scripts/check-constraints.ts:151` (`read("src/app/jarvis.tsx")`), `155-156` (`enJarvis`/`koJarvis`, `locales/*/jarvis.json`), `437-448` (`jarvisCitationCopyOk`, `jarvis.includes(...)`), `737, 773-774, 904-913` (A11y가 `src/app/jarvis.tsx` 읽고 `jarvisButtons`/`jarvisTabs` 카운트) · 현재: 경로·변수명에 `jarvis` 고정 · 수정안: 라우트/로케일 리네임과 동시 갱신(아니면 `npm run verify` C7·A11y 실패).

---

# 2. jarvis 외 레거시 코드네임 — 워커/캐릭터 내부 ID 불일치 (가장 큰 잔재)

표시명은 브랜드와 맞으나 **내부 id가 옛 코드네임**. 본인들도 인지 (`SoulcoreFinalArt.tsx:81, 490` 에 `TODO(naming): internal worker/asset ids (archi/gadi/lulu/momo/lumi) are NOT renamed`).

[id↔표시명 어긋남] 매핑:
- `lulu` → 표시 "루멘/Lumen" (id를 `lumen` 으로)
- `archi` → 표시 "아콘/Archon" (id를 `archon` 으로)
- `gadi` → 표시 "릴리아/Relia" (id를 `relia` 으로)
- `lumi` → 표시 "아이리스/Iris" (id를 `iris` 으로)
- `momo`/`secondb` 는 정합 (모모/세컨비)

근거 정의처:
[CharacterId 유니온] · `src/lib/characters.ts:16, 55-81, 101` · `"lulu"|"archi"|"gadi"` 키+CHARACTER_ORDER
[Persona] · `src/lib/chat/personas.ts:44(archi),57(gadi),70(lulu),96(lumi)` · id=옛코드네임, name=신규(`name:{en:"Lumen"...}`)
[WorkerId] · `src/components/art/WorkerSprite.tsx:21, 26-29, 37-40, 93` · 유니온 + **PNG 에셋 경로**(`lulu_premium_walk_strip_6f.png` 등)
[CompanionName] · `src/components/art/CompanionSprite.tsx:14, 28-30, 59-64`
[village 매핑] · `src/lib/village-ui.ts:10, 20, 31, 42, 64`
[색 토큰 키] · `src/lib/theme/tokens.ts:191-193`, `src/components/premium/graph-bits.tsx:97-99`
[기타] · `CharacterPathLayer.tsx:69`, `lib/graph/monologues.ts:17,22,27,37`, `lib/motion/signature.ts:57,64`, `lib/assets/soulcore-v3.ts:60-64`, `app/jarvis.tsx:240-242`, `app/onboarding.tsx:202`, `components/safety/CrisisRouter.tsx:67`, `app/capture.tsx:166`(주석 "루루")
[테스트 잠금] · `worldview-naming.test.ts`, `characters.test.ts:25-34,68,80`, `personas.test.ts:4,37`, `monologues.test.ts`, `signature.test.ts:32-33`

수정안: id 토큰을 `lumen/archon/relia/iris` 로 일괄 치환. **단 PNG 파일명**(`public/assets/2ndb-production-premium-v1/workers-redraw-v1/{lulu,archi,gadi,lumi}_*.png`)이 id와 묶여 있어 (a) 에셋 리네임 동반 or (b) id→파일명 매핑 테이블 도입 중 택1. 테스트 다수가 옛 id를 단언하므로 동시 갱신 필요. 규모 큰 변경이라 jarvis와 별 PR 권장.

[추가 비정합] · `src/lib/characters.ts` (5종: secondb/momo/lulu/archi/gadi) vs `src/lib/chat/personas.ts:96` (6종 — `lumi`/Iris 추가) · 현재: "캐릭터→라우트 단일 진실원"이라 선언한 characters.ts(line 9-12 주석)에 Iris 누락 → 로스터 분기 · 수정안: Iris에 라우트가 없다면 의도 명시 주석, 있으면 characters.ts에 추가해 일원화.

[죽은 코드네임] · `src/lib/chat/personas.ts:10` 주석 + `src/app/jarvis.tsx:246` · `vela` (공상→Divergent로 은퇴) · 현재: 주석/폴백에 잔존(테스트 `worldview-naming.test.ts:13-15` 가 부재를 단언) · 수정안: 잔여 주석 정리, 신규 코드 유입 방지(현 상태 기능 영향 없음).

---

# 3. 기타 브랜드/네이밍 비정합 (저신뢰·확인 요)

[제품명 vs 브랜드] · `app.json:3,9,51-52` · `name:"2nd-Brain"`, `scheme:"secondbrain"`, web `name/shortName:"2nd-Brain"` · 현재: OS/스토어 표기 "2nd-Brain" 인데 브랜드/AI가이드 = "세컨비/SecondB" · 수정안: 의도적 분리(제품=2nd Brain, 마스코트/AI=SecondB)면 유지, 단일 브랜드 통합이 목표면 표기 정렬 검토. **사용자 확인 항목**.

[미번역 라벨/코드네임] · `src/components/ui/BackArrow.tsx:60` · `"/trinity": {en:"Trinity", ko:"Trinity"}` · 현재: ko가 영문 "Trinity" 그대로(타 라우트는 전부 한글화) + "Trinity"가 코드네임성 · 수정안: 한국어 표시명 부여 또는 브랜드 용어로 정렬.

---

요약: jarvis 통합은 **라우트(`/secondb` 권장)+리다이렉트 스텁+i18n 네임스페이스+TabId+purpose+CI 스크립트** 6축 동기 변경으로 닫히며 DB 영향 없음(저위험). 더 큰 잔재는 **워커/캐릭터 내부 id(lulu/archi/gadi/lumi)**로, 에셋 파일명·테스트가 묶여 별도 PR 권장(중위험). app.json "2nd-Brain"·/trinity는 사용자 확인 필요.

##### copy-voice

점검 완료. 실제 파일 근거로 확인한 카피/voice/문맥 정합성 결함을 유형별·심각도순으로 정리합니다. (기준: VISION.md 정본 + conversation.ts L69 "사용자의 두번째 뇌 비서, 세컨비" → 앱명=두번째 뇌/2nd-Brain, AI 주체명=세컨비/SecondB. personas.ts=6 마스코트 캐논.)

---

## 결론 먼저: 브랜드 명칭이 5종으로 분열돼 있음
한 제품/주체가 **세컨비·SecondB / 두번째 뇌·2nd-Brain / 2ndB / 2nd-B / 개인 비서·비서**로 섞여 노출됨. 정본 규칙(conversation.ts L69, VISION.md L45)은 "앱=두번째 뇌(2nd-Brain), 주체=세컨비(SecondB)" 단 2종. 나머지(2ndB, 2nd-B, 비서)는 모두 드리프트.

---

## P0 — 브랜드/주체 명칭 분열 (가장 심각)

- [코드네임 누출]·`locales/en/import.json:5,20,39` + `locales/ko/import.json:5,20,39`·현재 `"2nd-B"`(into 2nd-B / 2nd-B will sort / Save to 2nd-B / 2nd-B로 가져와요·2nd-B가 정리·2nd-B에 저장)·수정 EN→`2nd-Brain`(목적지) / `SecondB`(주체), KO→`두번째 뇌`(목적지) / `세컨비`(주체). "2nd-B"는 GitHub 레포 코드네임이라 사용자 노출 금지.
- [동일 파일 내 자기모순]·`locales/ko/import.json:20,39 vs 44`·현재 같은 화면에서 주체를 `2nd-B`(L20,39)와 `SecondB`(L44, 한글locale에 영문)로 동시 호칭·수정 둘 다 `세컨비`로 통일.
- [코드네임 누출]·`locales/ko/support.json:23` + `locales/en/support.json:23`·현재 `"정리는 나중에 2nd-B가 도와드려요" / "2nd-B helps organize it later"`·수정 `세컨비가 도와드려요` / `SecondB helps organize`. (같은 FAQ L30 답변은 주체를 그냥 "AI"로 부름 → 주체 호칭 3종 혼재: 2nd-B/AI/—)
- [코드네임 누출]·`locales/ko/permissions.json:28` + `locales/en/permissions.json:28`·현재 `"2nd-B가 백그라운드에서…" / "2nd-B never reads…"`·수정 `두번째 뇌는…` / `2nd-Brain never reads…`.
- [영문 혼용(KO)]·`locales/ko/permissions.json:24`·현재 `"…SecondB 답변에 필요해요"`·수정 `세컨비 답변에 필요해요`.
- [EN 명칭 분열]·`locales/en/jarvis.json:2,5,7,8`·현재 `title "2ndB"`, `placeholder "Ask 2ndB..."`, `intro_title "Hi, I'm 2ndB"`, `intro_body "...I'm 2ndB"`·수정 모두 `SecondB`. (KO는 `세컨비`로 정상)
- [한 화면 내 EN 두 이름]·`src/app/jarvis.tsx:257,391,426,513` vs `locales/en/jarvis.json`·현재 화면 chrome(eyebrow `06. SecondB chat`, sprite/bubble/a11y label 전부 `SecondB`)는 SecondB인데 locale 본문(title/placeholder/intro)은 `2ndB` → EN 사용자가 한 화면에서 SecondB와 2ndB를 동시에 봄·수정 jarvis.json EN을 `SecondB`로 맞춰 화면 내 통일.
- [KO 앱명 분열]·`locales/ko/consent.json:4 vs 12,26`·현재 같은 namespace에서 `두번째 뇌`(L4)와 `2nd-Brain`(L12 intro, L26 ackSensitive) 혼용·수정 KO는 전부 `두번째 뇌`. (EN consent는 `2nd-Brain` 일관 → 정상)
- [영문 혼용(KO)]·`locales/ko/capture.json:53,88,124,155`·현재 한글 문장에 `SecondB`(되짚기/제안/물어보기/자동태그)·수정 `세컨비`.
- [영문 혼용(KO)]·`locales/ko/formats.json:14,122,124`·현재 한글 문장에 `SecondB`(제안/정리 기준 만들기)·수정 `세컨비`.
- [영문 혼용(KO)]·`locales/ko/auth.json:4`·현재 `"SecondB 입장 이미지"`·수정 `세컨비 입장 이미지`.
- [hero 블록 내 표기 불일치]·`locales/ko/wiki.json:7 vs 8`·현재 subtitle `"SecondB에 저장한 조각"`(영문) ↔ speech `"세컨비에게 물어볼 수 있어요"`(한글), 같은 hero에서 한 주체 2표기·수정 둘 다 `세컨비`. 또한 "저장한" 대상은 앱이므로 `두번째 뇌에 저장한 조각`이 의미상 정합(주체=세컨비, 보관소=두번째 뇌). EN `wiki.json:7 "saved to SecondB"`도 `saved to 2nd-Brain`.
- [홈스크린 라벨]·`app.json:3,50,51`·현재 expo.name/web.name/shortName = `"2nd-Brain"`(영문 단일, KO 로컬라이즈 없음)·수정 앱명 정본은 두번째 뇌/2nd-Brain이므로 코드네임 측면 문제는 없으나, "사용자 노출명을 세컨비로 통일"이라는 지시와 충돌하므로 **앱명=두번째 뇌 / 주체=세컨비**의 2층 브랜드 구조를 확정 후 전 화면 일괄 적용 필요(이 결정이 위 모든 항목의 기준).

---

## P1 — AI 주체 호칭 혼재 (세컨비 = 비서 = 루멘?)

- [주체 호칭 혼재]·`locales/ko/consent.json:17,72,106` + EN 동일줄·현재 주체를 `개인 비서`/`비서`(purposeService·long_term_memory·delete.body "비서 사용량") = `assistant`로 호칭, 다른 화면은 `세컨비`·수정 이름 호칭은 `세컨비`, 역할 설명에만 `개인 비서`(role-noun) 허용으로 규칙화. 최소한 `account.delete.body "비서 사용량"` → `세컨비 사용량`.
- [한 화면 2주체]·`locales/ko/capture.json:77 vs 53,88,155` (EN 동일)·현재 저장 확인은 `Lumen이/루멘`(L77 "Lumen saved a new piece")이 하고, 같은 캡처 화면의 자동 태그·형식 제안은 `SecondB/세컨비`(L53,88,155)가 함·수정 캡처 화면 담당 캐릭터 1인 확정. (추가 캐논 충돌: characters.ts는 `/capture`를 Lumen에 배정, 그러나 VISION/CONTEXT는 기록 분류=Narrative Core=모모 반장 → 저장 주체로 Lumen은 컨셉상 부정합. 모모 반장 또는 중립 세컨비로 정리 권장.)
- [영문 혼용(KO)]·`locales/ko/capture.json:77`·현재 `"Lumen이 새 조각을 저장했어요"`·수정 `루멘이 새 조각을 저장했어요`(주체 확정 후).

---

## P1 — 동일 개념 용어 혼재 (캡처/일기/위키/조각)

- [캡처 동작 용어 3종]·`capture.json`(담기: hero L19-23, modes L36-39, formats `goCapture` "담으러 가기") vs `inbox.json:4` "더 캡처하기"·`wiki.json:10` "캡처"·`settings.json:32`·`notFound.json:14` "기록 남기기"·`formats.json:4` "클리퍼"·현재 같은 동작을 담기/캡처/기록 남기기/클리퍼로 호칭·수정 KO 1동사 확정 권장(`담기` — gentle·native). "캡처"는 고유 화면명일 때만, "클리퍼"는 내부어라 노출 지양.
- [기록 단위어 혼재(EN)]·`locales/en/insights.json:13,19,26`·현재 한 화면에서 `pieces`(L13 speech) / `records`(L19 hero) / `entries`(L26 stats "Total entries") 3종이 같은 Log를 지칭·수정 단위어 1개 확정(소단위=`piece`, 누적집합=`record` 식으로 규칙화 후 화면 내 일관). KO `insights.json`도 `조각`(L14)·`기록`(L19,26) 혼재 → 동일 정리.
- [journal 표기 혼재]·`wiki.json:16` "저널로 돌아가기" + `inbox.json:5` "저널로 돌아가기" (EN "Back to journal") vs `capture.json:52` modes.journal `"일기"`·현재 기능명은 `일기`인데 뒤로가기 버튼만 음차 `저널`·수정 `일기로 돌아가기`.
- [위키/지식 보관소 명칭 6종]·`wiki.json:2` "위키" / `:3` "지식 그래프" / hero `:5` "서재"·`:6` "지식 창고" + `capture.json:44,47` "일상 Wiki/Pro Wiki"(KO에 영문 Wiki) + `data.json:17` "지식 창고" + `auth.json(signUp):45` "지식 저장소"·현재 동일 대상이 위키/지식 그래프/서재/지식 창고/지식 저장소 + 영문 Wiki·수정 사용자 노출 1차어 확정(예: `위키`), 음차 영문 `Wiki`→`위키`(일상 위키/Pro 위키), 비유어(서재/창고/저장소)는 보조 설명에서만.
- [기능명 혼재: 리서치 vs 자료실]·`profile.json:65` "리서치"(hint "근거 기반 안내") vs `research.json:9` hero.eyebrow "자료실"·현재 메뉴명과 화면명이 다름·수정 한쪽으로 통일(`자료실` 권장 — 음차 회피).
- [영문/음차 기능명]·`profile.json:36-37,57,60-61` "Big Five" / "인사이트" / "Trinity"·현재 KO 화면에 원문 영문 `Trinity`·`Big Five`와 음차 `인사이트` 혼재·수정 노출 정책 확정(검사명 Big Five는 고유명 유지 가능하나 `Trinity`는 `브레인 트리니티`/한글 라벨 권장, VILLAGE_LABEL 매핑과 정합).
- [체크인 명칭]·`profile.json:23` "지금 체크인" vs `esm.json:7` hero "가벼운 체크인"·현재 메뉴 vs 화면 명칭 불일치·수정 한쪽 통일.

---

## P1 — 캐논/코드 불일치

- [죽은+부정합 namespace]·`locales/ko/mascot.json`·`locales/en/mascot.json`(전체) + 등록 `src/lib/i18n/index.ts:15,37,50`·현재 **완전히 다른 구(舊) 로스터**(코어/셀프/필드/오그먼트 브레인, 엔그램, 시그널 분류원, 미러 뉴런, 트리니티 가이드, 오딧 컴패니언 / Core·Self·Field·Augment Brain, Engram, Signal Sorter, Mirror Neuron…)가 i18n에 등록·번들되나 어떤 화면도 `mascot.*`를 소비하지 않음(`useTranslation("mascot")`/`t("mascot…")` grep 0건). 현 세컨비/세컨드 마을 캐논과 정면 충돌·수정 mascot.json 2종 삭제 + NAMESPACES에서 제거(또는 마스코트 사전이 필요하면 personas.ts 로스터로 교체). 부수: 음성도 이탈(`사령탑/Star Boss`, `게이트키퍼/Gatekeeper`, augment `"검색 0.3초. 정확도는 안 보장."` — 경박/군대톤, gentle voice 위반).
- [로스터 누락]·`src/lib/characters.ts:16,32-90,101`·현재 5인(secondb/momo/lulu/archi/gadi)만 정의, **Muse Core = Iris(아이리스/lumi) 누락**·근거 `personas.ts:96-108`·`monologues.ts:37`·`CONTEXT.md:25`·`VISION.md:82` 모두 6인·수정 characters.ts에 `lumi/Iris(아이리스)` 추가, 또는 의도적 제외라면 주석 명시. (지시문의 5인 로스터는 characters.ts와 일치하나 코드베이스 정본은 6인 — 어느 쪽이 사용자 노출 기준인지 확정 필요.)
- [디자인 토큰 잔존]·`src/lib/theme/tokens.ts` mascot 색 키(`augment` 등, `mascot.test.ts:39` 참조)·현재 구 mascot.json 로스터와 짝인 옛 색 키 잔존·수정 mascot.json 제거 시 함께 정리(순수 카피 범위 밖이나 동일 드리프트).

---

## P2 — 브랜드 음성/문맥 침입

- [경쟁 내부맥락 노출]·`locales/ko/consent.json:4-5` + `locales/en/consent.json:3-5`·현재 일반 사용자 동의 화면 testimonial에 `"XPRIZE 심사관/XPRIZE judges"` 직접 노출·수정 judge 빌드 플래그 뒤로 게이팅하거나 "검증을 위해 익명 후기를 공유" 식으로 일반화(대회명은 내부 맥락).
- [심사관 모드 노출 정합]·`locales/ko/auth.json:98-100`(judge.badge "심사관 모드")·현재 일반 빌드에 심사관 어휘 존재·수정 judge 모드 게이팅 확인(노출 시 정상, 일반 사용자 도달 가능하면 숨김).
- [KO/EN 주어 불일치]·`locales/ko/safety.json:15` vs `locales/en/safety.json:15`·현재 KO는 `"두번째 뇌는 자기 이해와 성장에 집중해요"`(제품명 주어), EN은 `"We focus on…"`(이름 없음)·수정 한쪽 기준 통일(주체 일관성). 안전 어휘 자체(자기 이해/성장, 비임상)는 양쪽 정상 — voice 준수 양호.

---

### 참고: 정합 양호 사례 (수정 불필요)
- `src/lib/chat/personas.ts`, `monologues.ts`: 6 마스코트 이름·역할·voice(비임상·gentle) 정본과 일치.
- `recordDetail.json:17` `"세컨비에게 묻기"`, `src/app/core-brain.tsx:157,178` `세컨비/SecondB`, `jarvis.tsx` chrome: 주체명 정상 사용 — locale JSON 측 드리프트만 이들 기준에 맞추면 됨.
- 안전(safety.json), 동의(consent privacy/account)의 "AI는 도구, 주체는 당신"·local-first·비임상 voice는 전반 일관(support.json:30 "중요한 판단은 사용자가 직접" 포함).

핵심 우선순위: (1) 앱명/주체명 2층 구조 확정 → P0 일괄 치환, (2) `mascot.json` 삭제, (3) characters.ts에 Iris 추가, (4) 캡처/위키/일기 용어 사전 1종 확정.

##### assets

분석 완료. E:/2ndB(main, RN+Expo) 에셋 일관성(§26.1) 점검 결과. 모든 근거는 실제 파일·줄 기준이며, 활성 import/require 경로는 전부 실존 확인(깨진 import 없음). 핵심은 같은 5(실제 6)캐릭터가 **세 가지 네이밍 체계**로 갈라져 있고, public/assets에 죽은 버전 팩이 대량 잔존한다는 점.

---

## A. 캐릭터 네이밍 분리 (internal id vs 표시명 vs 에셋 파일명)

같은 인물이 코드 id / 표시명 / PNG 파일명 / SVG 폴더명에서 제각각. 매핑 표:

| 인물(표시) | 코드 id | PNG 파일명(라이브) | v3 SVG 폴더 | accent |
|---|---|---|---|---|
| 세컨비 SecondB | `secondb` | secondb_* | (없음) | soulViolet |
| 모모반장 Foreman Momo | `momo` | momo_* | foreman_momo | moonWhite |
| 루멘 Lumen | `lulu` | lulu_* | lumen | signalMint |
| 아콘 Archon | `archi` | archi_* | archon | signalBlue |
| 릴리아 Relia | `gadi` | gadi_* | relia | pixelLamp |
| 아이리스 Iris | `lumi` | lumi_* | iris | dreamPink |

1. **[네이밍분리]** · `src/components/art/WorkerSprite.tsx:24-40` (PNG: `lulu/archi/gadi/lumi`) vs `src/lib/assets/soulcore-v3.ts:21-25,59-65` (SVG: `archon/relia/lumen/iris`) · 동일 인물의 라이브 PNG 팩은 구(舊) id 파일명, v3 SVG 팩은 신(新) 표시명 파일명 → soulcore-v3.ts:59-65에서 `archi: ArchonIdle` 식으로 한 파일 안에서 두 체계를 억지로 브리지. · 정합안: 두 에셋 팩의 파일명을 한 체계로 통일(권장: 표시명 = `lumen/archon/relia/iris/foreman_momo`)하고 코드 id도 동시 리네임. 이미 `SoulcoreFinalArt.tsx:490-494`에 TODO(naming)로 부채 등록돼 있음 — 그 TODO 실행.

2. **[표시명 일관성 OK / 내부만 불일치]** · `src/lib/theme/tokens.ts:189-193`, `src/lib/chat/personas.ts:8-9` · 사용자 노출 문자열은 이미 신표시명으로 통일됨(구명 `Gadi/Lulu/Lumi/Archi/Vela`는 `src/lib/__tests__/worldview-naming.test.ts:9-14`가 차단). 즉 "사용자노출=세컨비/SecondB 통일" 요건은 표시층에서 충족. 불일치는 **개발자층(코드 id·파일명)에만** 잔존. · 정합안: 위 1번과 함께 정리(표시는 손대지 말 것).

---

## B. 소스 오브 트루스 누락 — 아이리스(Iris/lumi)

3. **[로스터 누락/CRITICAL]** · `src/lib/characters.ts:16` (`CharacterId = "secondb"|"momo"|"lulu"|"archi"|"gadi"`), `:101` (`CHARACTER_ORDER` 동일 5) · characters.ts 주석은 자신을 "character→route 매핑의 source of truth"라 선언하지만 **Muse Core 마스코트 아이리스(lumi)가 빠진 5명**만 정의. 그런데 아이리스는 `personas.ts:96-98`(name Iris/아이리스), `village-ui.ts:62-65`(taste village worker `lumi`), `graph/monologues.ts:37`, `app/jarvis.tsx:244`에서 **실사용·사용자 노출**됨. `personas.ts:4-5` 주석도 "five Pattern Core mascots"라 하지만 characters.ts엔 패턴 마스코트가 4명뿐. · 정합안: characters.ts에 `lumi`(아이리스/Iris, Muse Core, route `/capture` 또는 taste) 추가해 6명으로 일치시키거나, 브랜드가 5명 확정이면 아이리스를 personas/village-ui/monologues에서 제거. (과제 브랜드 스펙도 5명만 명시 → 어느 방향이든 한쪽이 틀림. 실배선 기준으론 characters.ts 누락이 버그.)

4. **[아바타 비대칭]** · `src/components/art/CompanionSprite.tsx:14` (`CompanionName = "momo"|"lulu"|"archi"|"gadi"`), `src/components/premium/graph-bits.tsx:119` (`CharacterBadge`가 `id as CompanionName`) · `CompanionName`이 아이리스(lumi)를 제외 → 그래프 워커·채팅 페르소나로는 존재하는 아이리스를 `CharacterBadge` 아바타로는 렌더 불가. WorkerId(6)·PERSONAS(6)와 어긋남. · 정합안: 3번 해결과 함께 `CompanionName`에 `lumi` 포함(또는 제거 방향과 일치).

---

## C. 죽은 버전 팩 (public/assets, src 참조 0건 — 웹 빌드에 그대로 동봉)

src·app.json·metro.config.js 전수 grep 결과 아래 팩은 참조 0. Expo 웹은 `public/`를 정적 복사하므로 웹 번들에 사장(死藏) 동봉됨(약 6.6MB).

5. **[미사용 에셋팩]** · `public/assets/cosmic-pixel-placeholder-v1/` (3.1MB), `public/assets/cosmic-pixel-v2/` (2.3MB), `public/assets/2ndb-refine/` (586KB), `public/assets/2ndb-closeout-v3/` (401KB), `public/assets/premium-closing/` (244KB), `public/assets/cosmic-pixel-v1/` (107KB), `public/assets/pattern-link/` (22KB) · 코드 참조 전무한 구 placeholder/v1/v2/refine/closeout 세대. · 정합안: 7개 폴더 삭제(git rm). 라이브 = `2ndb-production-premium-v1`·`cosmic-pixel-v3-soulcore`·`cosmic-pixel-v4-tesseract-v49`·`tesseract-v10` 4팩만 유지.

6. **[팩내 중복 워커 폴더]** · `public/assets/2ndb-production-premium-v1/workers/`, `.../workers-sharp/` · 라이브 팩 안에 워커 스프라이트가 `workers/`·`workers-sharp/`·`workers-redraw-v1/` 3벌 공존. 코드는 `workers-redraw-v1/`만 require(`WorkerSprite.tsx:24-40`). · 정합안: `workers/`·`workers-sharp/` 삭제, redraw-v1만 유지(또는 redraw-v1를 정식 폴더명으로 승격하고 버전접미사 제거).

7. **[버전접미사 혼재(중복 변형)]** · `public/assets/2ndb-production-premium-v1/graph/islands/` (`domain_*_premium.png` 비-hq 7개 + `core_center_premium_clean.png`), `.../auth/auth_secondb_gate_hero_clean.png` · 코드는 `*_premium_hq.png`만 사용(`IslandArt.tsx:17-23`, `sign-in/up·complete-profile.tsx`), 비-hq·`_clean` 변형은 미사용. · 정합안: 미사용 변형 삭제 후 단일 변형만 유지(접미사 통일).

8. **[고아 에셋(은퇴 캐릭터)]** · `public/assets/2ndb-production-premium-v1/workers-redraw-v1/vela_premium_idle.png`, `vela_premium_walk_strip_6f.png` · 벨라(Vela)는 은퇴(`src/lib/motion/signature.ts:73`, `personas.ts:10`, `worldview-naming.test.ts:12-14`)인데 라이브 워커 폴더에 PNG 잔존(WorkerId·STRIPS에서 제외돼 미사용). 동일 고아가 `cosmic-pixel-v2/.../sprites/vela/` 등에도 존재. · 정합안: vela_* 잔존 파일 삭제.

---

## D. 죽은 코드 / 접근방식 불일치

9. **[데드 export + 접근방식 불일치]** · `src/components/art/CompanionSprite.tsx:35` `getCompanionSpritePath()`, `:44` `getCompanionCuePath()` · 전체 src 소비처 0(테스트 포함). 게다가 둘 다 `require()`가 아니라 웹 전용 문자열 경로(`/assets/2ndb-production-premium-v1/...`, `:33`,`:44`)를 반환 — 프로젝트 전체가 쓰는 `require()` 번들 방식과 어긋나며, 네이티브(APK)에선 이 경로가 해석 안 됨. 호출됐다면 안드로이드에서 깨졌을 잠재 버그. · 정합안: 두 함수 삭제(미사용), 향후 필요 시 `require()` 맵으로 재작성.

---

## E. 스테일 주석 (경미)

10. **[스테일 주석]** · `src/components/art/WorkerSprite.tsx:2-4` "Six pixel companions plus Lumi" · 실제 `WorkerId`/`STRIPS`는 `secondb·momo·lulu·archi·gadi·lumi` 총 6(=secondb + 5 마스코트, vela 제외). "6 + Lumi"는 7을 시사 → 카운트 오기. · 정합안: "SecondB + five Pattern Core mascots (Vela retired)"로 수정.

11. **[스테일 주석]** · `src/components/art/SecondBSprite.tsx:1-3` "exposes the expressive v2 states" · `SecondBState` 12종을 노출하나 렌더는 WorkerSprite secondb + 액센트 오버레이뿐(walk만 paused 토글로 시각 차이), "v2 states"는 폐기된 세대 표현. · 정합안: 주석에서 "v2" 제거, 실제 동작(액센트 오버레이 기반)으로 갱신.

12. **[의도된 부재 — 참고]** · `src/lib/assets/soulcore-v3.ts:55-58`, `:21-25` · v3 companion 폴더에 `secondb` SVG만 없음(PNG fallback). 의도·문서화됨, 폴백 정상 → 버그 아님. 단 v3 companion의 비-idle 상태 SVG(`*_build/highlight/linking/sprite_sheet.svg` 등 다수)는 `EXPO_PUBLIC_USE_V3_ART` 기본 off + `_idle`만 import이라 전부 미사용. · 정합안: v3 art 정식 채택 전까지는 방치 가능, 폐기 결정 시 companion 상태 SVG 일괄 정리.

---

### 우선순위 요약
- **즉시(버그성)**: 3(아이리스 로스터 누락) → 4 동반, 9(데드+네이티브 깨짐 소지 함수 삭제).
- **정리(번들 위생)**: 5(죽은 팩 7개 삭제, ~6.6MB), 6(중복 워커 폴더), 7(변형 접미사), 8(vela 고아).
- **부채(대규모 리네임)**: 1·2(id↔파일명 네이밍 통일, 기존 TODO 실행).
- **경미**: 10·11·12(주석/플래그).

깨진 require/import: **없음**(활성 경로 전수 실존 검증 완료). 사용자 노출 표시명: 이미 통일(구명 누출 없음, 테스트가 차단). 불일치는 전부 개발자층(코드 id·파일명·죽은 에셋)과 아이리스 로스터 누락에 집중.

##### FIX-MAP

# 통합 수정 맵 — 3관점 coherence 감사 종합 (E:\2ndB, main)

3개 감사(naming·copy-voice·assets)를 교차 대조해 중복을 합치고, 의존성·위험도·담당을 붙인 실행 맵입니다. **담당 표기**: S=Simon(사용자 결정) · Cx=Codex(기계적 코드/로케일 편집) · C=Claude(온라인 git·라우트 리네임 PR·통합) · AG=Antigravity(네이티브/APK 검증·에셋 삭제 후 require 검증). 레포 루트 = `E:\2ndB`, 경로는 루트 기준.

---

## 0. 선결 의사결정 (S) — 막히면 하위 작업 블록, 최우선

| ID | 결정 사항 | 권장안 | 블록 대상 |
|---|---|---|---|
| D1 | **브랜드 2층 구조 확정**: 앱명=`두번째 뇌/2nd-Brain`, 주체=`세컨비/SecondB`. `app.json` "2nd-Brain" 유지? | 2층 확정·`app.json` 유지(앱명), 주체 호칭만 전 화면 세컨비로 | C 전체, A2(scheme) |
| D2 | **마스코트 로스터 5 vs 6** (Iris/아이리스 포함?) | **6인 확정** (실배선 근거: personas/village-ui/monologues/jarvis 모두 lumi 사용 → characters.ts 누락이 버그) | B, Iris 로스터, CompanionName |
| D3 | **캡처 화면 담당 캐릭터** (Lumen이 "저장" vs 모모반장 Narrative Core) | 모모반장 또는 중립 세컨비 (VISION/CONTEXT 컨셉상 Lumen 저장은 부정합) | C(capture.json), E |
| D4 | **용어 사전 1종 확정**: 담기/캡처/기록, 위키/지식창고/저장소, 일기/저널, 조각/기록/entries | 담기·위키·일기, 단위어 piece/record 규칙 | E |
| D5 | **신규 라우트명** + `/trinity` 한글 표시명 | `/secondb`(브랜드 1:1) · trinity=`브레인 트리니티` | A2, G |

> D1·D2·D3·D4가 가장 큰 분기점. 나머지(A1·D섹션 일부)는 결정 없이 즉시 착수 가능.

---

## A. jarvis → SecondB 통합 (단계적 — 사용자 지시 반영)

### A1 — Stage 1 (저위험: 식별자·네임스페이스·purpose, **route 무변경·사용자 비노출**) — 즉시 착수, 담당 Cx

| 작업 | 근거 파일 | 위험 |
|---|---|---|
| purpose `jarvis_chat`→`secondb_chat` | `src/lib/llm/types.ts:11`, `gemini.ts:86,105`, `chat/conversation.ts:178`, `chat/__tests__/conversation.test.ts:112` | LOW (DB CHECK·영속화 0건 확인) |
| 내부 식별자: ChatTurn role `"jarvis"`, 스타일명 `jarvisRow/jarvisBubble`, console `[jarvis]`, bubbleAction | `src/app/jarvis.tsx:50,138,209,216,229,402,417,443,482,705,787,157,230`, `components/graph/NavGraph.tsx:151` | LOW |
| i18n 네임스페이스 `jarvis`→`secondb` + 로케일 파일 리네임 | `src/lib/i18n/index.ts:14,36,50,54,55`, `app/jarvis.tsx:87`, `locales/{en,ko}/jarvis.json`→`secondb.json` | LOW (코드 전용, 서버/DB 무관, 5곳 동기로 닫힘) |
| **CI 스크립트 동기(네임스페이스 부분)** | `scripts/check-constraints.ts:155-156` (`enJarvis/koJarvis`, `locales/*/jarvis.json`) | LOW — 미동기 시 `npm run verify` C7 실패 |
| 주석 코드네임 정리 | `lib/chat/limits.ts:1`, `chat/conversation.ts:1`, `motion/useSignatureMotion.ts:82`, `app/mbti.tsx:10` | LOW |

> Stage 1은 라우트·URL·딥링크 무변경이라 단독 PR 머지 가능. 분석 이벤트 라벨 연속성만 1회 고지.

### A2 — Stage 2 (route 리네임 + 리다이렉트, **사용자 노출/딥링크/CI 영향**) — D5 확정 후, 담당 C(온라인 git·PR)

| 작업 | 근거 파일 | 위험 |
|---|---|---|
| 라우트 파일 리네임 `jarvis.tsx`→`secondb.tsx`, `function SecondBChat()` | `src/app/jarvis.tsx:1,86` | MED |
| **리다이렉트 스텁** 신규 `jarvis.tsx`에 `<Redirect href="/secondb"/>` (딥링크·웹URL 404 방지, 레포 관행 imagine/mbti와 동일) | 신규 `src/app/jarvis.tsx`, `app.json:78,80`(typedRoutes/baseUrl), scheme `secondbrain://` | MED — 스텁 누락 시 저장된 `/jarvis`·`/2nd-B/jarvis` 깨짐 |
| `/jarvis` 문자열 호출처 전수→`/secondb` | `core-brain.tsx:159,190,223,309,317`, `imagine.tsx:10`, `wiki.tsx:376`, `record/[id].tsx:202`, `NavGraph.tsx:1270,1280`, `lib/nav/tabs.ts:9`, `lib/characters.ts:38`, `persona/evidence.ts:38`, `persona/self-portrait.ts:75`, `components/ui/BackArrow.tsx:47`(키) | MED |
| TabId `"jarvis"`→`"secondb"` (type·TABS.href·switch) | `components/premium/tab-bar.tsx:22,34,80` | MED |
| 테스트 기대값 동기 | `characters.test.ts:63-64`, `persona/__tests__/evidence.test.ts:38`, `self-portrait.test.ts:70` | LOW |
| **CI 스크립트 동기(파일·A11y 부분)** | `check-constraints.ts:151,437-448,737,773-774,904-913` (`jarvis.tsx` 읽기, `jarvisButtons/jarvisTabs` 카운트) | MED — 미동기 시 verify C7·A11y 실패 |

> 머지 전 `npm run verify` 통과 필수(§18 라이브 검증 사이클). DB 영향 없음.

---

## B. 워커/캐릭터 내부 id 통일 (가장 큰 잔재) — D2 확정 후 **별도 PR**, 중위험, 담당 Cx+AG

코드 id가 옛 코드네임(`lulu/archi/gadi/lumi`)인데 표시명은 신규. 본인들도 `SoulcoreFinalArt.tsx:81,490` TODO(naming)로 부채 등록. **표시층은 이미 정합**(worldview-naming.test.ts가 구명 차단) — 손대지 말 것. 불일치는 **개발자층(코드 id·PNG/SVG 파일명·테스트)에만** 잔존.

매핑: `lulu→lumen` · `archi→archon` · `gadi→relia` · `lumi→iris` (momo/secondb 정합).

| 작업 | 근거 | 위험 |
|---|---|---|
| 코드 id 일괄 치환 | `characters.ts:16,55-81,101`, `chat/personas.ts:44,57,70,96`, `WorkerSprite.tsx:21,26-40,93`, `CompanionSprite.tsx:14,28-30,59-64`, `village-ui.ts`, `theme/tokens.ts:191-193`, `premium/graph-bits.tsx:97-99`, `CharacterPathLayer.tsx:69`, `graph/monologues.ts`, `motion/signature.ts:57,64`, `assets/soulcore-v3.ts:59-65`, `jarvis.tsx:240-242`, `onboarding.tsx:202`, `CrisisRouter.tsx:67`, `capture.tsx:166`(주석) | MED |
| **PNG 에셋 묶임 해소**: (a) 에셋 파일 리네임 동반 OR (b) id→파일명 매핑 테이블 도입 中 택1 | `public/assets/2ndb-production-premium-v1/workers-redraw-v1/{lulu,archi,gadi,lumi}_*.png`, soulcore-v3 SVG 폴더(`archon/relia/lumen/iris` — 이미 신명) | MED — AG가 require 실존 재검증 |
| 테스트 동시 갱신 | `worldview-naming.test.ts`, `characters.test.ts:25-34,68,80`, `personas.test.ts:4,37`, `monologues.test.ts`, `signature.test.ts:32-33` | LOW |
| **Iris 로스터 누락 수정**(D2=6인 시): characters.ts에 `iris` 추가 + `CompanionName`에 추가(CharacterBadge 렌더 가능화) | `characters.ts:16,101`, `CompanionSprite.tsx:14`, `graph-bits.tsx:119` — 근거 `personas.ts:96-108`,`monologues.ts:37`,`CONTEXT.md:25`,`VISION.md:82` | MED (기능 버그성) |
| characters.ts vs personas.ts 로스터 분기 일원화(Iris 라우트 명시 or 추가) | `characters.ts:9-12`(단일 진실원 선언) vs `personas.ts:96` | LOW |

> 에셋 파일명·테스트 다수가 옛 id를 단언 → 동시 갱신. jarvis와 분리 PR 권장.

---

## C. 브랜드/카피 명칭 분열 정리 (P0) — D1 확정 후, 저~중위험, 담당 Cx (로케일 전용)

정본: 앱=`두번째 뇌/2nd-Brain`, 주체=`세컨비/SecondB`. 현재 **5종 분열**(세컨비/두번째뇌/2ndB/2nd-B/비서). 모두 로케일 JSON 드리프트 → DB 영향 0.

| 결함 유형 | 근거 파일 | 수정 |
|---|---|---|
| 코드네임 `2nd-B` 누출 (GitHub 레포명, 노출 금지) | `locales/{en,ko}/import.json:5,20,39`, `support.json:23`, `permissions.json:28` | EN→2nd-Brain(목적지)/SecondB(주체), KO→두번째 뇌/세컨비 |
| 동일 파일 내 자기모순 (2nd-B↔SecondB) | `locales/ko/import.json:20,39 vs 44` | 둘 다 세컨비 |
| EN 명칭 분열 `2ndB`↔`SecondB` (한 화면 동시 노출) | `locales/en/jarvis.json:2,5,7,8` vs `app/jarvis.tsx:257,391,426,513` | jarvis.json EN 전부 SecondB |
| KO에 영문 `SecondB` 혼용 | `locales/ko/permissions.json:24`, `capture.json:53,88,124,155`, `formats.json:14,122,124`, `auth.json:4`, `wiki.json:7` | 세컨비 |
| KO 앱명 분열 (두번째 뇌↔2nd-Brain) | `locales/ko/consent.json:4 vs 12,26` | KO 전부 두번째 뇌 |
| 보관소 의미 정합 | `wiki.json:7,8`(EN `saved to SecondB`→`2nd-Brain`) | 저장 대상=앱(두번째 뇌), 주체=세컨비 |
| 주체 호칭 비서/AI/— 혼재 | `consent.json:17,72,106`(개인비서/비서), `support.json:23 vs 30` | 이름=세컨비, 역할명사로만 "개인 비서" 허용. `account.delete.body "비서 사용량"`→세컨비 사용량 |

> `app.json:3,50,51` "2nd-Brain"은 D1에서 "앱명 유지" 확정 시 **변경 없음**(코드네임 아님). D1이 C 전체의 기준.

---

## D. 죽은 namespace·에셋·코드 정리 (번들 위생) — 의존성 적음, 저위험, 즉시 착수 가능

| 작업 | 근거 | 담당 | 위험 |
|---|---|---|---|
| **mascot.json 2종 삭제** (구 로스터, `useTranslation("mascot")` grep 0건, 현 캐논과 정면 충돌·gentle voice 위반) + NAMESPACES 제거 | `locales/{ko,en}/mascot.json`, `i18n/index.ts:15,37,50` | Cx | LOW |
| ↳ 짝 디자인 토큰(`augment` 등 mascot 색 키) 동반 정리 | `theme/tokens.ts` (`mascot.test.ts:39` 참조) | Cx | LOW |
| **죽은 버전 팩 7개 삭제 (~6.6MB)** | `public/assets/{cosmic-pixel-placeholder-v1, cosmic-pixel-v2, 2ndb-refine, 2ndb-closeout-v3, premium-closing, cosmic-pixel-v1, pattern-link}/` | AG (삭제 후 빌드 검증) | LOW |
| 라이브 팩 내 중복 워커 폴더 삭제 (`workers/`,`workers-sharp/` — 코드는 `workers-redraw-v1`만 require) | `2ndb-production-premium-v1/workers*/` | AG | LOW |
| 버전접미사 변형 정리 (비-hq·`_clean` 미사용, `*_premium_hq.png`만 사용) | `2ndb-production-premium-v1/graph/islands/`, `auth/*_clean.png` | AG | LOW |
| **vela 고아 일괄 정리** (은퇴 캐릭터 PNG + 주석 + 폴백) | `workers-redraw-v1/vela_*.png`, `cosmic-pixel-v2/.../vela/`, `personas.ts:10`, `app/jarvis.tsx:246` | AG+Cx | LOW |
| **데드 함수 삭제** `getCompanionSpritePath/getCompanionCuePath` (소비처 0, 게다가 require 아닌 웹 문자열 경로 → APK서 깨질 잠재 버그) | `CompanionSprite.tsx:35,44` | Cx | LOW (latent 네이티브 버그 제거) |

---

## E. 동일 개념 용어 일관성 — D4 확정 후, 저위험, 담당 Cx

| 혼재 | 근거 | 통일안 |
|---|---|---|
| 캡처 동작 4종 (담기/캡처/기록 남기기/클리퍼) | `capture.json`, `inbox.json:4`, `wiki.json:10`, `settings.json:32`, `notFound.json:14`, `formats.json:4` | KO 1동사 `담기`, "캡처"=화면명만, "클리퍼" 노출 금지 |
| 기록 단위어 (pieces/records/entries · 조각/기록) | `en/insights.json:13,19,26`, `ko/insights.json:14,19,26` | piece=소단위/record=누적 규칙 후 화면 내 일관 |
| journal/저널 vs 일기 | `wiki.json:16`, `inbox.json:5` vs `capture.json:52` | `일기로 돌아가기` |
| 보관소 6종 (위키/지식그래프/서재/지식창고/지식저장소/Wiki) | `wiki.json:2,3,5,6`, `capture.json:44,47`, `data.json:17`, `auth.json:45` | 1차어 `위키`, 음차 Wiki→위키, 비유어는 보조설명만 |
| 리서치 vs 자료실 / 체크인 명칭 / Trinity·Big Five 노출 | `profile.json:65 vs research.json:9`, `profile.json:23 vs esm.json:7`, `profile.json:36-37,57,60-61`, `BackArrow.tsx:60`(/trinity ko=영문) | `자료실` 통일, 체크인 한쪽 통일, Trinity→한글(D5), Big Five는 고유명 유지 가능 |

---

## F. 음성/문맥 침입 — 저위험, 담당 Cx/C

| 작업 | 근거 | 수정 |
|---|---|---|
| **XPRIZE 내부맥락 노출** (일반 동의 화면 testimonial) | `consent.json:3-5`(ko/en) | judge 빌드 플래그 게이팅 or "익명 후기" 일반화 |
| 심사관 모드 어휘 일반 빌드 도달 점검 | `auth.json:98-100`(judge.badge) | judge 게이팅 확인 |
| KO/EN 주어 불일치 (안전) | `safety.json:15`(KO 제품명 주어 vs EN 무주어) | 한쪽 기준 통일 (어휘 자체는 비임상·정합 양호) |

---

## G. 경미 (주석/플래그) — 저위험, 담당 Cx, 아무 때나

스테일 주석: `WorkerSprite.tsx:2-4`("Six...plus Lumi"=7 시사 오기→"SecondB + five mascots, Vela retired") · `SecondBSprite.tsx:1-3`("v2 states" 제거) · v3 art 미사용 SVG는 `EXPO_PUBLIC_USE_V3_ART` 정식 채택 전까지 방치(soulcore-v3.ts:55-58, 의도된 부재=버그 아님).

---

## 실행 순서·의존성 그래프

```
[즉시·병렬 착수 — 결정 불필요]
  A1 (jarvis Stage1)      ─ Cx ─ LOW ─ 단독 머지
  D (mascot·죽은팩·데드함수) ─ Cx/AG ─ LOW ─ 단독 머지
  F, G                    ─ Cx ─ LOW

[D1 확정 후]  → C (브랜드 P0 일괄 치환)           ─ Cx ─ LOW~MED
[D2 확정(6인)] → B (id 통일 + Iris 로스터 + 에셋/테스트) ─ Cx+AG ─ MED ─ 별도 PR
[D3 확정]     → C-capture / E-캡처담당 정리
[D4 확정]     → E (용어 사전 적용)                ─ Cx ─ LOW
[D5 확정]     → A2 (jarvis route 리네임 + 리다이렉트 + CI) ─ C ─ MED ─ npm run verify 필수
```

**핵심 게이트**: ① jarvis는 A1(저위험 식별자/네임스페이스)을 먼저 단독 머지 → A2(route 리네임+스텁)를 후속 PR로 (지시대로 분리). ② B(캐릭터 id)는 에셋·테스트 묶임으로 jarvis와 별 PR. ③ 모든 사용자 노출 변경(C·B 표시층·app.json)은 D1·D2·D3·D4 선결 결정에 종속 → Simon 확정이 임계경로. ④ DB·마이그레이션 영향은 전 작업 통틀어 **0건**(purpose·네임스페이스 모두 코드 전용 확인).

**리스크 노트**: A2 리다이렉트 스텁 누락 = 저장된 딥링크/웹URL 404 (가장 흔한 회귀). CI `check-constraints.ts`는 A1(로케일줄)·A2(파일·A11y줄) 양쪽에서 각각 동기 안 하면 `npm run verify` 즉시 실패. B의 PNG 리네임 후 AG가 require 실존 전수 재검증 필요(현재 깨진 import 0건 상태 유지).