# Smart Sorting System 데이터베이스 설계

컨베이어 기반 초콜릿·사탕 자동 분류 시스템에서 사용하는 MySQL 데이터베이스의 구조와 설계 기준을 정리한 문서입니다.

---

## 1. ERD

![스마트 분류 시스템 ERD](./smart_sorting_system_erd.png)

관련 파일:

- SQL 스키마: `smart_sorting_system.sql`
- DBeaver 편집용 ERD: `smart_sorting_system.erd`
- GitHub 열람용 ERD: `smart_sorting_system_erd.png`

---

## 2. 설계 개요

데이터베이스는 생산 목표, 작업자별 생산 작업, 제품 감지 결과, 시스템 구성요소 상태, 알림 이력을 관리하도록 구성했습니다.

주요 데이터 흐름은 다음과 같습니다.

```text
production_targets
→ 하루 생산 목표 및 작업 인원 관리

users
→ production_sessions
→ product_detections

system_components
→ alerts

production_sessions
→ alerts

product_detections
→ alerts
```

`production_sessions`는 작업자별 생산 작업 단위를 관리하며, 해당 세션에서 생산된 초콜릿과 사탕 수량을 저장합니다.

`product_detections`는 생산 작업 중 발생한 개별 제품 감지 및 분류 결과를 저장합니다.

`alerts`는 생산 작업, 제품 감지 결과, 시스템 구성요소와 각각 독립적으로 연결될 수 있습니다. 생산과 직접 관계없는 시스템 오류도 저장할 수 있도록 관련 외래키에는 `NULL`을 허용합니다.

`production_targets`는 하루 전체 생산 목표와 작업 인원 및 다음 날 적용할 예약값을 관리하며, 다른 테이블과 직접적인 외래키 관계를 가지지 않습니다.

모든 관계는 자식 테이블이 독립적인 기본 키를 가지는 비식별 관계로 구성했습니다.

---

## 3. 테이블 구성

### 3.1 `users` — 사용자

작업자와 관리자의 로그인 정보 및 권한을 관리합니다.

| 컬럼 | 설명 |
|---|---|
| `user_id` | 사용자 번호 |
| `login_id` | 로그인 아이디 |
| `password_hash` | BCrypt 비밀번호 해시 |
| `name` | 사용자명 |
| `role` | 사용자 역할 |
| `created_at` | 계정 생성 일시 |

주요 규칙:

```text
login_id = UNIQUE

role
- ADMIN
- WORKER
```

---

### 3.2 `product_types` — 제품 유형

초콜릿과 사탕의 기준 정보를 관리합니다.

| 컬럼 | 설명 |
|---|---|
| `product_type_id` | 제품 유형 번호 |
| `product_type_code` | 서버 및 MQTT 연동용 제품 코드 |
| `product_name` | 제품명 |
| `unit_per_set` | 한 세트를 구성하는 낱개 수 |
| `created_at` | 생성 일시 |

초기 데이터:

| 코드 | 제품명 | 세트당 개수 |
|---|---|---:|
| `CHOCOLATE` | 초콜릿 | 10 |
| `CANDY` | 사탕 | 1 |

`unit_per_set`은 0보다 커야 합니다.

---

### 3.3 `system_components` — 시스템 구성요소

하드웨어와 소프트웨어 구성요소의 현재 상태를 관리합니다.

| 컬럼 | 설명 |
|---|---|
| `component_id` | 구성요소 번호 |
| `component_code` | API·MQTT 연동용 고정 코드 |
| `component_name` | 구성요소 이름 |
| `component_type` | 구성요소 유형 |
| `current_status` | 현재 상태 |
| `status_updated_at` | 상태 갱신 일시 |

구성요소 유형:

```text
SENSOR
ACTUATOR
CONTROLLER
DISPLAY
SOFTWARE
SERVER
DATABASE
```

현재 상태:

```text
NORMAL  : 정상
WARNING : 경고
ERROR   : 오류
OFFLINE : 연결 또는 통신 불가
```

주요 구성요소는 Raspberry Pi, Arduino, 센서, 카메라, 컨베이어, 서보모터, 부저, 작업자 화면, 관리자 Web, MQTT Broker, ASP.NET Core Server, MySQL Database 등으로 구성됩니다.

`status_updated_at`은 최초 등록 시 저장되며, 장비 상태가 변경될 때 서버에서 `current_status`와 함께 갱신합니다.

---

### 3.4 `production_targets` — 생산 목표

하루 전체 생산 목표와 작업 인원, 다음 날 적용할 예약값을 관리합니다.

