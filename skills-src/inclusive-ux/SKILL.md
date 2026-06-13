---
name: inclusive-ux
description: Use when designing or auditing UI for elderly, low-tech-literacy, or low-vision users — triggers "고령 UX", "시니어 앱", "노인도 쓰는", "저시력", "저문해", "큰 글씨 지원", "다이내믹 타입", "어르신 화면", "accessibility for elderly", "senior UX", "low literacy", "dynamic type", "font scaling", "large touch targets". Produces an inclusive-UX checklist plus concrete component patterns — OS dynamic-type / font-scaling support (iOS Dynamic Type, Android sp, web rem+zoom), reading-level reduction to grade 6 or below in plain language, progressive disclosure for low cognitive load, large-target high-contrast senior layouts (≥48px, no time pressure), guardian-assisted onboarding, and error-tolerant flows. Complements accessibility-audit (WCAG conformance) by focusing on age and literacy rather than checkbox compliance.
version: 0.1.0
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, WebSearch, WebFetch
compatibility: [claude-code]
author: simon-stack
---

# inclusive-ux

고령·저문해·저시력 사용자를 위한 포용적 UX를 설계·점검한다. WCAG 체크박스 준수(=accessibility-audit 담당)와 달리, **나이·문해력·인지부하** 축에서 "실제로 쓸 수 있는가"를 본다.

## When to use / boundaries

**쓴다:**
- 사용자층에 고령자·저시력·저문해·저 tech-literacy가 포함될 때 (정부·의료·금융·공공서비스, 시니어 타깃 앱)
- "글씨가 안 보인다", "어디 눌러야 할지 모르겠다", "복잡하다" 류 피드백
- CLAUDE.md §20 페르소나 시뮬에서 고령/유아 축 점검이 필요할 때
- 온보딩·결제·에러 플로우를 시니어가 막힘없이 통과해야 할 때

**안 쓴다 (다른 skill로):**
- WCAG 2.2 적합성 등급(A/AA/AAA) 정식 감사 → `accessibility-audit`
- 스크린리더(VoiceOver/TalkBack) 전용 심화 → accessibility-audit + 실기기 QA
- 디자인 시스템 토큰 수립 → `design-system-keeper`
- 순수 미관·AI-slop 점검 → `design-review`

이 skill은 위와 **보완** 관계다. 중복 점검 금지 — 여기선 age/literacy만.

## 선행 체크 (precheck)

스택을 먼저 식별해 어느 패턴 섹션을 쓸지 정한다.

```bash
# 스택 판별
test -f package.json && grep -qE '"react-native"|"expo"' package.json && echo "STACK=rn"
test -f package.json && grep -qE '"next"|"react-dom"' package.json && echo "STACK=web"
ls ios/*.xcodeproj 2>/dev/null && echo "STACK=ios-native"

# 글꼴 스케일을 끄는 안티패턴 스캔 (있으면 즉시 플래그)
grep -rn "allowFontScaling={false}" src/ app/ 2>/dev/null          # RN: 전역 비활성 금지
grep -rn "user-scalable=no\|maximum-scale=1" . --include="*.html" 2>/dev/null  # web: 줌 차단 금지
grep -rni "px" src/ --include="*.css" 2>/dev/null | grep -i "font-size" | head  # web: font-size 고정 px
```

`user-scalable=no` 또는 전역 `allowFontScaling={false}`가 잡히면 **다른 어떤 작업보다 먼저** 제거한다 (확대 자체를 막는 치명적 배제).

## 7-축 인클루시브 체크리스트

| 축 | 기준 | 실패 신호 | 검증 |
|---|---|---|---|
| 1. 글꼴 스케일 | OS 설정 200%까지 레이아웃 안 깨짐 | 고정 px, scaling 비활성 | OS 폰트 최대로 올려 스샷 |
| 2. 명도 대비 | 본문 4.5:1, 큰 글씨 3:1 (시니어 권장 7:1) | 회색 위 연회색 | 대비 계산기 |
| 3. 터치 타깃 | ≥48×48dp (시니어), 간격 ≥8dp | 작은 아이콘, 밀착 버튼 | 측정 |
| 4. 문해 수준 | 학년 ≤6, 평이한 말 | 전문용어·한자어·영어약어 | Flesch-Kincaid / 학년 추정 |
| 5. 인지 부하 | 화면당 1차 행동 1개, 점진적 공개 | 한 화면 폼 10칸 | 화면당 행동 카운트 |
| 6. 시간 압박 없음 | 타임아웃 없거나 연장 가능 | 자동 로그아웃 30초 | 카운트다운 탐색 |
| 7. 오류 관용 | 되돌리기·재시도·보호자 도움 | 비가역 삭제, 영구 오류 | 에러 경로 워크 |

## Workflow

### 1. OS 다이내믹 타입 / 폰트 스케일 지원

확대를 **수용**하되 극단값에서 레이아웃이 깨지지 않게 상한만 둔다. 전역 비활성은 금지.

