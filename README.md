# History

## 2023.03.10

1. 깃헙 레포 생성
2. ETL 파이프라인 기본 개념 학습

**언제든지 필요한 데이터를 가져와 꺼내 쓸 수 있도록 데이터를 계속 쌓아두는 파이프를 만드는 것**


- 데이터파이프라인이 하는 일
  - Data extracting: 데이터 추출
  - Data transforming: 데이터 변환
  - Data combining: 데이터 결합
  - Data validating: 데이터 검증
  - Data loading: 데이터 적재  
  &nbsp;  

  데이터 추출, 변환, 적재를 묶어 ETL 이라고 한다.  
  
  &nbsp;  
    ETL은 데이터 파이프라인 하위 개념으로, 하나의 시스템에서 데이터를 추출해 변환하여 데이터 베이스 or 데이터 웨어하우스에 차곡차곡 쌓아둔다.  
    &nbsp;
  - Extraction(API, Crawling)
    - Backend API 서버에서 응답하는 JSON 데이터  
    &nbsp;
  - Transform(Compression, Format Conversion)
    - 데이터 변환, 압축/저장 과정 
    - 압축 알고리즘
      - [LZ77 알고리즘](https://nightohl.tistory.com/entry/LZ77-%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%98)
      - [허프만 코딩 알고리즘](https://www.techiedelight.com/ko/huffman-coding/)  
    &nbsp;
  - Load
    - 데이터웨어하우스
    - 분산파일 시스템
    - NoSQL, 병렬 DBMS
    - 네트워크 구성 저장 시스템
    - 클라우드 파일 저장 시스템(AWS S3)  
    &nbsp;  
---
## 2023.03.11

1. 문자열 압축
### Error 처리
```
    data['user_id'] = base64.b64encode(bytes.fromhex(data['user_id'])).decode('utf-8') 
    ValueError: non-hexadecimal number found in fromhex() arg at position 0
```
- json 데이터의 ['user_id'] 가 16비트 문자열이 아닌 경우 발생하는 에러
```
    try:
        compressed_user_id = base64.b64encode(bytes.fromhex(data['user_id'])).decode('utf-8')
    except ValueError:  # 16진수 문자열이 아닌 경우
         compressed_user_id = base64.b64encode(uuid.UUID(data['user_id']).hex).decode('utf-8')
    
```
16진수 문자열이 아닌 경우에도 압축을 진행해야 한다
1. uuid.UUID() 함수를 사용하여 입력값 data['user_id']를 UUID 객체로 변환
2. UUID 객체의 16진수 표현을 uuid.UUID().hex를 통해 구한 뒤, 이를 다시 base64.b64encode() 함수를 사용하여 base64로 인코딩
3. decode() 메소드를 사용하여 bytes 객체를 str 객체로 디코딩

압축된 정보를 원래의 값으로 디코딩할 때는 base64.b64decode() 메소드 사용하면 된다.

--- 

### base64 인코딩에 대하여
base64 인코딩은 8비트 이진 데이터를 ASCII 문자코드로 변환하는 인코딩 방식이다. 입력 데이터 보다 더 길어질 수도 있지만, 모든 기기나 소프트웨어에서 이해할 수 있는 ASCII 문자열로 변환해주기 때문에 데이터를 안전하게 전송하거나 저장하는 데 사용된다.

base64 인코딩은 3바이트씩 끊어서 4개의 6비트 그룹으로 나누고, 각각을 64개의 문자로 매핑한다. 이렇게 매핑된 문자들을 순서대로 나열한 문자열이 base64로 인코딩된 문자열이다.

base64 인코딩 결과물은 원래 데이터보다 항상 같거나 혹은 길어지는 특징이 있는데, 이 길이는 원래 데이터의 길이에 의해 결정된다. 3의 배수로 끊어진다는 가정하에 다음과 같은 공식을 통해 계산된다.

$$\frac{4}{3} \times \text{원본 데이터의 길이}$$

16바이트의 UUID를 base64 인코딩했을 때 결과물의 길이가 항상 44자로 고정되는 이유는, 16바이트의 UUID를 base64 인코딩하면 항상 24바이트로 나오기 때문이다. 이 24바이트의 문자열에서 마지막 2바이트는 패딩 문자로, base64 인코딩 결과물의 길이에 포함되지 않는다. 따라서 이를 제외하면 22바이트의 문자열이 남게 되며, 이는 44자의 길이로 표현된다.

---
