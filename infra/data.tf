data "aws_s3_bucket" "bronze" {
    bucket = "elite-datalake-bronze-dev"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "../src"
  output_path = "../build/lambda.zip"
}