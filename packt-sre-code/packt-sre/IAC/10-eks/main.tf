#setup any local variables
locals {
  vpc_id              = "vpc-05939a73c8684c026"
  cluster_subnets     = ["subnet-071fabf574452338c", "subnet-0b05b60e1a8d9a65b","subnet-0b0e88e7e28517c5e","subnet-08a8928bd3ccbc36e"]
  worker_subnets      = ["subnet-071fabf574452338c", "subnet-0b05b60e1a8d9a65b"]
  cluster_name        = "tf-eks-pyglobal-eu-west-2"
  rds_instance_name   = "cars"
  eks_security_group  = "sg-0b2e88cc0874e81b9"
  alb_arn             = "arn:aws:elasticloadbalancing:eu-west-2:915793320862:loadbalancer/app/tf-ecs-simplepy-alb-eu-west-2/8d55184c3c904bd0"
  alb_name            = "tf-ecs-simplepy-alb-eu-west-2"
  alb_target_arn      = "arn:aws:elasticloadbalancing:eu-west-2:915793320862:targetgroup/tf-ecs-simplepy-eu-west-2/93d77d67f48af047"
  main-node-userdata = <<USERDATA
#!/bin/bash
set -o xtrace
/etc/eks/bootstrap.sh --apiserver-endpoint '${aws_eks_cluster.example.endpoint}' --b64-cluster-ca '${aws_eks_cluster.example.certificate_authority.0.data}' '${local.cluster_name}'
USERDATA
}


resource "aws_security_group" "eks-api" {
  name        = "terraform-eks-control-plane"
  description = "Security group for all nodes in the cluster"
  vpc_id      = local.vpc_id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "TCP"
    cidr_blocks = ["10.0.0.0/8"]
  }
}

resource "aws_eks_cluster" "example" {
  name     = local.cluster_name
  role_arn = aws_iam_role.example.arn
  vpc_config {
    security_group_ids = [aws_security_group.eks-api.id]
    subnet_ids = local.cluster_subnets
    endpoint_private_access = true 
    public_access_cidrs = ["0.0.0.0/0"]
  }
  depends_on = [
    aws_iam_role_policy_attachment.example-AmazonEKSClusterPolicy,
    aws_iam_role_policy_attachment.example-AmazonEKSServicePolicy,
  ]
}

resource "aws_iam_role" "example" {
  name               = "eks-cluster-policy"
  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
POLICY
}

resource "aws_iam_role_policy_attachment" "example-AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.example.name
}

resource "aws_iam_role_policy_attachment" "example-AmazonEKSServicePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
  role       = aws_iam_role.example.name
}
