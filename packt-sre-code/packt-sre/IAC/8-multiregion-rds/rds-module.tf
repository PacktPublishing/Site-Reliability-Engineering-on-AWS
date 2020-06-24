provider "aws" {
  version = "~> 2.0"
  alias = "euwest1"
  region = "eu-west-1"
}

provider "aws" {
  version = "~> 2.0"
  alias = "euwest2"
  region = "eu-west-2"
}


module "rds-mr" {
  source = "../4-rds"
  vpc_id      = "vpc-05939a73c8684c026"
  db_user     = "carsa"
  db_password = "LetmeinAWS!!"
  db_name     = "cars"
  db_subnets  = ["subnet-02d640b292e5a5709", "subnet-0801380048c54cef6"]
  providers = {
    aws     = aws.euwest2 
  } 
}

module "rds-mr2" {
  source = "../4-rds"
  vpc_id      = "vpc-019d1ae8239dda617"
  db_user     = "carsa"
  db_password = "LetmeinAWS!!"
  db_name     = "cars"
  db_subnets  = ["subnet-07ae0e1374160dcf3", "subnet-0bf12d04f354fa1cb"] 
  replica_arn = module.rds-mr.rds_arn
  providers = {
    aws     = aws.euwest1
  }
}

