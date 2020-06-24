locals {
  source_repo      = "https://git-codecommit.eu-west-2.amazonaws.com/v1/repos/pysimple"
  source_repo_cars = "https://git-codecommit.eu-west-2.amazonaws.com/v1/repos/py-cars"
  source_branch    = "refs/heads/master"
  vpc_id           = "vpc-05939a73c8684c026"
  subnet_ids       = ["subnet-0b05b60e1a8d9a65b","subnet-071fabf574452338c","subnet-02d640b292e5a5709","subnet-0801380048c54cef6"]
  sg_ids           = ["sg-0e4561a6947726ff0"]
}

resource "aws_codebuild_project" "simple" {
  name           = "pysimple"
  description    = "pysimple build project"
  build_timeout  = "5"
  service_role   = "arn:aws:iam::915793320862:role/service-role/codebuild-simple-py-service-role"
  source_version = local.source_branch
  artifacts {
    type = "NO_ARTIFACTS"
  }
  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/standard:2.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode             = true

    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = "eu-west-2"
    }
    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = "915793320862"
    }
    environment_variable {
      name  = "IMAGE_REPO_NAME"
      value = "pysimple"
    }
    environment_variable {
      name  = "IMAGE_TAG"
      value = "latest"
    }
  }
  logs_config {
    cloudwatch_logs {
      group_name  = "py-simple"
      stream_name = "build"
    }
  }
  source {
    type            = "CODECOMMIT"
    location        = local.source_repo
    git_clone_depth = 1
    git_submodules_config {
      fetch_submodules = true
    }
  }

  tags = {
    Environment = "Test"
  }
}

resource "aws_codebuild_project" "cars" {
  name           = "pycars"
  description    = "cars MS build project"
  build_timeout  = "5"
  service_role   = "arn:aws:iam::915793320862:role/service-role/codebuild-simple-py-service-role"
  source_version = local.source_branch
  artifacts {
    type = "NO_ARTIFACTS"
  }
  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/standard:2.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode             = true

    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = "eu-west-2"
    }
    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = "915793320862"
    }
    environment_variable {
      name  = "IMAGE_REPO_NAME"
      value = "py-cars"
    }
    environment_variable {
      name  = "AWS_SECOND_REGION"
      value = "eu-west-1"
    }
    environment_variable {
      name  = "IMAGE_TAG"
      value = "latest"
    }
    environment_variable {
      name  = "HOST"
      value = "cars.cu6dyxkvr5xc.eu-west-2.rds.amazonaws.com"
    }
    environment_variable {
      name  = "DB"
      value = "cars"
    }
    environment_variable {
      name  = "DB_USER"
      value = "carsa"
    }
    environment_variable {
      name  = "DB_PASS"
      value = "LetmeinAWS!!"
    }
  }
  logs_config {
    cloudwatch_logs {
      group_name  = "py-cars"
      stream_name = "build"
    }
  }
  source {
    type            = "CODECOMMIT"
    location        = local.source_repo_cars
    git_clone_depth = 1
    git_submodules_config {
      fetch_submodules = true
    }
  }
  vpc_config {
    vpc_id = local.vpc_id

    subnets = local.subnet_ids

    security_group_ids = local.sg_ids
  }

  tags = {
    Environment = "Test"
  }
}

