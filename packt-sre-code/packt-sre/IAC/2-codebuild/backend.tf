terraform {
  backend "s3" {
    bucket = "tfstate-widgets-com"
    key    = "codebuild/euwest2/terraform.tfstate"
    region = "eu-west-2"
  }
}
