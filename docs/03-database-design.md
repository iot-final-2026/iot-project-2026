# 1. 데이터베이스 설계

![alt text](DB-ERD.png)
- [ERDCloud](https://www.erdcloud.com/d/NaM6PQ2LibNW8kbbX)

## 1.1 시스템 구성 개요

본 시스템은 **컨베이어벨트를 통해 초콜릿과 사탕을 자동으로 감지·분류하고, 생산 작업 현황과 오류 및 알림을 통합 관리하는 자동 생산 모니터링 시스템**으로 구성한다.

전체 데이터베이스는 **생산 작업(PRODUCTION_SESSIONS)을 중심으로 작업자(USERS), 개별 제품(PRODUCTS), 제품 종류(PRODUCT_TYPES), 오류 및 알림(ALERTS), 시스템 구성요소(SYSTEM_COMPONENTS)**를 연결하는 구조이다.

작업자가 생산 작업을 시작하면 하나의 생산 세션이 생성되고, 해당 세션에서 감지된 개별 제품의 분류 결과와 생산 과정에서 발생한 오류 및 알림을 기록한다. 이를 통해 **작업자별 생산 실적 확인 → 제품 분류 결과 확인 → 오류 발생 상황 및 원인 추적**이 가능하도록 설계한다.

또한 제품에 작업자 정보를 직접 저장하지 않고 `PRODUCTS → PRODUCTION_SESSIONS → USERS` 구조로 연결하여, 하나의 생산 작업 단위 안에서 발생한 제품과 작업자를 관리하도록 구성한다. 오류가 발생한 경우에는 `ALERTS`를 통해 생산 세션, 제품, 시스템 구성요소 및 사용자 정보를 연결하여 **오류가 언제, 어떤 생산 작업에서, 어떤 제품 또는 시스템 구성요소와 관련하여 발생했는지** 추적할 수 있도록 한다.

---

## 1.2 USERS (사용자)

> 작업자와 관리자의 로그인 및 권한을 관리하는 테이블

| 컬럼명 | 데이터 타입 | PK | FK | NULL | 설명 |
|--------|------------|:--:|:--:|:---:|------|
| user_id | INT | ✓ | | X | 사용자 번호 |
| login_id | VARCHAR(30) | | | X | 로그인 ID |
| password | VARCHAR(255) | | | X | 암호화된 비밀번호 |
| name | VARCHAR(30) | | | X | 사용자 이름 |
| role | ENUM | | | X | 권한 (관리자/작업자) |
| created_at | DATETIME | | | X | 계정 생성 일시 |

**관계**
- USERS(1) ─ ─ ─< PRODUCTION_SESSIONS(N) **(Non-Identifying)**
- USERS(1) ─ ─ ─< ALERTS(N) **(Non-Identifying)**

> 사용자는 생산 작업을 수행하는 작업자와 시스템을 관리하는 관리자로 구분한다.
>
> 작업자가 생산 작업을 수행하면 해당 작업자의 `user_id`를 생산 세션에 기록하며, 오류 및 알림 발생 시 관련 사용자 정보를 추적할 수 있도록 한다.

---

## 1.3 PRODUCTION_SESSIONS (생산 작업)

> 작업자의 생산 작업 단위와 생산 목표 및 생산 실적을 관리하는 테이블

| 컬럼명 | 데이터 타입 | PK | FK | NULL | 설명 |
|--------|------------|:--:|:--:|:---:|------|
| session_id | INT | ✓ | | X | 생산 세션 번호 |
| user_id | INT | | ✓ | X | 작업자 번호 |
| production_date | DATE | | | X | 생산 날짜 |
| target_chocolate_set_count | INT | | | X | 목표 초콜릿 세트 수 (10개 = 1세트) |
| target_candy_count | INT | | | X | 목표 사탕 수량 (1개 = 1세트) |
| chocolate_count | INT | | | X | 생산된 초콜릿 개수 |
| chocolate_set_count | INT | | | X | 완료된 초콜릿 세트 수 (자동 계산) |
| candy_count | INT | | | X | 생산된 사탕 개수 (1개 = 1세트) |
| status | ENUM | | | X | 생산 작업 상태 |
| started_at | DATETIME | | | X | 작업 시작 일시 |
| ended_at | DATETIME | | | O | 작업 종료 일시 |
| updated_at | DATETIME | | | X | 최종 정보 갱신(수정) 일시 |

**관계**
- USERS(1) ─ ─ ─< PRODUCTION_SESSIONS(N) **(Non-Identifying)**
- PRODUCTION_SESSIONS(1) ─ ─ ─< PRODUCTS(N) **(Non-Identifying)**
- PRODUCTION_SESSIONS(1) ─ ─ ─< ALERTS(N) **(Non-Identifying)**

> 하나의 생산 세션은 작업자가 컨베이어벨트 생산 작업을 수행하는 하나의 작업 단위를 의미한다.
>
> 생산 세션별로 생산 날짜와 목표 생산량을 관리하며, 해당 세션에서 생산된 제품 및 발생한 오류 정보를 연결하여 작업자별 생산 실적과 오류 이력을 추적할 수 있도록 한다.

---

## 1.4 PRODUCTS (개별 제품 및 분류 결과)

> 컨베이어벨트를 통과한 개별 제품의 AI 분류 결과와 촬영 정보를 저장하는 테이블

| 컬럼명 | 데이터 타입 | PK | FK | NULL | 설명 |
|--------|------------|:--:|:--:|:---:|------|
| product_id | INT | ✓ | | X | 제품 번호 |
| session_id | INT | | ✓ | X | 생산 세션 번호 |
| product_type_id | INT | | ✓ | X | 제품 종류 번호 |
| confidence | DECIMAL(5,2) | | | X | 분류 신뢰도 |
| image_path | VARCHAR(255) | | | X | 촬영 이미지 경로 |
| classification_status | ENUM | | | X | 분류 성공 여부 |
| detected_at | DATETIME | | | X | 감지 및 분류 일시 |

**관계**
- PRODUCTION_SESSIONS(1) ─ ─ ─< PRODUCTS(N) **(Non-Identifying)**
- PRODUCT_TYPES(1) ─ ─ ─< PRODUCTS(N) **(Non-Identifying)**
- PRODUCTS(1) ─ ─ ─< ALERTS(N) **(Non-Identifying)**

> 제품은 카메라를 통해 촬영된 이미지를 기반으로 AI를 통해 자동으로 분류한다.
>
> 제품 자체에 작업자 정보를 직접 저장하지 않고 `PRODUCTION_SESSIONS`를 통해 당시 생산 작업을 수행한 작업자를 확인할 수 있도록 설계한다.
>
> 따라서 `PRODUCT → PRODUCTION_SESSIONS → USERS` 경로를 통해 제품이 생산된 당시의 작업자를 추적할 수 있으며, 오류 발생 시에도 해당 생산 세션과 작업자를 확인할 수 있다.

---

## 1.5 PRODUCT_TYPES (제품 종류)

> 생산 대상 제품의 종류와 제품별 생산 단위를 관리하는 테이블

| 컬럼명 | 데이터 타입 | PK | FK | NULL | 설명 |
|--------|------------|:--:|:--:|:---:|------|
| product_type_id | INT | ✓ | | X | 제품 종류 번호 |
| product_name | VARCHAR(20) | | | X | 제품명 (초콜릿/사탕) |
| unit_type | ENUM | | | X | 관리 단위 |
| set_quantity | INT | | | X | 1세트 구성 개수 (초콜릿: 10, 사탕: 1) |
| is_active | BOOLEAN | | | X | 사용 여부 |
| created_at | DATETIME | | | X | 등록 일시 |

**관계**
- PRODUCT_TYPES(1) ─ ─ ─< PRODUCTS(N) **(Non-Identifying)**

> 제품 종류 정보를 별도의 테이블로 관리하여 제품 분류 결과와 제품 기준 정보를 분리한다.
>
> 초콜릿은 `10개 = 1세트`, 사탕은 `1개 = 1세트`로 관리하며, 제품별 생산 단위 및 세트 구성 수량을 `set_quantity`를 통해 관리한다.

---

## 1.6 ALERTS (알림 및 오류 기록)

> 생산 과정에서 발생하는 오류 및 시스템 알림 정보를 관리하는 테이블

| 컬럼명 | 데이터 타입 | PK | FK | NULL | 설명 |
|--------|------------|:--:|:--:|:---:|------|
| alert_id | INT | ✓ | | X | 알림 번호 |
| session_id | INT | | ✓ | X | 생산 세션 번호 |
| product_id | INT | | ✓ | X | 제품 번호 |
| component_id | INT | | ✓ | X | 시스템 구성요소 번호 |
| user_id | INT | | ✓ | X | 사용자 번호 |
| alert_type | ENUM | | | X | 알림 종류 |
| result_status | ENUM | | | O | 처리 결과(선택) |
| severity | ENUM | | | X | 심각도 (LOW/MID/HIGH) |
| message | VARCHAR(1000) | | | X | 상세 내용 |
| status | ENUM | | | X | 확인 상태 |
| acknowledged_by_user_id | INT | | ✓ | O | 확인한 사용자(USERS, NULL 가능) |
| created_at | DATETIME | | | X | 발생 일시 |
| acknowledged_at | DATETIME | | | O | 확인 일시(NULL 가능) |

**관계**
- PRODUCTION_SESSIONS(1) ─ ─ ─< ALERTS(N) **(Non-Identifying)**
- PRODUCTS(1) ─ ─ ─< ALERTS(N) **(Non-Identifying)**
- SYSTEM_COMPONENTS(1) ─ ─ ─< ALERTS(N) **(Non-Identifying)**
- USERS(1) ─ ─ ─< ALERTS(N) **(Non-Identifying)**

> 생산 과정에서 센서, 컨베이어, 카메라, AI 등의 시스템 구성요소에서 오류 또는 이상 상황이 발생하면 알림 정보를 저장한다.
>
> `session_id`를 통해 오류가 발생한 생산 작업을 확인하고, `product_id`가 연결된 경우 특정 제품의 분류 또는 생산 과정에서 발생한 오류인지 확인할 수 있다.
>
> `component_id`를 통해 오류가 발생한 시스템 구성요소를 확인하며, `user_id`를 통해 해당 생산 작업과 관련된 사용자를 추적할 수 있다.
>
> 관리자가 오류를 확인하면 `acknowledged_by_user_id`와 `acknowledged_at`을 통해 해당 알림을 확인한 사용자를 기록한다.

---

## 1.7 SYSTEM_COMPONENTS (시스템 구성요소)

> 생산 시스템을 구성하는 센서, 카메라, AI, 컨베이어 등의 시스템 구성요소 상태를 관리하는 테이블

| 컬럼명 | 데이터 타입 | PK | FK | NULL | 설명 |
|--------|------------|:--:|:--:|:---:|------|
| component_id | INT | ✓ | | X | 구성요소 번호 |
| component_name | VARCHAR(50) | | | X | 구성요소 이름 |
| component_type | ENUM | | | X | 구성요소 종류 |
| status | ENUM | | | X | 현재 상태 |
| description | VARCHAR(200) | | | X | 설명 |
| updated_at | DATETIME | | | X | 상태 갱신 일시 |

**관계**
- SYSTEM_COMPONENTS(1) ─ ─ ─< ALERTS(N) **(Non-Identifying)**

> 시스템 구성요소의 현재 상태를 관리하고, 구성요소에서 발생한 오류 및 이상 상황을 `ALERTS` 테이블과 연결하여 오류 발생 원인을 추적할 수 있도록 한다.
>
> 예를 들어 카메라 인식 오류가 발생하면 `component_id`를 통해 해당 오류가 카메라에서 발생했음을 확인할 수 있다.

---

## 1.8 테이블 관계

| 부모 테이블 | 자식 테이블 | 관계 | 관계 유형 |
|--------------|------------|------|-----------|
| USERS | PRODUCTION_SESSIONS | 1 : N | Non-Identifying (점선) |
| USERS | ALERTS | 1 : N | Non-Identifying (점선) |
| PRODUCTION_SESSIONS | PRODUCTS | 1 : N | Non-Identifying (점선) |
| PRODUCTION_SESSIONS | ALERTS | 1 : N | Non-Identifying (점선) |
| PRODUCT_TYPES | PRODUCTS | 1 : N | Non-Identifying (점선) |
| PRODUCTS | ALERTS | 1 : N | Non-Identifying (점선) |
| SYSTEM_COMPONENTS | ALERTS | 1 : N | Non-Identifying (점선) |

### 관계 설명

- **USERS → PRODUCTION_SESSIONS**
  - 작업자가 생산 작업을 시작하면 해당 작업자의 `user_id`를 생산 세션에 기록한다.
  - 하나의 사용자는 여러 생산 세션을 수행할 수 있다.
  - 생산 세션을 통해 작업자별 생산 실적을 조회할 수 있다.

- **USERS → ALERTS**
  - 생산 작업 중 발생한 알림과 관련된 사용자를 기록한다.
  - 오류 발생 상황과 관련된 사용자를 추적하거나 알림 처리 담당자를 확인하는 데 사용한다.

- **PRODUCTION_SESSIONS → PRODUCTS**
  - 하나의 생산 세션에서 여러 개의 제품이 생산 및 분류될 수 있다.
  - 제품의 `session_id`를 통해 해당 제품이 어떤 생산 작업에서 발생했는지 확인할 수 있다.

- **PRODUCTION_SESSIONS → ALERTS**
  - 특정 생산 세션에서 발생한 오류 및 알림을 기록한다.
  - 생산 작업 단위별 오류 발생 이력을 조회할 수 있다.

- **PRODUCT_TYPES → PRODUCTS**
  - 하나의 제품 종류는 여러 개의 개별 제품에 적용될 수 있다.
  - `product_type_id`를 통해 AI가 분류한 제품의 종류를 확인할 수 있다.
  - 초콜릿과 사탕의 제품 종류 및 생산 단위를 별도로 관리할 수 있다.

- **PRODUCTS → ALERTS**
  - 특정 제품의 분류 또는 생산 과정에서 발생한 오류 및 알림을 기록한다.
  - 하나의 제품에 여러 오류가 발생할 수 있으므로 1:N 관계로 관리한다.

- **SYSTEM_COMPONENTS → ALERTS**
  - 센서, 카메라, AI, 컨베이어 등 특정 시스템 구성요소에서 발생한 오류를 기록한다.
  - 오류 발생 원인을 시스템 구성요소 단위로 추적할 수 있다.

---

## 1.9 데이터 추적 구조

본 데이터베이스는 **생산 작업(PRODUCTION_SESSIONS)을 중심으로 작업자, 제품, 제품 종류, 오류 및 시스템 구성요소 간의 관계를 관리**한다.

```text
USERS
  │
  │ 1:N
  ▼
PRODUCTION_SESSIONS
  │
  ├──────── 1:N ────────> PRODUCTS
  │                         │
  │                         │ N:1
  │                         ▼
  │                    PRODUCT_TYPES
  │
  └──────── 1:N ────────> ALERTS
                              ▲
                 ┌────────────┼────────────┐
                 │            │            │
                 │            │            │
             PRODUCTS       USERS    SYSTEM_COMPONENTS
                 │            │            │
                 └────────────┴────────────┘
```

### 주요 데이터 조회 흐름

**작업자 확인**

`PRODUCT → PRODUCTION_SESSIONS → USERS`

제품이 어떤 생산 세션에서 생성되었는지 확인한 후 해당 생산 세션을 수행한 작업자를 조회한다.

**생산 작업별 제품 확인**

`PRODUCTION_SESSIONS → PRODUCTS`

특정 생산 세션에서 감지 및 분류된 개별 제품 정보를 조회한다.

**생산 작업별 오류 확인**

`PRODUCTION_SESSIONS → ALERTS`

특정 생산 세션에서 발생한 오류 및 알림 이력을 조회한다.

**제품별 오류 확인**

`PRODUCTS → ALERTS`

특정 제품의 분류 또는 생산 과정에서 발생한 오류 및 알림을 조회한다.

**오류 발생 원인 확인**

`ALERTS → SYSTEM_COMPONENTS`

발생한 오류가 센서, 카메라, AI, 컨베이어 등 어떤 시스템 구성요소와 관련되어 있는지 확인한다.

**오류 발생 당시 작업자 확인**

`ALERTS → USERS`

오류 및 알림 정보에 기록된 `user_id`를 통해 관련 사용자를 확인한다.

---

## 1.10 데이터베이스 설계 방향

본 데이터베이스는 단순히 제품 생산량을 저장하는 것을 넘어, **생산 작업 단위의 이력 관리와 오류 원인 추적이 가능한 구조**를 목표로 설계한다.

특히 `PRODUCTION_SESSIONS`를 중심으로 제품과 오류 정보를 연결함으로써 다음과 같은 관리가 가능하다.

1. 작업자별 생산 작업 및 생산 실적 관리
2. 생산 세션별 개별 제품 분류 결과 관리
3. 초콜릿과 사탕의 제품 종류 및 생산 단위 관리
4. 제품 분류 및 생산 과정에서 발생하는 오류 및 알림 기록
5. 오류 발생 제품 및 생산 세션 추적
6. 오류가 발생한 시스템 구성요소 확인
7. 오류 및 알림과 관련된 사용자 확인
8. 관리자의 알림 확인 및 처리 이력 관리

이를 통해 최종적으로 **작업자 → 생산 작업 → 제품 → 오류 → 시스템 구성요소**로 이어지는 데이터 추적이 가능하며, 생산 현황 모니터링과 오류 원인 분석에 활용할 수 있도록 설계한다.
