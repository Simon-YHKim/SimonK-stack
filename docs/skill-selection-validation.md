# 스킬 선택 전후 비교

`scripts/evaluate_skill_selection.py`는 **이미 기록한 선택 결과만** 채점하는
표준 라이브러리 기반 오프라인 도구다. 기존 81개 계획·예산·탐색 테스트와 별개이며,
이 도구의 단위 테스트 통과는 Claude/GPT의 실제 선택 정확도를 입증하지 않는다.

```text
python -B scripts/evaluate_skill_selection.py --cases docs/evals/skill-selection-cases.json
python -B scripts/evaluate_skill_selection.py --cases docs/evals/skill-selection-cases.json --results path/to/observations.json
python -B scripts/evaluate_skill_selection.py --compare-hosts --claude-cases path/to/claude-cases.json --claude-results path/to/claude-observations.json --codex-cases path/to/codex-cases.json --codex-results path/to/codex-observations.json
python -B -m unittest discover -s scripts/tests -p test_evaluate_skill_selection.py
```

첫 명령은 관측이 없어 `pending`(종료코드 2)을 반환한다. 두 번째 명령은
사용자가 별도로 수집·검토한 기록을 받아 JSON을 stdout에 출력한다. 파일을 쓰지 않으며,
모델·네트워크·subprocess·스킬 실행을 하지 않는다. 입력 파일당 최대 1 MiB다.

## 관측 계약

케이스 JSON은 `schema_version: 1`과 `cases` 배열이다. 각 케이스는 `id`, `prompt`,
`acceptable`(허용 선택 집합들의 배열), `forbidden`, `kind`(`positive|negative|explicit`)를
가진다. `acceptable` 자체는 비워 둘 수 없지만 `[[]]`는 아무 스킬도 선택하지 않는
대조군이다. 이름은 namespace까지 정확히 일치해야 하며, `vibe`를
`simonk-core:vibe`로 자동 변환하지 않는다. 호스트별 카탈로그에 맞춰 케이스를 준비한다.

동봉한 30개 케이스는 로컬 소스의 canonical 이름을 사용한다. 설명만 주는 통제 실험에서는
모델에 **가장 적합한 주 스킬 하나 또는 스킬 없음(`[]`)**을 선택하도록 지시한다.
하위 도구·보조 스킬의 실행 계획은 묻지 않는다. 정답(`acceptable`, `forbidden`, `kind`)을
제외하고 요청 ID·본문과 고정 카탈로그만 제공하며, 어느 쪽이 수정 전인지도 알리지 않는다.
현재 호스트의 namespace 및 예산에 의해 잘린 설명까지 재현한 native 평가와는 구분한다.

결과 JSON 형식 예시(**관측 완료 증거가 아닌 형식 설명**):

```json
{
  "schema_version": 1,
  "evaluator": {
    "host": "실제 관측 호스트와 버전",
    "model": "실제 관측 모델",
    "effort": "실제 reasoning 설정",
    "observation_kind": "isolated-description-only"
  },
  "conditions": [
    {"id": "before", "catalog_sha256": "64자리 SHA-256", "records": []},
    {"id": "after", "catalog_sha256": "64자리 SHA-256", "records": []}
  ]
}
```

각 `records` 항목은 `case_id`, `selected`(선택한 정확한 이름의 배열), `evidence`
(비어 있지 않은 관측 근거/추적 식별자)다. 답을 추정·자동 채움하지 않는다.
두 조건은 동일한 host/model/effort 아래에서 비교하며, 카탈로그를 고정하고 실제
파일의 SHA-256을 `catalog_sha256`에 기록한다. 실행자는 원문 관측과 카탈로그의
일치를 별도로 검증해야 한다. 도구는 해시 형식만 검사하므로
`catalog_binding_verified`, `evidence_authenticity_verified`,
`native_compatibility_verified`는 항상 false다. 자기 기입한 `native-session` 라벨은
인증이 아니다. 출력의 cases/results 해시는 채점에 사용한 JSON의 정규화된 내용에
대응하며, 원본 파일 바이트 해시나 외부 증거의 진위를 대신하지 않는다.

관측 종류는 `native-session`(실제 호스트), `isolated-description-only`(격리된 설명
선택 실험), `static-review`(정적 검토)다. 종류를 섞어 같은 평가로 보고하지 않는다.
각 Claude/GPT 및 reasoning 설정은 별도 결과 파일로 남긴다. 축약되지 않은 설명만
제공한 실험을 호스트 컨텍스트 예산/설치/플러그인 활성화 검증으로 간주하지 않는다.

## Claude·Codex 교차 호스트 비교

### 배포 전 정적 본문 패리티

선택·실행 실측에 앞서 `scripts/audit_host_skill_parity.py`로 Claude 후보,
Codex 오버레이, D-29 일반 스킬 subset의 고정 SHA-256 영수증과 출처를 검증한다.
세 패키지 경로와 각 영수증 SHA-256을 `--claude`, `--claude-digest`,
`--codex-overlay`, `--overlay-digest`, `--codex-subset`, `--subset-digest`로
전달한다. 소스 파일·설치본은 변경하지 않는다.

