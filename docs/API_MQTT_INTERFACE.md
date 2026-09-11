# Smart Sorting System 통신 인터페이스

Smart Sorting System에서 구현한 REST API와 MQTT 통신 구조를 정리한 문서입니다.

시스템은 **관리자 Web**, **작업자 Qt**, **Raspberry Pi·Arduino 제어부**, **ASP.NET Core Server**로 구성되며, 기능의 성격에 따라 REST API와 MQTT를 구분하여 사용합니다.

- REST API: 로그인, 조회, 설정, 생산 작업 제어, 이력 확인, 이미지 업로드
- MQTT: 제품 감지, 장비 상태, 생산 현황, 알림 등 실시간 이벤트 전달

---

## 1. 전체 통신 구조

```text
관리자 Web
  ↕ REST API
  ↓ MQTT
ASP.NET Core Server
  ↑ REST API / MQTT
작업자 Qt

Raspberry Pi / Arduino 제어부
  ↓ REST API / MQTT
ASP.NET Core Server
```

Server는 클라이언트와 장비에서 전달된 데이터를 검증하고 DB에 저장한 뒤 필요한 상태와 이벤트를 다시 Web과 Qt에 전달합니다.

---

# 2. REST API

## 2.1 관리자 Web ↔ Server

관리자 Web은 초기 화면 로딩, 설정 변경, 이력 조회 및 알림 처리에 REST API를 사용합니다.

### 인증

| Method | Endpoint | 용도 |
|---|---|---|
| `POST` | `/api/auth/login` | 관리자 로그인 및 JWT 발급 |
| `GET` | `/api/auth/test` | JWT 인증 확인 |

### 생산 목표 및 작업 인원

| Method | Endpoint | 용도 |
|---|---|---|
| `GET` | `/api/production-targets/current` | 현재 및 예약 생산 목표 조회 |
| `PUT` | `/api/production-targets/current` | 생산 목표 설정 |
| `PUT` | `/api/production-targets/worker-count` | 하루 작업 인원 설정 |

생산 시작 전에는 변경값을 즉시 적용하고, 당일 생산이 이미 시작된 경우에는 다음 날 적용할 예약값으로 저장합니다.

```text
생산 시작 전
→ 현재 목표 / 작업 인원 즉시 변경

생산 시작 후
→ next_target_* / next_daily_worker_count에 예약
→ 다음 날 첫 생산 작업 시작 시 적용
```

### 대시보드

| Method | Endpoint | 용도 |
|---|---|---|
| `GET` | `/api/dashboard/summary` | 오늘 생산량 및 요약 조회 |
| `GET` | `/api/dashboard/hourly-production` | 오늘 시간대별 생산량 조회 |
| `GET` | `/api/dashboard/classification-ratio` | 오늘 제품 분류 비율 조회 |
| `GET` | `/api/dashboard/recent-detections` | 최근 제품 감지 결과 조회 |

### 제품 감지 이력

| Method | Endpoint | 용도 |
|---|---|---|
| `GET` | `/api/product-detections` | 제품 감지 목록 조회 |
| `GET` | `/api/product-detections/{id}` | 제품 감지 상세 조회 |

목록 조회에서는 Pagination, 제품 유형 필터, 분류 실패 필터, 감지 ID 검색을 지원합니다.

### 알림 및 이상 내역

| Method | Endpoint | 용도 |
|---|---|---|
| `GET` | `/api/alerts` | 알림 목록 조회 |
| `GET` | `/api/alerts/summary` | 알림 요약 통계 조회 |
| `GET` | `/api/alerts/{alertId}` | 알림 상세 조회 |
| `PATCH` | `/api/alerts/{alertId}/check` | 알림 확인 처리 |
| `PATCH` | `/api/alerts/{alertId}/recover` | 알림 복구 처리 |

### 시스템 구성요소

| Method | Endpoint | 용도 |
|---|---|---|
| `GET` | `/api/system-components` | 장비 및 시스템 상태 조회 |
| `PATCH` | `/api/system-components/{componentCode}/status` | 구성요소 상태 수동 변경 |

관리자 Web은 최초 상태를 REST API로 조회하고 이후 변경사항은 MQTT로 실시간 반영합니다.

---

## 2.2 작업자 Qt ↔ Server

작업자 Qt는 로그인과 생산 작업 제어에 REST API를 사용합니다.

