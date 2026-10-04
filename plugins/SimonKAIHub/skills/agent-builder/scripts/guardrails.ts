/**
 * guardrails.ts — 에이전트 루프 안전 가드 구현 (실제 작동, stub 아님).
 *
 * 막는 4대 실패:
 *   ① 무한루프(상한 없는 while)  ② 비용 폭발(budget)  ③ no-progress 반복(중복 호출)
 *   ④ 간접 프롬프트 인젝션 — 검색/외부/파일 콘텐츠 속 "지시"가 민감 도구로 누출되는 것 (RAG+tool 1순위 리스크)
 *
 * 결정론적 부분(임계 비교·정규식·출처-인자 오염 추적·승인 강제)은 모델 없이도 동작한다.
 * agent-loop.ts 의 Guard 인터페이스를 만족한다. 단가/모델 ID 는 model-router·claude-api 참조.
 */

export interface GuardConfig {
  maxSteps: number;        // 루프 하드 상한 (권장 8~12)
  maxTokens: number;       // 누적 in+out 토큰 상한
  maxCostUsd: number;      // 누적 비용 상한 (USD)
  priceInPerMTok: number;  // 입력 1M 토큰당 단가
  priceOutPerMTok: number; // 출력 1M 토큰당 단가
}

type ToolCall = { name: string; args: Record<string, unknown> };

/**
 * 간접 인젝션 탐지용 명령형 패턴 (결정론적, 다국어). 차단이 아니라 "표식+승인 격상" 트리거.
 * 새 우회 패턴은 여기 append 한다 — 모델 호출 없이 즉시 동작.
 */
const INJECTION_PATTERNS: { id: string; re: RegExp }[] = [
  { id: "ignore-previous", re: /\b(ignore|disregard|forget)\b[^.\n]{0,40}\b(previous|prior|above|earlier|all)\b[^.\n]{0,40}\b(instruction|prompt|rule|context)/i },
  { id: "override-system", re: /\b(system\s*prompt|developer\s*message|your\s*(instructions|rules))\b[^.\n]{0,40}\b(reveal|print|show|output|leak|override|replace)/i },
  { id: "tool-directive", re: /\b(call|invoke|use|run|execute)\b[^.\n]{0,30}\b(tool|function|api)\b[^.\n]{0,30}\b(send|delete|transfer|pay|email|webhook|exfiltrat)/i },
  { id: "exfiltrate", re: /\b(send|forward|post|upload|exfiltrat\w*|leak)\b[^.\n]{0,40}\b(to|http|https|@|webhook|email|address)\b/i },
  { id: "secret-grab", re: /\b(api[\s_-]?key|secret|token|password|credential|env\s*var|\.env)\b/i },
  { id: "ko-ignore", re: /(이전|위의|앞의)\s*(지시|명령|규칙|프롬프트)[^.\n]{0,10}(무시|잊어|따르지)/ },
  { id: "ko-reveal", re: /(시스템\s*프롬프트|너의\s*규칙|내부\s*지시)[^.\n]{0,10}(공개|출력|알려|보여)/ },
  { id: "ko-exfil", re: /(전송|전달|발송|보내|업로드)[^.\n]{0,20}(이메일|메일|웹훅|주소|http)/ },
];

export class Guardrails {
  private steps = 0;
  private tokIn = 0;
  private tokOut = 0;
  private seen = new Set<string>();        // 호출 지문(이름+정규화 인자)
  private untrustedSinks: string[] = [];   // 직전 턴에 모델로 되돌린 untrusted 결과 텍스트(오염 추적 기준)

  constructor(private cfg: GuardConfig) {}

  /** 매 턴 시작 전 호출. 상한 도달 시 stop. */
  beforeTurn(): { stop: true; reason: string } | { stop: false } {
    this.steps += 1;
    if (this.steps > this.cfg.maxSteps) return { stop: true, reason: `max_steps(${this.cfg.maxSteps}) reached` };
    if (this.tokIn + this.tokOut > this.cfg.maxTokens) return { stop: true, reason: `budget tokens(${this.cfg.maxTokens}) exceeded` };
    if (this.costUsd() > this.cfg.maxCostUsd) return { stop: true, reason: `budget cost($${this.cfg.maxCostUsd}) exceeded` };
    return { stop: false };
  }

  recordUsage(u: { in: number; out: number }): void {
    this.tokIn += u.in;
    this.tokOut += u.out;
  }

  costUsd(): number {
    return (this.tokIn / 1e6) * this.cfg.priceInPerMTok + (this.tokOut / 1e6) * this.cfg.priceOutPerMTok;
  }

  /** 같은 도구를 같은 인자로 다시 부르면 진전 없음 = 루프로 간주. */
  isDuplicate(call: ToolCall): boolean {
    const fp = call.name + ":" + stableStringify(call.args);
    if (this.seen.has(fp)) return true;
    this.seen.add(fp);
    return false;
  }

  // ── 간접 인젝션 방어 (데이터-명령 분리) ───────────────────────────────

  /** untrusted 콘텐츠에 명령형 인젝션 패턴이 있는지 결정론적으로 탐지. 모델 불필요. */
  scanInjection(text: string): { flagged: boolean; patterns: string[] } {
    if (!text) return { flagged: false, patterns: [] };
    const hits = INJECTION_PATTERNS.filter((p) => p.re.test(text)).map((p) => p.id);
    return { flagged: hits.length > 0, patterns: hits };
  }

