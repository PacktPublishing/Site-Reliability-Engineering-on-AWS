terraform {
  backend "s3" {
    bucket = "tfstate-widgets-com"
    key    = "ecs/task/pysimple/euwest2/terraform.tfstate"
    region = "eu-west-2"
  }
}
