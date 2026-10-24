# Terraform Hands-On Labs 🚀

This repository contains my hands-on Terraform labs as part of my AWS and DevOps training. It documents my practical learning journey, from installing Terraform and provisioning basic AWS resources to working with reusable modules, remote state management, and workspaces.

The goal of this repository is to strengthen my Infrastructure as Code (IaC) skills by practicing Terraform concepts through real-world-inspired AWS exercises.

## 📚 Learning Path

### Session 01 — Terraform Installation & Basic Operations

Introduction to Terraform and provisioning AWS infrastructure.

- Installing Terraform on Amazon Linux 2023
- Understanding Terraform providers and resources
- Configuring the AWS provider
- Provisioning EC2 instances and S3 buckets
- Running `terraform init`, `plan`, and `apply`
- Inspecting Terraform state
- Understanding the basic Terraform workflow

### Session 02 — Commands, Variables, Conditionals & Loops

Exploring Terraform commands and building more flexible configurations.

- Using `terraform validate`, `fmt`, `console`, `show`, and `graph`
- Working with output values
- Declaring and assigning input variables
- Using `.tfvars` files and environment variables
- Understanding local values
- Practicing conditional expressions and loops
- Making configurations more reusable and configurable

### Session 03 — Data Sources, Remote Backend & Provisioners

Learning how Terraform retrieves information, manages state remotely, and performs provisioning tasks.

- Querying existing AWS resources with data sources
- Working with Amazon Machine Images (AMIs)
- Configuring an Amazon S3 remote backend
- Exploring remote state and state locking
- Using `local-exec`, `remote-exec`, and `file` provisioners
- Understanding Terraform state management

### Session 04 — Terraform Modules & Import

Organizing infrastructure code into reusable components and bringing existing resources under Terraform management.

- Creating reusable Terraform modules
- Separating module files into `main.tf`, `variables.tf`, and `outputs.tf`
- Passing inputs to modules and exposing outputs
- Organizing configurations for development and production environments
- Importing existing AWS resources into Terraform state
- Practicing CLI-based imports and declarative import blocks
- Exploring generated configuration for imported resources

### Session 05 — Publishing Modules & Terraform Workspaces

Exploring module distribution and managing separate Terraform state environments.

- Preparing a reusable AWS EC2 module
- Configuring variables, outputs, and user data
- Publishing and versioning modules through GitHub and the Terraform Registry
- Using semantic version tags
- Creating and switching between Terraform workspaces
- Managing separate state for different workspaces
- Practicing environment-specific infrastructure configurations

## 🛠️ Technologies & Tools

- **Cloud Platform:** Amazon Web Services (AWS)
- **Infrastructure as Code:** Terraform
- **Compute:** Amazon EC2
- **Storage & Remote State:** Amazon S3
- **Networking:** Amazon VPC and Security Groups
- **Identity & Access Management:** AWS IAM
- **Version Control:** Git and GitHub
- **Scripting & Provisioning:** Bash and Terraform provisioners
- **Module Distribution:** Terraform Registry

## 📂 Repository Structure

The repository is organized by training session to keep each hands-on exercise separate and easy to follow.

```text
DevOps/
├── README.md
├── terraform-01-installation-basic-operations/
├── terraform-02-commands-variables-conditionals-loops/
├── terraform-03-data-sources-backend-provisioners/
├── terraform-04-modules-import/
└── terraform-05-publishing-modules-workspaces/
```

Each session directory contains its own hands-on documentation and, where applicable, Terraform configuration files and supporting resources.

*Directory names may be adjusted to match the actual folder names in the repository.*

## 🎯 Learning Objectives

Through these exercises, I aim to:

- Understand Terraform's declarative approach to infrastructure management.
- Provision and manage AWS resources using code.
- Write configurable and reusable Terraform configurations.
- Understand the Terraform lifecycle and state management.
- Store Terraform state remotely using Amazon S3.
- Build and reuse Terraform modules.
- Import existing infrastructure into Terraform management.
- Explore workspaces and environment-specific configurations.
- Follow better practices for infrastructure documentation and version control.

## 🔐 Security & Cost Considerations

These labs are intended for learning and experimentation, not production deployment.

- Never commit AWS access keys, private keys, passwords, or other secrets.
- Do not commit Terraform state files, local `.terraform` directories, or personal `.tfvars` files.
- Review IAM permissions and Security Group rules before deployment.
- Restrict SSH access to trusted IP addresses instead of exposing it publicly.
- Review the resources in `terraform plan` before applying changes.
- AWS resources may incur charges. Check costs and delete lab resources when they are no longer needed.
- Handle remote state carefully, as it may contain sensitive infrastructure information.

## 📈 Progress

**Current focus:** Terraform and Infrastructure as Code on AWS.

This repository will evolve as I continue my AWS DevOps training and work on more hands-on exercises and projects.

---

*Learning by doing — building, managing, and automating cloud infrastructure one lab at a time.*