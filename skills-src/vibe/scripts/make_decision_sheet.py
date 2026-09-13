# make_decision_sheet.py — /vibe v2.1 결정 시트 생성기
#
# 발주 §10 : 라운드 산출물 → 체크박스 HTML 1장. 항목마다 어느 레인이 냈는지 표기.
#            하단 [결과 저장] → decisions_<run_id>.json 다운로드.
# 발주 S4  : 워커 문자열 전부 이스케이프 · 외부 스크립트/CDN 없음 · 자체완결 1파일.
#
# ── 2026-09-04 독립 보안 감사 반영 ──────────────────────────────
# HIGH-1 인라인 JSON 의 </script> 가 script 문맥을 탈출해 저장형 XSS
#        → ui.json_for_inline_script() 로만 직렬화. 추가로 lane/id 를 생성 전에 거부.
# HIGH-2 ui.esc() 를 통과한 lane 이 JS 에서 복원돼 innerHTML 로 재유입 (별도 DOM XSS)
#        → 집계표를 문자열 연결 대신 createElement/textContent 로 조립.
# MED    같은 id 중복 시 화면 선택과 저장 채택률이 어긋남 → id 유일성 강제.
# MED    lane='__proto__' 가 집계 객체 prototype 을 오염 → Map 사용 + allowlist.
#        (뒤 둘은 HIGH 수정과 같은 함수라 함께 고쳤다. 재작성하며 남길 수 없다.)
#
# 입력 JSON:
#   {"run":"run_x1","objective":"…",
#    "items":[{"id":"i1","lane":"gpt-5.6-sol","title":"…","detail":"…",
#              "confidence":"강|약","revert":"되돌리는 법","default":true,
#              "options":["채택","보류"]}]}
#
# 사용: python make_decision_sheet.py <입력.json> [출력.html]
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import ledger   # noqa: E402
import routing  # noqa: E402
import ui       # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# fullmatch 를 쓴다 — Python 의 $ 는 끝 개행 앞에도 일치한다 (감사 LOW).
RUN_RE = re.compile(r"run_[A-Za-z0-9]{1,40}")
ID_RE = re.compile(r"[A-Za-z0-9_\-]{1,40}")


MAX_ITEMS = 500
MAX_STR = 4000
MAX_INPUT_BYTES = 2 * 1024 * 1024


def _safe(v, limit=24):
    """감사 LOW: 예외에 비신뢰 원문을 그대로 반사하지 않는다."""
    s = str(v)
    if len(s) > limit:
        import hashlib
        return f"<{len(s)}자, sha={hashlib.sha256(s.encode()).hexdigest()[:8]}>"
    return repr(s)


def _txt(v, field, n):
    """문자열 필드 — 타입·길이를 강제한다 (감사 MED)."""
    if v is None:
        return ""
    if not isinstance(v, str):
        raise SystemExit(f"items[{n}].{field} 는 문자열이어야 한다")
    if len(v) > MAX_STR:
        raise SystemExit(f"items[{n}].{field} 가 {MAX_STR}자를 넘는다")
    return v


