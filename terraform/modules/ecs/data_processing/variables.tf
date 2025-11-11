variable "environment" {}
variable "aws_region" {}

# vpc
variable "vpc_id" {}
variable "public_subnets" {}
variable "private_subnets" {}

# ecs
variable "app_image" {}
variable "fargate_cpu" {}
variable "fargate_memory" {}
variable "app_count" {
  default = 1
}
variable "ecs_cluster_id" {}

variable "ecs_cluster_name" {
  default = "cpaor-cluster"
}

variable "ecs_task_definition_name" {
  default = "cpaor-data-processing-task"
}

variable "ecs_service_name" {
  default = "cpaor-data-processing-service"
}

variable "ecs_container_name" {
  default = "cpaor-data-processing-container"
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
  default = "cpaor.net"
}

# efs
variable "efs_volume_id" {}

# secrets
variable "openai_api_key_arn" {}
variable "cpaor_email_arn" {}
variable "acaps_password_arn" {}
variable "acled_username_arn" {}
variable "acled_password_arn" {}