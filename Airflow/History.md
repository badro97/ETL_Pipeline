# History

## 2023.03.24

1. Airflow 기본 개념 학습

### Airflow란?  
![image](https://user-images.githubusercontent.com/49307262/228422094-857af6ee-44e2-4195-87f5-b905c929482a.png)  

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

## 2023.03.27   

### Airflow 설치

- EC2 인스턴스: t2.micro (1GB RAM)  
- python=3.8  
- direnv 설정  
- airflow version 2.5.2
- mysql 8.0  
db이름은 airflow_db  
유저이름/패스워드는 airflow/airflow
    ```sql
    CREATE DATABASE airflow_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER '$airflow_user' IDENTIFIED BY '$airflow_pass';
    GRANT ALL PRIVILEGES ON airflow_db.* TO '$airflow_user';
    ```
- Airflow 설정  
    sudo nano airflow.cfg  
    
    ```Bash
    default_timezone = Asia/Seoul

    # sql_alchemy_conn = mysql+mysqldb://<user>:<password>@<host>[:<port>]/<dbname>
    sql_alchemy_conn = mysql+mysqldb://airflow:airflow@$your_host:3306/airflow_db

    base_url = http://$your_webserver_public_url:8080
    default_ui_timezone = Asia/Seoul

    load_examples = True

    # workers 기본 값은 4, 조정해주지 않으면 서버에 부하때문에 가득차서 터질 위험이 있음
    workers = 2
    ```
- 데이터베이스 초기화
    ```Bash
    airflow db init
    
    # airflow user/password 설정
    airflow users create \
    --firstname admin \
    --lastname admin \
    --email admin \
    --password admin \
    --username admin \
    --role Admin
    ```
- mysql 접속 후 db table 확인  
sudo mysql -u airflow -p  
    1. show databases;
    2. use airflow_db;
    3. show tables;  
    
    | Tables_in_airflow_db           |
    |--------------------------------|
    | ab_permission                  |
    | ab_permission_view             |
    | ab_permission_view_role        |
    | ab_register_user               |
    | ab_role                        |
    | ab_user                        |
    | ab_user_role                   |
    | ab_view_menu                   |
    | alembic_version                |
    | callback_request               |
    | connection                     |
    | dag                            |
    | dag_code                       |
    | dag_owner_attributes           |
    | dag_pickle                     |
    | dag_run                        |
    | dag_run_note                   |
    | dag_schedule_dataset_reference |
    | dag_tag                        |
    | dag_warning                    |
    | dagrun_dataset_event           |
    | dataset                        |
    | dataset_dag_run_queue          |
    | dataset_event                  |
    | import_error                   |
    | job                            |
    | log                            |
    | log_template                   |
    | rendered_task_instance_fields  |
    | serialized_dag                 |
    | session                        |
    | sla_miss                       |
    | slot_pool                      |
    | task_fail                      |
    | task_instance                  |
    | task_instance_note             |
    | task_map                       |
    | task_outlet_dataset_reference  |
    | task_reschedule                |
    | trigger                        |
    | variable                       |
    | xcom                           |

    42 rows in set (0.00 sec)  

- airflow 웹서버 실행 systemctl 등록    
sudo nano /etc/systemd/system/airflow-webserver.service  

    ```Bash
    [Unit]
    Description="Airflow Webserver"
    Wants=network-online.target
    After=network-online.target

    [Service]
    Type=simple
    User=ubuntu
    Group=ubuntu
    Restart=on-failure

    WorkingDirectory=/home/ubuntu/airflow
    PIDFile=/home/ubuntu/airflow/airflow-webserver.pid

    ExecStart=/home/ubuntu/airflow/env/bin/airflow webserver --daemon
    ExecStop=/bin/kill "$MAINPID"


    [Install]
    WantedBy=multi-user.target
    ```  
    
- 스케줄러 등록 (로그 기록하기 위함)  
cd /home/ubuntu/airflow  
nano ExecStartPre_airflow-scheduler.sh  

    ```Bash
    #!/bin/bash
    POSTFIX=$(date +'%Y-%m-%d_%H:%M:%S')
    FILENAME=/home/ubuntu/airflow/airflow-scheduler.log
    if [ -f "$FILENAME" ] ; then
            mv $FILENAME "$FILENAME.$POSTFIX"
    fi
    FILENAME=/home/ubuntu/airflow/airflow-scheduler.err
    if [ -f "$FILENAME" ] ; then
            mv $FILENAME "$FILENAME.$POSTFIX"
    fi
    ```  
    
    스케줄러 systemctl 등록  
    sudo nano /etc/systemd/system/airflow-scheduler.service
    ```Bash
    [Unit]
    Description="Airflow Scheduler"
    Wants=network-online.target
    After=network-online.target

    [Service]
    Type=simple
    User=ubuntu
    Group=ubuntu
    Restart=on-failure

    WorkingDirectory=/home/ubuntu/airflow
    PIDFile=/home/ubuntu/airflow/airflow-scheduler.pid
    ExecStartPre=/home/ubuntu/airflow/ExecStartPre_airflow-scheduler.sh
    ExecStart=/home/ubuntu/airflow/env/bin/airflow scheduler
    ExecStop=/bin/kill "$MAINPID"
    StandardOutput=file:/home/ubuntu/airflow/airflow-scheduler.log
    StandardError=file:/home/ubuntu/airflow/airflow-scheduler.err


    [Install]
    WantedBy=multi-user.target
    ```
    
- airflow 실행
    ```Bash  
    sudo systemctl enable airflow-webserver.service
    sudo systemctl enable airflow-scheduler.service
    sudo systemctl start airflow-webserver.service
    sudo systemctl start airflow-scheduler.service
    ```

---  

## 2023.03.28  

EC2 프리티어 인스턴스 리소스 부족(1GB RAM)으로 airflow 서버가 터지는 문제점 발생  
-> UTM 가상머신 사용(m1 mac) 하여 Ubuntu Desktop 설치 (4GB RAM 설정)  

Ubuntu 20.04.6 LTS (Focal Fossa)  

- SSH 설치 및 설정  
    $ sudo apt update  
    
    $ sudo apt install openssh-server
    
    $ sudo systemctl status ssh  
    
    active(running) 확인  
    
    $ sudo ufw allow ssh
    
    방화벽이 SSH를 허용할 수 있도록 설정  
    
    $ ip a  
    
    192.168 ~ 우분투 ip address 확인
    
- 맥(로컬)에서 터미널 실행  
    $ ssh {ubuntu username}@{ubuntu ip address}
    
    우분투 접속 후 설치과정 진행  
    
<img width="1440" alt="Screenshot 2023-03-29 at 1 24 27 PM" src="https://user-images.githubusercontent.com/49307262/228426408-4c55f0cb-3071-4b45-8336-e64759999e6e.png">

airflow webserver, scheduler 정상 작동 확인  

  
  
--- 

## 2023.03.30  

스케줄러 강제종료 문제  
sudo nano /etc/systemd/system/airflow-scheduler.service  

Environment="PATH=/home/ubuntu/airflow/env/bin/airflow:$PATH"
추가  

~/.bashrc 에 PATH 추가하였으나 계속해서 스케줄러가 작동하지 않는 문제가 발생.  

### 예상되는 원인
로그기록을 살펴보니 ExecStartPre=/home/ubuntu/airflow/ExecStartPre_airflow-scheduler.sh 부분에서 막힌 것으로 보임.  

-> sudo kill -9 `pgrep -f airflow` 입력하여 모든 프로세스 강제 종료  
-> airflow standalone 으로 웹서버/스케줄러 실행 -> 문제 해결  
  &nbsp;  
  
1. DAG 파일을 추가한 뒤, 스케줄링(10분 간격) 진행
    <img width="1440" alt="Screenshot 2023-03-30 at 3 07 40 PM" src="https://user-images.githubusercontent.com/49307262/228745546-f16ef0f1-f718-4338-95cb-6d041f3b40d5.png">  
    
    <img width="1157" alt="Screenshot 2023-03-30 at 3 06 05 PM" src="https://user-images.githubusercontent.com/49307262/228745751-eeb59611-b5bf-4ac5-b645-8bd2ea3a5f8e.png">
    
    스케줄링 정상 작동 및 s3 버킷 적재 확인.

### 추후 개선 사항
1. Extract, Transform, Load task를 나눠 dag스케줄링 진행
2. 로그 확인 용 파일 입출력 함수 호출 시의 리소스 점유를 고려해 etl pipeline 코드 재작성
    - 일단 둘 다 돌려보고 시간이 적게 걸리면서 에러가 적은 코드 선택하기