**iOS (SwiftUI):** 기본 `Text` + 시스템 폰트는 iOS 14+에서 자동 스케일. 커스텀 값은 `@ScaledMetric`, 상·하한은 `dynamicTypeSize(...)`.

```swift
struct CardView: View {
  @ScaledMetric var iconSize: CGFloat = 24   // 폰트 설정 따라 비례 확대
  var body: some View {
    Label("결제하기", systemImage: "creditcard")
      .font(.title2)                          // 시멘틱 폰트 = 자동 Dynamic Type
      .dynamicTypeSize(.large ... .accessibility3) // 하한~상한만 제한, 끄지 않음
  }
}
```

**Android:** 텍스트 크기는 항상 `sp`(scale-independent), 컨테이너는 `dp`. Compose는 `MaterialTheme.typography` 사용 시 자동. `fontScale` 무시(고정 sp 금지)하지 말 것.

**React Native / Expo:** `allowFontScaling`은 기본 true — 유지. 레이아웃 방어는 `maxFontSizeMultiplier`(0.59+)로 상한만.

```tsx
// 전역 상한 1회 설정 (App.tsx 진입부)
import { Text, TextInput } from 'react-native';
// @ts-ignore - defaultProps 패턴
Text.defaultProps = { ...(Text.defaultProps||{}), maxFontSizeMultiplier: 1.8 };
TextInput.defaultProps = { ...(TextInput.defaultProps||{}), maxFontSizeMultiplier: 1.8 };

// ❌ 금지: allowFontScaling={false} (확대 거부 = 시니어 배제)
// ✅ 권장: 끄지 말고 상한만
<Text maxFontSizeMultiplier={2.0}>금액: 12,000원</Text>
```

**Web:** `font-size`를 `rem` 단위로(루트 기준 확대 반영), 절대 px 고정 금지. 줌을 막지 말 것.

```css
:root { font-size: 100%; }          /* 사용자 브라우저 설정 존중 */
body  { font-size: 1.125rem; line-height: 1.6; }  /* 본문 기본 18px, 줄간격 넉넉 */
.btn  { font-size: 1rem; min-height: 48px; }
```

```html
<!-- ✅ 줌 허용 -->
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- ❌ 절대 금지: user-scalable=no, maximum-scale=1 -->
```

### 2. 문해 수준 낮추기 (목표 학년 ≤6)

원문 → 평이한 말로. 한자어·전문용어·영어약어·이중부정 제거. 한 문장 한 개념.

```
❌ "본인 명의 계좌의 정상 등록 여부를 확인 후 인증을 진행하시기 바랍니다."
✅ "내 계좌가 맞는지 확인할게요. [확인] 버튼을 눌러 주세요."

❌ "결제 수단 미등록 시 거래가 제한될 수 있습니다."
✅ "카드를 먼저 등록해야 결제할 수 있어요."
```

원칙: 능동태 · 짧은 문장(≤15어) · 구체 동사 · 숫자는 아라비아 숫자 · 부정문보다 긍정문. 한국어 학년 추정 도구가 부족하므로 **문장 길이·어려운 단어 비율**로 근사 점검한다.

```bash
# 영문 본문 학년 근사 (textstat). 한국어는 문장당 단어수 휴리스틱.
pip install textstat -q 2>/dev/null
python -c "import textstat,sys; t=open(sys.argv[1],encoding='utf-8').read(); print('FK grade:', round(textstat.flesch_kincaid_grade(t),1))" copy.txt
```

### 3. 점진적 공개 (progressive disclosure) — 인지부하 ↓

한 화면에 다 보여주지 않는다. 화면당 1차 행동 1개. 선택은 단계로 쪼갠다.

```
❌ 가입 화면 1개: 이름·생년·전화·이메일·비번·주소·약관 5개 (필드 10+)
✅ 단계화: [1/3] 전화번호만 → [2/3] 인증번호 → [3/3] 이름
   진행 표시(1/3) 항상 노출. 뒤로 가기 자유. 입력값 보존.
```

```tsx
// 한 번에 한 결정. 큰 진행 인디케이터 + 단일 primary 버튼
<Screen>
  <StepIndicator step={1} total={3} />          {/* "1 / 3" 큰 글씨 */}
  <Question>전화번호를 알려 주세요</Question>
  <BigInput keyboardType="phone-pad" autoFocus />
  <PrimaryButton label="다음" />                 {/* 화면당 primary 1개 */}
</Screen>
```

부가 정보는 접어 두고("더 알아보기"), 기본은 최소만.

### 4. 라지-타깃 시니어 레이아웃

```tsx
// 시니어 버튼 기준: 높이 ≥48dp(권장 56), 폰트 ≥18, 간격 ≥12
const senior = {
  button: { minHeight: 56, paddingHorizontal: 24, borderRadius: 14 },
  label:  { fontSize: 18, fontWeight: '600' },
  gap:    12,                          // 인접 타깃 오접 방지
  contrast: '본문 4.5:1, 시니어 권장 7:1',
};
```

