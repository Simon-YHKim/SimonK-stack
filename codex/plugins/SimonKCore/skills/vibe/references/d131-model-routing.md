# D-131 후보 · /vibe 2.29.0 모델 배정

2026-11-24 KST · Simon 사용자 지시 · 브랜치의 구현 결정. 허브 원장 반영, 게시와 설치 승인은 별도다.

> gpt의 사용 한도가 복구 되었으니, gpt 6.1 계열들을 모두 6.2 계열로 vibe 스킬을 업데이트 한 뒤에, (astra, sol) 병렬로 최대한 돌려서 gpt 계열 모델을 최대한 활용할수 있게 하자. claude 혼자할필요 없어! 추가로 grmini(agy) 역시 gemini 4 neon, argon, hydrogen 이라는 모델들이 업데이트 되었으니 사용량을 고려해서 바이브 스킬에 편입시키고 작업을 시키자! (gpt 이던, gemini 이던, 항상 x 또는 애용갤의 사용자 후기를 확인하고 실효성을 생각해야해. 애매할때는 사용자 후기를 따러라. 예를들어 '한국어 글 작성은 gemini 가 최고존엄인 듯' 이런식의 문장 같은거)

## 배정과 확인 방법

| 작업 | 기본 선택 | 결과를 받을 때 |
|---|---|---|
| 일상 구현·문서·1차 리뷰 | GPT-6.2 Sol. 검토만 하면 Hydrogen low도 같은 순위 | 수용 조건별 테스트 결과 또는 다른 벤더의 리뷰. stub, 요구사항 누락, 범위 밖 diff 확인 |
| 설계·복잡한 디버깅·연구·에이전트·최종 리뷰 | GPT-6.2 Astra @xhigh. 독립 단계는 Sol과 동시에 배정 | Claude 순서 유지. GPT 두 모델은 한 벤더이며 Codex 한도를 공유 |
| 한국어 산문 | Neon medium 초안, 사용할 수 없으면 Argon high | 다른 벤더가 수치·고유명사·날짜·주장·문장 사이 모순 대조 |
| 코드·설계 보조 / 대량 / 추론 2차 의견 | Neon high / Hydrogen low / Argon high | agy는 제공한 브리프의 텍스트 결과를 한 번 반환. 실행 직전 모델 목록과 포함 사용량 재확인 |
| 화면 조작 | Codex Computer Use 담당은 6.2 Astra | 현재 호스트와 모델이 확인돼야 한다. Bot 우선·로컬 도구·사람 승인 조건 유지. 새 Terra가 나오면 같은 과제로 재평가 |

D-101의 GPT 한 자리 제약과 D-130의 6.1 Sol 공정 예외는 종료한다. 6.1 Terra·Sol과 6 Astra의 과거 원장 키는 보존한다.
D-127 순위는 11월 24일 06:07:33부터 12월 1일 00:00 KST까지다.
Argon의 공개 API 도입 가격이 12월 1일 바뀌므로 그때 재검토한다. 이 단가는 구독 포함 사용량과 별개다.
D-74에 따라 측정값이 85% 이상이거나 불명·오래됨이면 보내지 않는다. 재시도와 병렬 실행은 기존 실행 예산 안에서만 허용한다.

## 근거와 반대 관측

