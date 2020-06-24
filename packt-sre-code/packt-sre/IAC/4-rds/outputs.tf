output "rds_cname" {
  value       = aws_db_instance.default.endpoint
  description = "DB connection string"
}

output "rds_arn" {
  value       = aws_db_instance.default.arn
  description = "cross region replciation arn"
}

output "rds_sg_id" {
  value       = aws_security_group.default.id
  description = "DB connection string"
}