terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.44.0"
    }
  }
  required_version = "1.1.2"
  backend "s3" {
    bucket = "terraform-state-cpaor"
    key    = "cpaor_state/terraform.tfstate"
    region = ""
    #   dynamodb_table  = "terraform-lock-integration-db"
    encrypt = true
    #profile                = "cpaor_terraform"
    skip_region_validation = true
  }
}

provider "aws" {
  region = var.aws_region
  #profile = var.aws_profile
  #shared_credentials_files = ["~/.aws/credentials"]
}


module "cpaor_vpc" {
  source = "./modules/vpc"

  environment = var.environment
  aws_region  = var.aws_region

  # vpc
  cidr_block         = var.cidr_block
  availability_zones = var.availability_zones
}

module "secrets" {
  source = "./modules/secrets"
}

module "streamlit" {
  source = "./modules/ecs/server"

  environment = var.environment
  aws_region  = var.aws_region

  # ecs
  app_image      = var.streamlit_app_image
  app_port       = var.streamlit_app_port
  fargate_cpu    = var.streamlit_fargate_cpu
  fargate_memory = var.streamlit_fargate_memory

  # vpc
  vpc_id          = module.cpaor_vpc.aws_vpc_id
  private_subnets = module.cpaor_vpc.private_subnets
  public_subnets  = module.cpaor_vpc.public_subnets

  # ecs role
  ecs_task_execution_role = var.streamlit_ecs_task_execution_role
  ecs_task_role           = var.streamlit_ecs_task_role

  # efs volume
  efs_volume_id = module.efilesystem.efs_volume_id

  # secrets
  streamlit_password_arn        = module.secrets.streamlit_password_arn
  streamlit_app_environment_arn = module.secrets.streamlit_app_environment_arn
  streamlit_ga_tracking_id_arn  = module.secrets.streamlit_ga_tracking_id_arn

}

module "efilesystem" {
  source = "./modules/efs"

  environment = var.environment
  aws_region  = var.aws_region

  # vpc
  vpc_id                  = module.cpaor_vpc.aws_vpc_id
  availability_zone_count = module.cpaor_vpc.availability_zone_count
  private_subnets         = module.cpaor_vpc.private_subnets
}

module "dataprocessing" {
  source = "./modules/ecs/data_processing"

  environment = var.environment
  aws_region  = var.aws_region

  # ecs
  app_image      = var.data_processing_app_image
  fargate_cpu    = var.data_processing_fargate_cpu
  fargate_memory = var.data_processing_fargate_memory

  ecs_cluster_id = module.streamlit.ecs_cluster_id

  # vpc
  vpc_id          = module.cpaor_vpc.aws_vpc_id
  private_subnets = module.cpaor_vpc.private_subnets
  public_subnets  = module.cpaor_vpc.public_subnets

  # ecs role
  ecs_task_execution_role = var.dp_ecs_task_execution_role
  ecs_task_role           = var.dp_ecs_task_role

  # efs volume
  efs_volume_id = module.efilesystem.efs_volume_id

  # secrets
  openai_api_key_arn = module.secrets.openai_api_key_arn
  acled_api_key_arn  = module.secrets.acled_api_key_arn
  cpaor_email_arn    = module.secrets.cpaor_email_arn
  acaps_password_arn = module.secrets.acaps_password_arn
}