def _check(data):
    """생성 전에 거부한다. 렌더 시점 이스케이프에만 의존하지 않는다.

    감사 MED (재검증): top-level dict 확인 전에 data.get() 을 부르고,
    items/options 가 list 인지 검사하지 않고, default 를 bool() 로 강제해
    JSON 문자열 "false" 가 True 로 뒤집혔다(Edge 에서 checked 로 렌더 확인됨).
    """
    if not isinstance(data, dict):
        raise SystemExit("최상위가 객체가 아니다")

    run = data.get("run")
    if not isinstance(run, str) or not RUN_RE.fullmatch(run):
        raise SystemExit(f"run 형식이 맞지 않는다: {_safe(run)} (run_<영숫자 1~40>)")

    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise SystemExit("items 가 비었거나 배열이 아니다")
    if len(items) > MAX_ITEMS:
        raise SystemExit(f"items 가 {MAX_ITEMS}개를 넘는다 ({len(items)})")

    # 감사 MED: allowlist 에 CLI effort-suffix 슬러그를 섞으면
    # 저장 결과의 lane 이 suffix 상태로 나가 원장의 logical lane 과 매칭되지 않아
    # 회수가 영구 보류된다. **logical lane 만** 허용한다.
    allow = set(routing.LANES)
    seen = set()
    clean = []
    for n, it in enumerate(items):
        if not isinstance(it, dict):
            raise SystemExit(f"items[{n}] 이 객체가 아니다")
        iid = it.get("id") or f"i{n + 1}"
        if not isinstance(iid, str) or not ID_RE.fullmatch(iid):
            raise SystemExit(f"items[{n}].id 형식 위반 {_safe(iid)} (영숫자·_·- 1~40)")
        if iid in seen:
            raise SystemExit(f"items[{n}].id 중복: {_safe(iid)}")
        seen.add(iid)

        lane = it.get("lane")
        if not isinstance(lane, str) or lane not in allow:
            raise SystemExit(
                f"items[{n}].lane 이 라우팅 정본의 logical lane 이 아니다: {_safe(lane)}\n"
                f"  허용: {', '.join(sorted(allow))}\n"
                f"  (CLI 슬러그 gemini-3.8-flash-high 같은 값은 여기 쓰지 않는다)")

        d = it.get("default", True)
        if type(d) is not bool:          # "false" 문자열이 True 가 되던 문제
            raise SystemExit(f"items[{n}].default 는 bool 이어야 한다 (받은 값 {_safe(d)})")

        opts = it.get("options")
        if opts is not None:
            if not isinstance(opts, list) or len(opts) > 12:
                raise SystemExit(f"items[{n}].options 는 12개 이하 배열이어야 한다")
            for o in opts:
                if not isinstance(o, str) or len(o) > 200:
                    raise SystemExit(f"items[{n}].options 항목은 200자 이하 문자열")

        for f in ("title", "detail", "revert", "confidence"):
            _txt(it.get(f), f, n)

        clean.append((iid, lane, it))
    return run, clean


