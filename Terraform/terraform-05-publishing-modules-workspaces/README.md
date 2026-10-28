# Hands-on Terraform 05: Publishing Modules and Terraform Workspaces

## Overview

This hands-on session focuses on publishing reusable Terraform modules to the Terraform Registry and managing separate infrastructure states with Terraform workspaces.

## Learning Outcomes

By completing this session, you will learn how to:

- Build a reusable Terraform module for AWS infrastructure.
- Define module inputs and outputs.
- Use data sources to discover the latest Amazon Linux 2023 AMI.
- Configure EC2 instances, security groups, dynamic ingress rules, and user data.
- Publish a Terraform module using GitHub and the Terraform Registry.
- Version a module using semantic versioning and Git tags.
- Create, list, select, and delete Terraform workspaces.
- Use separate workspace states and workspace-based configuration values.

## Session Outline

- **Part 1:** Publish Terraform Modules
- **Part 2:** Use Terraform Workspaces

---

## Part 1: Publish Terraform Modules

### 1. Terraform Registry and Module Publishing

Terraform modules allow infrastructure configurations to be reused and shared.

The public Terraform Registry supports published modules that use GitHub repositories, standard module structures, and semantic version tags.

**Requirements for publishing a public module:**

- A public GitHub repository.
- A repository name following the `terraform-[PROVIDER]-[NAME]` convention.
- A repository description.
- A standard Terraform module structure.
- At least one semantic version tag, such as `v0.0.1`.

