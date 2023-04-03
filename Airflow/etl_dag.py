from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from etl_pipeline import ETL_Pipeline


with DAG(
    "ETL_Pipeline",
    default_args={
        "depends_on_past": False,
        "email": ["badro97@naver.com"],
        "email_on_failure": True,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=1),
        'wait_for_downstream': True, ## E->T->L 모두 완료되면 다음 ETL진행
    },
    
    description="ETL Pipeline",
    schedule=timedelta(minutes=3),
    start_date=datetime(2023, 3, 31),
    catchup=False,
    tags=["ETL"],
    
) as dag:
    
    def extract_task():
        etl_pipeline = ETL_Pipeline()
        etl_pipeline.extract()

    def transform_task():
        etl_pipeline = ETL_Pipeline()
        etl_pipeline.extract()
        etl_pipeline.transform()

    def load_task():
        etl_pipeline = ETL_Pipeline()
        etl_pipeline.extract()
        etl_pipeline.transform()
        etl_pipeline.load()
    '''
    결국에는 load_task() 에서 모든 작업이 실행되며 그 전 작업에서의 결과물은 버려지지만,
    이렇게 task를 나누는 이유는 각 task의 기능을 분리함으로써 코드의 가독성과 유지보수성을 높이기 위함이다.
    각 task를 별도로 실행하거나 스케줄링할 수 있기 때문에, 
    wait_for_downstream 옵션을 사용해서 각각의 task에 대한 성공/실패 여부를 파악하고 대처할 수 있다.
    + xcom이나 json, pickle, 외부데이터베이스, 파일저장 방법을 사용하지 않고 class 내 self 변수의 변화된 값을 각 task로 전달할 수 있다.
    '''
   
    ## Extract Task
    extract = PythonOperator(
        task_id="Extract",
        python_callable=extract_task,
    )
  
    ## Transform Task
    transform = PythonOperator(
        task_id="Transform",
        python_callable=transform_task,
    )
        
    ## Load Task
    load = PythonOperator(
        task_id="Load",
        python_callable=load_task,
    )
    
    extract >> transform >> load
