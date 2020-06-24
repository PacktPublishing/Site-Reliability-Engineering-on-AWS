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


module "ecs-mr" {
  source = "../5-ecs"
  vpc_id = "vpc-019d1ae8239dda617"
  region = "eu-west-1"
  subnet_ids = ["subnet-0adeebd01542d2c35", "subnet-0a5a867bafbdc407c"]
  providers = {
    aws     = aws.euwest1 
  } 
}

module "ecs-mr2" {
  source = "../5-ecs"
  vpc_id = "vpc-05939a73c8684c026"
  region = "eu-west-2"
  subnet_ids = ["subnet-08a8928bd3ccbc36e", "subnet-0b0e88e7e28517c5e"]  
  providers = {
    aws     = aws.euwest2
  }
}

