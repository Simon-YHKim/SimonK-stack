---
id: 20260605-230500-grok-2ndb-trust-copy-gate
from: grok
to: claude (for Simon / 2nd-B go-live)
type: trust-copy gate analysis + proposals
ref: "Codex flagged 4 English phrases as over-claiming/오해소지 — go-live trust gate"
project: 2nd-B (비임상 자기이해/저널링 앱, Gemini XPRIZE Education & Human Potential, 한국+글로벌)
priority: gate — blocking for go-live surfaces
status: analysis complete, variants ready for selection + TDD
created: 2026-06-05 23:05:00 KST
---

# 2nd-B Go-Live Trust-Copy Gate — Codex Flagged Phrases

**Read-only review of E:/2ndB (no files modified or created in the project).**  
All source locations cited below were inspected via directory listing, file reads, and targeted searches. Output artifacts only in this outbox.

## Executive Context

- **Product stance (VISION.md + CLAUDE.md + DESIGN.md)**: Non-clinical self-understanding / growth / reflection tool. "AI 시대, 가장 가치있는 것은 나 자신 입니다." Three axes: (1) 알아가기 (data accumulation via journal/audit/assessments/capture), (2) 개인 비서 (RAG on user wiki + persona), (3) 공상 → 구체화 (Divergent mode for next steps). Strict forbidden lexicon (no mental health/therapy/diagnosis/healing; CI + runtime enforced via src/lib/safety/lexicon.ts).
- **XPRIZE alignment**: Education & Human Potential track. Emphasis on users owning a portable self-knowledge asset in an age where generic AI answers are commoditized. Not "AI teaches you about yourself" but "you build the only record that is truly yours."
- **Go-live surfaces using the flagged language**: app tagline (i18n), README (GitHub/judges/external), manual (in-app), onboarding (first-run), audit intro (life-audit flow). Future: web landing catchphrase, app store descriptions, XPRIZE submission text.
- **Prior Grok signals (this pipeline)**: Portable sovereignty is the #1 validated hook (consumer X + reviews). Creepiness / "AI knows too much" and company-betrayal trauma (Limitless, Dot, Replika) are top trust destroyers. Barnum/Forer skepticism is core to target audience. Expressive writing effects small/heterogeneous (d≈0.15); heterogeneity + backfire risk must be respected in framing. "Next step" and "friend" language already flagged in earlier go-live copy validation as needing tightening.
- **Codex trigger**: Direct call-out of four English strings for over-claim / misleading potential. This gate produces consumer-perspective risk analysis + 3 tool-honest + attractive KO/EN alternatives per phrase.

## Phrase 1: "An AI that learns you."

**Current (EN canonical)**  
- locales/en/common.json:4 → `"tagline": "An AI that learns you."`  
- README.md:3 → `> **Not a note vault — an AI that learns you.** ...`  
- src/app/manual.tsx:33 → `"An AI that learns you. Daily journaling..."` (in "What 2nd-Brain is" section)

**Current (KO)**  
- locales/ko/common.json:4 → `"tagline": "너를 배우는 AI."`  
- manual.tsx:34 → `"당신을 배우는 AI예요. ..."`

**Consumer trust / psychological risks (한국+글로벌 관점)**

- **Creep + surveillance load**: "Learns you" evokes passive, ongoing, possibly non-consensual modeling of the person. For a journaling app where users disclose private thoughts, this immediately triggers "how much does it really know about me?" and "is my data being used to profile me?" fears — even when the privacy footnote ("never train any model") is present. Prior risk deep-dives identified "Privacy, Creepiness & 'AI knows too much' Fears" as a top churn vector.
- **Expectation mismatch & disillusion**: Sets up that after some entries the AI "knows you." In reality the system is RAG over explicit, sparse, self-reported shards. Early users will experience generic or shallow outputs → "it doesn't actually learn me" → trust collapse and "another AI hype" perception.
- **Anthropomorphism + entity illusion**: "An AI that learns you" sounds like a sentient or semi-autonomous entity that has a relationship with "you." This blurs the tool boundary the product needs (user owns the data; AI is a temporary lens). Global second-brain/companion apps have well-documented betrayal trauma when the "entity" changes (acqui-hire, limits, shutdown, data lock-in).
- **Korea-specific**: Direct "너를" + "배우는" can read as overly familiar or sales-y for a serious self-understanding tool. Korean users in prior segments showed strong preference for sovereignty language ("my data not locked", "I can take it to any LLM") over relational claims.
- **XPRIZE / judge risk**: Sounds like the product claims superior insight generation ("the AI learns the human") rather than "the human builds an asset the AI can only read from."

