
resource "random_id" "snapshot" {
  byte_length = 8
}

resource "aws_db_subnet_group" "default" {
  name       = "py-simple-${random_id.snapshot.hex}"
  subnet_ids = var.db_subnets
  tags = {
    Name = "pysimple-rds-group"
  }
}

resource "aws_security_group" "default" {
  name   = "pysimple-db-access-sg-${random_id.snapshot.hex}"
  vpc_id = var.vpc_id
  ingress {
    from_port   = 5432
    protocol    = "TCP"
    to_port     = 5432
    cidr_blocks = ["10.1.0.0/16","10.2.0.0/16"]
  }

  tags = {
    Env = "test"
  }
}

resource "aws_db_instance" "default" {
  identifier                      = var.db_name
  vpc_security_group_ids          = [aws_security_group.default.id]
  db_subnet_group_name            = aws_db_subnet_group.default.name
  backup_retention_period         = var.replica_arn == "" ? 1 : 0
  allocated_storage               = 5
  max_allocated_storage           = 25
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  storage_type                    = "gp2"
  engine                          = "postgres"
  engine_version                  = "10.7"
  instance_class                  = "db.t2.micro"
  name                            = var.db_name
  username                        = var.replica_arn == "" ? var.db_user : null
  password                        = var.replica_arn == "" ? var.db_password : null
  multi_az                        = true
  port                            = "5432"
  replicate_source_db             = var.replica_arn
  final_snapshot_identifier       = var.replica_arn == "" ? "cars-${random_id.snapshot.hex}" : null
  deletion_protection             = false
  publicly_accessible             = true
  skip_final_snapshot             = var.replica_arn == "" ? false : true
  tags = {
    Env = "test"
  }
}
