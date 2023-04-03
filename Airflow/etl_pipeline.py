import os
import re
import json
import requests
from b64uuid import B64UUID
import gzip
from cryptography.fernet import Fernet
## AWS S3
import boto3
from botocore.client import Config
## Key 보안 (dotenv)
from dotenv import load_dotenv
load_dotenv()
## 데이터 파티셔닝
from datetime import datetime


## ETL_PIPELINE 클래스
class ETL_Pipeline:
    def __init__(self):
        self.AWS_S3_BUCKETNAME = 'etlcp'
        self.AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
        self.AWS_SECRET_ACCESS_KEY_ID = os.getenv('AWS_SECRET_ACCESS_KEY_ID')
        
        self.API_URL = os.getenv('API_URL')
        self.FERNET_KEY = os.getenv('FERNET_KEY').encode()
        self.dateNum = re.compile('[0-9]')
        
        self.data = []
        self.gzip = None
    
    ## Extract(추출)
    def extract(self):
        fernet = Fernet(self.FERNET_KEY)
        data = requests.get(self.API_URL).json()
        decrypted_data = [ eval(fernet.decrypt(data[i]['data']).decode('ascii')) for i in range(len(data)) ]
        self.data = decrypted_data
        
    
    ## Transform(변환)
    def transform(self):
        ## json 문자열 압축 함수
        def str_compress(data):
            ## B64UUID 모듈을 사용하여 압축하는 방법 (최대 36자(32자 + '-'4자) 혀용하므로 '-'가 포함되지 않은 64자의 문자열이라면 반으로 나눠서 진행)
            data['user_id'] = B64UUID(data['user_id'][32:]).string + B64UUID(data['user_id'][:32]).string
            ## HTTP Method를 숫자로 변경
            data['method'] = {'GET': 1, 'POST': 2}.get(data['method'], 0) # 사전에 없는  method면 0
            ## url을 딕셔너리 타입을 사용해 숫자로 변경
            data['url'] = {'/api/products/product/': 1}.get(data['url'], 0) # 사전에 없는 url이면 0
            ## inDate 형식 변환
            data['inDate'] = ''.join(self.dateNum.findall(data['inDate']))[2:] # 년도 앞 부분(20) 생략 
            return data
        
        ## gzip 압축 함수
        def gzip_compress(data):
            gz_data = gzip.compress(bytes(json.dumps(data), 'utf-8'))
            return gz_data

        json_data = [ str_compress(self.data[i]) for i in range(len(self.data)) ]
        self.gzip = gzip_compress(json_data)
        
        
    
    ## Load(저장)
    def load(self):
        ## AWS S3 연결 (boto3)
        def s3_connection(self):
            try:
                s3 = boto3.client(
                    service_name = 's3',
                    region_name = 'ap-northeast-2',
                    aws_access_key_id = self.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key = self.AWS_SECRET_ACCESS_KEY_ID,
                    config = Config(signature_version='s3v4'),
                )
            except Exception as e: print(e)
            else: return s3
            
        ## AWS S3 파티셔닝 업로드
        def s3_upload_partitioning(self):
            now = datetime.now()
            # (분:초) 
            first = self.data[0]['inDate'][8:10] + ':' + self.data[0]['inDate'][10:12]  # 부터
            last = self.data[-1]['inDate'][8:10] + ':' + self.data[-1]['inDate'][10:12] # 까지
            s3_path = f'data/{now.year}_y/{now.month}_m/{now.day}_d/{now.hour}_h/{first}~{last}.gz'
            s3 = s3_connection(self)
            s3.put_object(Body=self.gzip, Bucket=self.AWS_S3_BUCKETNAME, Key=s3_path)
            
        s3_upload_partitioning(self)