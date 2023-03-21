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
ORIGIN_GZIP_PATH = './origin.gz'
COMPRESSED_JSON_PATH = './str_compressed_data.json'
COMPRESSED_GZIP_PATH = './str_comp.gz'
AWS_S3_BUCKETNAME = 'etlcp'
AWS_S3_FILENAME = 'compressed.gz'

API_URL = os.getenv('API_URL')
FERNET_KEY = os.getenv('FERNET_KEY').encode()
dateNum = re.compile('[0-9]')


def ETL_Pipeline():
    
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


    ## AWS S3 연결 (boto3)
    def s3_connection():
        try:
            s3 = boto3.client(
                service_name = 's3',
                region_name = 'ap-northeast-2',
                aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY_ID'),
                config = Config(signature_version='s3v4'),
            )
        except Exception as e: print(e)
        else: return s3


    ## 데이터 파티셔닝 S3 적재 함수
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
        
    
    
    
    decrypted_data, str_compressed_data = json_gen(API_URL, FERNET_KEY)
    json_save(ORIGIN_JSON_PATH, decrypted_data)
    json_save(COMPRESSED_JSON_PATH, str_compressed_data)
    print('Extract(데이터 추출) Complete!')
    
    
    GZIP(ORIGIN_JSON_PATH, ORIGIN_GZIP_PATH) # 모든 원본 데이터를 쌓아놓은 압축파일
    GZIP(COMPRESSED_JSON_PATH, COMPRESSED_GZIP_PATH)
    print('Transform(데이터 변환) Complete!!')
    
    
    s3_upload_partitioning()
    print('Load(데이터 저장) Complete!!!\n\n')
    
    
    print(f'전체 json 데이터 길이: {len(gz_decoding(ORIGIN_GZIP_PATH))}\n')

    if len(gz_decoding(ORIGIN_GZIP_PATH)) % 600 == 0: # 10분 스케줄링 기준
        print(f'ETL_Pipeline 가동된지 {len(gz_decoding(ORIGIN_GZIP_PATH))//600} hour 경과\n\n')




# ETL_Pipeline()


## APscheduling
scheduler = BlockingScheduler()
# 10분 간격으로 실행
scheduler.add_job(ETL_Pipeline, 'interval', minutes=10)
try:
    scheduler.start()
except KeyboardInterrupt:
    scheduler.shutdown()
    print('Scheduler 정지')