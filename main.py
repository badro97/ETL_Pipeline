import re
import base64
import uuid
import requests
from cryptography.fernet import Fernet

dateNum = re.compile('[0-9]')

url = 'http://ec2-3-37-12-122.ap-northeast-2.compute.amazonaws.com/api/data/log'
key = b't-jdqnDewRx9kWithdsTMS21eLrri70TpkMq2A59jX8='

fernet = Fernet(key)
data = requests.get(url).json()

## 복호화, 데이터 저장
decrypted_data = [ eval(fernet.decrypt(data[i]['data']).decode('ascii')) for i in range(len(data)) ]

## 문자열 압축
def str_compressed(data):
    # user_id를 64자에서 44자로 압축
    # 변환하려는 원본 바이트 데이터 길이가 3의 배수가 아닌 경우 끝에 '='패딩문자가 붙는다.(base64)
    try:
        compressed_user_id = base64.b64encode(bytes.fromhex(data['user_id'])).decode('utf-8')
    except ValueError:  # 16진수 문자열이 아닌 경우
        compressed_user_id = base64.b64encode(uuid.UUID(data['user_id']).hex).decode('utf-8')
    
    data['user_id'] = compressed_user_id
    
    # HTTP Method를 숫자로 변경
    data['method'] = {'GET': 1, 'POST': 2}.get(data['method'], 0) # method 값이 없다면 0 -> 데이터 수정

    # url을 딕셔너리 타입을 사용해 숫자로 변경
    url_dict = {
        # 현재는 url 주소가 하나만 존재. 주소가 늘면 추가할 것.
        '/api/products/product/': 1, 
    }
    data['url'] = url_dict.get(data['url'], 0) # 사전에 없는 url이면 0 -> 후에 모두 모아서 사전에 추가
    
    # inDate 형식 변환
    dt = dateNum.findall(data['inDate'])
    data['inDate'] = ''.join(dt)[2:] # 년도 앞 부분(20) 생략 

    return data

## 문자열 압축 완료 데이터 저장 ( list(dict()) )
str_compressed_json = [ str_compressed(decrypted_data[i]) for i in range(len(data)) ]

print(str_compressed_json)