- 아이콘 단독 금지 → **아이콘 + 텍스트 라벨** 병기 (예: ⚙ 대신 "설정 ⚙")
- 색상만으로 의미 전달 금지 → 텍스트·아이콘 보조
- 폰트는 tinted-neutral 위 충분한 대비. 순흑(#000)·순회색 지양(CLAUDE.md), 단 대비는 절대 희생 금지
- 줄간격 1.5 이상, 양끝정렬 금지(좌측정렬)

### 5. 보호자 동반 온보딩 (guardian-assisted)

고령 사용자는 자녀·보호자가 설정을 도와주는 경우가 많다. 두 경로를 모두 둔다.

```
온보딩 분기:
├─ "혼자 설정" → 큰 글씨·단계 최소화 경로
└─ "도움받아 설정" → 공유 링크/QR로 보호자가 원격 설정 → 본인은 인증만
```

- 핵심 설정(알림·연락처·결제)은 보호자 대리 입력 후 본인 1회 확인 패턴 허용
- 민감 동작(결제·삭제)은 보호자 대리 시에도 **본인 명시 확인** 필수 (CLAUDE.md 파괴/비용 게이트와 동일)

### 6. 오류 관용 플로우

```
❌ 잘못 누름 → 즉시 비가역 삭제 → "오류 코드 500"
✅ 잘못 누름 → "정말 지울까요? [취소] [지우기]" → 지운 뒤 "되돌리기"(undo) 5초 노출
✅ 통신 오류 → "연결이 잠깐 끊겼어요. [다시 시도]" (전문 에러코드 숨김, 재시도 1버튼)
```

- 타임아웃 있으면 **연장 가능**하고 카운트다운을 크게 보여주기 (WCAG 2.2.1 정신)
- 입력 실수는 인라인으로 친절히("전화번호는 숫자만 넣어 주세요"), 폼 전체 리셋 금지
- 모든 파괴적 행동에 undo 또는 2단계 확인

## 안티패턴

```
❌ user-scalable=no / maximum-scale=1            → 확대 자체를 차단 (최악)
❌ 전역 allowFontScaling={false}                 → OS 폰트 설정 거부
❌ font-size를 px로 고정                          → 브라우저 확대 무시
❌ 아이콘만 있는 버튼 (라벨 없음)                 → 의미 추측 강요
❌ 색상만으로 상태 표시 (빨강=오류, 라벨 없음)    → 저시력·색각 배제
❌ 화면 하나에 폼 필드 10개                        → 인지 과부하, 이탈
❌ 30초 자동 로그아웃, 연장 불가                  → 느린 사용자 배제
❌ 비가역 삭제, undo 없음                          → 실수 = 데이터 손실
❌ "에러 코드 0x80004005"를 그대로 노출           → 저문해 사용자 공포
❌ 한자어·영어약어 남발 ("PG 미연동 시 거래 fail") → 학년 ↑, 이해 불가
```

## 검증 (verification)

```bash
# 1. 확대 차단 안티패턴이 0건인지 (가장 중요)
grep -rn "user-scalable=no\|maximum-scale=1\|allowFontScaling={false}" . \
  --include="*.html" --include="*.tsx" --include="*.jsx" 2>/dev/null \
  && echo "FAIL: 확대 차단 발견" || echo "PASS: 확대 차단 없음"

# 2. 터치 타깃 최소 높이 누락 의심 (수동 확인 보조)
grep -rn "minHeight" src/ 2>/dev/null | grep -E "minHeight:\s*([0-3]?[0-9])\b" \
  && echo "WARN: 48 미만 minHeight 후보 검토" || echo "OK: 작은 타깃 미발견"
```

수동 검증(필수, 자동화 불가):
- [ ] OS 폰트 크기를 **최대**로 올리고 핵심 화면(온보딩·결제·에러) 스샷 → 잘림·겹침 0
- [ ] 명도 대비 계산기로 본문 ≥4.5:1 확인 (시니어 타깃이면 7:1 목표)
- [ ] 핵심 카피를 학년 ≤6로 다시 읽었을 때 추측 없이 이해되는가
- [ ] CLAUDE.md §20 페르소나 4축(고령·저소득·저 tech-literacy·글로벌)으로 첫 실행+핵심 루프 워크
- [ ] 모든 파괴적 행동에 undo 또는 2단계 확인이 있는가

산출물: 위 7-축 체크리스트 결과표 + 수정한 컴포넌트 패턴 + 안티패턴 제거 diff.

## 참고 (출처)

- iOS Dynamic Type / `@ScaledMetric` / `dynamicTypeSize`: Apple HIG + createwithswift.com, avanderlee.com
- RN `allowFontScaling` / `maxFontSizeMultiplier`(0.59+): RN docs, ignitecookbook AccessibilityFontSizes
- WCAG 2.2.1(타이밍 조정), 2.5.8 Target Size 최소 24px / 2.5.5 권장 44px, Material 48dp, 3.1.5 Reading Level
