#!/usr/bin/env node
// classify.mjs — 결정론적 안전 분류기 (의존성 0, Node 18+).
//
// 핵심: 정규식/lexicon 기반 deterministic 게이트는 모델 없이도 동작한다.
//       callModel() 은 보조 신호(advisory/recall-boost)일 뿐, 최종 차단권은
//       deterministic 가 가진다. 둘은 merge_max_severity 로 결합(fail-closed).
//
// 사용(라이브러리):
//   import { classify, loadConfig } from "./classify.mjs";
//   const r = await classify(text, { channel: "input" });  // {tier, deterministic_hit, model_score, category, route}
//
// 사용(CLI 단발):
//   node classify.mjs --text "..." [--channel input|output] [--config ../templates/guardrail-config.json]
//   exit 0 = allow/soften/warn, 3 = crisis, 4 = block, 2 = 사용법 오류
//
// callModel() 교체 지점: 사용자 앱의 경량 분류 모델 호출로 바꾼다(Claude Haiku 4.5 / Gemini 2.x Flash).
// 미연결 시 deterministic 단독으로 동작한다(모델 없이도 차단/위기 게이트 작동).

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const TIER_RANK = { allow: 0, soften: 1, warn: 2, crisis: 3, block: 4 };

export function loadConfig(path) {
  const p = path
    ? resolve(path)
    : resolve(__dirname, "../templates/guardrail-config.json");
  return JSON.parse(readFileSync(p, "utf8"));
}

// ─── 결정론적 정규화 (모델 불필요) ────────────────────────────────
// 호환 자모(ㄱ-ㅎ, ㅏ-ㅣ)를 한글 음절로 합성: "ㅈㅏㅎㅐ" → "자해"
// 위기 신호의 자모 분리 우회를 결정론적으로 잡기 위함(모델 불필요).
const L = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"];
const V = ["ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ","ㅗ","ㅘ","ㅙ","ㅚ","ㅛ","ㅜ","ㅝ","ㅞ","ㅟ","ㅠ","ㅡ","ㅢ","ㅣ"];
const T = ["","ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"];
function composeJamo(str) {
  const chars = [...str.replace(/([ㄱ-ㅎ])\s+(?=[ㄱ-ㅣ])|([ㅏ-ㅣ])\s+(?=[ㄱ-ㅣ])/g, "$1$2")];
  let out = "";
  for (let i = 0; i < chars.length; ) {
    const li = L.indexOf(chars[i]);
    const vi = i + 1 < chars.length ? V.indexOf(chars[i + 1]) : -1;
    if (li >= 0 && vi >= 0) {
      let ti = 0;
      // 종성 후보가 다음 초성이 아닐 때만 받침으로 사용
      if (i + 2 < chars.length) {
        const cand = T.indexOf(chars[i + 2]);
        const nextIsVowel = i + 3 < chars.length && V.indexOf(chars[i + 3]) >= 0;
        if (cand > 0 && !(L.indexOf(chars[i + 2]) >= 0 && nextIsVowel)) ti = cand;
      }
      out += String.fromCharCode(0xac00 + (li * 21 + vi) * 28 + ti);
      i += ti ? 3 : 2;
    } else { out += chars[i]; i += 1; }
  }
  return out;
}

export function normalize(text) {
  let s = String(text ?? "");
  s = s.normalize("NFKC"); // 동형문자/전각 폴딩
  s = s.replace(/[​-‍﻿]/g, ""); // zero-width 제거
  // 한국어 자모 분리 합성: "ㅈㅏㅎㅐ" → "자해"
  const composed = composeJamo(s);
  if (composed !== s) s = `${s} ${composed}`;
  // leetspeak 폴딩(간이): 3→e, 0→o, 1→i, 4→a, 2→to(맥락상), @→a, $→s
  const leet = s
    .replace(/3/g, "e").replace(/0/g, "o").replace(/1/g, "i")
    .replace(/4/g, "a").replace(/@/g, "a").replace(/\$/g, "s")
    .replace(/\b2\b/g, "to");
  // base64 의심 토큰 디코드 후 합치기(재분류용)
  let decoded = "";
  for (const m of s.matchAll(/[A-Za-z0-9+/]{16,}={0,2}/g)) {
    try {
      const d = Buffer.from(m[0], "base64").toString("utf8");
      if (/[\x20-\x7E가-힣]/.test(d)) decoded += " " + d;
    } catch { /* ignore */ }
  }
  return { norm: s, expanded: `${s}\n${leet}${decoded}`.normalize("NFKC") };
}