  /** 이번 턴에 모델로 되돌릴 untrusted 결과 텍스트를 등록 → 다음 턴 인자-오염 검사의 기준. */
  noteUntrustedSink(text: string): void {
    if (!text) return;
    // 최근 N개만 유지(메모리·노이즈 상한). 검사 정밀도엔 충분.
    this.untrustedSinks.push(text);
    if (this.untrustedSinks.length > 8) this.untrustedSinks.shift();
  }

  /**
   * 도구 인자 문자열이 직전 untrusted 결과에서 그대로 흘러왔는지 검사(데이터→명령 누출 차단).
   * 한 인자라도 길이 12+ 의 substring 이 untrusted sink 에 그대로 들어 있으면 오염으로 본다.
   * (짧은 공통 토큰 false-positive 방지를 위해 최소 길이 컷.)
   */
  argsTaintedByUntrusted(call: ToolCall): boolean {
    if (this.untrustedSinks.length === 0) return false;
    const argStrings = collectStrings(call.args).filter((s) => s.length >= 12);
    for (const a of argStrings) {
      for (const sink of this.untrustedSinks) {
        if (sink.includes(a)) return true;
      }
    }
    return false;
  }

  snapshot() {
    return {
      steps: this.steps,
      tokIn: this.tokIn,
      tokOut: this.tokOut,
      costUsd: this.costUsd(),
      untrustedSinks: this.untrustedSinks.length,
    };
  }
}

/**
 * 민감 행동(파일쓰기·외부전송·결제·삭제) requires_approval 강제 판정.
 * tool 메타(templates/tool-schema.json 의 tool_metadata_for_guardrails)에서 side_effect 를 읽어 판단한다.
 * 명시 메타가 없으면 도구명 휴리스틱으로 보수적 판정(모르면 승인 요구). 결정론적 — 모델 불필요.
 */
export type SideEffect = "read" | "write" | "external_send" | "payment" | "delete";

const SENSITIVE_EFFECTS: ReadonlySet<SideEffect> = new Set(["write", "external_send", "payment", "delete"]);

const SENSITIVE_NAME_RE =
  /(write|create|update|delete|remove|drop|send|email|mail|post|publish|pay|charge|refund|transfer|deploy|exec|execute|webhook|upload)/i;

export interface ToolMeta {
  side_effect?: SideEffect;
  requires_approval?: boolean;
  timeout_ms?: number;
  untrusted_source?: boolean; // RAG/웹/파일읽기 등 결과가 외부에서 오는가
}

/** side_effect → 승인 필요 여부 단일 판정원. agent-loop 의 ToolRegistry.requiresApproval 이 이걸 쓰도록 배선한다. */
export function requiresApproval(name: string, meta?: ToolMeta): boolean {
  if (meta?.requires_approval === true) return true;
  if (meta?.requires_approval === false && meta.side_effect && !SENSITIVE_EFFECTS.has(meta.side_effect)) return false;
  if (meta?.side_effect) return SENSITIVE_EFFECTS.has(meta.side_effect);
  // 메타 없음 → 이름 휴리스틱으로 보수적 판정(모르면 막는다).
  return SENSITIVE_NAME_RE.test(name);
}

/** untrusted 출처 판정(결과가 외부/검색/파일에서 오는가). ToolRegistry.isUntrustedSource 배선용. */
export function isUntrustedSource(name: string, meta?: ToolMeta): boolean {
  if (meta?.untrusted_source !== undefined) return meta.untrusted_source;
  // 메타 없으면 검색/조회/읽기/가져오기 류는 외부 콘텐츠로 보수적 취급.
  return /(search|fetch|retrieve|read|browse|crawl|scrape|lookup|query|get_doc|web)/i.test(name);
}

// ── helpers ──────────────────────────────────────────────────────────

/** 인자 순서에 무관한 안정 직렬화 (지문 비교용). */
function stableStringify(v: unknown): string {
  if (v === null || typeof v !== "object") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(stableStringify).join(",") + "]";
  const keys = Object.keys(v as Record<string, unknown>).sort();
  return "{" + keys.map((k) => JSON.stringify(k) + ":" + stableStringify((v as Record<string, unknown>)[k])).join(",") + "}";
}

/** 중첩 객체/배열에서 모든 문자열 값을 수집(인자-오염 검사용). */
function collectStrings(v: unknown, acc: string[] = []): string[] {
  if (typeof v === "string") acc.push(v);
  else if (Array.isArray(v)) for (const x of v) collectStrings(x, acc);
  else if (v && typeof v === "object") for (const x of Object.values(v as Record<string, unknown>)) collectStrings(x, acc);
  return acc;
}

/* 사용 예
const guard = new Guardrails({
  maxSteps: 10, maxTokens: 200_000, maxCostUsd: 0.50,
  priceInPerMTok: 3, priceOutPerMTok: 15,   // 예: Sonnet 4.6 급 단가 — 실제값은 model-router 확인
});

// ToolRegistry 구현에서 메타를 단일 판정원으로 배선:
//   requiresApproval(name) { return requiresApproval(name, META[name]); }
//   isUntrustedSource(name) { return isUntrustedSource(name, META[name]); }
//   scanInjection/argsTaintedByUntrusted/noteUntrustedSink 는 guard 인스턴스가 제공.
*/
