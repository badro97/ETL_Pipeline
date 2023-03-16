# Assignment


## 1. ETL 파이프라인 구축

- 데이터 추출 url : [http://ec2-3-37-12-122.ap-northeast-2.compute.amazonaws.com/api/data/log](http://ec2-3-37-12-122.ap-northeast-2.compute.amazonaws.com/api/data/log)
- key = b't-jdqnDewRx9kWithdsTMS21eLrri70TpkMq2A59jX8='

- 암호화, 복호화

    ```
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    print(f"대칭키:{key}")

    fernet = Fernet(key)
    json_log = {"url": "/api/products/product/24", "method": "DELETE", "product_id": 24, "user_id": 21, "name": "log_file2", "inDate": "2022-12-01T01:32:21.437Z", "detail": {"message": "DELETE access Board Detail", "levelname": "INFO"}}
    encrypt_str = fernet.encrypt(f"{json_log}".encode('ascii'))
    print("암호화된 문자열:", encrypt_str)

    decrypt_str = fernet.decrypt(encrypt_str)
    print("복호화된 문자열: ", decrypt_str)
    ```

- 문자열 압축 진행
  - user_id : 64자로 구성된 user_id를 `b64uuid` 모듈을 이용하여 44자로 바꿀 수 있습니다.
  - method : `{’GET’: 1, ‘POST’:2}` 또는 `{1:’GET’, 2:’POST’}`와 같이 HTTP Method를 숫자로 변경할 수 있습니다.
  - url : method와 마찬가지로 사전형 데이터타입을 사용하여 사용할 수 있습니다.
  - inDate : `2022-12-05T12:14:00.179Z` 의 형태를 `221205121400179`의 형태로 바꿀 수 있습니다.

- Data Compression - 압축 알고리즘 적용(gzip 라이브러리)
  - 압축 전 vs 압축 후 : 압축률 비교
  - LZ77 + huffman
  - [압축 알고리즘](https://chaarlie.tistory.com/668)
  - [gzip 라이브러리](https://chaarlie.tistory.com/670)
### 2. AWS S3 저장

- 압축된 로그데이터 저장
- 도전과제
    - AWS Athena를 사용한 검색
    - dynamic partitioning - 년도, 날짜, 시간, 분 단위로 디렉토리를 구분해서 넣는 것
        - data
            - 2023
                - 03
                    - 15
                        - 14
                            - 14:00:00.000 - 14:59:59.999 데이터 넣기(10,000개 단위)

### 3. 파이프라인 스케쥴링 구현

- AWS Lambda
- APScheduler
- Crontab

### 4. 개발 문서 작성

- ReadMe 작성
    - Architecture
    - 프로젝트 설명