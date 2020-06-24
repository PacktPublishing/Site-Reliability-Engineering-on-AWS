terraform {
  backend "s3" {
    bucket = "tfstate-widgets-com"
    key    = "ecs/euwest2/terraform.tfstate"
    region = "eu-west-2"
  }
}
