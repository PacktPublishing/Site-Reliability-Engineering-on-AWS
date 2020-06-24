variable "vpc_id" {
  description = "the VPC ID being used for provsiioning"
}


variable "db_user" {
  description = "the name of database user to create"
}

variable "db_password" {
  description = "the datebase user password"
}

variable "db_name" {
  description = "the name of database instance to create"
}


variable "replica_arn" {
  description = "is the dtabase being created a read replica"
  default     = ""
}

variable "db_subnets" {
  description = "a list of subnets hosting the database"
}
