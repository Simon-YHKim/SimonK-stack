# design.md — {{PROJECT_NAME}}

> 이 프로젝트의 시각·UX 원칙. 디자인 작업 시 `simon-design-first` skill 이 이 파일을 first 참조한다.

## Tone

**{{TONE_ANCHOR}}**

한 단어로: 프로페셔널 / 친근 / 프리미엄 / 실험적 — 이 중 하나.

## References

1. {{REF_1}}
2. {{REF_2}}
3. {{REF_3}}
{{#REF_4}}4. {{REF_4}}{{/REF_4}}
{{#REF_5}}5. {{REF_5}}{{/REF_5}}

이 사이트들의 *느낌* 을 따른다. 그대로 복제하지 않는다.

## Palette (≤ 3 colors)

| 역할 | 값 | 설명 |
|---|---|---|
| Accent | `{{ACCENT_HEX}}` | 강조·CTA·링크 |
| Text | `{{TEXT_HEX}}` | 본문 (pure black 금지 — tinted neutral) |
| Background | `{{BG_HEX}}` | 배경 (pure white 금지) |

3색을 넘기지 않는다. AI slop 의 가장 빠른 길은 multi-color.

## Fonts

- **한국어**: {{KO_FONT}} (기본: Pretendard)
- **영문**: {{EN_FONT}} (Inter 금지 — AI 티 남)
- **제목용** (선택): {{HEADING_FONT}}

## 금지

- ❌ Inter, pure black (#000), pure white (#FFF)
- ❌ 이모지 아이콘 (lucide / heroicons / material 사용)
- ❌ bounce / elastic easing
- ❌ 4색 이상의 multi-color UI
- ❌ Gradient-on-everything

## Approved 패턴

{{APPROVED_PATTERNS}}

---

> 만들어진 날: {{CREATED}}
> 갱신: 디자인 방향이 바뀌면 이 파일 먼저, 그 다음 컴포넌트.