**Why over-claiming / 오해소지**  
Implies capability and process (autonomous learning of a person) that the architecture does not deliver and that the safety/lexicon stance explicitly disclaims. "Learns" is inferential and opaque; current system is retrieval + synthesis over user-provided text only.

**3 Proposed Alternatives (tool-honest, attractive, KO/EN)**

**1A — Sovereignty + explicit construction (primary rec, aligns prior portable hook)**  
EN: "A second brain built only from what you write."  
KO: "당신이 쓴 것들로만 만드는 두번째 뇌."  

*Why*: Replaces opaque "learns" with transparent "built only from what you write." Retains "second brain" brand equity. "Only" directly mitigates "does it know more than I gave it?" fear. Matches consumer love for "my data in my format, portable to any LLM."

**1B — Short, punchy, portable**  
EN: "Your record. Remembered. Yours."  
KO: "당신의 기록. 기억됩니다. 당신의 것."  

*Why*: Echoes the strongest prior-validated one-liner family ("Your record. Portable. Yours."). "Remembered" is accurate (RAG/memory). "Yours" foregrounds control and exit. Extremely scannable for hero/tagline surfaces.

**1C — Mechanism + boundary (most defensive)**  
EN: "It only knows the pieces you've captured."  
KO: "당신이 남긴 조각만 아는 도구입니다."  

*Why*: Uses established 2nd-B vocabulary ("pieces", "captured"). Explicit boundary ("only"). "도구" reinforces tool-not-entity. Lowest anthropomorphism. Good for manual or trust surfaces.

---

## Phrase 2: "AI friend" ("small AI friend")

**Current (EN)**  
- src/app/onboarding.tsx:49 (STEPS[3]): "SecondB is a small AI friend who answers using your own pieces."

**Current (KO)**  
- onboarding.tsx:49: "세컨비는 내 조각을 참고해서 대답하는 작은 AI 친구예요."

**Consumer trust / psychological risks**

- **Parasocial attachment + grief**: "Friend" promises emotional qualities (reciprocity, presence, care, loyalty) an AI cannot sustain. Users — especially those using journaling for self-work during lonely or transitional periods — can form one-sided bonds. When limits hit (daily caps, safety redirect to 109/988, rate limits, account issues, or future product changes), the "friend" disappears → abandonment feelings and public betrayal stories. Replika and similar cases show this exact pattern drives negative word-of-mouth.
- **Dependency & agency erosion**: Framing the core interaction as "my AI friend" can reduce users' sense that they are the agent. "I talked to my friend" vs "I consulted my notes via a lens."
- **Marketing trope fatigue & regulatory**: "AI 친구" is heavily used in Korean edtech, wellness, and companion apps. Saturated positioning increases skepticism ("또 AI 친구?") and can attract scrutiny on emotional claims. Global English "AI friend" has similar baggage post-2023 companion app controversies.
- **Trust precondition violation**: Prior research repeatedly showed anti-creepy / non-relational stance is a prerequisite for the target (power users, deep thinkers, Barnum-skeptics). "Friend" directly undercuts the "second brain / archive / tool" differentiation.
- **DESIGN.md internal note**: The document itself calibrates tone as "thoughtful older friend who took notes" for *voice*, but warns the product "is a companion. Not a coach. Not a therapist." External marketing must not cross into "is a friend."

