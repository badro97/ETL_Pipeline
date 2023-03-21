# ETL Pipeline Basemodel 
&nbsp;  
## 프로젝트 개요
API 서버에서 주기적으로 생성되고 있는 암호화된 로그데이터를 추출하여 복호화 하고, 효율적으로 압축 변환을 거친 뒤 AWS S3에 파티셔닝하여 저장하는 ETL 파이프라인 구축 프로젝트  
&nbsp;  

## ETL_Pipeline  
추출(Extraction) - 변환(Transformation) - 로드(Load)의 절차를 따르는 데이터의 수집 및 가공•정비•구축의 데이터 처리 프로세스  

---
장점  
- 다양하고 복잡한 변환 수행    
- 데이터 통제 유리  
- 시각화 편리  

단점  
- 실시간 처리 부적합 (대용량 파일)
- 불필요한 대기 시간 발생  

활용
- 배치

사례
- DW구축, 데이터 집중화, 표준화
- Data Silo간 이동

---  
&nbsp; 
## Architecture  
&nbsp;  

![Untitled](https://user-images.githubusercontent.com/49307262/226516012-2b09eb37-dc1b-4ef9-9a4d-99f31b8b152b.png)  
![image](https://user-images.githubusercontent.com/49307262/226508918-91910ef5-a0e7-457c-8a14-d13a1f0f18d0.png)
Json log Data &rarr; Extract & Transform & Load &rarr; AWS S3 upload &rarr; AWS Athena  

### 데이터 추출 (Extract)
```python
decrypted_data, str_compressed_data = json_gen(API_URL, FERNET_KEY)
json_save(ORIGIN_JSON_PATH, decrypted_data)
json_save(COMPRESSED_JSON_PATH, str_compressed_data)
print('Extract(데이터 추출) Complete!')
```
- Json 데이터 추출 후 Json파일 저장(문자열 압축 적용)  
&nbsp;  

### 데이터 변환 (Transform)
```python
GZIP(ORIGIN_JSON_PATH, ORIGIN_GZIP_PATH) # 모든 원본 데이터를 쌓아놓은 압축파일
GZIP(COMPRESSED_JSON_PATH, COMPRESSED_GZIP_PATH)
print('Transform(데이터 변환) Complete!!')
```
- 저장한 Json 파일을 gzip 압축하여 변환.  
&nbsp;  

### 데이터 저장 (Load)
```python
s3_upload_partitioning()
print('Load(데이터 저장) Complete!!!\n\n')
``` 
- .gz 압축파일을 파티셔닝하여 AWS S3 객체 업로드  
&nbsp;  

## 수행 절차

0. json 데이터 문자열 압축
    ```python
    ## 문자열 압축 함수
    def str_compress(data):
        ## B64UUID 모듈을 사용하여 압축하는 방법 (최대 36자(32자 + '-'4자) 혀용하므로 '-'가 포함되지 않은 64자의 문자열이라면 반으로 나눠서 진행)
        data['user_id'] = B64UUID(data['user_id'][32:]).string + B64UUID(data['user_id'][:32]).string
        
        ## HTTP Method를 숫자로 변경
        data['method'] = {'GET': 1, 'POST': 2}.get(data['method'], 0) # 사전에 없는  method면 0

        ## url을 딕셔너리 타입을 사용해 숫자로 변경
        url_dict = {
            '/api/products/product/': 1, 
        }
        data['url'] = url_dict.get(data['url'], 0) # 사전에 없는 url이면 0
        
        ## inDate 형식 변환
        data['inDate'] = ''.join(dateNum.findall(data['inDate']))[2:] # 년도 앞 부분(20) 생략 
        return data
    ``` 
    - json 로그 문자열 변환 &rarr; 전체 파일 크기 감소  
    
    - b64uuid 모듈을 사용해 문자열 압축  
    &nbsp;  
    
1. json 로그를 받아와 문자열 변환 후 저장
    ```python
    ## json 받아오는 함수
        def json_gen(url, key):
            fernet = Fernet(key)
            data = requests.get(url).json()
            decrypted_data = [ eval(fernet.decrypt(data[i]['data']).decode('ascii')) for i in range(len(data)) ]
            raw = copy.deepcopy(decrypted_data)
            str_compressed_data = [ str_compress(raw[i]) for i in range(len(raw)) ]
            return decrypted_data, str_compressed_data
    ```
    - 암호화된 json 로그의 data 문자열 복호화하여 반환  
    
    - cryptography 모듈 사용하여 복호화 진행  
    &nbsp;  

2. 파일 압축/저장
    ```python
    ## json 로그 데이터 저장/추가. 중복되는 데이터는 추가 하지 않음
    def json_save(filepath, add_data):
        if not os.path.isfile(filepath):
            with open(filepath, 'w') as file:
                json.dump(add_data, file, indent=4)
        else:
            with open(filepath, 'r') as f:
                data = json.load(f)
            for new in add_data:
                if not is_duplicate(new, data): # 중복 데이터가 아닌 것들만 추가
                    data.append(new)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)


    def GZIP(datafilepath, filename):
            if not os.path.isfile(filename):
                with open(datafilepath, 'rb') as file_in:
                    with gzip.open(filename, 'wb') as file_out:        
                        file_out.writelines(file_in)
            else:
                decoded_json = gz_decoding(filename)
                tmp_json = copy.deepcopy(decoded_json)
                with open(datafilepath, 'r') as f:
                    add_data = json.load(f)
                for new in add_data:
                    if not is_duplicate(new, tmp_json): # 중복 데이터가 아닌 것들만 추가
                        tmp_json.append(new)
                if tmp_json != decoded_json: # 새로 들어온 json 데이터가 있을 때만 .gz 파일 업데이트
                    with gzip.open(filename, 'wb') as f:
                        json_bytes = json.dumps(tmp_json).encode('utf-8')
                        f.write(json_bytes)
    ```
    - gzip 모듈을 사용하여 압축 진행
    - 저장한 Json파일을 불러와 Gzip 압축하여 .gz파일로 저장 (중복 값 무시)  
        - 데이터 손실 및 프로세스 오류 발생 시 비교를 위해 원본 데이터를 로컬에 남겨놓는다.  
            - 파일을 읽고 쓰는 리소스가 필요   
            
            - 단순 처리 속도를 위해서 파일 입출력 과정 생략 가능  
    &nbsp;  

3. 데이터 파티셔닝 S3 적재
    ```python
    def s3_upload_partitioning():
        comp_data = gz_decoding(COMPRESSED_GZIP_PATH)
        flag = comp_data[0]['inDate']
        
        f_year = flag[:2]
        f_month = flag[2:4]
        f_day = flag[4:6]
        f_hour = flag[6:8]
        s3_path = f'data/20{f_year}_y/{f_month}_m/{f_day}_d/{f_hour}_h/'+AWS_S3_FILENAME
        
        for log in comp_data:
            in_date_str = log['inDate']
            year = in_date_str[:2]
            month = in_date_str[2:4]
            day = in_date_str[4:6]
            hour = in_date_str[6:8]
            if year!=f_year or month!=f_month or day!=f_day or hour!=f_hour: # 시간대 별로 데이터가 나뉜다
                s3 = s3_connection() # s3 버킷 연결
                s3.upload_file('./log.gz', AWS_S3_BUCKETNAME, s3_path)       # 시간이 달라지면 모아진 로그데이터 한번에 적재
                print(f'{s3_path}\nS3 적재 완료')
                f_year, f_month, f_day, f_hour = year, month, day, hour      # 시간대 기준 바꿔주고
                list(map(os.remove, ['./log.json', './log.gz', COMPRESSED_JSON_PATH, COMPRESSED_GZIP_PATH])) # 전 시간에 쌓여있던 로그, 압축파일들 삭제
                json_save('./log.json', [log]) # 바뀐 시간대로 로그를 다시 써준다
                GZIP('./log.json', 'log.gz')
            else:
                json_save('./log.json', [log]) # 시간이 바뀌지 않는다면 그냥 로그데이터를 쌓아놓는다
                GZIP('./log.json', 'log.gz')
    ```
    - 시간대를 기준으로 1시간에 한 번씩만 S3 버킷 업로드를 진행한다.  
    
    - 로그 자체는 현 시간을 담고 있는 듯하나, 무작위 시간대가 담긴 로그 정보 또한 처리할 수 있어야 한다.  
    
    - 따라서 json 데이터의 ['inDate']를 기준점으로 설정했다.
        - 저장해놓은 로그를 돌며 시간대 변화를 관찰  
        
        - S3 객체 업로드 후 데이터 초기화 &rarr; 새로운 데이터 대처   
         
    - 3분마다 100개의 json 로그가 생성된다.  
        - 3분 스케줄링의 경우 시간당 2000개의 로그가 쌓이게 되는데 이를 위해서 1초에 최소 11개 이상의 로그 처리가 필요하다.  
        
        - 일반적인 파일 입출력 함수를 사용하는 이상 시스템 과부화가 우려되므로 5분 ~ 10분 스케줄링이 적합하다.  
    &nbsp;  

4. EC2 인스턴스 내에서 파이프라인 실행
    - APScehduling, 5분 기준 7시간 이상 정상 작동.  
    
    - 이후 2초 정도의 딜레이가 생겨 정지되었으나 다른 원인일 수 있다.
        - 안정적으로 초당 1개 이상의 로그 처리가 필요한 10분 스케줄링으로 변경.  
    &nbsp;  

## [프로젝트 진행 과정](https://github.com/badro97/ETL_Pipeline/blob/main/History.md)

&nbsp;  

## 수행 결과  

<img width="1439" alt="Screenshot 2023-03-20 at 7 19 19 PM" src="https://user-images.githubusercontent.com/49307262/226311460-93507ea8-ead0-4f9d-8a5d-448b0cee920b.png">  

- S3 데이터 파티셔닝 업로드 정상 작동
    - 시간 별로 json 데이터가 구분되어 정상적으로 저장된다
- ETL_Pipeline 베이스 모델 구축 완료  
&nbsp;  

## 추후 개선사항  

1. AWS Athena 조회, AWS Glue 크롤러 사용법 숙지하고 적용하기  

2. 대용량 파일 프로세스 처리 최적화
    - Airflow 학습 후 적용