def build(data, out_path):
    run, items = _check(data)
    objective = data.get("objective", "")
    lanes = sorted({lane for _, lane, _ in items})

    # 감사 MED: provenance. 시트를 만들 때 Downloads 밖에 pending manifest 를 남긴다.
    # 회수는 이 manifest 와 정확히 맞는 미소비 결과 하나만 처리한다 → 재생·위조 차단.
    manifest = ledger.write_pending_manifest(
        run, [{"id": iid, "lane": lane} for iid, lane, _ in items])

    cards = []
    for iid, lane, it in items:
        conf = str(it.get("confidence", "")).strip()
        default_on = it.get("default", True)      # _check 에서 bool 로 검증됨
        conf_tag = ""
        if conf:
            strong = conf.startswith("강")
            conf_tag = (f'<span class="tag{" strong" if strong else ""}">확신 {ui.esc(conf)}'
                        f'{" · 기계검증" if strong else " · 판단"}</span>')
        revert = it.get("revert")
        revert_html = (f"<details><summary>되돌리는 법</summary>"
                       f'<p class="det">{ui.esc(revert)}</p></details>') if revert else ""
        opts = it.get("options") or []
        opts_html = ""
        if opts:
            opts_html = ('<p class="det">선택지: '
                         + " · ".join(f"<b>{ui.esc(o)}</b>" for o in opts) + "</p>")
        cards.append(
            f'<div class="item{" on" if default_on else ""}" data-id="{ui.esc(iid)}" '
            f'data-lane="{ui.esc(lane)}">'
            f'<div class="itop">'
            f'<input type="checkbox" id="c_{ui.esc(iid)}"{" checked" if default_on else ""} '
            f'aria-label="{ui.esc(it.get("title",""))} 채택">'
            f'<div style="flex:1">'
            f'<label class="ttl" for="c_{ui.esc(iid)}">{ui.esc(it.get("title",""))}</label>'
            f'<div class="meta"><span class="tag lane">{ui.esc(lane)}</span>{conf_tag}</div>'
            f'<p class="det">{ui.esc(it.get("detail",""))}</p>'
            f"{opts_html}{revert_html}"
            f"</div></div></div>")

    lane_badges = "".join(f'<span class="tag lane">{ui.esc(l)}</span>' for l in lanes)
    body = (
        f'<h1>결정 시트 <span class="note">{ui.esc(run)}</span></h1>'
        f'<p class="sub">{ui.esc(objective)}<br>'
        f"체크된 항목이 <strong>채택</strong>이다. 기본값은 워커 제안 그대로 켜져 있다. "
        f"다 고른 뒤 <strong>[결과 저장]</strong>을 누르면 파일이 다운로드되고, "
        f"다음 <code>/vibe</code> 실행 때 자동으로 학습 원장에 합쳐진다.</p>"
        f'<section class="quota"><h2>이 라운드의 레인 '
        f'<span class="note">항목마다 어느 레인이 냈는지 배지로 표시된다</span></h2>'
        f'<div class="chips">{lane_badges}</div></section>'
        f"{''.join(cards)}"
        f'<div class="tally"><div class="row">'
        f'<button class="act" id="save">결과 저장</button>'
        f'<button class="act ghost" id="all">전체 선택</button>'
        f'<button class="act ghost" id="none">전체 해제</button>'
        f'<span class="status" id="st"></span></div>'
        f'<table class="sum" id="sum"></table></div>')

    payload = {"run": run, "nonce": manifest["nonce"],
               "items": [{"id": iid, "lane": lane} for iid, lane, _ in items]}

    script = """
(function(){
'use strict';
var DATA=__PAYLOAD__;
function boxes(){return Array.prototype.slice.call(document.querySelectorAll('.item input[type=checkbox]'));}
/* 감사 MED: id 중복 시 getElementById 가 항상 첫 요소만 보므로
   Python 쪽에서 유일성을 강제하되, 여기서도 요소 참조를 한 번만 잡아 둔다. */
var REFS=DATA.items.map(function(it){
  return {id:it.id, lane:it.lane, el:document.getElementById('c_'+it.id)};
});
function tally(){
  /* 감사 MED: {} 는 lane='__proto__' 에 오염된다 → Map 사용 */
  var by=new Map();
  REFS.forEach(function(r){
    if(!by.has(r.lane)){by.set(r.lane,{items:0,accepted:0});}
    var b=by.get(r.lane);
    b.items++;
    if(r.el&&r.el.checked){b.accepted++;}
  });
  /* 감사 HIGH-2: innerHTML 문자열 연결은 lane 이 다시 HTML 로 파싱되는 DOM XSS sink 다.
     createElement + textContent 로만 조립한다. */
  var t=document.getElementById('sum');
  t.replaceChildren();
  var head=document.createElement('tr');
  ['레인','항목','채택','채택률'].forEach(function(h,i){
    var th=document.createElement('th');
    th.textContent=h;
    if(i>0){th.className='n';}
    head.appendChild(th);
  });
  t.appendChild(head);
  Array.from(by.keys()).sort().forEach(function(lane){
    var b=by.get(lane);
    var tr=document.createElement('tr');
    var td0=document.createElement('td');
    td0.textContent=lane;                    /* 절대 innerHTML 로 넣지 않는다 */
    tr.appendChild(td0);
    [b.items, b.accepted, (b.items?Math.round(b.accepted/b.items*100):0)+'%']
      .forEach(function(v){
        var td=document.createElement('td');
        td.className='n';
        td.textContent=String(v);
        tr.appendChild(td);
      });
    t.appendChild(tr);
  });
  var out={};
  by.forEach(function(v,k){out[k]={items:v.items,accepted:v.accepted};});
  return out;
}
REFS.forEach(function(r){
  if(!r.el){return;}
  r.el.addEventListener('change',function(){
    var card=r.el.closest('.item');
    if(card){card.classList.toggle('on',r.el.checked);}
    tally();
  });
});
document.getElementById('all').addEventListener('click',function(){
  boxes().forEach(function(b){b.checked=true;var c=b.closest('.item');if(c){c.classList.add('on');}});tally();});
document.getElementById('none').addEventListener('click',function(){
  boxes().forEach(function(b){b.checked=false;var c=b.closest('.item');if(c){c.classList.remove('on');}});tally();});
document.getElementById('save').addEventListener('click',function(){
  var out={run:DATA.run,nonce:DATA.nonce,by_lane:tally()};
  var txt=JSON.stringify(out,null,2);
  var name='decisions_'+DATA.run+'.json';
  try{
    var blob=new Blob([txt],{type:'application/json'});
    var a=document.createElement('a');
    a.href=URL.createObjectURL(blob);a.download=name;
    document.body.appendChild(a);a.click();
    setTimeout(function(){URL.revokeObjectURL(a.href);document.body.removeChild(a);},400);
    document.getElementById('st').textContent=name+' 저장됨 - 다음 /vibe 에서 자동 회수된다';
  }catch(e){
    var pre=document.createElement('pre');pre.textContent=txt;
    document.querySelector('.tally').appendChild(pre);
    document.getElementById('st').textContent='다운로드가 막혔다 - 아래 내용을 '+name+' 로 저장할 것';
  }
});
tally();
})();
"""
    script = script.replace("__PAYLOAD__", ui.json_for_inline_script(payload))
    doc = ui.page(f"결정 시트 — {run}", body, script)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)
    return doc, len(items), lanes


