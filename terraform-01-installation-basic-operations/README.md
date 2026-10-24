# Terraform Session 01 — Installation & Basic Operations 🚀

## 📌 Overview

This session introduces **Terraform** and the fundamentals of Infrastructure as Code (IaC). It covers installing Terraform on Amazon Linux 2023, configuring the AWS provider, defining infrastructure resources, and learning the basic Terraform workflow.

The hands-on exercises focus on provisioning AWS resources and understanding how Terraform manages infrastructure through configuration files and state.

## 🎯 Learning Objectives

By the end of this session, you will understand how to:

- Install Terraform on Amazon Linux 2023.
- Configure the AWS provider.
- Define Terraform providers and resources.
- Work with basic AWS resources such as EC2 and S3.
- Initialize a Terraform working directory.
- Review planned infrastructure changes before applying them.
- Create and inspect infrastructure using Terraform.
- Understand the role of Terraform state.

## 🧰 Technologies & Tools

- **Terraform** — Infrastructure as Code
- **AWS** — Cloud infrastructure
- **Amazon EC2** — Virtual servers
- **Amazon S3** — Object storage
- **Amazon Linux 2023** — Operating system used for installation
- **Git & GitHub** — Version control and documentation

## 📚 Topics Covered

### 1. Terraform Installation

Install Terraform on an Amazon Linux 2023 environment and verify that the installation works.

### 2. Providers & Resources

Learn the role of providers and resources in Terraform configuration files.

- Configure the AWS provider.
- Define AWS infrastructure resources.
- Understand the relationship between configuration and deployed infrastructure.

### 3. Basic AWS Resources

Explore Terraform configurations for common AWS services:

- Amazon EC2 instances
- Amazon S3 buckets

### 4. The Terraform Workflow

Practice the core Terraform commands:

| Command | Purpose |
|---|---|
| `terraform init` | Initialize the working directory and download required providers. |
| `terraform plan` | Preview the infrastructure changes Terraform intends to make. |
| `terraform apply` | Apply the proposed infrastructure changes. |
| `terraform show` | Inspect the current state or a saved plan. |
| `terraform state list` | List resources tracked in the Terraform state. |

### 5. Terraform State

Understand how Terraform state tracks the resources managed by a configuration and why state is important when working with infrastructure.

## 🔄 Typical Workflow

```text
Write Configuration
        ↓
terraform init
        ↓
terraform plan
        ↓
Review Changes
        ↓
terraform apply
        ↓
Inspect Resources & State
```

## 🔐 Security & Cost Considerations

- Never commit AWS access keys, private keys, passwords, or other secrets.
- Do not commit Terraform state files or sensitive variable files.
- Review the execution plan before applying changes.
- Avoid unrestricted inbound access to AWS resources.
- Be aware that EC2 instances and other AWS resources may incur charges.
- Remove lab resources when they are no longer needed, after verifying what will be destroyed.

## ✅ Session Summary

This session establishes the foundation for working with Terraform on AWS. It introduces the basic configuration structure, common Terraform commands, resource provisioning, and state management.

These concepts provide the starting point for more advanced topics, including variables, data sources, remote backends, modules, and reusable infrastructure.

---

**Learning by doing — one Terraform session at a time.**