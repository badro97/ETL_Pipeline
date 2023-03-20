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
## 2023.03.13
1. 문자열 압축 수정
- base64 + uuid -> B64UUID 모듈로 수정
  - B64UUID 모듈은 32자의 문자와 4자의 '-'를 변환해 주는 모듈이다.
  - '-'는 모두 제거하므로 결국 32자의 문자열을 22자로 압축해 준다.
  - 64자의 문자열을 압축하기 위해 슬라이싱하여 붙여주는 방법을 이용.
  - base64 인코딩과 달리 패딩 문자 '=' 가 붙지 않는 장점이 있다.

2. gzip() 사용하여 데이터 압축 진행
- 먼저 json 파일을 저장한 뒤에 비교하였다.
- 쓴 파일을 다시 열어 파일이 깨지지 않고 압축이 되었는지 확인 후 진행.

### 특이한 점
1. **문자열 압축을 진행하지 않은 복호화 원본 Json파일의 gzip 압축 결과  
압축률이 무려 99.89% 로 가장 높았다.**  
문자열 압축을 진행한 파일의 gzip 압축 결과보다 더 압축률이 높았으며, 파일의 크기도 더 작았다.  

2. 압축을 진행할 때마다 아주 근소한 차이(약 1B)로 압축파일 크기가 변한다.
---
### 압축률 비교  
&nbsp;

원본 Json:  39782 Bytes  
문자열 압축 Json:  34082 Bytes  
압축률:  14.33  %  
&nbsp;

원본 Json:  39782 Bytes  
원본 Json + Gzip 압축:  42 Bytes  
압축률:  99.89  %  
&nbsp;

문자열 압축 Json:  34082 Bytes  
문자열 압축 Json + Gzip 압축:  51 Bytes  
압축률:  99.85  %  
&nbsp;

원본 Json:  39782 Bytes  
문자열 압축 Json + Gzip 압축:  51 Bytes  
압축률:  99.87  %  

---
## 2023.03.14

1. Gzip 압축 함수 오류 수정  
오류:  
gzip 파일을 쓸 때 열어놓은 파일에 써야 하지만 그 부분이 들여 쓰기가 안 되어 있어 열고 쓰기가 따로 진행됨 -> data 매개변수의 str 값 그 자체가 저장되기 때문에 파일 이름 길이에 따라 파일 크기가 변하는 기현상이 발생하게 된다.
```
    # 파일 쓰기
        with gzip.open(filename, 'wb') as f:
            f.write(data.encode('utf-8'))
    # 쓴 파일 열기
        with gzip.open(filename, 'rb') as f:
            read_data = f.read().decode('utf-8') 
```
&nbsp;

따라서 아래와 같이 GZIP함수 전체 코드를 수정하였고
```
    def GZIP(data, filename):
        if not os.path.isfile(filename):
            with open(data, 'rb') as file_in:
                with gzip.open(filename, 'wb) as file_out:        
                    file_out.writelines(file_in)
        return os.path.getsize(filename)
    
```
이후 압축률 비교 프로세스가 오류 없이 직관적으로 출력되는 것을 확인할 수 있었다.  
&nbsp;

원본 Json:  39782 Bytes  
문자열 압축 Json:  34082 Bytes  
압축률:  14.33  %  
&nbsp;

원본 Json:  39782 Bytes  
원본 Json + Gzip 압축:  5169 Bytes  
압축률:  87.01  %  
&nbsp;

문자열 압축 Json:  34082 Bytes  
문자열 압축 Json + Gzip 압축:  4679 Byte  
압축률:  86.27  %  
&nbsp;

원본 Json:  39782 Bytes  
문자열 압축 Json + Gzip 압축:  4679 Bytes  
**압축률:  88.24  %**
&nbsp;  

---
L777 + Huffman = deflate 알고리즘 (gzip의 압축 알고리즘과 같다)  
gzip 포맷은 추가적인 헤더와 체크섬을 사용하여 오류검출에 더 강점이 있다.
deflate보다 gzip이 더 권장되는 것으로 보인다.  
### [L777 + Huffman](https://velog.io/@shroad1802/%EC%9B%B9-%EA%B0%9C%EB%B0%9C%EA%B3%BC-%EC%95%95%EC%B6%95-%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%98)

---
## 2023.03.15
### Amazon S3
확장성과 데이터 가용성 및 보안과 성능을 제공하는 객체 스토리지 서비스  
원하는 만큼의 데이터를 저장하고 보호할 수 있다.  

