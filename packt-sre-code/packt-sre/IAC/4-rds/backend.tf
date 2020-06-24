terraform {
  backend "s3" {
    bucket = "tfstate-widgets-com"
    key    = "rds/multiregion/terraform.tfstate"
    region = "eu-west-2"
  }
}