Reference: [Publishing Modules to the Terraform Registry](https://developer.hashicorp.com/terraform/registry/modules/publish)

### 2. Build an AWS EC2 Module

The hands-on exercise creates a reusable module that provisions an EC2 instance using the latest Amazon Linux 2023 AMI, installs Docker through user data, and configures a security group.

**Module structure:**

```text
terraform-aws-docker-instance/
├── main.tf
├── variables.tf
├── outputs.tf
├── versions.tf
├── userdata.sh
├── README.md
└── .gitignore
```

**Key files and responsibilities:**

| File | Purpose |
|---|---|
| `versions.tf` | Declares the required AWS provider version |
| `variables.tf` | Defines configurable inputs such as instance type, key name, instance count, tags, and ports |
| `main.tf` | Defines the AMI data source, EC2 instance, and security group |
| `outputs.tf` | Exposes instance public IP addresses, instance IDs, and security group ID |
| `userdata.sh` | Configures the hostname and installs and enables Docker |
| `README.md` | Documents the module and explains how to use it |
| `.gitignore` | Excludes local Terraform files, state files, and variable files |

### 3. Terraform Concepts Practiced

The module demonstrates several Terraform features:

- **Data sources:** Retrieve the latest Amazon Linux 2023 AMI matching the specified filters.
- **Input variables:** Customize the instance type, SSH key name, instance count, server name, and security group ports.
- **`count`:** Control how many EC2 instances are created.
- **Dynamic blocks:** Generate security group ingress rules from a list of ports.
- **`templatefile()`:** Pass a variable into the user-data script.
- **Outputs:** Expose useful resource attributes after deployment.

The example security group includes ports `22`, `80`, and `8080`. Restrict inbound access to trusted IP ranges when adapting the lab for real environments.

### 4. Publish the Module with GitHub

Create a public GitHub repository named:

`terraform-aws-docker-instance`

Copy the module files into the repository, then commit and push them:

```bash
git add .
git commit -m "Add reusable AWS Docker instance module"
git push
```

Create and push a semantic version tag:

```bash
git tag v0.0.1
git push --tags
```

Then sign in to the Terraform Registry with GitHub and publish the repository as a module.

The module's repository description and standard structure help the Registry display its documentation and usage information.

### 5. Consume the Published Module

Create a separate Terraform configuration that calls the published module:

```hcl
provider "aws" {
  region = "us-east-1"
}

module "docker_instance" {
  source   = "<github-username>/docker-instance/aws"
  key_name = "mykey"
}
```

Replace the example module source and key name with the actual values for your published module and AWS environment.

Initialize and deploy:

```bash
terraform init
terraform apply
```

After verifying the lab resources, clean them up:

```bash
terraform destroy
```

---

## Part 2: Terraform Workspaces

### 1. Understanding Workspaces

Terraform workspaces let you use the same configuration and working directory with separate state data.

Each initialized working directory has a `default` workspace. Additional workspaces can represent separate copies of the infrastructure, such as development and production.

**Important:** Workspaces separate state, but they do not automatically isolate AWS permissions, credentials, or infrastructure environments.

### 2. Create Workspace-Based Configuration

The lab uses `terraform.workspace` to customize the infrastructure according to the selected workspace.

The configuration demonstrates:

- Selecting an AMI through a map variable.
- Choosing an instance type with a conditional expression.
- Setting the number of EC2 instances based on the workspace.
- Naming resources with workspace-specific tags.
- Exposing AMI, instance type, and tags through outputs.

Example expressions:

```hcl
ami = lookup(var.myami, terraform.workspace)

instance_type = terraform.workspace == "dev" ? "t3a.medium" : "t2.micro"

count = terraform.workspace == "prod" ? 3 : 1
```

These examples illustrate workspace-dependent configuration. Ensure the AMI IDs are valid for the selected AWS region and that your account has permission and quota to create the requested resources.

### 3. Manage Workspaces

List available workspaces and inspect the current selection:

```bash
terraform workspace list
terraform workspace show
```

Create the development and production workspaces:

```bash
terraform workspace new dev
terraform workspace new prod
```

Switch between workspaces:

```bash
terraform workspace select dev
terraform workspace select prod
terraform workspace select default
```

### 4. Plan and Apply Infrastructure

Initialize Terraform and inspect the plan for the selected workspace:

```bash
terraform init
terraform plan
```

Select `dev` and review the planned instance type, AMI, instance count, and tags:

```bash
terraform workspace select dev
terraform plan
```

Repeat the process for `prod`:

```bash
terraform workspace select prod
terraform plan
```

Only apply the configuration after reviewing the planned changes and confirming that the selected workspace is correct.

### 5. Understand Workspace State

Terraform stores state separately for each workspace. In a local backend, non-default workspace states are commonly stored under:

```text
terraform.tfstate.d/
├── dev/
│   └── terraform.tfstate
└── prod/
    └── terraform.tfstate
```

The `default` workspace uses the main state location for the working directory.

### 6. Clean Up Workspaces

In a lab environment, destroy the resources managed by each workspace before deleting the workspace:

```bash
terraform workspace select dev
terraform destroy
```

Repeat for `prod` if resources were created there, and ensure no resources remain managed by those workspaces.

Switch to another workspace before deleting an empty workspace:

```bash
terraform workspace select default
terraform workspace delete prod
terraform workspace delete dev
```

**Warning:** Deleting a workspace is not a substitute for destroying its infrastructure. Verify the state and real AWS resources before cleanup.

---

## Key Takeaways

This session demonstrates two important Terraform practices:

1. **Reusable infrastructure:** Package an AWS EC2 and Docker configuration as a module, publish it through GitHub and the Terraform Registry, and reuse it from another configuration.
2. **Separate state management:** Use workspaces to manage multiple instances of a configuration with independent state data and workspace-dependent values.

## Important Safety Notes

- Do not commit AWS credentials, private keys, or sensitive `.tfvars` files.
- Review security group ingress rules before exposing services.
- Run `terraform plan` before applying changes.
- Verify the selected workspace before creating or destroying resources.
- Clean up lab resources to avoid unnecessary AWS charges.

## References

- [Terraform Registry — Publishing Modules](https://developer.hashicorp.com/terraform/registry/modules/publish)
- [Terraform CLI — Workspaces](https://developer.hashicorp.com/terraform/cli/workspaces)
- [Terraform Language — Modules](https://developer.hashicorp.com/terraform/language/modules)
