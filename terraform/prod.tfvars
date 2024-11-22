environment = "prod"
aws_region  = "eu-central-1"
aws_profile = "cpaor_terraform"

# vpc
cidr_block         = "172.21.0.0/16"
availability_zones = ["eu-central-1a", "eu-central-1b"]

# ecs
streamlit_app_image      = "cpaor_streamlit"
streamlit_app_port       = 8501
streamlit_fargate_cpu    = "1024"
streamlit_fargate_memory = "4096"

data_processing_app_image      = "cpaor_data_processing"
data_processing_fargate_cpu    = "1024"
data_processing_fargate_memory = "4096"


# ecs role
streamlit_ecs_task_execution_role = "ECSTaskExecutionServerRole"
streamlit_ecs_task_role           = "ECSTaskServerRole"
dp_ecs_task_execution_role        = "ECSTaskExecutionServerRoleDP"
dp_ecs_task_role                  = "ECSTaskServerRoleDP"