- 로컬에서 Codex 모델 캐시의 6.2 Astra·Sol, 6.1 Terra·Sol을 확인했다. 6.2 Terra는 없었다. 코디네이터가 codex-cli 0.171.0과 Terra probe 성공을 보고했다. 이번에 확인한 agy 1.5.15 목록은 Neon·Hydrogen low/medium/high/xhigh와 Argon low/medium/high를 포함한다. `/usage`는 0턴·0토큰이었고 공유 5시간·주간 창을 확인했다. 사용량 측정은 모델 실행 증거와 구분한다.
- OpenAI의 모델 선택표는 일상 코딩에 Sol, 복잡한 엔지니어링에 Astra를 안내하고 컴퓨터 사용 표에도 6.2 Astra를 첫 자리에 둔다. Codex 기본 문맥 Astra 272K·Sol 500K와 11월 17일 출시는 코디네이터의 출처 조사다. API 문맥 크기와 구분한다. [공식 선택표](https://developers.openai.com/api/docs/guides/model-selection) · [발표 X](https://x.com/OpenAIDevs/status/2122752394002071717) · [Codex 기본 설정 자료](https://www.memorylake.ai/en/blogs/gpt-6-2-astra-vs-sol-codex)
- 코디네이터가 전달한 AA 측정에서 Astra의 Coding Agent Index는 전 세대와 비슷했고 Sol은 6.1 대비 3점 낮았다. SWE-Atlas-QnA 하락과 max effort 환각률 Astra 59%·Sol 55%는 해당 평가 수치다. HN·블로그의 첫 출력 품질 평가는 엇갈렸고 요구사항 생략, 미완 구현을 완료로 보고, 불필요한 수정에 관한 불만도 있었다. 두 X 링크는 여기서 403이어서 수치를 직접 대조하지 못했다. [AA X](https://x.com/ArtificialAnlys/status/2122751016055754830) · [HN 토론](https://news.ycombinator.com/item?id=50535230) · [GPTunneL 후기 모음](https://www.gptunnel.ru/en/blog/gpt-6-2-astra-sol-reviews)
- 코디네이터의 1차 검색에서는 애용갤·X의 한국어 사용기를 직접 찾지 못했다. 이번 추가 검색에서는 애용갤 사용자가 medium~high Sol의 코딩·리뷰 효율을 긍정적으로 평가하면서 UI 기본 결과에는 구체적인 지시가 필요했다고 썼다. 다른 사용자는 Astra의 결과 품질과 함께 엉뚱한 부분에 집중하는 사례를 적었다. 모델·과제가 같은 후기에 우선순위를 둔다. [Sol·Astra 24시간 사용기](https://gall.dcinside.com/mgallery/board/view/?id=ai_utilize&no=192862) · [Astra 사용기](https://gall.dcinside.com/mgallery/board/view/?id=ai_utilize&no=192462)
- Google의 발표는 Neon xhigh의 AA 코딩 지수 1위와 네 단계의 effort를 명시한다. 애용갤의 위젯 제작자는 한 번에 나온 디자인을 좋게 평가했다. 코디네이터 조사에는 잦은 도구 호출·과잉 검증 의견도 있다. [Google 발표](https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301) · [Neon 위젯 사용기](https://gall.dcinside.com/mgallery/board/view/?id=ai_utilize&no=195165) · [코딩 비교](https://bito.ai/blog/gemini-4-neon-vs-carbon-hydrogen/)
- 작문 평가는 갈린다. 긍정 요약은 코디네이터가 전달했고 해당 페이지를 이번에는 열지 못했다. 부정 요약의 원문 제목은 반복적인 정정 문체를 지적한다. 한국어 글의 논리 오류율 측정으로 해석할 근거는 없다. 11월 19일 사용자의 Neon 선호와 한국어 초안 지정에 따라 Neon을 먼저 쓰고 D-126에서 선호됐던 Argon을 보존한다. [부정 후기와 원문 표시](https://www.promppy.com/item/3199544) · [긍정 후기 링크](https://www.promppy.com/item/3191071)
- Hydrogen은 일상 코딩·에이전트 작업에 맞게 설계됐다. 비교 자료에는 Argon에 필적하는 코딩과 많은 단계 수에 관한 평이 있다. Argon은 추론 2차 의견에 배정한다. [Google Hydrogen](https://ai.google.dev/gemini-api/docs/models/gemini-4-hydrogen) · [Google Argon](https://ai.google.dev/gemini-api/docs/models/gemini-4-argon) · [Hydrogen 비교](https://the-decoder.com/googles-gemini-4-hydrogen-outscores-the-bigger-argon-just-four-weeks-after-its-launch/) · [Gemini 비교·12월 가격](https://medium.com/data-science-in-your-pocket/gemini-4-neon-vs-carbon-vs-hydrogen-vs-argon-cd5377c1f812)

## 승격 조건

기존 prospective 24시간 공개 피드백 창과 서로 다른 관측 시점 2개(간격 20시간 이상)를 지킨다.
과거 글의 게시일을 이 PC의 관측 시각으로 소급하지 않는다. 이번 편집은 해당 watch 영수증이나 6.2 전송 canary를 만들지 않았다.
배포 승인에는 후보 소스 SHA와 Claude/Codex 배포 digest의 별도 확인이 필요하다. D-130 허용값은 이 후보를 승인하지 않는다.
