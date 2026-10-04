# IAP Sandbox 테스트 체크리스트

상품 등록 후 **반드시** sandbox에서 구매 흐름을 끝까지 돌려본다. 스토어 등록만으로는
영수증 검증·갱신·환불 경로가 검증되지 않는다.

## App Store (StoreKit) sandbox

- [ ] App Store Connect → Users and Access → **Sandbox Testers** 에 테스트 계정 생성 (실제 기기의 Apple ID와 분리)
- [ ] 기기 설정 → App Store → 로그아웃 후, 구매 시점에 sandbox 계정으로 로그인
- [ ] 상품 ID가 코드의 product identifier와 **정확히** 일치 (대소문자·점 위치)
- [ ] 구독 갱신 가속: sandbox는 1개월=5분, 1년=1시간 등 압축 — 갱신 이벤트 수신 확인
- [ ] **Ask to Buy** (자녀 승인) 흐름 — 14-17 미성년 대상이면 필수 검증
- [ ] 영수증 검증은 production 먼저 → 21007 응답 시 sandbox로 폴백 (Apple 권장 단일 엔드포인트)
- [ ] 복원(restore purchases) 동작 — non_consumable / auto_renewable 재설치 후 복원
- [ ] StoreKit Configuration File로 로컬 시뮬레이터 테스트도 병행 (네트워크 없이 빠른 회귀)

## Google Play Billing sandbox

- [ ] Play Console → Setup → **License testing** 에 테스터 Gmail 등록 (실제 청구 없이 구매 가능)
- [ ] 앱을 **내부 테스트 트랙**에 업로드 — IAP는 서명된 트랙 빌드에서만 동작 (debug 빌드 불가)
- [ ] 테스트 카드: "Test, always approves" / "Test, always declines" 로 성공·실패 양쪽 검증
- [ ] 구독 갱신 가속: Play sandbox도 주기 압축 (1주=5분 등) — 갱신/만료 확인
- [ ] **Real-time Developer Notifications (RTDN)** Pub/Sub 토픽 수신 — 서버가 갱신·취소·환불 이벤트를 받는지
- [ ] `purchaseToken` 서버 검증 (Google Play Developer API) — 클라이언트 신뢰 금지
- [ ] 환불/취소 후 entitlement 회수 동작
- [ ] 업그레이드/다운그레이드 proration mode 검증 (IMMEDIATE_WITH_TIME_PRORATION 등)

## 양 스토어 공통

- [ ] 상품 ID는 **영구·전역** — 한 번 만들면 삭제해도 재사용 불가. 오타 발견 시 새 ID로
- [ ] 가격 변경은 기존 구독자에게 즉시 적용 안 됨 (스토어별 사전 고지 + 동의 흐름 별도)
- [ ] 구독 그룹 내 tier 전환이 새 구독이 아닌 업그레이드로 처리되는지
- [ ] 무료 체험은 계정당 1회 — 재구매 시 체험 미적용 확인
- [ ] 결제 코드 자체 검증은 `payment-integrator` skill의 webhook/영수증 검증 체크리스트로 이어감
