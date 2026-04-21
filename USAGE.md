# 사용법

## 1. `uv`로 환경 생성

```bash
uv sync
```

기존 pip 방식이 필요하면 아래도 사용할 수 있습니다.

```bash
pip install -r requirements.txt
```

## 2. 설정 파일 준비

`config.yaml.example`을 복사해서 `config.yaml`을 만듭니다.

```bash
cp config.yaml.example config.yaml
```

예시:

```yaml
ORACLE_USER: scott
ORACLE_PASSWORD: tiger
ORACLE_DSN: localhost:1521/XEPDB1
ORACLE_CLIENT_LIB_DIR: /path/to/instantclient
ORACLE_CLIENT_CONFIG_DIR: /path/to/network/admin
```

Windows 예시:

```yaml
ORACLE_USER: scott
ORACLE_PASSWORD: tiger
ORACLE_DSN: localhost:1521/XEPDB1
ORACLE_CLIENT_LIB_DIR: 'C:\oracle\instantclient_23_5'
ORACLE_CLIENT_CONFIG_DIR: 'C:\oracle\network\admin'
```

`ORACLE_DSN` 대신 아래 조합도 사용할 수 있습니다.

```yaml
ORACLE_HOST: localhost
ORACLE_PORT: 1521
ORACLE_SERVICE_NAME: XEPDB1
```

## 3. 빠른 시작

가장 간단한 사용 예시는 아래와 같습니다.

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    rows = client.select(
        "SELECT * FROM users WHERE ROWNUM <= :limit",
        {"limit": 5},
    )
    print(rows)
```

직접 실행도 가능합니다.

```bash
uv run oracle_db_client.py
```

## 4. 공개 메서드 개요

`OracleDBClient`의 주요 공개 메서드는 아래와 같습니다.

- `OracleDBClient(config_file="config.yaml")`
- `connect()`
- `close()`
- `cursor()`
- `select(query, params=None)`
- `execute_dml(query, params=None, auto_commit=True)`
- `test_connection()`
- `insert(query, params=None, auto_commit=True)`
- `update(query, params=None, auto_commit=True)`
- `delete(query, params=None, auto_commit=True)`
- `commit()`
- `rollback()`

`_load_config`, `_require_config`, `_optional_config`, `_build_dsn`, `_init_thick_mode`, `_execute`는 내부 구현용 메서드이므로 직접 호출하지 않는 쪽이 맞습니다.

## 5. 메서드별 상세 사용법

### `OracleDBClient(config_file="config.yaml")`

설정 파일을 읽고 Oracle Thick mode를 초기화한 뒤 클라이언트 객체를 생성합니다.

시그니처:

```python
client = OracleDBClient(config_file="config.yaml")
```

인자:

- `config_file`: YAML 설정 파일 경로

예제:

```python
from oracle_db_client import OracleDBClient

client = OracleDBClient("config.yaml")
try:
    print("Client initialized")
finally:
    client.close()
```

예외가 발생할 수 있는 경우:

- 설정 파일이 없으면 `FileNotFoundError`
- 필수 설정이 빠졌으면 `ValueError`
- Instant Client 경로가 잘못됐거나 Oracle Client 초기화가 실패하면 `oracledb` 예외

### `__enter__()` / `__exit__()`

이 클래스는 context manager를 지원합니다. 가장 안전한 사용 방식은 `with` 블록입니다.

예제:

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    print(client.test_connection())
```

효과:

- `with` 진입 시 `connect()` 호출
- `with` 종료 시 `close()` 호출

### `connect()`

필요할 때 실제 DB 연결을 생성하거나, 이미 살아 있는 연결이 있으면 재사용합니다.

시그니처:

```python
connection = client.connect()
```

반환값:

- `oracledb.Connection`

예제:

```python
from oracle_db_client import OracleDBClient

client = OracleDBClient("config.yaml")
try:
    connection = client.connect()
    print(connection.version)
finally:
    client.close()
```

언제 쓰면 좋은가:

- 순수 SQL wrapper 외에 `oracledb.Connection` 자체 기능을 써야 할 때
- 고급 트랜잭션 제어가 필요할 때

### `close()`

