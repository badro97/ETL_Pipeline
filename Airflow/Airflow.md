# Airflow scheduling
&nbsp;  
## 프로젝트 개요
API 서버에서 주기적으로 생성되고 있는 암호화된 로그데이터를 추출하여 복호화 하고, 효율적으로 압축 변환을 거친 뒤 AWS S3에 파티셔닝하여 저장하는 ETL 파이프라인을 구축하고 Airflow DAG를 작성해 스케줄링
&nbsp;  

---  

### Airflow란?   

AirBnB에서 만든 workflow management tool 이다.   


**Airflow의 4가지의 구성요소**

- Webserver
    - ui를 통해 Airflow 로그, 스케쥴러(Scheduler)에 의해 생성된 DAG 목록, Task 상태 정보 등 제공  
    
- Scheduler
    - airflow로 할당된 work들을 스케쥴링 해주는 component  
    
    - Scheduled된 workflow들의 triggering과 실행하기 위해서 executor에게 task를 제공해주는 역할을 수행  
    
- Executor
    - 실행중인 task를 handling하는 component  
    
    - default 설치시에는 scheduler에 있는 모든 것들을 다 실행시키지만, production 수준에서의 executor는 worker에게 task를 push  
    
- Workers  
    - 실제 task를 실행하는 주체  
    
- Database
    - DAG, Task 등의 metadata를 저장하고 관리  
    
- DAG(Directed Acyclic Graph)  
    - DAG는 비순환 그래프로써 순환하는 싸이클이 없는 그래프  
    
    - DAG를 이용해 Workflow를 구성하여 어떤 순서로 task를 실행시킬 것인지 dependency를 어떻게 표현할 것인지 등을 설정


**ariflow의 특징**

- 파이썬기반의 데이터파이프라인 프레임워크 -> ETL작성 및 관리(실행순서,재실행,backfill) 유용하다  

- 웹ui 지원  
- DAG : 데이터파이프라인 하나의 단위 , 하나이상의 task로 구현
- TASK : 에어플로우의 operator, extract, transform, load 등 각각의 task가 되고 task간의 실행순서 정의가능
- 다수의 서버로 분산이 가능한 클러스터 (스케일아웃 지원)
- DAG의 과거 실행정보를 기록할 DB필요 (기본 sqlite)
  
---  
&nbsp;  

## Architecture  
&nbsp;  

![image](https://user-images.githubusercontent.com/49307262/228422094-857af6ee-44e2-4195-87f5-b905c929482a.png)  

Json log Data &rarr; Extract & Transform & Load &rarr; AWS S3 upload &rarr; AWS Athena  

### ETL 파이프라인
클래스를 사용해 ETL 파이프라인 코드 재작성  

- 기존의 파일 입출력/저장 프로세스를 제거  
    
- 스케줄링을 고려해 파티셔닝 과정을 간소화  

&nbsp;  

[etl_pipeline.py](https://github.com/badro97/ETL_Pipeline/blob/main/Airflow/etl_pipeline.py)


&nbsp;  
---  

### DAG 파일
- 클래스를 import 하여 task로 함수를 구분할 경우  
내부 self로 선언한 변수와 함수 간 변화된 값의 정보가 각 task 간에 공유되지 않음. (task는 별도의 프로세스로 분류되기 때문)  

- 따라서 xcom, 외부데이터베이스, 로컬파일저장/불러오기 방법을 사용해야 하지만, 그렇게 되면 굳이 클래스로 파이프라인을 작성할 이유가 없다.
- task 구분의 장점(스케줄링, 에러확인, 유지보수)만을 살리기로 결정하고 task로 각 단계를 구분
- 마지막 task인 load_task()에서 모든 과정이 실행되고 이때의 데이터만이 최종적으로 사용된다
&nbsp;  

[etl_dag.py](https://github.com/badro97/ETL_Pipeline/blob/main/Airflow/etl_dag.py)
  

&nbsp;  

## 수행 결과  

### Airflow 스케줄링  

<img width="1440" alt="Screenshot 2023-04-19 at 1 19 32 PM" src="https://user-images.githubusercontent.com/49307262/232966495-65c4b7ef-52d5-49de-ad33-7a8de007a8b6.png">  

<img width="1440" alt="Screenshot 2023-04-19 at 1 20 39 PM" src="https://user-images.githubusercontent.com/49307262/232966547-e62e9c04-bf97-49c2-8149-0b2fc205959d.png">  

<img width="1440" alt="Screenshot 2023-04-19 at 1 20 58 PM" src="https://user-images.githubusercontent.com/49307262/232966583-9b8d62d5-d8ea-4fbe-8cc6-c04aa9b5acd6.png">  
  
&nbsp;  
### S3 파티셔닝  

<img width="1440" alt="Screenshot 2023-04-19 at 1 22 25 PM" src="https://user-images.githubusercontent.com/49307262/232966655-0010b28b-4b87-44e3-b582-6e21b556cf07.png">  

<img width="1440" alt="Screenshot 2023-04-19 at 1 22 19 PM" src="https://user-images.githubusercontent.com/49307262/232966779-b4cebc85-be8a-4ad4-b0a0-f779eff0edf0.png">  
  
<img width="1440" alt="Screenshot 2023-04-19 at 1 22 06 PM" src="https://user-images.githubusercontent.com/49307262/232966792-2a2b706c-103c-4af2-9710-2f01640ba687.png">  

- ETL_Pipeline 모델 구축 완료  
&nbsp;  

## 추후 개선사항  

1. 대용량 파일 프로세스 처리 최적화 - Spark, Kafka
    - spark/kafka는 오버엔지니어링일 수 있다.