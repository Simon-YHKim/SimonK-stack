# SimonKDesign

![version](https://img.shields.io/badge/version-0.2.0-5b8cff) ![license](https://img.shields.io/badge/license-MIT-green) [![validate](https://github.com/Simon-YHKim/SimonKDesign/actions/workflows/validate-plugin.yml/badge.svg)](https://github.com/Simon-YHKim/SimonKDesign/actions/workflows/validate-plugin.yml)

> 예술·디자인 작업 오케스트레이션 플러그인

오케스트레이션 진입점: `/skdesign`

### 사용 예시

```
/skdesign 우리 카페 로고 만들어줘
/skdesign 내 앱 메인 화면 디자인 잡아줘
/skdesign 인스타용 카드뉴스 시리즈 만들어줘
```

인자 없이 `/skdesign` 만 입력하면 무엇을 만들지부터 물어본다.

## 설치
```
/plugin marketplace add Simon-YHKim/SimonKDesign
/plugin install simonk-design@simonk-design
```

## 의존
SimonKCore 권장 동반 설치 (agent-delegate, model-router, instincts 등 공유 인프라). 없으면 일부 기능 제한.

## 구조
- `skills/` — 도메인 스킬
- `agents/` — 서브에이전트
- `commands/` — 슬래시 커맨드

## 수록 스킬 (19개)

진입점 `/skdesign` 가 의도를 진단해 아래 스킬로 라우팅합니다. 개별 직접 호출도 가능.

`coloring-art` · `consistency-guard` · `dashboard-review` · `design-consultation` · `design-html` · `design-review` · `design-shotgun` · `design-system-keeper` · `design-system-page` · `logo-generator` · `photo-album` · `plan-design-review` · `remotion-best-practices` · `scientific-paper` · `simon-design-first` · `skdesign` · `slides` · `social-graphic` · `stitch-design-flow`

## 기여

스킬 추가·수정은 **평가셋(`evals/cases.json`) + CI 품질게이트**를 통과해야 한다.
자세한 절차·스키마는 [`CONTRIBUTING.md`](./CONTRIBUTING.md) 참고.

```bash
python -B -m unittest discover -s .github/skill-ci -p test_run_ci_encoding.py
python -B .github/skill-ci/run_ci.py   # 머지 전 로컬 게이트
```

품질 게이트는 자식 Python을 UTF-8로 실행하고 결과를 엄격하게 해석하므로
Windows 기본 CP949 콘솔에서도 같은 검증을 수행한다. 모델/API 호출은 없다.

## 라이선스

MIT. © Simon Kim (Simon-YHKim).
