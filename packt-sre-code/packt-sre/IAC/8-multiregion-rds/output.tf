output "rds_cname" {
  value       = module.rds-mr.rds_cname
  description = "DB connection string"
}

output "rds_arn" {
  value       = module.rds-mr.rds_arn
  description = "cross region replciation arn"
}

output "rds_sg_id" {
  value       = module.rds-mr.rds_sg_id
  description = "DB connection string"
}

output "rds_cname2" {
  value       = module.rds-mr2.rds_cname
  description = "DB connection string"
}

output "rds_arn2" {
  value       = module.rds-mr2.rds_arn
  description = "cross region replciation arn"
}

output "rds_sg_id2" {
  value       = module.rds-mr2.rds_sg_id
  description = "DB connection string"
}