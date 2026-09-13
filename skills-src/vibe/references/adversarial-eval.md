# 주기 적대평가 — 영역별 최적 레인을 데이터로 정한다

> SKILL.md 에서 옮겼다(2026-09-13) — SimonK-stack CI 의 본문 500줄 상한(E007) 때문이다. 내용은 그대로다.


**왜 필요한가.** 라우팅 표는 사람이 손으로 정한 값이고, 모델은 계속 바뀐다. 그런데 실제 라운드는
늘 1순위만 태우므로 **2순위 이하는 영원히 관측이 안 쌓인다.** 탐색 슬롯 1개로는 메우지 못한다.

**어떻게.** 라운드와 별개로, **정답이 기계로 확인되는 문제**를 같은 조건에 두 레인이 풀고
**제3의 레인이 채점**한다.

```bash
python "<skill>/scripts/adversarial_eval.py" --due        # 평가할 때가 됐나 (주기 14일)
python "<skill>/scripts/adversarial_eval.py" --validate   # 정답 생성기 점검. 비용 0
python "<skill>/scripts/adversarial_eval.py" --plan       # 대진표만. 비용 0
python "<skill>/scripts/adversarial_eval.py" --run --dry  # 전 구간 배선 점검. 비용 0
python "<skill>/scripts/adversarial_eval.py" --preflight  # 벤더 가용성. 아주 싼 호출 4회
python "<skill>/scripts/adversarial_eval.py" --run        # 실제 회차
python "<skill>/scripts/adversarial_eval.py" --report     # 누적 점수 + 제안
```

**순서는 `--validate` → `--plan` → `--run --dry` → `--run` 이다.** 앞의 셋이 비용 0 이라
실제 호출 전에 정답·대진·배선을 전부 확인할 수 있다.

⚠ **실행 경로가 Orca 워커가 아니다 — 벤더 CLI 직행이다**
(`claude -p` · `codex exec` · `agy --print` · `grok -p`). 그래서 라우팅 표의
**"grok·gemini 는 effort 지정 불가"가 여기에는 해당하지 않는다** — 그건 Orca 가 `--model` 을
거부한다는 뜻이고, CLI 직행에는 `--model`·`--effort` 가 둘 다 있다(2026-09-13 실측:
`agy --effort low|medium|high`, `grok --reasoning-effort`). **이 사실로 표를 고치지 말 것 —
표는 워커 경로를 적는다.** 대신 이 경로에는 워크트리 격리·`worker_done`·게이트가 없고
전부 read-only 로 돈다.

⚠ **G12 — 가용성은 쿼터로 알 수 없다.** 2026-09-13 1회차 프리플라이트 실측:

```
claude ✅ ok      codex ✅ ok      gemini ✅ ok (agy 경유)
grok   ❌ 잔액 소진(402)           gemini 단독 CLI ❌ IneligibleTierError → agy 로만 닿는다
```

**쿼터 %로는 grok 도 여유 있어 보인다** — 못 쓰는 이유가 쿼터가 아니기 때문이다.
쓸 수 있는 벤더가 3개 미만이면 G10 을 어기느니 **라운드를 통째로 포기한다**(종료코드 2).

| 규율 | 내용 |
|---|---|
| 정답 | `eval/probes.json` 의 `truth_cmd` **+ `truth_post`** 가 만든다. **채점자가 정답을 짓지 않는다** |
| `truth_post` | truth_cmd 의 출력을 **질문이 물은 단위**로 바꾼다(`count_suffix` · `exit_to_yesno` · `grep_yesno` · `prefix_count` · `grep_count` · `raw`). ⚠ 2026-09-13 까지 **선언만 있고 구현이 없었다** — 세는 문제에 파일 목록이 정답으로 들어가고, 부재 확인 문제는 `cat-file -e` 의 종료코드 1 이 "정답 생성 실패"로 처리돼 정답이 아예 안 만들어졌다. **지표가 질문보다 좁으면 0 은 안전이 아니라 침묵이다** |
| 손 핀 금지 | `manual:<값>` 으로 정답을 박아두지 않는다. 저장소가 바뀌어도 안 바뀌므로 언젠가 반드시 거짓이 되고, 그때 평가가 **조용히 거꾸로 채점한다.** 판정이 복잡하면 `eval/truth/*.py` 로 생성기를 쓴다 |
| G10 | 채점자는 두 생산자와 **벤더가 다르다.** 벤더 3개를 못 채우면 그 문제는 건너뛴다 |
| 채점 순서 | **"둘 다 틀렸을 가능성"을 먼저 본다.** 확인이 아니라 반증이 기본 동작이다 |
| UNKNOWN | 틀린 확답보다 **덜** 감점한다. 모르는 걸 아는 척하는 쪽이 더 나쁘다 |
| 범위 | 답 직전에 "무엇을 어디까지 셌는지" 한 줄. G6 와 같은 규율 |
| 표 수정 | **자동으로 안 한다.** 제안만 낸다. 승인은 사람이 한다 |
| 데몬 | **만들지 않는다.** `--due` 가 알릴 뿐이고 실행은 사람이 한다 |

**문제를 늘릴 때**: 답이 한 줄로 떨어져야 한다(숫자·경로·yes/no). 서술형은 채점이 주관이 되어
쓸모가 없다. 그리고 `domain` 은 라우팅 표의 클래스와 이어야 결과를 표에 되먹일 수 있다.

**제안은 영역별 관측 3회 이상일 때만 나온다.** 부족하면 "관측 부족"이라고 명시 출력한다 —
침묵하지 않는다. `--dry` 행과 채점 실패 행은 **점수에서 제외**된다(`mode` · `grader_failed` 필드).

**건너뛴 probe 는 조용히 넘기지 않는다** — 왜 건너뛰었는지(G10 위반 · 정답 생성 실패 ·
벤더 부족) 회차 끝에 목록으로 찍는다. 조용한 축소가 "다 돌았다"로 읽히는 것을 막는다.
