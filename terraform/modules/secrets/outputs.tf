output "openai_api_key_arn" {
  value = data.aws_ssm_parameter.openai_api_key.arn
}

output "cpaor_email_arn" {
  value = data.aws_ssm_parameter.cpaor_email.arn
}

output "acaps_password_arn" {
  value = data.aws_ssm_parameter.acaps_password.arn
}

output "streamlit_password_arn" {
  value = data.aws_ssm_parameter.streamlit_pwd.arn
}

output "streamlit_app_environment_arn" {
  value = data.aws_ssm_parameter.app_environment.arn
}

output "streamlit_ga_tracking_id_arn" {
  value = data.aws_ssm_parameter.ga_tracking_id.arn
}

output "acled_username_arn" {
  value = data.aws_ssm_parameter.acled_username.arn
}

output "acled_password_arn" {
  value = data.aws_ssm_parameter.acled_password.arn
}