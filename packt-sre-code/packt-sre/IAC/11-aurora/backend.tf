terraform {
  backend "s3" {
    bucket = "tfstate-widgets-com"
    key    = "rds/aurora/euwest2/terraform.tfstate"
    region = "eu-west-2"
  }
}
