output "endpoint" {
  value = aws_eks_cluster.example.endpoint
}
output "kubeconfig-certificate-authority-data" {
  value = aws_eks_cluster.example.certificate_authority.0.data
}

output "userdata" {
    value = local.main-node-userdata
}