# Terraform Session 02 — Commands, Variables, Conditionals & Loops 🚀

## 📌 Overview

This session explores essential Terraform commands, input variables, local values, conditional expressions, and iteration techniques.

Through hands-on exercises with AWS resources, this session demonstrates how to validate and format Terraform configurations, inspect infrastructure, customize resource definitions, and manage multiple resources using `count` and `for_each`.

## 🎯 Learning Objectives

By the end of this session, you will be able to:

- Use essential Terraform CLI commands.
- Validate and format Terraform configuration files.
- Explore Terraform expressions using the interactive console.
- Inspect Terraform state and resource dependencies.
- Define and use input variables and output values.
- Assign variable values through CLI arguments, environment variables, and `.tfvars` files.
- Use local values to avoid repeating expressions.
- Create multiple resources with `count` and `for_each`.
- Apply conditional expressions to Terraform configurations.
- Provision and manage AWS S3 buckets and IAM users through Terraform.

## 🧰 Technologies & Tools

- **Terraform** — Infrastructure as Code
- **AWS** — Cloud infrastructure
- **Amazon EC2** — Virtual compute instances
- **Amazon S3** — Object storage
- **AWS IAM** — Identity and access management
- **Git & GitHub** — Version control and documentation

## 📚 Topics Covered

### Part 1 — Terraform Commands

Practice the following commands and understand how they support the Terraform workflow.

| Command | Purpose |
|---|---|
| `terraform init` | Initializes the working directory and installs required providers. |
| `terraform plan` | Previews proposed infrastructure changes. |
| `terraform apply` | Applies the planned configuration changes. |
| `terraform validate` | Checks configuration syntax and internal consistency. |
| `terraform fmt` | Formats Terraform files using the standard style. |
| `terraform console` | Evaluates Terraform expressions interactively. |
| `terraform show` | Displays information about the current state or a saved plan. |
| `terraform graph` | Generates a DOT-format graph of resource dependencies. |
| `terraform output` | Displays output values stored in Terraform state. |
| `terraform destroy` | Plans and removes resources managed by the configuration. |

#### Terraform Console

Use the interactive console to explore resource attributes, expressions, and built-in functions.

Examples from the exercises:

```hcl
aws_instance.tf-ec2.private_ip
min(1, 2, 3)
lower("HELLO")
aws_s3_bucket.tf-s3.arn
```

The console can also evaluate expressions that reference resource attributes and local files.

#### Outputs

Output blocks expose selected information about managed resources.

```hcl
output "tf_example_public_ip" {
  value = aws_instance.tf-ec2.public_ip
}

output "tf_example_s3_meta" {
  value = aws_s3_bucket.tf-s3.region
}
```

Retrieve output values with:

```bash
terraform output
terraform output -json
terraform output tf_example_public_ip
```

### Part 2 — Variables & Local Values

#### Input Variables

Input variables make configurations more flexible by allowing values to be changed without rewriting resource definitions.

The exercises use variables for:

- EC2 instance names
- EC2 instance types
- AMI IDs
- S3 bucket names

Example:

```hcl
variable "ec2_type" {
  default = "t2.micro"
}

variable "s3_bucket_name" {
  type = string
}
```

#### Assigning Variable Values

Explore different ways to provide values to Terraform variables.

**1. Command-line arguments**

```bash
terraform plan -var="s3_bucket_name=my-unique-bucket-name"
```

**2. Environment variables**

```bash
export TF_VAR_s3_bucket_name="my-unique-bucket-name"
terraform plan
```

**3. Variable definition files**

`terraform.tfvars`:

```hcl
s3_bucket_name = "my-unique-bucket-name"
```

Load a specific variable file with:

```bash
terraform plan -var-file="my.tfvars"
```

The exercises also introduce automatically loaded `*.auto.tfvars` files.

> **Note:** S3 bucket names must be globally unique. Replace all example names with names suitable for your AWS environment.

#### Local Values

Local values let you assign a reusable name to an expression within a Terraform module.

```hcl
locals {
  mytag = "my-local-name"
}
```

A local value can then be referenced in resource configurations:

```hcl
tags = {
  Name = "${local.mytag}-from-locals-block"
}
```

### Part 3 — Conditionals & Loops

Terraform provides `count` and `for_each` to manage multiple instances of a resource without duplicating entire resource blocks.

#### Using `count`

The `count` meta-argument creates a specified number of resource instances.

```hcl
variable "num_of_buckets" {
  default = 2
}

resource "aws_s3_bucket" "tf-s3" {
  count  = var.num_of_buckets
  bucket = "${var.s3_bucket}-${count.index}"
}
```

In this exercise, the configuration uses `count.index` to distinguish the generated bucket names.

#### Conditional Expressions

Conditional expressions select a value based on a Boolean condition.

```hcl
count = var.num_of_buckets != 0 ? var.num_of_buckets : 3
```

This example uses a conditional expression to select the resource count.

#### Using `for_each`

The `for_each` meta-argument creates resource instances from a map or a set of strings.

The exercise introduces a collection of user names:

```hcl
variable "users" {
  default = ["santino", "michael", "fredo"]
}
```

Example resources:

```hcl
resource "aws_s3_bucket" "tf-s3" {
  for_each = toset(var.users)
  bucket   = "example-tf-s3-bucket-${each.value}"
}

resource "aws_iam_user" "new_users" {
  for_each = toset(var.users)
  name     = each.value
}
```

Each item in the collection is used to create a corresponding resource instance.

## 🔄 Hands-On Workflow

The exercises follow an iterative workflow:

1. Create or modify the Terraform configuration.
2. Initialize the working directory when needed.
3. Validate and format the configuration.
4. Review the proposed changes with `terraform plan`.
5. Apply the configuration when the plan is correct.
6. Inspect the resulting AWS resources and Terraform outputs.
7. Clean up lab resources when finished.

Useful commands:

```bash
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
terraform output
terraform destroy
```

## 🔐 Security & Cost Considerations

- Never commit AWS credentials, private keys, passwords, or other secrets.
- Exclude Terraform state files and sensitive variable files from Git.
- Use unique S3 bucket names for your exercises.
- Verify that the AMI ID, AWS region, and EC2 key pair match your environment.
- Follow the principle of least privilege when assigning IAM permissions. Avoid broad policies such as `IAMFullAccess` unless explicitly required in a controlled lab.
- Review every execution plan before applying changes.
- Check for billable resources and destroy lab infrastructure when it is no longer needed.

## ✅ Session Summary

This session builds on the Terraform fundamentals introduced in Session 01.

It focuses on writing more flexible configurations with variables and local values, inspecting Terraform configurations with CLI tools, and managing multiple AWS resources through conditional expressions, `count`, and `for_each`.

These concepts provide a foundation for more advanced Terraform topics, including data sources, remote state, provisioners, modules, and environment management.

---

**Learning by doing — making infrastructure configurations more flexible and reusable.**