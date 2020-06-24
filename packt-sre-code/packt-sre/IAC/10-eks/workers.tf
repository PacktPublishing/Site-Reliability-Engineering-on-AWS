data "aws_ami" "eks-worker" {
  filter {
    name   = "name"
    values = ["amazon-eks-node-${aws_eks_cluster.example.version}-v*"]
  }

  most_recent = true
  owners      = ["602401143452"] # Amazon EKS AMI Account ID
}

resource "aws_security_group" "main-node" {
  name        = "terraform-eks-worker-node"
  description = "Security group for all worker nodes in the cluster"
  vpc_id      = local.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_launch_configuration" "main" {
  associate_public_ip_address = false
  iam_instance_profile        = aws_iam_instance_profile.main-node.name
  image_id                    = data.aws_ami.eks-worker.id
  instance_type               = "t3.small"
  name_prefix                 = "terraform-eks-main"
  security_groups             = [aws_security_group.main-node.id]
  user_data_base64            = base64encode(local.main-node-userdata)

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "main" {
  desired_capacity     = 3
  launch_configuration = aws_launch_configuration.main.id
  max_size             = 3
  min_size             = 1
  name                 = "terraform-eks-main"
  vpc_zone_identifier  = local.worker_subnets
  tag {
    key                 = "kubernetes.io/cluster/${local.cluster_name}"
    value               = "owned"
    propagate_at_launch = true
  }
}