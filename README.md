# DevOps Learning Portfolio

Welcome to my DevOps Learning Portfolio! 🚀

This repository documents my learning journey, hands-on labs, and practical exercises across DevOps technologies and tools.

## 📚 Topics

### Terraform

Infrastructure as Code (IaC) with Terraform, including installation, configuration, variables, data sources, state management, modules, and workspaces.

📂 **[Explore Terraform](./Terraform/README.md)**

Topics covered:
- Terraform installation and basic operations
- Commands, variables, conditionals, and loops
- Data sources, backend configuration, and provisioners
- Modules and resource import
- Publishing Terraform modules and using workspaces

### Docker

Containerization fundamentals, Docker image operations, and multi-container application setup with Docker Compose.

📂 **[Explore Docker projects](./Docker/)**

### Amazon ECR

Hands-on practice with Amazon Elastic Container Registry: provision a Docker host using Terraform, create private repositories, authenticate Docker with an EC2 IAM role, and build, push, pull, tag and delete container images.

📂 **[Explore the Amazon ECR hands-on](./ECR/README.md)**

Topics covered:
- EC2 Docker host provisioning with Terraform
- ECR registry and repository configuration through the AWS Console and CLI
- Docker image build, tag, push and pull workflows
- Mutable and immutable image tags
- ECR lifecycle policies and repository cleanup

### Kubernetes

A progressive collection of hands-on Kubernetes labs. The learning path starts with cluster installation and core resources, then covers networking, persistent storage, application configuration, microservices, autoscaling, Amazon EKS, and advanced scheduling and health checks.

📂 **[Explore all Kubernetes lessons](./Kubernetes/README.md)**

Lessons include:
- Cluster installation on AWS EC2 with kubeadm, containerd, and Flannel
- Pods, ReplicaSets, Deployments, namespaces, rolling updates, and rollbacks
- Services, ClusterIP, NodePort, DNS, endpoints, and service discovery
- Volumes, PersistentVolumes, PersistentVolumeClaims, StorageClasses, and dynamic provisioning
- Secret types, application credentials, registry authentication, ServiceAccount tokens, and bootstrap tokens
- A Node.js/MongoDB ToDo application, Metrics Server, and Horizontal Pod Autoscaler
- Amazon EKS cluster setup, worker nodes, IRSA, and Cluster Autoscaler
- EKS Ingress path and host-based routing, rewrite-target annotations, and dynamic Amazon EBS provisioning
- Pod scheduling with nodeName, nodeSelector, node affinity, Pod affinity, taints, and tolerations
- Container health checks with liveness, readiness, and startup probes using HTTP, TCP, and exec

### Helm

Package and manage Kubernetes applications with Helm. The learning material covers charts, repositories, releases, templates, values, versioning, and chart distribution.

📂 **[Explore Helm fundamentals](./Helm/README.md)**

Topics covered:
- Helm installation and chart discovery with Artifact Hub
- Chart creation, values files, template objects, and template functions
- Release installation, inspection, upgrades, history, and rollback
- Packaging charts and publishing a classic chart repository with static GitHub hosting

#### Helm Chart Repository — ChartMuseum

A companion hands-on guide to hosting a classic Helm chart repository with ChartMuseum.

📂 **[Explore ChartMuseum](./Helm/Helm-Chart-Museum/README.md)**

Topics covered:
- Running ChartMuseum with local filesystem storage
- Adding a ChartMuseum endpoint as a Helm repository
- Uploading chart archives through the ChartMuseum API
- Publishing chart versions with the helm-push plugin
- Installing, upgrading, and rolling back releases from the repository

### Git & GitHub

Version control fundamentals, repository organization, and tracking project changes with commits and pushes.

## 🧭 Learning Approach

- Practice concepts through hands-on labs.
- Keep project instructions and configuration examples documented.
- Make changes in small, trackable steps.

## 🎯 Goals

- Build practical DevOps skills through hands-on projects.
- Learn Infrastructure as Code principles.
- Organize labs and projects in a clear, reusable repository structure.
- Document technical knowledge and implementation steps.

## 🛠️ Technologies

- Terraform
- Docker and Docker Compose
- Kubernetes, kubeadm, containerd, and Flannel
- AWS, Amazon EC2, Amazon EKS, IAM, Amazon EBS, and Amazon ECR
- Kubernetes Ingress, CSI storage, Metrics Server, HPA, scheduling controls, and container health probes
- Helm, Helm charts, ChartMuseum, and chart repositories
- Git and GitHub

More tools and projects will be added as I continue learning.

---

*This repository is a work in progress and will grow alongside my DevOps journey.*