1. AWS S3 버킷생성
- 버킷 이름(etlcp) 및 AWS 지역(ap-northeast-2(서울))지정
- 퍼블릭 액세스 설정  
외부에 S3를 공개할 경우 모든 퍼블릭 액세스 차단 체크해제 (체크해제함)
- 버킷 버전 관리 및 기본 암호화.  
버킷 버전 관리 기능 활성화 -> 파일을 버전별로 관리하기 때문에 비용이 더 들지만 실수로 파일을 삭제해도 복원할 수 있다. (비활성화함)  
기본 암호화 활성화 -> 버킷에 저장되는 모든 새 객체를 암호화한다. 객체를 다운 로드할 때 암호를 해독해야 한다. (비활성화함)  
&nbsp;
2. 버킷 정책 생성/추가  
[버킷 정책 생성기](https://awspolicygen.s3.amazonaws.com/policygen.html)  
Select Type of Policy: S3 Bucket Policy  
Effect: Allow (접근하는 사람을 선택해서 받지 않고 모두 허용)  
principal: * (모든 사람 접근 가능)  
Actions: 특정 작업의 허용 또는 거부 여부를 지정. * (모든 작업 허용)  
ARN: arn:aws:s3::bucketname*/  
&nbsp;
3. IAM 사용자 추가    
**AWS의 루트 사용자의 Key가 노출되면 해당 계정의 리소스가 위험하므로, AWS에서는 IAM에서 사용자를 만들어 각각 AWS에 있는 리소스에 접근하게 설정하라고 권장한다.**

- AWS 자격 증명 유형 선택:  
액세스 키 -> 문제 발생  
access 키, access 비밀키가 발급되지 않고 다른 형식의 로그인 ID와 콘솔 비밀번호가 발급됨 ->  
해당 정보로 콘솔에 로그인했으나 액세스 키 관련 정보를 찾지 못했다. ->  
일단 루트 사용자의 액세스 키를 사용함. (S3 서비스 콘솔에서 액세스 키 발급) ->  
**IAM 사용자 액세스 키 발급 성공(로컬 어플리케이션 사용 액세스 키)** -> S3 적재 완료  
key 보안을 위해 dotenv 모듈 사용(.env파일에 key를 환경 변수로 지정하고 불러오는 방식)  
&nbsp;
4. pytyhon boto3 이용하여 S3에 압축파일 업로드  
    ```
        ## AWS S3 파일 업로드
        def s3_File_Upload(filename, bucketname, loadname):
            try:
                s3.upload_file(filename, bucketname, loadname)
                print(f'{loadname}저장 완료!!')
            except Exception as e:
                print(e)

        s3_File_Upload('./comp.gz', 'etlcp', 'compressed.gz')
    ```
    <img width="1051" alt="Screenshot 2023-03-15 at 11 01 12 AM" src="https://user-images.githubusercontent.com/49307262/225185412-6b667629-487b-416b-85ff-bdb4903fda80.png">

&nbsp;
### References
- [[AWS] Python으로 AWS S3에 이미지 파일 업로드](https://fubabaz.tistory.com/20)
- [[AWS] S3 bucket policy (S3 버킷 정책)](https://24hours-beginner.tistory.com/151)
- [파이썬으로 S3 버킷에 파일 업로드하기(boto3)](https://baejinsoo.github.io/aws/AWS-02/)
- [python-dotenv _ 환경변수를 .env 파일로 관리하기](https://daco2020.tistory.com/480)

---
## 추가
1. zlib vs gz -> gz 파일 크기가 더 작으므로 gz 사용.  
2. gz 디코딩 함수 작성. 디코딩 문제없이 작동함.  
3. 받아오는 json 파일 중복된 값이 아닌 것들만 덮어쓰고 저장하는 로직 작성 -> 작동은 하나...  
API에서 받아오는 데이터의 문자열은 전부 다르게 표현되지만(record_id는 멈춰있음)  
fernet.decrypt를 거치면 죄다 똑같은 데이터로 복호화 된다...???!?!  
따라서 새로 추가되는 json 데이터가 항상 없다..  
request.get()에서 params을 time.time() 현 시간으로 설정하여 캐싱을 방지해도 결과는 똑같다.  
**data = requests.get(url).json()에서  
data 값의 문자열들은 항상 다르게 출력되지만 도대체 왜  
그 문자열을 복호화 한 값들은 모두 같은 것일까?**  
결론 > API 서버 업데이트가 잠시 정지되어 있었기 때문..문자열 바뀌는 건 암호화 로직이 그러한 듯 싶다.  
현재는 정상 작동.  

---
## 2023.03.16

1. gz 파일 덮어쓰기 및 저장 함수
2. 함수 모두 합치기 (ETL_Pipline)
    - json 데이터 길이로 S3 저장하는 함수 호출 횟수 제한
3. 스케줄러 적용하기
    - APscheduler 사용, cron 표현식
4. 데이터파티셔닝 구현
    - 새로 들어온 데이터만을 가지고 S3 .gz 최신화한다.(.gz 최초 저장하는 경우만 예외)
        - 원래 있었던 데이터는 다시 하나하나 확인하고 나눠서 적재할 필요가 없기때문
    - 로컬에도 시간 기준 파티션을 나눠 폴더를 생성하고 gz를 저장할 수 있는지 확인해 볼 것.
        - 폴더의 구조 및 내부 파일들을 그대로 들고 와서 S3에 적재하는 방법이 있을까?
    - 현재 API서버 업로드가 정지됨. 잘 돌아가는지는 내일 확인해보고 최종본 커밋하기  
    - 일단 .gz 최초 생성 시 파티셔닝 정상작동 확인.
        - 데이터가 추가되는 경우 확인 필요.
    <img width="1095" alt="Screenshot 2023-03-16 at 7 22 21 PM" src="https://user-images.githubusercontent.com/49307262/225587849-ac1290bf-650c-4c5e-9d69-d8ea5bdf6c26.png">

    ### 문제점
    1. 100개의 데이터가 추가되므로 100번의 업로딩이 이루어진다.
        - 시간이 약간 소요됨, 혹시라도 서비스 사용요금이 많이..?
        - 아예 json 데이터를 받아올 때 년도/월/일/시간으로 구분해서 저장해 주는 게 좋으려나 싶다.
    
### 내일 할 것
1. 데이터파티셔닝 확인/수정
2. AWS Athena로 데이터 조회하기
3. bigquery 알아보기  

---

## 2023.03.17
AWS 키 털림 -> 과금폭탄 -> IAM user/액세스 키 삭제, MFA 설정  
보안 주의할 것
1. 깃헙레포 새로 생성
2. 데이터파티셔닝 수정
    - S3에는 객체로 저장되기 때문에 데이터를 붙여 쓸 수 없고 다시 써야 함
        - S3 객체를 불러와서 데이터를 추가하고 다시 쓰는 방법은 데이터가 많아질수록 처리시간과 리소스가 많이 필요해진다.
    - 어차피 생성되는 로그 데이터['inDate']는 현 시간을 담고 있는 듯하지만 혹시라도 다른 시간이 끼어들어가 있는 경우를 대비해야 한다.
        - 시간대를 기준으로 연도, 월, 일, 시간이 바뀌면 그때 S3에 데이터를 저장하도록 한다.
        - 시간대가 바뀌기 전까지는 로그를 쌓아놓고 바뀌는 순간 적재한 뒤 쌓아놓았던 로그를 삭제(새로운 데이터 대처) 해준다.
        
      <img width="1095" alt="Screenshot 2023-03-17 at 3 26 06 PM" src="https://user-images.githubusercontent.com/49307262/225829498-aa48327c-e691-4389-a4ed-2eab9770731e.png">
    - 들어가 있는 json 로그데이터들을 살펴보면
      <img width="1087" alt="Screenshot 2023-03-17 at 3 27 48 PM" src="https://user-images.githubusercontent.com/49307262/225829698-3c3c37a6-e3a8-4430-bc95-ea320cbfe8c5.png">
    - 마지막 데이터의 inDate가 14시59분으로 14시에 생성된 데이터들을 잘 담고 있는 것을 확인 할 수 있었다.
    - 일단은 하루종일 돌려보고 최종 수정
        - 502 error로 돌려보지 못함
      
3. 스케줄링
    - APscheduler, cron표현식
    - 5분 간격으로 실행하도록 설정. (crontab: */5 * * * *)  
  

[[AWS] 📚 Athena 사용법 정리 (S3에 저장된 로그 쿼리하기)](https://inpa.tistory.com/entry/AWS-%F0%9F%93%9A-Athena-%EC%82%AC%EC%9A%A9%EB%B2%95-%EC%A0%95%EB%A6%AC-S3%EC%97%90-%EC%A0%80%EC%9E%A5%EB%90%9C-%EB%A1%9C%EA%B7%B8-%EC%BF%BC%EB%A6%AC%ED%95%98%EA%B8%B0)

---

## 2023.03.18
1. 데이터파티셔닝 수정
    - 돌려보지 못함
        - api 서버 502 error -> 종료된 듯..  
            - api url, fernet 키 dotenv 적용..  
            
    - 압축파일을 제거하여 추가 데이터를 처리하는 과정에서 함수 실행될 때마다 삭제되어 시간 반영이 안되는 문제가 발생한다.  
        - 적재가 된 경우에만 삭제하도록 for문-if문 내부로 옮김.  
    &nbsp;
2. 로그가 쌓일수록 읽고 저장하는 횟수가 늘어난다.
    - 에러 발생  
        - Execution of job "ETL_Pipeline (trigger: cron[minute='*/1'], next run at: 2023-03-18 14:35:00 KST)" skipped: maximum number of running instances reached (1)  
        
    - 스케줄링 시간을 조정해 그에 따라 읽어와야 하는 로그 데이터 수와 처리시간 사이의 절충안을 찾아야 한다.
        - 5분 스케줄링 = 시간당 1200 개의 로그가 쌓임(초당 4개 이상의 로그 처리 필요함)  
        
        - 10분 스케줄링 = 시간당 600 개의 로그가 쌓이며 초당 1개의 로그 처리가 되므로 가장 안정적일 것이라 판단됨.  
        
    - 5분 스케줄링 결과. 정상적으로 S3에 데이터가 적재되었음을 확인했다.
        <img width="1093" alt="Screenshot 2023-03-18 at 4 56 50 PM" src="https://user-images.githubusercontent.com/49307262/226093168-db45b295-e1fb-42b3-bc37-d443b13fb444.png">  
        <img width="1089" alt="Screenshot 2023-03-18 at 4 56 40 PM" src="https://user-images.githubusercontent.com/49307262/226093149-649452e3-802f-4d9b-b595-df2918450680.png"> 
    - 15시 8분에 실행. 15:08 ~ 15:58 동안 쌓인 로그들 16:05 분에 1번의 S3 파일 업로드로 적재 완료. 총 1100 개의 로그가 저장되었다.    
    - But, 16시 33분 이후로 서버로부터 json 데이터를 받아오지 못함  
        - json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)  
        - API url 504 에러  
        - 원활한 스케줄링을 위해선 서버가 작동되는 시간을 정확히 알 필요가 있다.  
&nbsp;
3. EC2에 레포 클론하고 스케줄링
    - 인스턴스 만든 후 .pem 파일 chmod 400 으로 권한 설정 -> connection.sh 생성 후 실행.
    - 깃 설치 후 깃 레포 클론
    - 계속되는 pip 문제로 requirements.txt 설치는 물론 pip 명령어도 먹통이 되는 상황 발생
        - 아마도 setuptools 버전 문제 혹은 pip 버전 문제일 가능성이 높았지만.. setuptools를 업그레이드 해줘도 아무런 변화가 없었다.
    - **miniconda 설치 -> 콘다가상환경 생성 (python=3.9) -> 성공**  
&nbsp;
4. File Zilla 사용해서 로컬 데이터 통신
    - .env 파일을 로컬에서 우분투로 넣어줘야 실행이 가능하기떄문
    1. File Zilla Setting -> SFTP -> Add key file -> .pem 파일 추가
    2. Site Manager -> new site -> protocol:SFTP -> Host는 인스턴스의 Public IPv4 DNS -> port: 22 (기본값) -> logon type: Key file -> user: ubuntu -> .pem 파일 추가 -> 항상 신뢰 --> 연결성공.
    3. .env 파일 복사해서 넣어주기
        <img width="1198" alt="Screenshot 2023-03-18 at 11 47 22 PM" src="https://user-images.githubusercontent.com/49307262/226113217-e2ba390d-5428-49e2-ae5c-fba2467abe8f.png">  
    4. ETL_pipline 인스턴스 내 정상 실행 확인.  
    
---
## 2023.03.20
  
  
1. AWS Glue 크롤러 생성 후 Athena 실행  
    <img width="1332" alt="Screenshot 2023-03-20 at 12 11 58 PM" src="https://user-images.githubusercontent.com/49307262/226243210-e4b1f7a5-06d8-45f3-a9a9-f47fa64c5578.png">
    전체 버킷 폴더를 크롤링. array는 한 줄만 들어가있다.  
    
    <img width="1319" alt="Screenshot 2023-03-20 at 12 57 12 PM" src="https://user-images.githubusercontent.com/49307262/226243343-138782f0-832e-414b-a507-8badb31e00b9.png">

- JSON 데이터의 형식에 맞춰 테이블은 정상적으로 생성되지만, SELECT * FROM으로 데이터를 확인 해보려 하니 아무런 값도 출력이 안 된다.  

- 쿼리를 맞게 작성한 것인지 모르겠다..
    - Athena 사용법에 관한 공부가 필요  

- 저장되어있는 JSON 파일의 형식([{}])문제일 수도 있음.  
    - []는 빼고, 한 줄씩 dict 형식의 로그만 덧붙이는 식으로 대충 저장하면 될런지 잘 모르겠다.