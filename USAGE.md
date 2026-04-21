# 사용법

## 1. 패키지 설치

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

`ORACLE_DSN` 대신 아래 조합도 사용할 수 있습니다.

```yaml
ORACLE_HOST: localhost
ORACLE_PORT: 1521
ORACLE_SERVICE_NAME: XEPDB1
```

## 3. 코드에서 사용

```python
from oracle_db_client import OracleDBClient

with OracleDBClient("config.yaml") as client:
    rows = client.select(
        "SELECT * FROM users WHERE ROWNUM <= :limit",
        {"limit": 5},
    )
    print(rows)
```

## 4. 직접 실행

```bash
python3 oracle_db_client.py
```

## 주의사항

- `config.yaml`에는 계정 정보가 들어가므로 저장소에 커밋하지 않는 편이 안전합니다.
- Thick mode를 사용하므로 Oracle Instant Client 경로가 정확해야 합니다.
