resource "aws_ecr_repository" "pysimple" {
  name                 = "pysimple"
  image_scanning_configuration {
    scan_on_push = true
  }
}
