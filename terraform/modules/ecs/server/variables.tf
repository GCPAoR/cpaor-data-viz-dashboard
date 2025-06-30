variable "environment" {}
variable "aws_region" {}

# vpc
variable "vpc_id" {}
variable "public_subnets" {}
variable "private_subnets" {}

# ecs
variable "app_image" {}
variable "app_port" {}
variable "fargate_cpu" {}
variable "fargate_memory" {}
variable "app_count" {
  default = 1
}

variable "ecs_cluster_name" {
  default = "cpaor-cluster"
}

variable "ecs_task_definition_name" {
  default = "cpaor-streamlit-task"
}

variable "ecs_service_name" {
  default = "cpaor-streamlit-service"
}

variable "ecs_container_name" {
  default = "cpaor-streamlit-container"
}

# ecs role
variable "ecs_task_execution_role" {}
variable "ecs_task_role" {}

# alb
variable "health_check_path" {
  default = "/"
}

# route 53
variable "domain_name" {
  default = "data.cpaor.net"
}

# efs
variable "efs_volume_id" {}

# autoscaling
variable "cpaor_streamlit_scaling_max_capacity" {
  default = 5
}

variable "cpaor_streamlit_scaling_min_capacity" {
  default = 1
}

variable "cpaor_streamlit_max_mem_target_value" {
  default = 50
}

variable "cpaor_streamlit_min_mem_target_value" {
  default = 40
}

variable "monitoring_period" {
  default = 30
}

variable "evaluation_period_max" {
  default = 2
}

variable "evaluation_period_min" {
  default = 8
}

# secrets
variable "streamlit_password_arn" {}
variable "streamlit_app_environment_arn" {}
variable "streamlit_ga_tracking_id_arn" {}