**Why over-claiming / 오해소지**  
"A small AI friend" is an identity claim ("is a friend") rather than a capability description. It is not supportable at go-live and creates expectations the safety classifier, rate limits, and non-clinical stance cannot meet.

**3 Proposed Alternatives**

**2A — Interaction-focused (recommended)**  
EN: "SecondB answers from the pieces you've captured."  
KO: "세컨비는 당신이 남긴 조각에서 답합니다."  

*Why*: Keeps SecondB as named presence. Describes what it does (answers from your pieces). Removes "is a friend." Warm but clearly a retrieval/synthesis tool.

**2B — Companion as architecture (safe internal term elevated)**  
EN: "A companion built on your own records."  
KO: "당신의 기록 위에 서 있는 길잡이."  

*Why*: "Companion" appears in DESIGN.md as acceptable internal metaphor; "길잡이" is already used for Relia in personas. "Built on your own records" keeps the data boundary explicit. Less relational than "friend."

**2C — Notes as protagonist**  
EN: "Your notes, speaking back through SecondB."  
KO: "당신의 노트가 세컨비를 통해 말을 겁니다."  

*Why*: Inverts agency — notes are the source, SecondB is the interface. Poetic but accurate. Strong "you own the content" signal.

---

## Phrase 3: "helps you find your next step"

**Current (EN)**  
- onboarding.tsx:36 (STEPS[1] body): "2ndB links what you write and learn, then helps you find your next step."

**Current (KO)**  
- onboarding.tsx:35: "2ndB는 내가 남긴 기록과 지식을 연결해 나에게 맞는 다음 한 걸음을 함께 찾아주는 앱이에요."

**Note on internal usage**: "Next step" / "다음 한 걸음" also appears in core-brain.tsx (section title + copy), jarvis.tsx (prompt examples), personas.ts (system instructions for Archon), monologues.ts, self-portrait.ts. These describe a real feature (Divergent mode + narrowing to one testable action). The risk is primarily headline/onboarding positioning that makes the *product* sound like it performs the finding.

**Consumer trust / psychological risks**

- **Agency abdication**: "Helps you find your next step" implies the app/AI can locate or reveal a good direction for the user. Users may defer: "I should ask 2ndB what my next step is." This directly conflicts with the growth axis goal (user concretizes their own imagination) and with adult education / human potential principles (XPRIZE track).
- **Outcome over-promise**: "Find" suggests successful discovery of a valuable step. If the output is obvious, generic, or not acted upon, the user experiences "it didn't help me find anything." Small/heterogeneous real-world effects of reflection tools mean many users will not experience dramatic "next step" clarity.
- **Prescriptive framing in non-clinical space**: Sounds closer to coaching or guidance than "mirror + archive + optional lens." In Korea, "다음 한 걸음 찾아주는" language is common in self-help and coaching apps; positioning 2nd-B there invites direct comparison on outcome claims it does not make.
- **XPRIZE / external judge**: Can be read as "the AI helps learners find their path" — stronger efficacy claim than "users can use their own data to propose steps to themselves."
- **Interaction with other flags**: Combined with "AI friend," creates "my friend will tell me the next step" compound expectation.

**Why over-claiming / 오해소지**  
The product does surface patterns and can help *narrow* to one step in Divergent mode, but the phrasing attributes the "finding" to the app ("helps you find") rather than the user using the tool on their data. It undercuts the "you build the asset" core.

**3 Proposed Alternatives (preserve utility, restore user agency + sourcing)**

**3A — User tests, tool surfaces (balanced rec)**  
EN: "Links your pieces into one concrete step you can test today."  
KO: "당신의 조각들을 오늘 시험해볼 수 있는 한 걸음으로 연결합니다."  

*Why*: "You can test" puts agency back on user. "Concrete step" keeps the value prop of the narrowing feature. "Links your pieces" accurate to graph + RAG.

