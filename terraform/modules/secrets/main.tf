data "aws_ssm_parameter" "openai_api_key" {
  name = "openai_api_key"
}

data "aws_ssm_parameter" "cpaor_email" {
  name = "cpaor_email"
}

data "aws_ssm_parameter" "acaps_password" {
  name = "acaps_password"
}

data "aws_ssm_parameter" "streamlit_pwd" {
  name = "streamlit_password"
}

data "aws_ssm_parameter" "app_environment" {
  name = "app_environment"
}

data "aws_ssm_parameter" "ga_tracking_id" {
  name = "ga_tracking_id"
}

data "aws_ssm_parameter" "acled_username" {
  name = "acled_username"
}

data "aws_ssm_parameter" "acled_password" {
  name = "acled_password"
}