현재 연결이 있으면 닫고 내부 연결 상태를 `None`으로 되돌립니다.

시그니처:

```python
client.close()
```

예제:

```python
client = OracleDBClient("config.yaml")
client.connect()
client.close()
```

권장 사항:

- `with OracleDBClient(...)`를 쓰면 직접 `close()`를 호출하지 않아도 됩니다.
- `with`를 쓰지 않는 경우에는 반드시 `finally`에서 닫는 편이 안전합니다.

### `cursor()`

커서 객체를 직접 다뤄야 할 때 사용하는 context manager입니다. 내부적으로 `connect()`를 호출하고, 블록 종료 시 커서를 자동으로 닫습니다.

시그니처:

```python
with client.cursor() as cursor:
    ...
```

예제:

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    with client.cursor() as cursor:
        cursor.execute("SELECT SYSDATE FROM DUAL")
        print(cursor.fetchone())
```

이 메서드가 유용한 경우:

- `fetchone()`, `fetchall()` 외의 커서 동작을 직접 제어할 때
- PL/SQL 호출, 배열 바인딩, `executemany()` 같은 저수준 API가 필요할 때

### `select(query, params=None)`

조회용 메서드입니다. SQL을 실행하고 결과를 `list[dict]` 형태로 반환합니다.

시그니처:

```python
rows = client.select(query, params=None)
```

인자:

- `query`: `SELECT` 문
- `params`: `dict`, `list`, `tuple`, 또는 `None`

반환값:

- 각 행이 딕셔너리인 리스트

특징:

- 컬럼명은 `cursor.description` 기준으로 들어갑니다.
- Oracle에서 보통 컬럼명이 대문자로 반환되므로 키도 대문자일 가능성이 큽니다.

예제 1. 이름 기반 바인드:

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    rows = client.select(
        """
        SELECT user_id, username, status
        FROM users
        WHERE status = :status
        """,
        {"status": "ACTIVE"},
    )
    print(rows)
```

예제 2. 한 건 조회:

```python
with OracleDBClient("config.yaml") as client:
    rows = client.select(
        "SELECT user_id, username FROM users WHERE user_id = :user_id",
        {"user_id": 1001},
    )
    user = rows[0] if rows else None
    print(user)
```

### `execute_dml(query, params=None, auto_commit=True)`

`INSERT`, `UPDATE`, `DELETE`처럼 데이터 변경 SQL을 실행하는 공통 메서드입니다.

시그니처:

```python
affected_rows = client.execute_dml(
    query,
    params=None,
    auto_commit=True,
)
```

인자:

- `query`: DML SQL
- `params`: 바인드 파라미터
- `auto_commit`: `True`면 실행 직후 `commit()`

반환값:

- 영향받은 행 수

예제:

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    affected = client.execute_dml(
        """
        UPDATE users
        SET last_login_at = SYSDATE
        WHERE user_id = :user_id
        """,
        {"user_id": 1001},
    )
    print(f"updated rows: {affected}")
```

`auto_commit=False` 예제:

```python
client = OracleDBClient("config.yaml")
try:
    client.execute_dml(
        "UPDATE accounts SET balance = balance - :amount WHERE account_id = :account_id",
        {"amount": 100, "account_id": 1},
        auto_commit=False,
    )
    client.execute_dml(
        "UPDATE accounts SET balance = balance + :amount WHERE account_id = :account_id",
        {"amount": 100, "account_id": 2},
        auto_commit=False,
    )
    client.commit()
except Exception:
    client.rollback()
    raise
finally:
    client.close()
```

### `test_connection()`

연결이 정상인지 간단히 확인합니다. 내부적으로 `SELECT 1 FROM DUAL`을 실행합니다.

시그니처:

```python
ok = client.test_connection()
```

반환값:

- 성공 시 `True`

예제:

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    if client.test_connection():
        print("Oracle connection is healthy")
```

용도:

- 배포 직후 연결 점검
- 앱 시작 시 health check

### `insert(query, params=None, auto_commit=True)`

실제로는 `execute_dml()`의 래퍼입니다. 의미를 더 분명하게 하려고 분리된 메서드입니다.

시그니처:

