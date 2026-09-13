# ui.py — /vibe 폼·시트 공용 렌더링
#
# 발주 §10: "make_intake.py 의 HTML 렌더링을 재사용한다. 새 스택을 도입하지 말 것."
# → CSS 와 이스케이프를 여기로 빼서 인테이크 폼과 결정 시트가 같은 것을 쓴다.
# 발주 S4: 외부 스크립트·CDN 없음. 자체완결 단일 파일.
import html
import json

# 인테이크 폼(v2.0)에서 그대로 가져온 토큰·컴포넌트. 색 3색 이내, 라이트/다크 자동.
CSS = """
:root{--bg:#f7f6fb;--text:#221f33;--accent:#3f3a8c;
--panel:color-mix(in srgb,var(--bg) 60%,white);--line:color-mix(in srgb,var(--text) 14%,var(--bg));
--muted:color-mix(in srgb,var(--text) 62%,var(--bg));--soft:color-mix(in srgb,var(--accent) 10%,var(--bg));
--sans:"Pretendard Variable",Pretendard,-apple-system,"Segoe UI","Malgun Gothic",sans-serif;
--mono:"Cascadia Code",Consolas,"D2Coding",monospace}
@media (prefers-color-scheme:dark){:root{--bg:#16151f;--text:#ecebf4;--accent:#aca7f0;
--panel:color-mix(in srgb,var(--bg) 70%,black)}}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);font-size:15px;line-height:1.6}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.wrap{max-width:880px;margin:0 auto;padding:30px 20px 70px}
h1{font-size:23px;letter-spacing:-.02em;margin:0 0 4px}
.sub{color:var(--muted);font-size:13.5px;margin:0 0 20px}
h2{font-size:15px;margin:0 0 8px}
.note{color:var(--muted);font-size:12.5px;font-weight:400}
.quota{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px 16px;margin-bottom:20px}
.qrow{display:grid;grid-template-columns:150px 1fr 128px;gap:10px;align-items:center;font-size:13px;margin-top:5px}
.bar{height:6px;background:var(--line);border-radius:3px;overflow:hidden}
.bar i{display:block;height:100%;background:var(--accent)}
.qn{font-family:var(--mono);font-size:12px;color:var(--muted);text-align:right}
.warn{color:var(--accent);font-weight:600;font-size:13px;margin:10px 0 0}
fieldset.axis{border:0;padding:0;margin:0 0 18px}
legend{font-size:14px;font-weight:700;padding:0;margin-bottom:7px}
.chips{display:flex;flex-wrap:wrap;gap:7px}
.chip{position:relative;font:inherit;text-align:left;background:var(--panel);color:var(--text);
border:1px solid var(--line);border-radius:9px;padding:8px 12px;cursor:pointer;
transition:border-color .12s,background .12s}
.chip b{display:block;font-size:13.5px;font-weight:600}
.chip i{display:block;font-style:normal;font-size:11.5px;color:var(--muted);margin-top:1px}
.chip:hover{border-color:var(--accent)}
.chip[aria-checked=true],.chip[aria-pressed=true]{background:var(--soft);border-color:var(--accent)}
.chip.dunno b{color:var(--muted);font-weight:500}
.chip[aria-checked=true].dunno b,.chip[aria-pressed=true].dunno b{color:var(--accent)}
.chip.multi{padding-left:30px}
.chip.multi::before{content:"";position:absolute;left:11px;top:50%;transform:translateY(-50%);
width:13px;height:13px;border:1.5px solid var(--line);border-radius:4px}
.chip.multi[aria-pressed=true]::before{background:var(--accent);border-color:var(--accent)}
.chip.multi[aria-pressed=true]::after{content:"";position:absolute;left:15px;top:50%;
margin-top:-4px;width:4px;height:7px;border:solid var(--bg);border-width:0 2px 2px 0;transform:rotate(42deg)}
textarea{width:100%;min-height:96px;font:inherit;font-size:14px;background:var(--panel);color:var(--text);
border:1px solid var(--line);border-radius:9px;padding:10px 12px;resize:vertical}
textarea:focus{border-color:var(--accent)}
.out{margin-top:24px;border-top:1px solid var(--line);padding-top:18px}
pre{font-family:var(--mono);font-size:12.5px;background:var(--panel);border:1px solid var(--line);
border-radius:9px;padding:12px 14px;white-space:pre-wrap;word-break:break-word;margin:0 0 10px;min-height:80px}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
button.act{font:inherit;font-size:13.5px;font-weight:700;background:var(--accent);color:var(--bg);
border:0;border-radius:8px;padding:9px 16px;cursor:pointer}
button.ghost{background:none;color:var(--accent);border:1px solid var(--accent)}
.status{font-size:12.5px;color:var(--muted)}
#fb{display:none;margin-top:10px}
#fb textarea{font-family:var(--mono);font-size:12px;min-height:130px}
/* ── 결정 시트 전용 ── */
.item{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px 16px;margin-bottom:11px}
.item.on{border-color:var(--accent);background:var(--soft)}
.itop{display:flex;gap:10px;align-items:flex-start}
.itop input[type=checkbox]{width:17px;height:17px;margin-top:3px;accent-color:var(--accent);flex:0 0 auto}
.ttl{font-size:14.5px;font-weight:700;margin:0}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.tag{font-family:var(--mono);font-size:11px;padding:2px 7px;border-radius:5px;
border:1px solid var(--line);color:var(--muted);background:var(--bg)}
.tag.lane{border-color:var(--accent);color:var(--accent)}
.tag.strong{font-weight:700}
.det{font-size:13px;color:var(--muted);margin:7px 0 0}
.det b{color:var(--text)}
details{margin-top:7px}
summary{cursor:pointer;font-size:12.5px;color:var(--accent)}
.tally{position:sticky;bottom:0;background:var(--panel);border:1px solid var(--line);
border-radius:10px;padding:12px 16px;margin-top:18px}
table.sum{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:8px}
table.sum th,table.sum td{text-align:left;padding:4px 8px;border-bottom:1px solid var(--line)}
table.sum td.n{font-family:var(--mono);text-align:right}
@media print{.tally,button{display:none}}
"""