USAGE = """사용: python make_decision_sheet.py <입력.json> [출력.html]

  결정 시트(HTML)를 만든다. 이 시트의 [결과 저장] 버튼이 내는
  `decisions_<run>.json` 이 **채택률이 원장으로 돌아오는 유일한 경로**다.

  ⚠ 손으로 조립한 시트에는 그 버튼이 없다. 그러면 그 라운드의 채택률은
    영영 회수되지 않는다(2026-09-13 실측: 미회수 4건이 전부 이 경우였다).
    시트는 반드시 이 스크립트로 만든다.

  입력 JSON: {"run": "run_xxx", "items": [{"id","lane","title",...}, ...]}
  기본 출력: E:/Coding Infra/reports/vibe-decisions-<run>.html
  회수 확인: python scripts/aggregate_ledger.py  (상태가 셋으로 갈려 나온다)
"""


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        # 사용법을 물은 것은 오류가 아니다. 인자가 아예 없을 때만 2 를 낸다.
        raise SystemExit(0 if argv else 2)
    src = argv[0]
    # MED-84: 존재·형태를 먼저 본다. getsize 가 먼저면 없는 경로에서 traceback 이 난다.
    if not os.path.isfile(src):
        raise SystemExit("입력 파일이 없다")
    if os.path.getsize(src) > MAX_INPUT_BYTES:
        raise SystemExit(f"입력이 {MAX_INPUT_BYTES}바이트를 넘는다")
    with open(src, "rb") as f:
        raw = f.read()
    data = json.loads(raw.decode("utf-8"),
                      object_pairs_hook=ledger._reject_dupe_keys,
                      parse_constant=lambda c: (_ for _ in ()).throw(
                          ValueError("NaN/Infinity 거부")))
    run = str(data.get("run", "run_unknown"))
    out = argv[1] if len(argv) > 1 else \
        os.path.join(r"E:\Coding Infra\reports", f"vibe-decisions-{run}.html")
    doc, n, lanes = build(data, out)
    print(out)
    # 감사 LOW: 비신뢰 문자열을 로그에 반사하지 않는다. 개수만 보고한다.
    print(f"항목 {n}개 · 레인 {len(lanes)}종 · {round(len(doc.encode('utf-8')) / 1024, 1)}KB")
    print(f"[결과 저장] → decisions_{run}.json (다음 /vibe 가 자동 회수)")


if __name__ == "__main__":
    main()
