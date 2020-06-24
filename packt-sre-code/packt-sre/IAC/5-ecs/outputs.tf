output "alb_arn" {
  value       = aws_alb.main.arn
  description = "ALB ARN refernces"
}

output "alb_name" {
  value       = aws_alb.main.name
  description = "ALB names"
}

output "alb_target_arn" {
  value       = aws_alb_target_group.app.arn
  description = "ALB target group ARN names"
}

output "ecs_security_group" {
  value       = aws_security_group.ecs_tasks.id
  description = "SG id's for ECS groups"
}

output "regions" {
  value       = var.region
  description = "list of the configured regions"
}