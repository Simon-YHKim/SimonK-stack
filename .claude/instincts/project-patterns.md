# 프로젝트별 반복 패턴

> **목적**: 각 프로젝트가 가진 고유한 관용·제약·API·데이터 모델·명명 규칙을 기록한다.
> **갱신 규칙**: 새 프로젝트 진입 시 섹션 추가. 패턴이 바뀌면 수정.
> **읽는 시점**: 프로젝트 루트에서 새 세션 시작할 때 이 파일과 프로젝트 `CLAUDE.md` 를 함께 참조.

---

## 템플릿

```
## <project-name>

- **스택**: 언어, 프레임워크, DB, 호스팅
- **도메인 용어**: 특수 용어 정의
- **데이터 모델 핵심**: 주요 엔티티·관계
- **API 관용**: 명명·응답 포맷·에러 처리
- **빌드/테스트**: 실행 명령어, CI 링크
- **금기**: 건드리면 안 되는 곳
- **최근 업데이트**: YYYY-MM-DD
```

---

## 프로젝트 목록

## 전역 — 웹 디자인 철학 (모든 프로젝트 공통)

- **참조 skill**: Impeccable (pbakaus), Supanova Design Skill (uxjoseph)
- **최근 업데이트**: 2026-04-16

### 디자인 워크플로 (반드시 지킬 것)
1. **레퍼런스 먼저 추천** — 유사 제품 3-5개. 반드시 접속 가능한 URL 포함
2. **사용자가 방향 선택** — "이런 느낌이 좋다" or "다른 것 보여줘"
3. **폰트 선택권 제공** — Google Fonts 미리보기 URL 포함. AI는 추천만
4. **21st.dev 등 UI 구성요소** — 사용자에게 선택지 + URL 제시
5. **사용자가 "알아서 해" 하거나 갈피 못 잡을 때만** AI 단독 진행
6. 절대 레퍼런스 확인 없이 바로 코드 작성 금지

### 링크 제공 규칙
- 레퍼런스 추천 시 반드시 접속 가능한 URL을 함께 출력
- 폰트 추천 시 Google Fonts 미리보기 링크 포함
- 레퍼런스 탐색용 사이트:
  - https://dribbble.com/
  - https://www.awwwards.com/
  - https://www.lapa.ninja/
  - https://21st.dev/ (UI 구성요소 프롬프트/코드)
- 폰트 탐색: https://fonts.google.com/

### AI Slop 방지 3원칙 (순서대로)
1. **불필요한 것 제거** — 이모지 아이콘, 장식, 과잉 요소 삭제
2. **모노톤 색상** — UI 색상 3개 이내 (accent 1 + text black/white + 보조 1)
3. **레퍼런스에서 착안** — Dribbble/Awwwards 참조하되 자체 방향 추구

### 금기
- Inter 폰트 (AI 생성 티 남) → 한국어: Pretendard, 영어: 대안 산세리프
- pure black/gray → 반드시 tinted neutrals (violet/blue tint)
- 이모지를 아이콘 대용으로 사용
- skill-tag 등에 multi-color (4색+)
- bounce/elastic easing (구식 느낌)
- 카드 중첩 패턴

### 랜딩 페이지 필수 구조
- **Nav**: 투명 배경 → 스크롤 시 backdrop-filter 불투명 전환. 경계선 없음
- **Hero**: 한 문장 메인 카피 (3초 이해) + 행동 유도장치(CTA 버튼 or 입력창). Pretendard + word-break: keep-all
- **Feature**: 핵심 기능 3-4개. 아이콘 없이 텍스트만. 카드 또는 그리드
- **하단 CTA**: 반드시 존재. 방문자가 마지막에 할 행동을 명확히
- **Footer**: 로고 + 링크 그룹. 최소한으로

### 매 섹션 검증 질문
- "이 섹션이 사용자를 다음 단계로 이동시키는가?" → No면 삭제

### 한국어 타이포그래피
- font: Pretendard Variable (CDN: cdn.jsdelivr.net/gh/orioncactus/pretendard)
- word-break: keep-all
- 코드: JetBrains Mono
