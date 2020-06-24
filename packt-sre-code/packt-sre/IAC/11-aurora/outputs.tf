output "arn" {
  value       = join("", aws_rds_cluster.main.*.arn)
  description = "Amazon Resource Name (ARN) of cluster"
}

output "endpoint" {
  value       = join("", aws_rds_cluster.main.*.endpoint)
  description = "The DNS address of the RDS instance"
}

output "cluster_identifier" {
  value       = join("", aws_rds_cluster.main.*.cluster_identifier)
  description = "Cluster Identifier"
}

