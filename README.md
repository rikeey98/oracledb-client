# oracledb-client

Python `oracledb` 기반의 간단한 Oracle DB 클라이언트입니다.  
환경 설정은 `.env`가 아니라 `config.yaml` 파일로 관리합니다.

## 구성

- `oracle_db_client.py`: Oracle 연결 및 기본 쿼리 실행 클라이언트
- `config.yaml.example`: 설정 예시 파일
- `USAGE.md`: 빠른 사용법

## 요구사항

- Python 3.9+
- Oracle Instant Client
- `requirements.txt`에 정의된 패키지

## 설치

```bash
pip install -r requirements.txt
```

## 설정

예시 파일을 복사해 `config.yaml`을 만든 뒤 실제 값을 채웁니다.

```bash
cp config.yaml.example config.yaml
```

필수 항목:

- `ORACLE_USER`
- `ORACLE_PASSWORD`
- `ORACLE_CLIENT_LIB_DIR`
- `ORACLE_DSN` 또는 `ORACLE_HOST` + `ORACLE_SERVICE_NAME`

## 실행 예시

```bash
python3 oracle_db_client.py
```

자세한 사용법은 [USAGE.md](/Users/yonghyun-kwon/WorkSpace/py-script/oracledb/USAGE.md:1)를 참고하세요.
