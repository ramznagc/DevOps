# Docker — Hands-on Labs 🐳

Welcome to the Docker section of my DevOps Learning Portfolio.

This directory contains hands-on exercises, configuration files, and practical examples for learning Docker and containerization.

## 📚 Lessons

### Docker-01: Installing Docker on AWS EC2

Learn how to install and configure Docker on an Amazon Linux 2023 EC2 instance.

**Topics covered**
- Launching an EC2 instance and connecting through SSH
- Installing Docker with `dnf`
- Starting and enabling the Docker service
- Configuring Docker access for the `ec2-user`
- Verifying the Docker installation
- Provisioning a Docker-ready EC2 instance with Terraform or AWS CloudFormation

📂 [Open Docker-01: Installation on EC2](./docker-01-installation-ec2/README.md)

## 🛠️ Technologies

- Docker
- AWS EC2
- Amazon Linux 2023
- Terraform
- AWS CloudFormation
- Git and GitHub

## 🔐 Security Notes

- Restrict SSH access to trusted IP addresses instead of exposing port 22 to the entire internet.
- Open only the ports required by your application.
- Never commit private keys, credentials, access tokens, or other secrets.
- Review AWS resources and costs after completing each lab.

## 🎯 Learning Goals

- Understand containerization fundamentals.
- Practice installing and managing Docker on cloud infrastructure.
- Automate infrastructure provisioning.
- Document practical DevOps exercises in a version-controlled repository.

---

*This section is a work in progress. More Docker labs will be added as I continue learning.*