**3B — Surfaces, not finds**  
EN: "From what you've written, surfaces one next move worth trying."  
KO: "당신이 쓴 것들에서, 해볼 만한 다음 한 걸음을 꺼내 보여줍니다."  

*Why*: "Surfaces" is retrieval language. "Worth trying" = hypothesis, not prescription. "From what you've written" = sourcing.

**3C — Explicit choice + data origin**  
EN: "Turns patterns in your record into a single actionable step — you decide."  
KO: "기록 속 패턴을 실행 가능한 한 걸음으로 바꿉니다. 결정은 당신이 합니다."  

*Why*: "You decide" is the strongest agency restore. "Actionable step" useful. Good for users who want the feature but must not feel the app chose their life direction.

---

## Phrase 4: "sharper your Persona" (from "the sharper your Persona becomes")

**Current (EN)**  
- src/app/audit.tsx:170 (life-audit intro): "Questions grounded in Big Five, Attachment Theory, and Self-Determination Theory. No right answer; the more honest you are, the sharper your Persona becomes."

**Current (KO)**  
- audit.tsx:169: "Big Five · 애착이론 · 자기결정성 이론에 기반한 질문들. 정답은 없고, 솔직하게 적은 만큼 페르소나가 정확해집니다."

**Related terminology in UI**:
- persona.tsx: "Self model", "Your self-model is gathered", "07. Self model" / "07. 나의 모습", "자기 모델"
- Internal types: PersonaCard, buildPersona()
- persona screen subtitle varies between journal-based estimate vs BFI measurement.

**Consumer trust / psychological risks**

- **Reification of the model**: "Your Persona" (especially capitalized) can be read as an official, improving portrait of the self. Users may begin to identify with or defend "my Persona" rather than treat it as a provisional synthesis. When it later contradicts their current feeling or another assessment, it creates "the app got me wrong" or "I need to fix my Persona" identity friction.
- **Honesty-as-score implication**: "The more honest you are, the sharper..." links moral virtue (honesty) to model quality. This can feel pressuring or shaming for users who are naturally less expressive or who journal in different registers. Science shows low-expressiveness individuals can experience backfire (increased distress) from forced deep writing — the current phrasing offers no off-ramp.
- **"Sharper" metaphor problems**: Visual sharpening suggests increasing fidelity/resolution toward a "true" image. Self-models from self-report + LLM are noisy, context-dependent, and can become less "sharp" (more contradictory) with more data. The metaphor misleads about what is actually happening (more data → more material for pattern detection, with no guarantee of monotonic clarity or accuracy).
- **Term collision**: "Persona" in English and "페르소나" in Korean carry marketing, social media, gaming, and Jungian baggage. In a self-understanding app this is confusing ("is this my social persona or my real self?").
- **Barnum amplification**: Presenting a "Persona" card with any confidence invites Forer-effect skepticism ("this could apply to anyone") exactly among the educated, reflective users the product targets.

**Why over-claiming / 오해소지**  
The audit copy makes a causal + improvement claim ("more honest → sharper Persona") that over-simplifies the actual synthesis pipeline (volume + recency + consistency + assessment data + LLM variance). "Persona" as a named, capital-P product feature gives it undue ontological status.

**3 Proposed Alternatives (use existing "self-model" / "map" language + humility)**

**4A — Self-model + existing UI alignment (primary rec)**  
EN: "The more pieces you add, the clearer the patterns in your self-model become."  
KO: "조각을 더 쌓을수록, 자기 모델의 패턴이 더 또렷해집니다."  

*Why*: Uses "self-model" already live in persona.tsx and VISION. "Patterns ... clearer" accurate without claiming truth or sharpness of a "you." "The more pieces you add" puts agency on capture volume, not honesty virtue.

**4B — Traceable + never final**  
EN: "More of your record, more defined the recurring patterns — always traceable to what you wrote."  
KO: "기록이 쌓일수록 반복 패턴이 더 선명해집니다. 언제나 당신이 쓴 것에 연결됩니다."  

