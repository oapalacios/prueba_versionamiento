resource "aws_lambda_function" "ingest_cities" {

    function_name                  = "lambda-fcn-dev-api-s3-ingesta-cities"
    role                           = "arn:aws:iam::733918434492:role/role-dev-lambda-function-ingest"
    handler                        = "lambda_function.lambda_handler"
    memory_size                    = 300
    runtime                        = "python3.13"
    timeout                        = 60   

    filename                       = data.archive_file.lambda_zip.output_path
    source_code_hash               = data.archive_file.lambda_zip.output_base64sha256
    publish                        = true

    environment {
        variables = {
            "BUCKET_BRONZE" = "elite-datalake-bronze"
            "ENV"           = "dev"
        }
    }

    vpc_config {
        security_group_ids          = [
            "sg-0156d900a5874598a",
        ]
        subnet_ids                  = [
            "subnet-03d5807320b31bbb8",
            "subnet-0d6157b3094f292d4",
        ]
        vpc_id                      = "vpc-0f28d7cc60e173b34"
    }

    layers = [
        "arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python313:7",
    ]

    ephemeral_storage {
        size = 512
    }

    tracing_config {
        mode = "PassThrough"
    }

    logging_config {
        log_format            = "Text"
        log_group             = "/aws/lambda/lambda-fcn-dev-api-s3-ingesta-cities"
    }

}


# ----------------------------------
# Alias dev (recurso separado)
resource "aws_lambda_alias" "dev" {
  name             = "dev"
  function_name    = aws_lambda_function.ingest_cities.function_name
  function_version = aws_lambda_function.ingest_cities.version
}