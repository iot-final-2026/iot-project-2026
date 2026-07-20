# 6. 데이터베이스 설계

## 6.1 USER (사용자)

> 작업자와 관리자의 로그인 및 권한을 관리하는 테이블

| 컬럼명 | 데이터 타입 | PK | FK | NULL | 설명 |
|--------|------------|:--:|:--:|:---:|------|
| user_id | INT | ✓ | | X | 사용자 번호 |
| login_id | VARCHAR(30) | | | X | 로그인 ID |
| password | VARCHAR(255) | | | X | 암호화된 비밀번호 |
| name | VARCHAR(30) | | | X | 사용자 이름 |
| role | ENUM('관리자','작업자') | | | X | 사용자 권한 |
| created_at | DATETIME | | | X | 계정 생성일 |

**관계**
- USER(1) ─ ─ ─< PRODUCT(N) **(Non-Identifying)**
- USER(1) ─ ─ ─< PRODUCTION(N) **(Non-Identifying)**

---

## 6.2 PRODUCT (제품 분류)

> 컨베이어벨트를 통과한 제품의 분류 결과를 저장하는 테이블

| 컬럼명 | 데이터 타입 | PK | FK | NULL | 설명 |
|--------|------------|:--:|:--:|:---:|------|
| product_id | INT | ✓ | | X | 제품 번호 |
| user_id | INT | | ✓ | X | 작업자 번호 |
| product_type | VARCHAR(20) | | | X | 초콜릿 / 사탕 |
| confidence | DECIMAL(5,2) | | | X | 분류 신뢰도(%) |
| image_path | VARCHAR(255) | | | X | 촬영 이미지 경로 |
| detected_at | DATETIME | | | X | 제품 분류 시각 |

**관계**
- USER(1) ─ ─ ─< PRODUCT(N) **(Non-Identifying)**
- PRODUCT(1) ─ ─ ─ ALERT(0..1) **(Non-Identifying)**

> 제품은 OpenCV를 통해 자동으로 분류되며, 당시 생산 라인을 운영 중인 작업자를 함께 기록하여 작업자별 생산 실적 및 오류 발생 시 담당 작업자를 확인할 수 있도록 한다.

---

## 6.3 PRODUCTION (생산 현황)

> 날짜별 생산량과 목표 생산량을 관리하는 테이블

| 컬럼명 | 데이터 타입 | PK | FK | NULL | 설명 |
|--------|------------|:--:|:--:|:---:|------|
| production_id | INT | ✓ | | X | 생산 번호 |
| user_id | INT | | ✓ | X | 작업자 번호 |
| production_date | DATE | | | X | 생산 날짜 |
| target_count | INT | | | X | 목표 생산량 |
| chocolate_count | INT | | | X | 생산된 초콜릿 개수 |
| chocolate_set_count | INT | | | X | 완료된 초콜릿 세트 수 (10개 = 1세트) |
| candy_count | INT | | | X | 생산된 사탕 개수 (1개 = 1세트) |
| recorded_at | DATETIME | | | X | 생산 정보 기록 시각 |

**관계**
- USER(1) ─ ─ ─< PRODUCTION(N) **(Non-Identifying)**

> 생산 현황은 날짜별 목표 생산량과 실제 생산량을 집계하여 관리하는 테이블이며, 작업자별 생산 실적을 조회하기 위해 USER와 연결한다.

---

## 6.4 ALERT (오류 감지)

> 제품 분류 과정에서 발생한 오류를 저장하는 테이블

| 컬럼명 | 데이터 타입 | PK | FK | NULL | 설명 |
|--------|------------|:--:|:--:|:---:|------|
| alert_id | INT | ✓ | | X | 오류 번호 |
| product_id | INT | | ✓ (UNIQUE) | X | 제품 번호 |
| alert_type | ENUM('SENSOR','CONVEYOR','CAMERA','AI') | | | 오류 종류 |
| message | VARCHAR(200) | | | X | 오류 내용 |
| status | ENUM('미확인','확인') | | | 처리 상태 |
| alert_time | DATETIME | | | X | 오류 발생 시각 |

**관계**
- PRODUCT(1) ─ ─ ─ ALERT(0..1) **(Non-Identifying)**

> 오류는 특정 제품에 대해서만 발생하므로 PRODUCT와 연결한다. 오류 발생 시 `PRODUCT → USER`를 조회하여 당시 작업 중이던 담당 작업자를 확인할 수 있다.

---

## 6.5 테이블 관계

| 부모 테이블 | 자식 테이블 | 관계 | 관계 유형 |
|--------------|------------|------|-----------|
| USER | PRODUCT | 1 : N | Non-Identifying (점선) |
| USER | PRODUCTION | 1 : N | Non-Identifying (점선) |
| PRODUCT | ALERT | 1 : 0..1 | Non-Identifying (점선) |

### 관계 설명

- **USER → PRODUCT**
  - 로그인한 작업자가 생산 라인을 운영하는 동안 생성된 제품 정보를 기록한다.
  - 작업자별 생산 실적 조회 및 오류 발생 시 담당 작업자를 확인하기 위해 사용한다.

- **USER → PRODUCTION**
  - 작업자별 생산 목표 및 생산량을 관리하기 위한 관계이다.
  - 하나의 작업자는 여러 생산 기록을 가질 수 있다.

- **PRODUCT → ALERT**
  - 제품 분류 과정에서 오류가 발생한 경우에만 오류 정보를 저장한다.
  - 제품 하나당 최대 하나의 오류 정보만 등록할 수 있다.