| Method | Endpoint | 용도 |
|---|---|---|
| `POST` | `/api/auth/login` | 작업자 로그인 및 JWT 발급 |
| `POST` | `/api/production-sessions/start` | 생산 작업 시작 |
| `GET` | `/api/production-sessions/current` | 현재 생산 작업 조회 |
| `PATCH` | `/api/production-sessions/finish` | 현재 생산 작업 종료 |

생산 시작 시 Server는 당일 세션 수와 작업 인원을 기준으로 현재 작업자에게 배정할 생산 목표를 계산하여 `production_sessions`에 저장합니다.

```text
작업자 로그인
→ 생산 시작 요청
→ 당일 세션 수 확인
→ 작업 인원 확인
→ 세션별 목표 계산
→ production_sessions 저장
```

생산 종료 시 초콜릿과 사탕 목표를 모두 달성하면 `COMPLETED`, 미달성하면 `CANCELLED`로 처리합니다.

---

## 2.3 제어부 ↔ Server

Raspberry Pi 제어부는 제품 이미지를 Server에 저장할 때 REST API를 사용합니다.

| Method | Endpoint | 용도 |
|---|---|---|
| `POST` | `/api/product-images` | 제품 이미지 업로드 |

지원 형식은 JPG, JPEG, PNG이며 최대 파일 크기는 5MB입니다.

이미지는 다음 경로에 저장됩니다.

```text
wwwroot/images/products/
```

Server는 저장 후 다음 형태의 상대 경로를 반환합니다.

```text
/images/products/{파일명}
```

이 경로는 이후 제품 감지 데이터의 `imagePath`로 사용합니다.

---

# 3. MQTT

## 3.1 제어부 → Server

Server는 제어부에서 전달되는 제품 감지 결과와 장비 상태를 Subscribe합니다.

| Topic | 방향 | 용도 |
|---|---|---|
| `smart_sorting/camera/product_detection` | 제어부 → Server | 제품 감지 및 분류 결과 전달 |
| `smart_sorting/component/status/update` | 제어부 → Server | 실제 장비 상태 및 Error Code 전달 |

### 제품 감지

```text
smart_sorting/camera/product_detection
```

주요 데이터:

```text
productTypeCode
confidence
imagePath
classificationStatus
```

처리 흐름:

```text
Raspberry Pi
→ 제품 촬영 및 분류
→ MQTT Publish
→ Server Subscribe
→ 제품 감지 결과 검증
→ product_detections 저장
→ production_sessions 생산량 갱신
→ Web용 제품 감지 / 생산 현황 MQTT Publish
```

`SUCCESS`는 정상 분류 결과이며, `FAILED`는 제품 분류 실패 결과입니다. 제품 분류 실패와 실제 장비 오류는 별도로 관리합니다.

### 장비 상태

```text
smart_sorting/component/status/update
```

주요 데이터:

```text
componentCode
status
errorCode
```

허용 상태:

```text
NORMAL
WARNING
ERROR
OFFLINE
```

기본 규칙:

```text
NORMAL
→ errorCode = null

WARNING / ERROR / OFFLINE
→ errorCode 필요
```

처리 흐름:

```text
제어부
→ component/status/update
→ Server
→ componentCode / status / errorCode 검증
→ system_components 갱신
→ Error Code 기반 Alert 생성 또는 복구
→ DB 저장
→ Web / Qt로 상태 및 알림 Publish
```

---

## 3.2 Server → 관리자 Web / 작업자 Qt

Server는 처리 결과를 다음 Topic으로 Publish합니다.

| Topic | Web | Qt | 용도 |
|---|---:|---:|---|
| `smart_sorting/production/status` | O | O | 생산 상태·생산량·진행률 |
| `smart_sorting/product/detection` | O | - | 신규 제품 감지 결과 |
| `smart_sorting/alert` | O | O | 신규 알림 |
| `smart_sorting/component/status` | O | O | 장비 상태 변경 |

### 생산 현황

```text
smart_sorting/production/status
```

주요 데이터:

```text
sessionId
status

chocolate
- currentCount
- targetCount
- unitPerSet
- setCount
- progress

candy
- currentCount
- targetCount
- unitPerSet
- setCount
- progress
```

관리자 Web과 작업자 Qt는 생산 상태 변경 시 현재 생산량과 진행률을 실시간으로 갱신합니다.

