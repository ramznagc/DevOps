# Docker — Hands-on Labs 🐳

Welcome to the Docker section of my DevOps Learning Portfolio!

This directory contains hands-on exercises, configuration files, and practical examples for learning Docker, containerization, and infrastructure automation.

## 📚 Lessons

### Docker-01: Installing Docker on AWS EC2

Learn how to install and configure Docker on an Amazon Linux 2023 EC2 instance.

**Topics covered:**
- Launching an EC2 instance and connecting through SSH
- Installing Docker with `dnf`
- Starting and enabling the Docker service
- Configuring Docker access for `ec2-user`
- Verifying the Docker installation
- Provisioning a Docker-ready EC2 instance using Terraform or AWS CloudFormation

📂 [Open Docker-01: Installation on EC2](./docker-01-installation-ec2/README.md)

### Docker-02: Docker Container Basic Operations

Learn how to manage Docker containers throughout their lifecycle.

**Topics covered:**
- Exploring Docker command help
- Running interactive Ubuntu containers
- Listing running and stopped containers
- Understanding container IDs, names, and statuses
- Starting and stopping containers
- Executing commands inside running containers
- Inspecting container configuration
- Removing containers safely

📂 [Open Docker-02: Container Basic Operations](./docker-02-container-basic-operations/README.md)

## 🛠️ Technologies

- Docker
- AWS EC2
- Amazon Linux 2023
- Terraform
- AWS CloudFormation
- Linux
- Git and GitHub

## 🔐 Security Best Practices

- Restrict SSH access to trusted IP addresses instead of exposing port 22 to the entire internet.
- Open only the network ports required by your application.
- Never commit private keys, AWS credentials, access tokens, or other secrets.
- Review infrastructure configuration before deploying AWS resources.
- Use Docker volumes when data must persist independently of a container's lifecycle.
- Remove only the containers and resources created for your own lab.

## 🎯 Learning Goals

- Understand Docker and containerization fundamentals.
- Practice installing and managing Docker.
- Learn the lifecycle of Docker containers.
- Build practical Linux and DevOps skills.
- Explore Infrastructure as Code using Terraform and CloudFormation.
- Maintain a clear, organized, version-controlled learning portfolio.

## 📁 Repository Structure

```text
Docker/
├── README.md
├── docker-01-installation-ec2/
│   ├── README.md
│   ├── ec2-docker.tf
│   └── docker-installation-template.yml
└── docker-02-container-basic-operations/
    └── README.md
```

## 🧹 Lab Cleanup

Review the resources created during each lab and remove only those that are no longer needed. AWS infrastructure deployment is optional for these documentation files; committing them to GitHub does not create AWS resources.

---

*This section is a work in progress. More Docker labs will be added as I continue learning.*