```python
affected_rows = client.insert(query, params=None, auto_commit=True)
```

예제:

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    affected = client.insert(
        """
        INSERT INTO users (user_id, username, status)
        VALUES (:user_id, :username, :status)
        """,
        {
            "user_id": 1001,
            "username": "rikeey",
            "status": "ACTIVE",
        },
    )
    print(f"inserted rows: {affected}")
```

### `update(query, params=None, auto_commit=True)`

`UPDATE` 문 전용 의미를 주는 래퍼입니다.

시그니처:

```python
affected_rows = client.update(query, params=None, auto_commit=True)
```

예제:

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    affected = client.update(
        """
        UPDATE users
        SET status = :status
        WHERE user_id = :user_id
        """,
        {
            "status": "INACTIVE",
            "user_id": 1001,
        },
    )
    print(f"updated rows: {affected}")
```

### `delete(query, params=None, auto_commit=True)`

`DELETE` 문 전용 의미를 주는 래퍼입니다.

시그니처:

```python
affected_rows = client.delete(query, params=None, auto_commit=True)
```

예제:

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    affected = client.delete(
        "DELETE FROM users WHERE user_id = :user_id",
        {"user_id": 1001},
    )
    print(f"deleted rows: {affected}")
```

### `commit()`

현재 연결에 대해 수동 커밋을 수행합니다.

시그니처:

```python
client.commit()
```

언제 쓰는가:

- `auto_commit=False`로 여러 DML을 한 트랜잭션으로 묶을 때

예제:

```python
client = OracleDBClient("config.yaml")
try:
    client.insert(
        "INSERT INTO logs (log_id, message) VALUES (:log_id, :message)",
        {"log_id": 1, "message": "start"},
        auto_commit=False,
    )
    client.update(
        "UPDATE jobs SET status = :status WHERE job_id = :job_id",
        {"status": "DONE", "job_id": 10},
        auto_commit=False,
    )
    client.commit()
finally:
    client.close()
```

### `rollback()`

현재 연결의 미커밋 변경을 되돌립니다.

시그니처:

```python
client.rollback()
```

예제:

```python
client = OracleDBClient("config.yaml")
try:
    client.update(
        "UPDATE accounts SET balance = balance - :amount WHERE account_id = :account_id",
        {"amount": 500, "account_id": 1},
        auto_commit=False,
    )

    raise RuntimeError("simulate failure")
except Exception:
    client.rollback()
finally:
    client.close()
```

## 6. 자주 쓰는 패턴

### 조회 전용 스크립트

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    rows = client.select(
        "SELECT employee_id, first_name, last_name FROM employees WHERE department_id = :dept_id",
        {"dept_id": 90},
    )
    for row in rows:
        print(row)
```

### 여러 DML을 한 트랜잭션으로 처리

```python
from oracle_db_client import OracleDBClient

client = OracleDBClient("config.yaml")
try:
    client.insert(
        "INSERT INTO orders (order_id, status) VALUES (:order_id, :status)",
        {"order_id": 101, "status": "PENDING"},
        auto_commit=False,
    )
    client.insert(
        """
        INSERT INTO order_items (order_id, item_id, qty)
        VALUES (:order_id, :item_id, :qty)
        """,
        {"order_id": 101, "item_id": 2001, "qty": 2},
        auto_commit=False,
    )
    client.commit()
except Exception:
    client.rollback()
    raise
finally:
    client.close()
```

### Raw cursor 사용

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    with client.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM user_tables
            ORDER BY table_name
            """
        )
        for row in cursor:
            print(row[0])
```

## 7. 주의사항

- `config.yaml`에는 계정 정보가 들어가므로 저장소에 커밋하지 않는 편이 안전합니다.
- Thick mode를 사용하므로 Oracle Instant Client 경로가 정확해야 합니다.
- Windows 경로는 YAML escape 이슈를 피하려고 작은따옴표를 권장합니다.
- `select()` 결과의 컬럼 키는 Oracle이 반환하는 컬럼명 형식을 따릅니다.
- 트랜잭션을 직접 제어하려면 `auto_commit=False`와 `commit()` 또는 `rollback()`을 함께 사용해야 합니다.
