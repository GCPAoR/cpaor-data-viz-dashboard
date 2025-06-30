resource "aws_ecs_cluster" "cluster" {
  name = "${var.ecs_cluster_name}-${var.environment}"
}

data "aws_caller_identity" "current_user" {}

locals {
  app_image_url = "${data.aws_caller_identity.current_user.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.app_image}:latest"
}

data "template_file" "config" {
  template = file("./modules/ecs/server/templates/ecr_image/image.json")

  vars = {
    app_image                     = local.app_image_url
    app_port                      = var.app_port
    fargate_cpu                   = var.fargate_cpu
    fargate_memory                = var.fargate_memory
    aws_region                    = var.aws_region
    environment                   = var.environment
    container_name                = var.ecs_container_name
    streamlit_password_arn        = var.streamlit_password_arn
    streamlit_app_environment_arn = var.streamlit_app_environment_arn
    streamlit_ga_tracking_id_arn  = var.streamlit_ga_tracking_id_arn
  }
}

resource "aws_ecs_task_definition" "task-def" {
  family                   = "${var.ecs_task_definition_name}-${var.environment}"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory
  container_definitions    = data.template_file.config.rendered
  volume {
    name = "data-volume"
    efs_volume_configuration {
      file_system_id = var.efs_volume_id
      root_directory = "/"
    }
  }
}

resource "aws_ecs_service" "service" {
  name                   = "${var.ecs_service_name}-${var.environment}"
  cluster                = aws_ecs_cluster.cluster.id
  task_definition        = aws_ecs_task_definition.task-def.arn
  desired_count          = var.app_count
  launch_type            = "FARGATE"
  enable_execute_command = true

  network_configuration {
    security_groups = [
      aws_security_group.ecs_sg.id
    ]
    subnets          = var.public_subnets
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_alb_target_group.tg.arn
    container_name   = "${var.ecs_container_name}-${var.environment}"
    container_port   = var.app_port
  }

  depends_on = [
    aws_alb_listener.app_listener,
    aws_iam_role_policy_attachment.ecs_task_execution_role
  ]
}