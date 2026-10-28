# Docker-01: Installing Docker on Amazon Linux 2023 EC2 🐳

## 📌 Overview

This hands-on lab demonstrates how to install and configure Docker on an Amazon Linux 2023 EC2 instance. It also introduces infrastructure provisioning using AWS CloudFormation and Terraform.

## 🎯 Learning Objectives

By completing this lab, you will learn how to:

- Launch an Amazon Linux 2023 EC2 instance and connect via SSH.
- Update system packages using `dnf`.
- Install Docker and manage its system service.
- Configure Docker to start automatically after a reboot.
- Configure Docker access for the `ec2-user`.
- Verify the Docker installation.
- Provision a Docker-ready EC2 instance using Infrastructure as Code (IaC).

## 🧰 Prerequisites

- An AWS account with permission to create EC2 instances and security groups.
- An EC2 key pair.
- Basic Linux command-line and SSH knowledge.
- Terraform or AWS CloudFormation for the provisioning examples.

## 📂 Project Files

| File | Description |
|---|---|
| `ec2-docker.tf` | Terraform configuration for creating an EC2 instance and installing Docker |
| `docker-installation-template.yml` | AWS CloudFormation template for provisioning a Docker-ready EC2 instance |

## 🚀 Part 1 — Launch and Connect to EC2

Launch an Amazon Linux 2023 EC2 instance and configure SSH access. For security, restrict inbound SSH traffic to your trusted public IP address.

Connect using your own private key and instance public DNS name:

```bash
chmod 400 .ssh/my-key.pem
ssh -i .ssh/my-key.pem ec2-user@YOUR_EC2_PUBLIC_DNS
```

Replace `YOUR_EC2_PUBLIC_DNS` with your instance's public DNS name.

**Security:** Never upload your private key or actual connection credentials to GitHub.

## ⚙️ Part 2 — Install Docker

### 1. Update system packages

```bash
sudo dnf update -y
```

### 2. Install Docker

```bash
sudo dnf install docker -y
```

### 3. Start the Docker service

```bash
sudo systemctl start docker
```

### 4. Enable Docker at boot

```bash
sudo systemctl enable docker
```

### 5. Check the service status

```bash
sudo systemctl status docker
```

Confirm that the service is active and running.

### 6. Add `ec2-user` to the Docker group

```bash
sudo usermod -aG docker ec2-user
```

Reconnect to your SSH session for the new group membership to take effect. Alternatively, activate the group in a new shell:

```bash
newgrp docker
```

> **Security note:** Membership in the `docker` group grants powerful privileges on the host. Only add trusted users.

### 7. Verify the installation

Check the Docker client and server versions:

```bash
docker version
```

Inspect the Docker environment:

```bash
docker info
```

Run a test container:

```bash
docker run hello-world
```

If the test image is downloaded and the welcome message appears, Docker is working.

## 🏗️ Part 3 — Infrastructure as Code

This lesson includes two alternative approaches to provisioning a Docker-ready EC2 instance.

### Option A: Terraform

Review `ec2-docker.tf` to understand how infrastructure can be defined using Terraform.

### Option B: AWS CloudFormation

Review `docker-installation-template.yml` to understand how AWS resources can be defined using CloudFormation.

These are alternative approaches. Review the configuration and security group rules before deployment, and avoid creating duplicate resources unnecessarily.

## 🔐 Security Best Practices

- Restrict SSH access to trusted IP addresses instead of `0.0.0.0/0`.
- Open only the network ports required by your application.
- Never commit private keys, AWS credentials, or other secrets.
- Review the AMI, instance type, and security group rules before deployment.
- Check AWS resources and costs after completing the lab.

## 🧹 Cleanup

Remove the AWS resources created for this lab when they are no longer needed.

- For Terraform-managed resources, check the active workspace and state before running `terraform destroy`.
- For CloudFormation-managed resources, review the stack and its resources before deleting it.

Do not delete resources belonging to other projects.

## ✅ Summary

In this lab, we installed Docker on Amazon Linux 2023, configured the Docker service, verified the installation, and explored two Infrastructure as Code approaches for provisioning a Docker-ready EC2 instance.

---

*Part of my DevOps Learning Portfolio.*
