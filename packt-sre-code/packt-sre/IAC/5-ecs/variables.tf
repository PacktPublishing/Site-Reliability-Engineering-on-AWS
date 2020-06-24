variable "vpc_id" {
  description = "the VPC ID used for provisioning"
}

variable "subnet_ids" {
  description = "the public subnets id's used for ALB provisioning"
}

variable "region" {
  description = "the AWS region be used for provisioning"
}