# ── 감사 HIGH-1 (2026-09-04) 대응 ────────────────────────────────
# json.dumps 는 '<' 를 이스케이프하지 않는다. HTML 파서는 JavaScript 문자열보다
# 먼저 대소문자 무관 </script> 를 종료 태그로 처리하므로, 데이터 안의 '</script>' 가
# script raw-text 문맥을 탈출해 저장형 XSS 가 된다.
# Edge 152 + Playwright 에서 html[data-vibe-proof]=="1" 실행이 실제로 확인됐다.
#
# 백슬래시를 chr(92) 로 만든다 — 소스에 리터럴 백슬래시를 쓰면 편집 도구·셸·
# heredoc 의 이스케이프 층을 지나며 조용히 '<' 자기 자신으로 접혀 치환이 무의미해진다.
# (이 파일을 고치다 실제로 두 번 그렇게 깨졌다.)
_BS = chr(92)
_INLINE_JSON_ESCAPES = (
    ("<", _BS + "u003c"),
    (">", _BS + "u003e"),
    ("&", _BS + "u0026"),
    (chr(0x2028), _BS + "u2028"),   # JS 에서 줄바꿈으로 취급되어 문자열을 깬다
    (chr(0x2029), _BS + "u2029"),
)


def esc(s):
    """S4 — HTML 텍스트·속성 문맥용 이스케이프.

    <script> 안(raw text 문맥)에는 절대 쓰지 말 것 — json_for_inline_script() 를 쓴다.
    """
    return html.escape(str(s), quote=True)


def json_for_inline_script(obj):
    """<script> 안에 JSON 을 넣는 유일한 직렬화 경로.

    JSON 문자열 안의 \\uXXXX 는 파싱 후 원래 문자로 복원되므로 데이터 의미는 보존된다.
    """
    s = json.dumps(obj, ensure_ascii=False)
    for src, dst in _INLINE_JSON_ESCAPES:
        s = s.replace(src, dst)
    return s


def page(title, body, script=""):
    """자체완결 단일 HTML. 외부 참조 0."""
    return (
        '<!doctype html>\n<html lang="ko"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{esc(title)}</title>\n<style>{CSS}</style></head><body>"
        f'<div class="wrap">{body}</div>'
        + (f"<script>\n{script}\n</script>" if script else "")
        + "</body></html>\n"
    )
