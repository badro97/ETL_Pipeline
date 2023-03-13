import os
import re
import gzip
import json
import math
from io import StringIO
from b64uuid import B64UUID
import base64
import uuid
import copy
import requests
from cryptography.fernet import Fernet

dateNum = re.compile('[0-9]')

url = 'http://ec2-3-37-12-122.ap-northeast-2.compute.amazonaws.com/api/data/log'
key = b't-jdqnDewRx9kWithdsTMS21eLrri70TpkMq2A59jX8='

fernet = Fernet(key)
data = requests.get(url).json()

## 복호화, json파일 저장
decrypted_data = [ eval(fernet.decrypt(data[i]['data']).decode('ascii')) for i in range(len(data)) ]

if not os.path.isfile('./origin_data.json'):
    with open('./origin_data.json', 'w') as file:
        json.dump(decrypted_data, file, indent=4)
        
## 메모리를 파일처럼 사용하고싶으면
# io = StringIO()
# json.dump(decrypted_data, io, indent=4)
# print(io.getvalue())


## 문자열 압축
def str_compress(data):
    ## user_id를 64자에서 44자로 압축
    
    ## base64, uuid 모듈을 사용하는 방법
    ## 변환하려는 원본 바이트 데이터 길이가 3의 배수가 아닌 경우 끝에 '='패딩문자가 붙는다.(base64)
    # try:
    #     compressed_user_id = base64.b64encode(bytes.fromhex(data['user_id'])).decode('utf-8')
    # except ValueError:  # 16진수 문자열이 아닌 경우
    #     compressed_user_id = base64.b64encode(uuid.UUID(data['user_id']).hex).decode('utf-8')
    
    ## B64UUID 모듈을 사용하여 압축하는 방법 (최대 36자(32자 + '-'4자) 혀용하므로 '-'가 포함되지 않은 64자의 문자열이라면 반으로 나눠서 진행)
    data['user_id'] = B64UUID(data['user_id'][32:]).string + B64UUID(data['user_id'][:32]).string
    
    ## HTTP Method를 숫자로 변경
    data['method'] = {'GET': 1, 'POST': 2}.get(data['method'], 0) # method 없으면 0

    ## url을 딕셔너리 타입을 사용해 숫자로 변경
    url_dict = {
        # 현재는 url 주소가 하나만 존재. 주소가 늘면 추가할 것.
        '/api/products/product/': 1, 
    }
    data['url'] = url_dict.get(data['url'], 0) # 사전에 없는 url이면 0 -> 후에 모두 모아서 사전에 추가
    
    ## inDate 형식 변환
    dt = dateNum.findall(data['inDate'])
    data['inDate'] = ''.join(dt)[2:] # 년도 앞 부분(20) 생략 

    return data

## 문자열 압축 완료 데이터 저장 ( list(dict()) )
raw = copy.deepcopy(decrypted_data)
str_compressed_data = [ str_compress(raw[i]) for i in range(len(data)) ]

if not os.path.isfile('./str_compressed_data.json'):
    with open('./str_compressed_data.json', 'w') as file:
        json.dump(str_compressed_data, file, indent=4)
        

## Gzip을 사용한 데이터 압축/저장, 파일크기 반환
def GZIP(data, filename):
    if not os.path.isfile(filename):
        with gzip.open(filename, 'wb') as f:
            f.write(data.encode('utf-8'))
        with gzip.open(filename, 'rb') as f:
            read_data = f.read().decode('utf-8')
        assert data == read_data # 압축이 깨지지 않고 정상 완료되었다면 continue
        return os.path.getsize(filename)
    else:
        return os.path.getsize(filename)



## 압축률 비교
## Json 파일 크기
org_file_size = int(os.path.getsize('./origin_data.json'))
str_comp_file_size = int(os.path.getsize('./str_compressed_data.json'))
## gzip 압축 후 파일 크기
gzip_str_comp_file_size = int(GZIP('./str_compressed_data.json', 'comp.gz'))
gzip_org_comp_file_size = int(GZIP('./origin_data.json', 'org.gz'))

## 원본 Json | 문자열 압축 Json
print('원본 Json: ',org_file_size, 'Bytes')
print('문자열 압축 Json: ',str_comp_file_size, 'Bytes')
print('압축률: ', round((1 - str_comp_file_size/org_file_size)*100, 2), ' %\n')

## 원본 Json | 원본 Json + Gzip 압축
print('원본 Json: ',org_file_size, 'Bytes')
print('원본 Json + Gzip 압축: ', gzip_org_comp_file_size, 'Bytes')
print('압축률: ', round((1 - gzip_org_comp_file_size/org_file_size)*100, 2), ' %\n')

## 문자열 압축 Json | 문자열 압축 Json + Gzip 압축
print('문자열 압축 Json: ',str_comp_file_size, 'Bytes')
print('문자열 압축 Json + Gzip 압축: ', gzip_str_comp_file_size, 'Bytes')
print('압축률: ', round((1 - gzip_str_comp_file_size/str_comp_file_size)*100, 2), ' %\n')

## 원본 Json | 문자열 압축 Json + Gzip 압축  ->  최종 압축 결과
print('원본 Json: ',org_file_size, 'Bytes')
print('문자열 압축 Json + Gzip 압축: ', gzip_str_comp_file_size, 'Bytes')
print('압축률: ', round((1 - gzip_str_comp_file_size/org_file_size)*100, 2), ' %\n')
