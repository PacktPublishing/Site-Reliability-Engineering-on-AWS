terraform {
  backend "s3" {
    bucket = "tfstate-widgets-com"
    key    = "ecs/task/pycars/euwest2/terraform.tfstate"
    region = "eu-west-2"
  }
}
