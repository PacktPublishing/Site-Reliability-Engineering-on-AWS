#setup any local variables

locals {
  app_port           = 8080
  access_logs        = "alb-access-logs-widgets.com"
}


#create the ALB security group
resource "aws_security_group" "lb" {
  name        = "tf-ecs-alb-sg-${var.region}"
  description = "controls access to the ALB"
  vpc_id      = var.vpc_id

  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
#create the ECS container security group
resource "aws_security_group" "ecs_tasks" {
  name        = "tf-ecs-tasks-sg-${var.region}"
  description = "allow inbound access from the ALB only"
  vpc_id      = var.vpc_id

  ingress {
    protocol        = "tcp"
    from_port       = 8000
    to_port         = local.app_port
    security_groups = ["${aws_security_group.lb.id}"]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

#create the application ALB
resource "aws_alb" "main" {
  name            = "tf-ecs-simplepy-alb-${var.region}"
  subnets         = var.subnet_ids
  security_groups = ["${aws_security_group.lb.id}"]
  tags = {
    Environment = "test"
  }
  access_logs {
    bucket  = "${local.access_logs}-${var.region}"
    prefix  = "pysimple"
    enabled = true
  }
}

# Redirect all traffic from the ALB to the target group
resource "aws_alb_listener" "front_end" {
  load_balancer_arn = aws_alb.main.id
  port              = "80"
  protocol          = "HTTP"
  default_action {
    target_group_arn = aws_alb_target_group.app.id
    type             = "forward"
  }
}

#create the target group for the ECS hosts
resource "aws_alb_target_group" "app" {
  name        = "tf-ecs-simplepy-${var.region}"
  port        = 8001
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {
    healthy_threshold   = 3
    unhealthy_threshold = 10
    timeout             = 10
    interval            = 20
    path                = "/api/v0.1/health"
    port                = "8001"
  }
}


resource "aws_ecs_cluster" "main" {
  name = "tf-ecs-pyglobal-ecs-${var.region}"
}

