#setup any local variables
locals {
  vpc_id              = "vpc-05939a73c8684c026"
  app_port            = 8001
  app_private_subnets = ["subnet-071fabf574452338c", "subnet-0b05b60e1a8d9a65b"]
  db_user             = "carsa"
  db_passwd           = "LetmeinAWS!!"
  fargate_cpu         = 256
  fargate_memory      = 512
  app_image           = "py-cars"
  app_version         = "0.0.1"
  app_fqdn            = "${local.app_image}:${local.app_version}"
  app_count           = 2
  cluster_name        = "tf-ecs-pyglobal-ecs-eu-west-2"
  lb_tg_name          = "tf-ecs-simplepy"
  local_sec_group     = ["tf-ecs-tasks-sg"]
  rds_instance_name   = "cars"
  ecs_security_group      = "sg-0b2e88cc0874e81b9"
  alb_arn             = "arn:aws:elasticloadbalancing:eu-west-2:915793320862:loadbalancer/app/tf-ecs-simplepy-alb-eu-west-2/8d55184c3c904bd0"
  alb_name            = "tf-ecs-simplepy-alb-eu-west-2"
  alb_target_arn      = "arn:aws:elasticloadbalancing:eu-west-2:915793320862:targetgroup/tf-ecs-simplepy-eu-west-2/93d77d67f48af047"
}

#get cluster data
data "aws_ecs_cluster" "ecs" {
  cluster_name = local.cluster_name
}

#get database data
data "aws_db_instance" "db" {
  db_instance_identifier = local.rds_instance_name
}

#get alb data
data "aws_lb" "ecs" {
  arn  = local.alb_arn
  name = local.alb_name
}
#get repro 
data "aws_ecr_repository" "app" {
  name = local.app_image
}

data "aws_lb_target_group" "ecs" {
  arn  = local.alb_target_arn
  name = local.lb_tg_name
}

data "aws_security_group" "ecs" {
  id = local.ecs_security_group
}

data "aws_iam_role" "ecs_task_execution_role" {
  name = "ecsTaskExecutionRole"
}

resource "aws_iam_role" "task_role" {
  name = "bespoke-simply-py-task-execution-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}
 
resource "aws_ecs_task_definition" "ecs" {
  task_role_arn            = "arn:aws:iam::915793320862:role/pysimple-task-role"
  family                   = "py-cars"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = local.fargate_cpu
  memory                   = local.fargate_memory
  execution_role_arn       = data.aws_iam_role.ecs_task_execution_role.arn
  container_definitions = <<DEFINITION
[
  {
    "cpu": ${local.fargate_cpu},
    "environment": [{"name":"HOST","value":"${element(split(":",data.aws_db_instance.db.endpoint),0)}"},{"name":"DB","value":"${local.rds_instance_name}"},{"name":"DB_USER","value":"${local.db_user}"},{"name":"DB_PASS","value":"${local.db_passwd}"},{"name":"ECS_RUN","value":"TRUE"}],
    "image": "${data.aws_ecr_repository.app.repository_url}:${local.app_version}",
    "memory": ${local.fargate_memory},
    "name": "py-cars",
    "networkMode": "awsvpc",
    "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "py-simple",
                    "awslogs-region": "eu-west-2",
                    "awslogs-stream-prefix": "ecs-pysimple"
                }
    },
    "portMappings": [
      {
        "containerPort": ${local.app_port},
        "hostPort": ${local.app_port}
      }
    ]
  }
]
DEFINITION
}

resource "aws_ecs_service" "main" {
  name            = "tf-ecs-pycars-service"
  cluster         = data.aws_ecs_cluster.ecs.id
  task_definition = aws_ecs_task_definition.ecs.arn
  desired_count   = local.app_count
  launch_type     = "FARGATE"

  network_configuration {
    security_groups = [data.aws_security_group.ecs.id]
    subnets         = local.app_private_subnets
  }

  load_balancer {
    target_group_arn = data.aws_lb_target_group.ecs.id
    container_name   = "py-cars"
    container_port   = local.app_port
  }

}

