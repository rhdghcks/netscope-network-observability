# TCP 연결 기록

Python 3 표준 라이브러리만 사용한다. 저장소 루트에서 직접 확인하려는 서비스의 주소와 포트를 지정한다.

```sh
python tools/tcp_probe.py example.com 443
```

한 번 실행할 때마다 JSON 한 줄을 출력하고 현재 디렉터리의 `netscope.sqlite3`에 같은 측정값을 추가한다. `--db`로 파일 경로를 바꿀 수 있다. 부모 디렉터리는 미리 만들어 둔다. 최근 기록을 확인하는 SQL은 다음과 같다.

```sql
SELECT observed_at, host, port, elapsed_ms, ok, error
FROM tcp_probes ORDER BY id DESC LIMIT 20;
```

시각은 UTC다. 소요 시간에는 호스트 이름 조회와 TCP 연결 시도가 포함된다. `--timeout 3`은 각 주소에 연결할 때 적용하는 소켓 제한 시간이다. DNS 조회와 여러 주소 재시도로 전체 측정 시간이 더 길어질 수 있다.

종료 코드 0은 연결 성공, 1은 연결 실패가 기록됐음을 뜻한다. 2는 인자 또는 저장 오류다. TCP 연결이 성공해도 이후 TLS나 HTTP 응답까지 정상인지는 별도로 확인해야 한다.

테스트는 로컬 루프백 소켓과 임시 DB를 사용한다.

```sh
python -m unittest discover -s tests -v
```
