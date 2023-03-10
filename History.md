# History

## 2023.03.10

1. 깃헙 레포 생성
---
2. [ETL 파이프라인 기본 개념 학습](https://judicious-crystal-89c.notion.site/ETL-492a55740f9442f88da3766718ca66f0)

**언제든지 필요한 데이터를 가져와 꺼내 쓸 수 있도록 데이터를 계속 쌓아두는 파이프를 만드는 것**

---
### 데이터파이프라인이 하는 일
- Data extracting: 데이터 추출
- Data transforming: 데이터 변환
- Data combining: 데이터 결합
- Data validating: 데이터 검증
- Data loading: 데이터 적재
---
  데이터 추출, 변환, 적재를 묶어 ETL 이라고 한다.  
  
  &nbsp;  
    ETL은 데이터 파이프라인 하위 개념으로, 하나의 시스템에서 데이터를 추출해 변환하여 데이터 베이스 or 데이터 웨어하우스에 차곡차곡 쌓아둔다.  
    &nbsp;
  - 1. Extraction(API, Crawling)
    - Backend API 서버에서 응답하는 JSON 데이터  
    &nbsp;
  - 2. Transform(Compression, Format Conversion)
    - 데이터 변환, 압축/저장 과정 
    - 압축 알고리즘
      - [LZ77 알고리즘](https://nightohl.tistory.com/entry/LZ77-%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%98)
      - [허프만 코딩 알고리즘](https://www.techiedelight.com/ko/huffman-coding/)
    &nbsp;
  - 3. Load
    - 데이터웨어하우스
    - 분산파일 시스템
    - NoSQL, 병렬 DBMS
    - 네트워크 구성 저장 시스템
    - 클라우드 파일 저장 시스템(AWS S3)
    