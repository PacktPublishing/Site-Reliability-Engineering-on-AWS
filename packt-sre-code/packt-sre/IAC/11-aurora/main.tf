locals {
  engine_ver = "10.6" #postgres 10.6
}

resource "random_id" "snapshot" {
  byte_length = 8
}

resource "aws_security_group" "default" {
  name   = "pyglocal-db-access-sg-${random_id.snapshot.hex}"
  vpc_id = var.vpc_id
  ingress {
    from_port   = 5432
    protocol    = "TCP"
    to_port     = 5432
    cidr_blocks = ["10.1.0.0/16","10.2.0.0/16"]
  }
}

resource "aws_rds_cluster_instance" "main" {
  count                = 3
  identifier           = "aurora-pyglobal-${count.index}"
  cluster_identifier   = aws_rds_cluster.main.id
  instance_class       = "db.r5.2xlarge"
  engine               = "aurora-postgresql"
  engine_version       = local.engine_ver
  db_subnet_group_name = aws_db_subnet_group.main.name
}

resource "aws_rds_cluster" "main" {
  cluster_identifier   = "aurora-pyglobal"
  engine               = "aurora-postgresql"
  engine_version       = local.engine_ver
  availability_zones   = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
  database_name        = var.db_name
  master_username      = var.db_user
  master_password      = var.db_password
  db_subnet_group_name = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.default.id]
  skip_final_snapshot  = true
}

resource "aws_db_subnet_group" "main" {
  name       = "main"
  subnet_ids = var.db_subnets
  tags = {
    env = "test"
  }
}