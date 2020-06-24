terraform {
  backend "s3" {
    bucket = "tfstate-widgets-com"
    key    = "eks/euwest2/terraform.tfstate"
    region = "eu-west-2"
  }
}
