output "alb_arn" {
  value       = module.ecs-mr.alb_arn
  description = "ALB ARN refernces"
}

output "alb_name" {
  value       = module.ecs-mr.alb_name
  description = "ALB names"
}

output "alb_target_arn" {
  value       = module.ecs-mr.alb_target_arn
  description = "ALB target group ARN names"
}

output "ecs_security_group" {
  value       = module.ecs-mr2.ecs_security_group
  description = "SG id's for ECS groups"
}

output "alb_arn2" {
  value       = module.ecs-mr2.alb_arn
  description = "ALB ARN refernces"
}

output "alb_name2" {
  value       = module.ecs-mr2.alb_name
  description = "ALB names"
}

output "alb_target_arn2" {
  value       = module.ecs-mr2.alb_target_arn
  description = "ALB target group ARN names"
}

output "ecs_security_group2" {
  value       = module.ecs-mr2.ecs_security_group
  description = "SG id's for ECS groups"
}