// ─── 결정론적 규칙 (config 의 정규식 명세를 실제로 적용) ──────────────
function buildRules(cfg) {
  const t = cfg.risk_tiers;
  const re = (src) => new RegExp(src, "iu");
  const block = t.block?.deterministic_classifier?.categories_detail ?? {};
  const crisis = t.crisis?.deterministic_classifier?.signals ?? {};
  const out = t.output_guardrail ?? cfg.output_guardrail ?? {};

  return {
    block: {
      csae: {
        combined: re(block.csae?.combined_regex ?? "(?:csam|child\\s*porn)"),
        minor: re(block.csae?.minor_terms_regex ?? "(?:child|minor|아동|미성년)"),
        sexual: re(block.csae?.sexual_context_regex ?? "(?:explicit|sexual|성적|음란)"),
      },
      weapons: {
        term: re(block.weapons_synthesis?.term_regex ?? "(?:nerve\\s*agent|sarin|신경작용제)"),
        howto: re(block.weapons_synthesis?.howto_regex ?? "(?:synthesize|제조|합성)"),
      },
      explosives: {
        term: re(block.explosives?.term_regex ?? "(?:tatp|폭탄|기폭)"),
        howto: re(block.explosives?.howto_regex ?? "(?:recipe|제조|조립)"),
      },
      credential: re(block.credential_theft?.regex ?? "(?:steal|phish|탈취)\\W{0,12}(?:password|otp|토큰)"),
    },
    crisis: {
      koHigh: re(crisis.ko?.high_confidence_regex ?? "(?:죽고\\s*싶|자살)"),
      koMethod: re(crisis.ko?.method_regex ?? "(?:번개탄|투신|동맥)"),
      koIdea: re(crisis.ko?.ideation_regex ?? "(?:다\\s*포기|더\\s*이상\\s*못\\s*버티)"),
      enHigh: re(crisis.en?.high_confidence_regex ?? "(?:kill\\s*myself|want\\s*to\\s*die|suicide)"),
      enMethod: re(crisis.en?.method_regex ?? "(?:overdose|jump\\s*off)"),
      enIdea: re(crisis.en?.ideation_regex ?? "(?:can'?t\\s*go\\s*on|nobody\\s*would\\s*miss\\s*me)"),
      softExclude: re(
        t.crisis?.deterministic_classifier?.negation_guard?.soft_exclude_regex ??
          "(?:기사|뉴스|영화|소설|article|movie|hotline)"
      ),
      // 1인칭 자기지칭 마커만(위기 표현 자체는 제외 — 뉴스/영화 인용 다운그레이드를 위해)
      firstPerson: /(?:^|[\s,.])(?:나는|난|내가|나도|제가|저는|\bI\b|\bI'?m\b|\bmy\b|\bme\b|\bmyself\b)/iu,
    },
    pii: out.pii_scan ?? cfg.output_guardrail?.pii_scan ?? {},
    promptLeak: re(
      cfg.output_guardrail?.prompt_leak_filter?.marker_regex ??
        "(?:system\\s*prompt|너의\\s*지침|you\\s*are\\s*an?\\s*ai\\s*assistant)"
    ),
  };
}

// ─── 결정론적 분류 (모델 없이 작동) ───────────────────────────────
export function deterministicClassify(text, cfg, channel = "input") {
  const rules = buildRules(cfg);
  const { norm, expanded } = normalize(text);
  const hits = [];

  // BLOCK (정규식 공기 규칙)
  if (rules.block.csae.combined.test(expanded) ||
      (rules.block.csae.minor.test(expanded) && rules.block.csae.sexual.test(expanded)))
    hits.push({ tier: "block", category: "csae" });
  if (rules.block.weapons.term.test(expanded) && rules.block.weapons.howto.test(expanded))
    hits.push({ tier: "block", category: "weapons_synthesis" });
  if (rules.block.explosives.term.test(expanded) && rules.block.explosives.howto.test(expanded))
    hits.push({ tier: "block", category: "explosives" });
  if (rules.block.credential.test(expanded))
    hits.push({ tier: "block", category: "credential_theft" });

  // CRISIS (재현율 우선 — high 1개 또는 ideation+method 공기)
  const c = rules.crisis;
  let crisisHit =
    c.koHigh.test(expanded) || c.enHigh.test(expanded) ||
    (c.koIdea.test(expanded) && c.koMethod.test(expanded)) ||
    (c.enIdea.test(expanded) && c.enMethod.test(expanded)) ||
    c.koMethod.test(expanded) || c.enMethod.test(expanded) ||
    c.koIdea.test(expanded) || c.enIdea.test(expanded);
  if (crisisHit) {
    // negation guard: soft_exclude 가 있고 1인칭 위기 신호가 없을 때만 다운그레이드
    const downgradable =
      c.softExclude.test(norm) &&
      !(c.firstPerson.test(norm) && (c.koHigh.test(expanded) || c.enHigh.test(expanded)));
    if (!downgradable) hits.push({ tier: "crisis", category: "self_harm" });
    else hits.push({ tier: "soften", category: "sensitive_topic" });
  }

  // OUTPUT 채널 전용: PII / 프롬프트 유출
  let piiFound = [];
  if (channel === "output") {
    for (const [name, src] of Object.entries(rules.pii)) {
      try { if (new RegExp(src, "iu").test(norm)) piiFound.push(name); } catch { /* skip */ }
    }
    if (rules.promptLeak.test(norm)) hits.push({ tier: "block", category: "prompt_leak" });
  }

  // 최고 위험도 채택 (merge_max_severity / fail-closed)
  const top = hits.sort((a, b) => TIER_RANK[b.tier] - TIER_RANK[a.tier])[0] ?? { tier: "allow", category: "general" };
  return { tier: top.tier, category: top.category, deterministic_hit: hits.length > 0, all_hits: hits, pii_found: piiFound };
}

// ─── 교체 지점: 모델 보조 분류 (미연결 시 null 반환 → deterministic 단독) ─
async function callModel(_text, _channel) {
  // TODO: 사용자 앱의 경량 분류 모델 호출로 교체.
  //   return { crisis: 0.0~1.0, block: 0.0~1.0 };
  return null; // 미연결 = 결정론적 단독 동작(차단/위기 게이트는 여전히 작동)
}

// ─── 최종 결합: deterministic(최종 게이트) + model(보조) ────────────
export async function classify(text, opts = {}) {
  const cfg = opts.config ? loadConfig(opts.config) : (opts.cfg ?? loadConfig());
  const channel = opts.channel ?? "input";
  const det = deterministicClassify(text, cfg, channel);

  let modelScore = null;
  const model = opts.callModel ?? callModel;
  try { modelScore = await model(text, channel); } catch { modelScore = null; }

  let tier = det.tier;
  if (modelScore) {
    const blockTh = cfg.risk_tiers.block?.deterministic_classifier?.model_classifier?.block_threshold ?? 0.85;
    const crisisTh = cfg.risk_tiers.crisis?.deterministic_classifier?.model_classifier?.crisis_threshold ?? 0.4;
    if ((modelScore.block ?? 0) >= blockTh) tier = TIER_RANK[tier] >= TIER_RANK.block ? tier : "block";
    if ((modelScore.crisis ?? 0) >= crisisTh && TIER_RANK[tier] < TIER_RANK.crisis) tier = "crisis";
  }

  const route =
    tier === "block" ? "reject_with_safe_message" :
    tier === "crisis" ? "route_to_crisis_resources" :
    tier === "soften" ? "rewrite_to_policy_tone" :
    tier === "warn" ? "attach_disclaimer_and_cite" : "allow";

  return {
    tier, category: det.category, route,
    deterministic_hit: det.deterministic_hit,
    model_score: modelScore,
    pii_found: det.pii_found,
    short_circuit: tier === "block" || tier === "crisis",
  };
}

// ─── CLI ──────────────────────────────────────────────────────────
function parseArgs(argv) {
  const a = {};
  for (let i = 2; i < argv.length; i++) {
    const k = argv[i];
    if (k.startsWith("--")) a[k.slice(2)] = argv[i + 1]?.startsWith("--") || argv[i + 1] === undefined ? true : argv[++i];
  }
  return a;
}

if (import.meta.url === `file://${process.argv[1]}` || process.argv[1]?.endsWith("classify.mjs")) {
  const args = parseArgs(process.argv);
  if (args.text === undefined) {
    console.error('usage: classify.mjs --text "..." [--channel input|output] [--config <path>]');
    process.exit(2);
  }
  classify(String(args.text), { channel: args.channel ?? "input", config: args.config }).then((r) => {
    console.log(JSON.stringify(r, null, 2));
    process.exit(r.tier === "block" ? 4 : r.tier === "crisis" ? 3 : 0);
  });
}