| 컬럼 | 설명 |
|---|---|
| `target_id` | 생산 목표 번호 |
| `target_chocolate_set_count` | 현재 적용 중인 초콜릿 목표 세트 수 |
| `target_candy_set_count` | 현재 적용 중인 사탕 목표 세트 수 |
| `next_target_chocolate_set_count` | 다음 날 적용할 초콜릿 목표 세트 수 |
| `next_target_candy_set_count` | 다음 날 적용할 사탕 목표 세트 수 |
| `daily_worker_count` | 현재 적용 중인 하루 작업 인원 |
| `next_daily_worker_count` | 다음 날 적용할 작업 인원 |
| `updated_at` | 마지막 수정 일시 |

현재 적용 중인 목표값은 생산 세션이 시작될 때 작업 인원 수를 기준으로 각 작업자 세션에 분배됩니다.

생산이 이미 시작된 이후 목표 또는 작업 인원을 변경하면 `next_*` 컬럼에 저장하여 다음 날 첫 생산 세션 시작 시 적용합니다.

다음 날 예약값이 적용된 이후 해당 `next_*` 값은 `NULL`로 초기화합니다.

---

### 3.5 `production_sessions` — 생산 작업

작업자 한 명이 수행하는 하나의 생산 작업 단위를 관리합니다.

| 컬럼 | 설명 |
|---|---|
| `session_id` | 생산 작업 번호 |
| `user_id` | 작업자 번호 |
| `target_chocolate_set_count` | 해당 세션의 초콜릿 목표 세트 수 |
| `target_candy_set_count` | 해당 세션의 사탕 목표 세트 수 |
| `chocolate_count` | 생산된 초콜릿 낱개 수 |
| `candy_count` | 생산된 사탕 낱개 수 |
| `status` | 생산 작업 상태 |
| `started_at` | 작업 시작 일시 |
| `ended_at` | 작업 종료 일시 |
| `updated_at` | 마지막 수정 일시 |

상태:

```text
RUNNING   : 생산 진행 중
PAUSED    : 일시 정지
COMPLETED : 생산 완료
CANCELLED : 생산 취소
```

주요 규칙:

- 목표량과 생산량은 음수가 될 수 없습니다.
- 생산 세션의 목표는 하루 전체 목표를 `daily_worker_count` 기준으로 분배하여 저장합니다.
- `RUNNING`, `PAUSED` 상태에서는 작업이 종료되지 않은 상태입니다.
- `COMPLETED`, `CANCELLED` 상태에서는 작업 종료 시각을 기록합니다.
- 당일 생산 세션만 현재 생산 작업으로 사용합니다.
- 이전 날짜에 종료되지 않은 `RUNNING`, `PAUSED` 세션은 새 생산 작업 시작 시 `CANCELLED` 처리합니다.

초콜릿과 사탕의 완성 세트 수는 각 제품의 `unit_per_set`을 기준으로 계산합니다.

```text
세트 수 = 생산 낱개 수 / unit_per_set
```

---

### 3.6 `product_detections` — 제품 감지 및 분류 결과

제품이 감지되고 촬영·분류될 때마다 한 행씩 저장합니다.

| 컬럼 | 설명 |
|---|---|
| `product_detection_id` | 제품 감지 번호 |
| `session_id` | 생산 작업 번호 |
| `product_type_id` | 제품 유형 번호 |
| `confidence` | 분류 신뢰도 |
| `image_path` | 촬영 이미지 경로 |
| `classification_status` | 분류 상태 |
| `detected_at` | 감지 일시 |

분류 상태:

```text
SUCCESS : 분류 성공
FAILED  : 분류 실패
```

주요 규칙:

- 제품 감지 결과는 당일 진행 중인 생산 세션과 연결합니다.
- 신뢰도는 0 이상 1 이하의 값을 사용합니다.
- `SUCCESS`이면 정상적으로 분류된 제품 유형을 저장합니다.
- `FAILED`이면 제품 유형을 특정할 수 없으므로 `product_type_id`가 `NULL`일 수 있습니다.
- 이미지 저장 여부에 따라 `image_path`는 `NULL`일 수 있습니다.
- 분류 실패 자체와 장비 오류 상태는 별도로 관리합니다.

---

### 3.7 `alerts` — 알림

생산 과정과 시스템에서 발생한 정보, 경고, 오류의 이력을 저장합니다.

| 컬럼 | 설명 |
|---|---|
| `alert_id` | 알림 번호 |
| `session_id` | 관련 생산 작업 번호 |
| `component_id` | 관련 구성요소 번호 |
| `product_detection_id` | 관련 제품 감지 번호 |
| `checked_by_user_id` | 알림을 확인한 사용자 번호 |
| `alert_type` | 알림 유형 |
| `priority` | 중요도 |
| `error_code` | 장비 및 시스템 오류 코드 |
| `recovery_status` | 복구 상태 |
| `check_status` | 확인 상태 |
| `alert_message` | 알림 상세 메시지 |
| `created_at` | 발생 일시 |
| `recovered_at` | 복구 일시 |
| `checked_at` | 확인 일시 |

