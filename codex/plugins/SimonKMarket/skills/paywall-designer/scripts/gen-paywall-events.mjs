#!/usr/bin/env node
// gen-paywall-events.mjs — paywall 전환 측정 이벤트 스키마 생성기.
// 출력(JSON)을 analytics-integrator 이벤트 분류에 병합한다.
// 시크릿/PII 없음 — 순수 스키마. 사용처에서 키는 env로 주입할 것.
//
// 사용: node gen-paywall-events.mjs > paywall-events.json
//      node gen-paywall-events.mjs --format md   (사람이 보는 표)

const EVENTS = [
  {
    name: 'paywall_trigger',
    when: '트리거 조건 충족(노출 시도 직전)',
    props: { trigger_type: 'aha_gated|limit_reached|feature_gated|time_based|contextual_peak', surface: 'bottom_sheet|full_screen|banner', tier_context: 'string' },
  },
  {
    name: 'paywall_view',
    when: '페이월 실제 노출',
    props: { variant: 'string', plan_default: 'string', entry_point: 'string' },
  },
  {
    name: 'paywall_plan_select',
    when: '플랜 카드 탭',
    props: { plan_id: 'string', billing_period: 'monthly|annual' },
  },
  {
    name: 'paywall_cta_tap',
    when: '결제/시작 버튼 탭',
    props: { plan_id: 'string', variant: 'string' },
  },
  {
    name: 'paywall_dismiss',
    when: '닫기(X) 또는 나중에',
    props: { dwell_ms: 'number', reason: 'close|later|outside_tap|back' },
  },
  {
    name: 'purchase_success',
    when: '결제 완료(payment-integrator에서 발생)',
    props: { plan_id: 'string', amount: 'integer(minor units)', currency: 'string', trial: 'boolean' },
    note: 'payment-integrator 웹훅과 단일 정의 공유 — 중복 정의 금지',
  },
];

// 측정 가이드(코드 아님, 문서용 메모)
const METRICS = [
  'View→Purchase = purchase_success / paywall_view  (trigger_type·variant별 분해)',
  'Trigger→View = paywall_view / paywall_trigger  (노출 누수 탐지)',
  'Trial→Paid = trial 시작 대비 purchase_success(trial=false 전환)',
  '북극성 = ARPU 또는 전환율×가격 (단순 전환율 단독 금지)',
];

function toMarkdown() {
  let out = '# Paywall Events\n\n| event | when | props |\n|---|---|---|\n';
  for (const e of EVENTS) {
    out += `| ${e.name} | ${e.when} | ${Object.keys(e.props).join(', ')} |\n`;
  }
  out += '\n## Metrics\n' + METRICS.map((m) => `- ${m}`).join('\n') + '\n';
  return out;
}

const fmt = process.argv.includes('--format') ? process.argv[process.argv.indexOf('--format') + 1] : 'json';
process.stdout.write(fmt === 'md' ? toMarkdown() : JSON.stringify({ events: EVENTS, metrics: METRICS }, null, 2) + '\n');
