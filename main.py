import io
import os
import re
import copy
import json
import requests
import base64
import uuid
from b64uuid import B64UUID
import gzip
import zlib
from io import StringIO
from cryptography.fernet import Fernet
## AWS S3
import boto3
from botocore.client import Config
## Key 보안 (dotenv)
from dotenv import load_dotenv
load_dotenv()
## 스케쥴링
from apscheduler.schedulers.blocking import BlockingScheduler
## 데이터 파티셔닝
import datetime
import time


ORIGIN_JSON_PATH = './origin_data.json'
COMPRESSED_JSON_PATH = './str_compressed_data.json'
COMPRESSED_GZIP_PATH = './comp.gz'
AWS_S3_BUCKETNAME = 'etlcp'
AWS_S3_FILENAME = 'compressed.gz'


def ETL_Pipeline():
    
    url = 'http://ec2-3-37-12-122.ap-northeast-2.compute.amazonaws.com/api/data/log'
    key = b't-jdqnDewRx9kWithdsTMS21eLrri70TpkMq2A59jX8='
    dateNum = re.compile('[0-9]')
    
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


    ## json 받아오는 함수
    def json_gen(url, key):
        fernet = Fernet(key)
        data = requests.get(url).json()
        decrypted_data = [ eval(fernet.decrypt(data[i]['data']).decode('ascii')) for i in range(len(data)) ]
        raw = copy.deepcopy(decrypted_data)
        str_compressed_data = [ str_compress(raw[i]) for i in range(len(raw)) ]
        return decrypted_data, str_compressed_data
    

    ## 파일의 데이터 중복 여부 검사 함수
    def is_duplicate(new_data, existing_data):
        for item in existing_data:
            if item == new_data: return True
        return False


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
    
    
    ## gz파일 디코딩 함수
    def gz_decoding(gzfilepath):
        with gzip.open(gzfilepath, 'rb') as f:
            json_bytes = f.read()
        decoded_json = eval(json.dumps(json.loads(json_bytes.decode('utf-8')), indent=4))
        return decoded_json

   
    ## Gzip을 사용한 데이터 압축/저장, .gz파일 업데이트 함수
    def GZIP(datafilepath, filename):
        # forPartition = []
        if not os.path.isfile(filename):
            with open(datafilepath, 'rb') as file_in:
                with gzip.open(filename, 'wb') as file_out:        
                    file_out.writelines(file_in)
            # forPartition = gz_decoding(filename)
        else:
            decoded_json = gz_decoding(filename)
            tmp_json = copy.deepcopy(decoded_json)
            with open(datafilepath, 'r') as f:
                add_data = json.load(f)
            for new in add_data:
                if not is_duplicate(new, tmp_json): # 중복 데이터가 아닌 것들만 추가
                    tmp_json.append(new)
                    # forPartition.append(new)
            if tmp_json != decoded_json: # 새로 들어온 json 데이터가 있을 때만 .gz 파일 업데이트
                with gzip.open(filename, 'wb') as f:
                    json_bytes = json.dumps(tmp_json).encode('utf-8')
                    f.write(json_bytes)
        # return forPartition


    ## AWS S3 연결 (boto3)
    def s3_connection():
        try:
            # s3 클라이언트 생성
            s3 = boto3.client(
                service_name = 's3',
                region_name = 'ap-northeast-2',
                aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY_ID'),
                config = Config(signature_version='s3v4'),
            )
        except Exception as e: print(e)
        else: 
            print('s3 connected')
            return s3

                   
    # ## AWS S3 파일 업로드
    # def s3_File_Upload(filename, bucketname, s3_path):
    #     s3 = s3_connection()
    #     try:
    #         s3.upload_file(filename, bucketname, s3_path)
    #     except Exception as e:
    #         print(e)
    # s3_File_Upload(COMPRESSED_GZIP_PATH, AWS_S3_BUCKETNAME, AWS_S3_FILENAME)
    
    
    
    ## 데이터 파티셔닝 S3 적재 함수
    def s3_upload_partitioning():
        s3 = s3_connection()
        all_data = gz_decoding(COMPRESSED_GZIP_PATH)
        flag = all_data[0]['inDate'] # 실행될 때마다 기준이 첫 데이터라 로그 데이터가 많이 쌓이면 S3 호출도 많아진다.
                                     # 밖으로 빼서 처리하는 방법을 생각해 보자.
        
        f_year = flag[:2]
        f_month = flag[2:4]
        f_day = flag[4:6]
        f_hour = flag[6:8]
        s3_path = f'data/20{f_year}_y/{f_month}_m/{f_day}_d/{f_hour}_h/'+AWS_S3_FILENAME
        
        for log in all_data:
            in_date_str = log['inDate']
            year = in_date_str[:2]
            month = in_date_str[2:4]
            day = in_date_str[4:6]
            hour = in_date_str[6:8]
            if year!=f_year or month!=f_month or day!=f_day or hour!=f_hour: # 시간대별로 데이터가 나뉜다.
                s3.upload_file('./log.gz', AWS_S3_BUCKETNAME, s3_path) # 시간이 달라지면 모아진 로그데이터 한번에 적재
                print(f'{s3_path}\nS3 적재 완료')
                f_year, f_month, f_day, f_hour = year, month, day, hour # 시간대 기준 바꿔주고
                list(map(os.remove, ['./log.json', './log.gz'])) # 전 시간에 쌓여있던 로그들 삭제
            else:
                json_save('./log.json', [log]) # 시간이 바뀌지 않는다면 그냥 로그데이터를 쌓아놓는다
                GZIP('./log.json', 'log.gz')
    
    
    # ## AWS S3 파일 업로드 (데이터파티셔닝. 새로 들어온 데이터들을 처리한다.)
    # def s3_partitioning(forPartition):
    #     s3 = s3_connection()
    #     update_data = []
    #     for log in forPartition:
    #         in_date_str = log['inDate']
    #         year = in_date_str[:2]
    #         month = in_date_str[2:4]
    #         day = in_date_str[4:6]
    #         hour = in_date_str[6:8]
    #         s3_path = f'data/20{year}_y/{month}_m/{day}_d/{hour}_h/'+AWS_S3_FILENAME
            
            
    #         json_save('./log.json', [log])
    #         GZIP('./log.json', 'log.gz')
    #         s3.upload_file('./log.gz', AWS_S3_BUCKETNAME, s3_path)
            
            
    #     ## 새로운 데이터 대처를 위해 사용 후 log 파일 삭제
    #     list(map(os.remove, ['./log.json', './log.gz']))
    
    # ## AWS S3 파일 업로드 (데이터파티셔닝. 새로 들어온 데이터들을 처리한다.)
    # def s3_partitioning(forPartition):
        
    #     s3 = s3_connection()
    #     s3.upload_file(filename, bucketname, loadname)
        
    #     for log in forPartition:
    #         in_date_str = log['inDate']
    #         year = in_date_str[:2]
    #         month = in_date_str[2:4]
    #         day = in_date_str[4:6]
    #         hour = in_date_str[6:8]
    #         s3_folder = f'data/20{year}_y/{month}_m/{day}_d/{hour}_h/'
    #         s3_path = s3_folder+AWS_S3_FILENAME
            
    #         # 폴더가 없으면 생성
    #         if not s3.list_objects_v2(Bucket=AWS_S3_BUCKETNAME, Prefix=s3_folder)['Contents']:
    #             s3.put_object(Bucket=AWS_S3_BUCKETNAME, Key=s3_folder+'/')
            
    #         json_save('./log.json', [log])  # 이 부분이 좀 꺼림칙하다.. 수정이 필요할 수도
    #         GZIP('./log.json', 'log.gz')    # 새로운 데이터가 들어왔을 때 데이터가 정상적으로 추가되는지 확인할 것!!
    #         new_data = gz_decoding('./log.gz')
    #         # s3.upload_file('./log.gz', AWS_S3_BUCKETNAME, s3_path)
            
            # 기존 파일 내용을 가져와서 JSON 객체로 변환
            # response = s3.get_object(Bucket=AWS_S3_BUCKETNAME, Key=s3_path)
            # data = response['Body'].read()
            # old_data = gz_decoding(data)
            
            # update = old_data.extend(new_data)
            # json_save('./update.json', update)
            # GZIP('./update.json', 'update.gz')
            # s3.upload_file('./update.gz', AWS_S3_BUCKETNAME, s3_path)
            
            
    #     ## 새로운 데이터 대처를 위해 사용 후 log 파일 삭제
    #     list(map(os.remove, ['./log.json', './log.gz']))
        
        
    # ## 데이터 파티셔닝을 위한 inDate(ISO 8601 형식) 파싱
    # def date_partitioning(data, add_json): # decrypted_data
    #     for item, added in zip(data, add_json):
    #         in_date_str = item['inDate'][:-1]  # Z 제거
    #         dt = datetime.datetime.fromisoformat(in_date_str)
    #         year, month, day, hour = dt.year, dt.month, dt.day, dt.hour
    #         s3_path = f'data/{year}_y/{month}_m/{day}_d/{hour}_h/'+AWS_S3_FILENAME
    
    
    ## json 복호화/문자열압축 로그 데이터 
    decrypted_data, str_compressed_data = json_gen(url, key)
    json_save(ORIGIN_JSON_PATH, decrypted_data)
    json_save(COMPRESSED_JSON_PATH, str_compressed_data)
    print('Extract(데이터 추출) Complete!')
    
    GZIP(COMPRESSED_JSON_PATH, COMPRESSED_GZIP_PATH)
    print('Transform(데이터 변환) Complete!!')
    
    s3_upload_partitioning()
    print('Load(데이터 저장) Complete!!!\n\n')
    
    print(f'전체 json 데이터 길이: {len(gz_decoding(COMPRESSED_GZIP_PATH))}\n')
    print(f'ETL_Pipeline 가동된지{round(len(gz_decoding(COMPRESSED_GZIP_PATH))/600, 2)}hour 경과\n\n')
    # if len(gz_decoding(COMPRESSED_GZIP_PATH)) % 100 == 0: 
    #     # s3_File_Upload(COMPRESSED_GZIP_PATH, AWS_S3_BUCKETNAME, AWS_S3_FILENAME) # S3 compressed.gz 파일 최신화
    #     print('Load(데이터 저장) Complete!!!\n\n')
    # else:
    #     print(f'gzip json user id 개수: {len(gz_decoding(COMPRESSED_GZIP_PATH))}')

# ETL_Pipeline()

## APscheduling, cron 표현식
scheduler = BlockingScheduler()
# 매일 5분 간격으로 실행
scheduler.add_job(ETL_Pipeline, 'cron', minute='*/5') # crontab: */5 * * * *
scheduler.start()