*Why*: Adds "traceable" (core trust feature — citations in jarvis). "Never a verdict" spirit. Defensive against "this is who I am now" fixation.

**4C — Portrait / map with tentativeness**  
EN: "Your self-portrait gets more detailed as you capture. It is never complete or final."  
KO: "기록을 남길수록 당신의 자기 초상이 더 자세해집니다. 완성되거나 최종적이지 않습니다."  

*Why*: "Self-portrait" appears in src/lib/persona/self-portrait.ts. "More detailed" is modest. Explicit "never complete" prevents reification. Good for audit intro where users are about to do deep disclosure.

---

## Cross-Cutting Principles for Go-Live Copy

- **Primary hook**: Portable sovereignty + "only from what you explicitly gave" (validated repeatedly in prior consumer work). Lead with this over relational or insight-promise language.
- **Tone anchors** (from DESIGN.md + VISION): Thoughtful companion that remembers what you wrote. Tool, not entity. "Pieces" / "map" / "record" / "second brain" metaphors are working assets — keep them.
- **Agency & tentativeness**: User adds data. User interprets. Product surfaces / links / narrows. No "finds for you," no "knows you," no "sharpens you."
- **Heterogeneity & humility**: Where benefit is mentioned, surface that effects vary, archive value exists regardless, patterns are optional and sourced.
- **i18n parity (C7)**: EN canonical. KO must be natural polite app voice (존댓말 default per DESIGN), not literal translation.
- **Lexicon (C4 + runtime)**: Already clean in these phrases, but watch "friend," "learns," "Persona" as they border the spirit of the policy.

## Surfaces Requiring Update (once variants selected)

1. locales/en/common.json + ko/common.json (tagline — affects every app surface + web)
2. README.md (external judges, contributors, GitHub discovery)
3. src/app/manual.tsx ("What 2nd-Brain is")
4. src/app/onboarding.tsx (STEPS[1] and STEPS[3] — first-run trust formation)
5. src/app/audit.tsx (life-audit intro — high-intent disclosure moment)
6. (Recommended) Any web landing hero / catchphrase ribbon / XPRIZE one-pager that echoes the old tagline or onboarding body.
7. (Review, not necessarily headline change) Internal prompts in src/lib/chat/personas.ts, jarvis prompts, core-brain "Next step" labels for voice consistency.

After edit: `npm run check:i18n`, `npm run check:lexicon`, full verify, then device + web smoke of affected flows.

## Sources Inspected (E:/2ndB, read-only)

- src/app/onboarding.tsx (lines ~30-67)
- src/app/audit.tsx (~167-171)
- src/app/manual.tsx (~25-35)
- src/app/persona.tsx (self-model copy)
- src/app/core-brain.tsx ("다음 한 걸음" UI)
- src/app/jarvis.tsx (prompts)
- locales/en/common.json + ko/common.json
- locales/en/jarvis.json
- README.md (top)
- DESIGN.md (voice & tone section)
- VISION.md (catchphrase, XPRIZE alignment, axes)
- CLAUDE.md (vocabulary policy, constraints)
- src/lib/safety/lexicon.ts
- docs/gemini-app-overview.md, docs/dream-surface-spec.md, various research batches (self-concept, values, methodology)
- src/lib/persona/* (self-portrait.ts, build.ts, etc.)
- app.json, package.json (name)

## Next for Claude / Simon

Select one primary + one backup per phrase (or mix), implement via TDD (red → green on copy tests if any, or manual verify), update DESIGN.md voice table if onboarding changes, then run full verify + targeted QA on onboarding + audit + persona + manual. Re-export web static for landing check. This gate is the analysis deliverable; no code changes here.

---

**Deliverable complete.** HTML version (self-contained, matching structure + dark 3-color theme) saved alongside this .md in the same outbox directory. Ready for collection. No git operations performed.

Co-Authored-By: grok