### 제품 감지

```text
smart_sorting/product/detection
```

제품 감지 결과가 저장된 뒤 관리자 Web에 신규 감지 내용을 전달합니다.

전체 이력 및 상세 조회는 REST API, 새 감지 발생 알림은 MQTT로 처리합니다.

### 알림

```text
smart_sorting/alert
```

주요 데이터:

```text
alertId
alertType
priority
componentCode
errorCode
shortMessage
alertMessage
createdAt
```

클라이언트별 사용 기준:

```text
작업자 Qt
→ shortMessage

관리자 Web
→ alertMessage
```

`shortMessage`는 작업자가 빠르게 확인할 수 있는 짧은 메시지이며, `alertMessage`는 관리자 Web과 DB에서 사용하는 상세 메시지입니다.

### 장비 상태

```text
smart_sorting/component/status
```

실제 Component 상태가 변경된 경우에만 Server가 Publish합니다.

주요 데이터:

```text
componentCode
status
```

관리자 Web과 작업자 Qt는 이 Topic을 Subscribe하여 장비 상태를 실시간 반영합니다.

---

# 4. 클라이언트별 통신 요약

## 4.1 관리자 Web ↔ Server

### REST API

```text
- 관리자 로그인
- 생산 목표 조회 및 설정
- 작업 인원 조회 및 설정
- 대시보드 초기 데이터 조회
- 제품 감지 목록 및 상세 조회
- 알림 목록 / 상세 / 요약 조회
- 알림 확인 및 복구
- 장비 상태 초기 조회
```

### MQTT

```text
- 생산 현황 실시간 수신
- 신규 제품 감지 실시간 수신
- 신규 알림 실시간 수신
- 장비 상태 변경 실시간 수신
```

---

## 4.2 작업자 Qt ↔ Server

### REST API

```text
- 작업자 로그인
- 생산 작업 시작
- 현재 생산 작업 조회
- 생산 작업 종료
```

### MQTT

```text
- 생산 현황 실시간 수신
- 작업자용 알림 수신
- 장비 상태 변경 수신
```

---

## 4.3 Raspberry Pi·Arduino 제어부 ↔ Server

### REST API

```text
- 제품 이미지 업로드
```

### MQTT

```text
- 제품 감지 결과 전송
- 실제 장비 상태 전송
```

---

# 5. 주요 데이터 흐름

## 5.1 제품 감지 흐름

```text
카메라
→ 이미지 촬영
→ REST 이미지 업로드
→ 이미지 경로 반환

Raspberry Pi
→ YOLO 제품 분류
→ MQTT product_detection Publish

Server
→ 제품 감지 결과 저장
→ 생산량 갱신
→ product/detection Publish
→ production/status Publish

관리자 Web
→ 신규 제품 감지 / 생산 현황 갱신

작업자 Qt
→ 생산 현황 갱신
```

## 5.2 장비 이상 흐름

```text
Raspberry Pi / Arduino
→ 장비 이상 감지
→ component/status/update Publish

Server
→ 상태 및 Error Code 검증
→ system_components 갱신
→ Alert 생성
→ component/status Publish
→ alert Publish

관리자 Web
→ 장비 상태 및 상세 알림 표시

작업자 Qt
→ 장비 상태 및 shortMessage 표시
```

## 5.3 장비 복구 흐름

```text
제어부
→ NORMAL 상태 Publish

Server
→ Component 상태 NORMAL 변경
→ 자동 생성된 미복구 Alert 복구
→ component/status Publish

관리자 Web / 작업자 Qt
→ 정상 상태 반영
```

---

# 6. REST API와 MQTT 역할 비교

| 구분 | REST API | MQTT |
|---|---|---|
| 방식 | 요청 → 응답 | Publish → Subscribe |
| 목적 | 조회·설정·명령·이력 | 실시간 상태·이벤트 전달 |
| 관리자 Web | 조회·설정·알림 처리 | 생산·감지·알림·장비 상태 |
| 작업자 Qt | 로그인·생산 시작/조회/종료 | 생산·알림·장비 상태 |
| 제어부 | 이미지 업로드 | 제품 감지·장비 상태 전송 |

Smart Sorting System은 **정확한 데이터 조회와 제어는 REST API**, **실시간 상태 변화와 이벤트 전달은 MQTT**가 담당하도록 통신 역할을 분리했습니다.