2026-09-30 `/vibe` 2.12.15 후보에서 Claude 182개와 Codex 177개 중 공통
본문 176개와 공통 payload 파일 612개가 바이트까지 동일했다. payload 수에는
본문 파일도 포함하며, `SKILL.md` 외의 공통 scripts/references/assets/evals도 검사한다.
`zoom-out` 하나는 Claude 전용 수동 호출 frontmatter
한 줄만 제거하고 Codex의 동등한 수동 호출 정책 파일로 투영됐다. D-29 결정에
따라 안전 훅 미지원 4개와 종속 `unfreeze` 1개는 Codex 일반 subset에서
명시적으로 제외된다. 공통 본문·보조 파일 변형, 추가·누락 스킬,
`zoom-out`의 추가 변형이나 출처 영수증 불일치는 검사 실패다.

이 PASS는 **정적 콘텐츠 보존**만 뜻한다. 5개 제외 스킬의 안전 동등성,
설명 축약에 따른 선택률, 모델/effort·산출물 품질은 아래의 호스트별
실측을 통과해야 한다. 새 후보의 격리 호스트 적재·등록은
[설치 기록](INSTALL.md)에
별도로 남겼으며 실제 작업 동작을 증명하지 않는다. 검사 출력의 `host_behavior_verified`,
`selection_quality_verified`, `installation_ready`는 항상 `false`다.

`--compare-hosts`는 호스트별 케이스·관측 파일 네 개를 **읽기만** 한다. 각 파일은
위와 같은 스키마를 쓰되 `evaluator.host`가 각각 `Claude...`, `Codex...`로
시작해야 한다. 양쪽 케이스의 ID·요청 원문·`kind`가 같아야 하고
`observation_kind`도 같아야 한다. 호스트마다 실제 등록 이름과 namespace가
다를 수 있으므로 `acceptable`·`forbidden`은 호스트별로 작성한다. 대신 같은
과제의 합격 여부를 비교한다. 서로 다른 이름을 무조건 같은 스킬로 간주하지 않는다.

도구는 각 호스트의 `before`/`after`를 독립 채점한 뒤, 둘 다 모든 `after`
케이스에 합격하고 회귀가 없어야 `recorded_host_comparison_passed`를 낸다.
`claude_only_correct_case_ids`·`codex_only_correct_case_ids`는 한쪽만 통과한
케이스를 드러낸다. 누락은 `incomplete`(종료코드 2), 오답·회귀는
`recorded_host_comparison_failed`(1)다. 비교 통과는 기록된 **선택**의
정답성만 뜻한다. 양쪽 모두 오답이면 통과시키지 않는다.

실제 성능 저하 없음은 별도 검증이 필요하다. 동일한 대표 요청에서 각 호스트의
스킬 로딩 본문·참조, 요청/실효 모델·effort, 실행 산출물, 테스트, 독립 리뷰,
구독 포함·초과 과금 차단을 관측해야 한다. 이 채점기는 호스트 실행·원문 증거의
진위·카탈로그 해시와 실제 로딩의 연결을 확인하지 않는다. 따라서 교차 호스트
결과에서도 `native_compatibility_verified`, `evidence_authenticity_verified`,
`catalog_binding_verified`는 항상 false다. 현재 저장소에 실제 Claude/Codex
관측 파일은 동봉하지 않았으므로, 이 기능 추가만으로 성능 동등성을 선언하지 않는다.

## 판정과 제한

선택한 집합이 허용 집합 중 하나와 정확히 같고 금지 스킬이 없어야 정답이다.
순서는 무관하지만 중복은 거부하며, 추가 스킬을 선택한 상위 집합은 정답이 아니다.
양쪽 조건·모든 케이스가 있어야 완전 비교다. 누락은 `incomplete`(2)이며, 관측된
오답과 구분한다. before 정답 → after 오답은 `regressions`로 기록한다.
완전 비교에서 after 전체 정답·회귀 0건이면 `recorded_comparison_passed`(0),
그 외는 `recorded_comparison_failed`(1)다. 잘못된 입력은 `invalid_input`(1)이다.
정적 검토도 **기록된 답의 비교**는 통과할 수 있지만, 모델 실측이나 전체 스킬 품질
통과를 뜻하지 않는다. 중복/미상 ID, 비어 있는 근거, 잘못된 선택 형식은 거부한다.

추가 과금 $0을 유지한다. 과거 Grok HOLD는 영구 금지가 아니지만, 새 실호출 전
최신 쿼터·선택 모델의 구독 포함·추가 과금 차단을 다시 확인한다. Claude/GPT 읽기 전용 평가에 대한
사용자의 조건부 허용도 구독 포함·추가 과금 차단 확인 후에만 별도 실행자가 사용한다.
이 도구나 그 성공 결과는 호출 권한·결제 승인·제공자 사용 가능성의 증거가 아니다.