알림 유형:

```text
INFO    : 단순 정보
WARNING : 경고
ERROR   : 오류
```

중요도:

```text
LOW    : 낮음
MEDIUM : 보통
HIGH   : 높음
```

복구 상태:

```text
NOT_RECOVERED : 미복구
RECOVERED     : 복구 완료
```

확인 상태:

```text
UNCHECKED : 미확인
CHECKED   : 확인 완료
```

`INFO` 알림은 복구 및 확인 대상이 아니므로 관련 상태값과 시간값에 `NULL`을 사용할 수 있습니다.

장비에서 발생한 오류는 `error_code`를 이용하여 오류 종류를 구분합니다.

예:

```text
CAMERA_ERROR
NO_DETECTION
SERIAL_DISCONNECTED
```

주요 규칙:

- `RECOVERED` 상태이면 `recovered_at`을 기록합니다.
- 미복구 상태에서는 `recovered_at`이 `NULL`입니다.
- 사용자가 알림을 확인하면 `checked_by_user_id`와 `checked_at`을 기록합니다.
- 자동 생성된 장비 알림은 Component가 `NORMAL`로 복구될 때 자동으로 `RECOVERED` 처리할 수 있습니다.
- 수동 생성 알림은 자동 복구 대상에서 제외합니다.
- 동일 Component와 동일 `error_code`의 미복구 알림은 중복 생성하지 않습니다.

알림 발생 당시 작업자는 다음 관계를 이용해 확인할 수 있습니다.

```text
alerts.session_id
→ production_sessions.user_id
→ users.user_id
```

---

## 4. 테이블 관계

| 부모 테이블 | 자식 테이블 | 관계 | 자식 FK |
|---|---|---|---|
| `users` | `production_sessions` | 1:N | NOT NULL |
| `production_sessions` | `product_detections` | 1:N | NOT NULL |
| `product_types` | `product_detections` | 1:N | NULL 가능 |
| `production_sessions` | `alerts` | 1:N | NULL 가능 |
| `system_components` | `alerts` | 1:N | NULL 가능 |
| `product_detections` | `alerts` | 1:N | NULL 가능 |
| `users` | `alerts` | 1:N | NULL 가능 |

`production_targets`는 다른 테이블과 외래키로 직접 연결하지 않고 독립적으로 관리합니다.

---

## 5. 주요 기준 데이터

### 제품 유형

- `CHOCOLATE`
- `CANDY`

### 시스템 구성요소

시스템에서 사용하는 하드웨어 및 소프트웨어 구성요소를 `system_components`에 초기 등록하여 관리합니다.

각 구성요소는 `component_code`를 이용하여 REST API 및 MQTT 메시지와 연결합니다.

### 사용자

관리자와 작업자 계정을 `users`에서 관리하며 비밀번호는 BCrypt 해시값으로 저장합니다.

---

## 6. 주요 설계 특징

### 생산 목표와 작업자별 목표 분리

하루 전체 목표는 `production_targets`에서 관리합니다.

```text
production_targets
        ↓
daily_worker_count 기준 목표 분배
        ↓
production_sessions
```

각 작업자가 생산을 시작하면 해당 세션의 목표량을 별도로 저장합니다.

### 생산 수량과 세트 수 분리

DB에는 실제 생산된 낱개 수를 저장하고 세트 수는 `product_types.unit_per_set`을 기준으로 계산합니다.

```text
CHOCOLATE
10개 = 1세트

CANDY
1개 = 1세트
```

### 제품 감지와 장비 상태 분리

제품 분류 실패(`FAILED`)는 제품 감지 결과이며, 장비 자체 오류와 동일하게 처리하지 않습니다.

장비 상태는 별도의 `system_components.current_status`와 `alerts.error_code`를 통해 관리합니다.

### REST API와 MQTT 연동을 고려한 코드값 사용

다음 식별 코드는 화면 표시명이 아닌 시스템 연동용 고정값으로 사용합니다.

```text
product_type_code
component_code
error_code
```

---

## 7. 실행 방법

DBeaver에서 `smart_sorting_system.sql` 파일을 열고 전체 스크립트를 실행합니다.

전체 스크립트 실행:

```text
Alt + X
```

현재 커서가 있는 SQL 문만 실행:

```text
Ctrl + Enter
```

생성 확인:

```sql
USE smart_sorting_system;

SHOW TABLES;
```

예상 테이블:

```text
alerts
product_detections
product_types
production_sessions
production_targets
system_components
users
```

총 7개의 테이블이 생성되면 정상입니다.
