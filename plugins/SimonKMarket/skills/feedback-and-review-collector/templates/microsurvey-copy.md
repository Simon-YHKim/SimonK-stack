# 마이크로설문 카피 (EN ↔ KO 쌍)

한 화면 = 한 질문. 바텀시트로 띄우고, 1탭 응답, "나중에/닫기"는 항상 노출. 모달을 노드/콘텐츠 위에 덮지 말 것. EN 이 canonical, KO 는 동일 의미로 번역.

> 사용법: 제품 상황에 맞게 한 지표만 골라 위젯에 넣는다. 척도·트리거는 그대로 코드에 매핑. 자유응답(verbatim)은 점수 응답 직후 1개만, 선택 입력으로.

---

## NPS (관계·애착) — 분기 추적용

| 요소 | EN | KO |
|---|---|---|
| 질문 | How likely are you to recommend this app to a friend? | 이 앱을 친구에게 추천할 가능성은 얼마나 되나요? |
| 척도 라벨(0) | Not at all likely | 전혀 아님 |
| 척도 라벨(10) | Extremely likely | 매우 그렇다 |
| 후속(Promoter 9-10) | Great to hear — what did you like most? | 좋아요! 어떤 점이 가장 마음에 드셨나요? |
| 후속(Passive 7-8) | Thanks — what would make it a 10? | 감사합니다. 무엇이 더 있으면 10점이 될까요? |
| 후속(Detractor 0-6) | Sorry to hear that — what went wrong? | 불편하셨군요. 무엇이 아쉬우셨나요? |
| 닫기 | Maybe later | 나중에 |

> Detractor 후속은 **인앱 피드백 폼**으로 연결. 스토어로 보내지 않는다.

---

## CSAT (특정 경험 직후) — 거래/지원 완료 시

| 요소 | EN | KO |
|---|---|---|
| 질문 | How satisfied were you with that experience? | 방금 경험에 얼마나 만족하셨나요? |
| 척도 | 1 (Very unsatisfied) — 5 (Very satisfied) | 1 (매우 불만족) — 5 (매우 만족) |
| 후속(4-5) | Glad it worked for you. | 도움이 되었다니 다행이에요. |
| 후속(1-2) | What would have made it better? | 무엇이 더 나았으면 좋았을까요? |
| 닫기 | Skip | 건너뛰기 |

> 4-5 응답은 만족 시그널로 게이트에 전달, 1-2 응답은 사유 수집 후 피드백 채널로.

---

## CES (마찰·사용성 진단)

| 요소 | EN | KO |
|---|---|---|
| 질문 | How easy was it to get what you needed? | 원하시는 것을 처리하기가 얼마나 쉬웠나요? |
| 척도 | 1 (Very difficult) — 7 (Very easy) | 1 (매우 어려움) — 7 (매우 쉬움) |
| 후속(1-3) | Where did you get stuck? | 어느 단계에서 막히셨나요? |
| 닫기 | Not now | 다음에 |

---

## 불만 유저용 인앱 피드백 폼 (스토어 대체 경로)

| 요소 | EN | KO |
|---|---|---|
| 헤더 | Tell us what's not working | 불편한 점을 알려주세요 |
| 안내 | Your note goes straight to the team — not a public review. | 남겨주신 내용은 공개 리뷰가 아니라 팀에게 바로 전달됩니다. |
| 입력 | Describe the issue (optional) | 어떤 점이 불편했는지 적어주세요 (선택) |
| 전송 | Send | 보내기 |
| 확인 | Thanks — we read every message. | 감사합니다. 모든 메시지를 읽고 있어요. |

---

## 만족 유저용 리뷰 요청 (게이트 통과 시에만)

네이티브 시트는 OS 가 직접 그리므로 커스텀 문구가 안 들어간다. 시트 호출 **전** 선택적 인트로 1줄만 둘 수 있다. 점수를 특정해 요구하지 않는다.

| 요소 | EN | KO |
|---|---|---|
| 인트로(선택) | Enjoying the app? A quick rating helps a lot. | 앱이 마음에 드셨나요? 짧은 평가가 큰 도움이 됩니다. |

> 금지: "5점 주세요", 보상 제공, 시트 뒤 강제 "고마워요" 화면. 인트로 후 곧장 `StoreReview.requestReview()` 만 호출.
