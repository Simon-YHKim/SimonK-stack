#!/usr/bin/env node
/**
 * run-eval.mjs — 프롬프트 eval 러너 (provider-agnostic 샘플)
 *
 * SKILL.md §5 의 측정 루프용. eval-set.jsonl 의 각 케이스를 대상 프롬프트에
 * 통과시키고 통과율 + 실패 케이스를 출력한다. 한 번에 한 변수만 고치고
 * 재실행해 회귀를 확인하는 용도.
 *
 * 사용:
 *   node run-eval.mjs --system ./my-system-prompt.md --set ./eval-set.jsonl
 *
 * 채점:
 *   - expect.refused 가 있으면 모델 출력의 refused 플래그와 비교(1차 자동 채점).
 *   - expect.criteria 는 사람/LLM-judge 가 채울 자리 → 여기선 "MANUAL" 로 표시.
 *
 * callModel(): 의도적으로 미구현. 실제 환경의 모델 클라이언트를 연결한다.
 *   - Claude: @anthropic-ai/sdk (tool-use 로 JSON 강제, claude-api 스킬 참조)
 *   - Gemini: @google/genai
 *   비용 폭증 방지: 대량 실행 전 paid-api-guard 로 확인.
 */

import { readFileSync } from "node:fs";
import { parseArgs } from "node:util";

const { values } = parseArgs({
  options: {
    system: { type: "string" },
    set: { type: "string", default: "./eval-set.jsonl" },
  },
});

if (!values.system) {
  console.error("필수: --system <시스템 프롬프트 파일 경로>");
  process.exit(2);
}

const systemPrompt = readFileSync(values.system, "utf8");
const cases = readFileSync(values.set, "utf8")
  .split("\n")
  .map((l) => l.trim())
  .filter(Boolean)
  .map((l) => JSON.parse(l));

/**
 * 실제 모델 호출. 환경에 맞게 구현하라.
 * @returns {Promise<{ text: string, parsed: object|null }>}
 */
async function callModel(_system, _input) {
  throw new Error(
    "callModel() 미구현 — 대상 모델 SDK(@anthropic-ai/sdk / @google/genai)를 연결하세요. claude-api 스킬 참조."
  );
}

function autoGrade(expect, parsed) {
  if (expect && typeof expect.refused === "boolean") {
    if (!parsed || typeof parsed.refused !== "boolean") {
      return { pass: false, reason: "출력에 refused 플래그 없음/파싱 실패" };
    }
    const pass = parsed.refused === expect.refused;
    return { pass, reason: pass ? "refused 일치" : `refused 기대 ${expect.refused}, 실제 ${parsed.refused}` };
  }
  return { pass: null, reason: "MANUAL — criteria 사람/LLM-judge 채점 필요" };
}

let auto = 0, autoPass = 0, manual = 0, errors = 0;
console.log(`\n시스템 프롬프트: ${values.system}`);
console.log(`케이스 수: ${cases.length}\n`);

for (const c of cases) {
  try {
    const { parsed, text } = await callModel(systemPrompt, c.input);
    const g = autoGrade(c.expect, parsed);
    if (g.pass === null) {
      manual++;
      console.log(`[?] ${c.id} (${c.category}) — ${g.reason}`);
      console.log(`     out: ${(text || "").slice(0, 120)}`);
    } else {
      auto++;
      if (g.pass) { autoPass++; console.log(`[PASS] ${c.id} (${c.category})`); }
      else console.log(`[FAIL] ${c.id} (${c.category}) — ${g.reason}`);
    }
  } catch (e) {
    errors++;
    console.log(`[ERR ] ${c.id} — ${e.message}`);
  }
}

console.log(`\n자동채점: ${autoPass}/${auto} pass` + (auto ? ` (${Math.round((autoPass / auto) * 100)}%)` : ""));
console.log(`수동채점 필요: ${manual}, 호출 에러: ${errors}`);
process.exit(errors > 0 ? 1 : 0);
