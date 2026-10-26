# Hands-on Terraform 04: Modules and Import

This hands-on session introduces Terraform modules and explains how to import existing AWS infrastructure into Terraform state.

## Learning Outcomes

By the end of this session, you will be able to:

- Understand Terraform modules and their directory structure.
- Create reusable Terraform configurations.
- Use input variables and outputs in modules.
- Call a local module from a root configuration.
- Import existing AWS resources into Terraform state.
- Understand the differences between CLI import, import blocks, and generated configuration.

## Session Outline

- [Part 1: Terraform Modules](#part-1-terraform-modules)
- [Part 2: Import Existing Resources](#part-2-import-existing-resources)
- [Part 3: Import Methods](#part-3-import-methods)
- [Cleanup](#cleanup)

---

## Part 1: Terraform Modules

### What Is a Terraform Module?

A Terraform module is a collection of Terraform configuration files in a directory. The root configuration is itself a module, and it can call other modules to reuse infrastructure definitions.

Modules help organize configurations, reduce duplication, and make infrastructure patterns easier to maintain.

### Step 1: Create a Module Directory

Create a directory for the module and its files:

```bash
mkdir -p ~/terraform-modules/ec2
cd ~/terraform-modules/ec2

touch main.tf variables.tf outputs.tf versions.tf
```

The directory structure will look like this:

```text
ec2/
├── main.tf
├── variables.tf
├── outputs.tf
└── versions.tf
```

### Step 2: Define the Required Provider

Add the following to `versions.tf`:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

This declares the AWS provider requirement for the module.

### Step 3: Define Input Variables

Add the following to `variables.tf`:

```hcl
variable "instance_type" {
  type    = string
  default = "t2.micro"
}

variable "key_name" {
  type = string
}

variable "num_of_instance" {
  type    = number
  default = 1
}

variable "tag" {
  type    = string
  default = "Docker-Instance"
}

variable "server-name" {
  type    = string
  default = "docker-instance"
}

variable "docker-instance-ports" {
  type        = list(number)
  description = "Inbound ports for the Docker instance security group"
  default     = [22, 80, 8080]
}
```

Input variables let callers customize the module without editing its internal configuration.

### Step 4: Define the AWS Resources

Add the following to `main.tf`:

```hcl
data "aws_ami" "amazon-linux-2023" {
  owners      = ["amazon"]
  most_recent = true

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "owner-alias"
    values = ["amazon"]
  }

  filter {
    name   = "name"
    values = ["al2023-ami-2023*"]
  }
}

resource "aws_instance" "tfmyec2" {
  ami                    = data.aws_ami.amazon-linux-2023.id
  instance_type          = var.instance_type
  count                  = var.num_of_instance
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.tf-sec-gr.id]

  user_data = templatefile(
    "${path.module}/userdata.sh",
    { myserver = var.server-name }
  )

  tags = {
    Name = var.tag
  }
}

resource "aws_security_group" "tf-sec-gr" {
  name = "${var.tag}-terraform-sec-grp"

  tags = {
    Name = var.tag
  }

  dynamic "ingress" {
    for_each = var.docker-instance-ports
    iterator = port

    content {
      from_port   = port.value
      to_port     = port.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

The configuration uses:

- An AMI data source to find an Amazon Linux 2023 image.
- Variables to control the instance type, key pair, count, tags, and inbound ports.
- A dynamic block to create ingress rules from a list of ports.
- A `templatefile` function to pass a server name into the startup script.

**Security note:** The example allows inbound access from `0.0.0.0/0`. For a safer configuration, restrict SSH and other inbound rules to the specific IP addresses or networks that require access.

### Step 5: Add the User Data Script

Create `userdata.sh` in the module directory:

```bash
#!/bin/bash

hostnamectl set-hostname ${myserver}

dnf update -y
dnf install -y docker

systemctl start docker
systemctl enable docker

usermod -a -G docker ec2-user

curl -SL \
  https://github.com/docker/compose/releases/download/v2.40.0/docker-compose-linux-x86_64 \
  -o /usr/local/bin/docker-compose

chmod +x /usr/local/bin/docker-compose
```

The script sets the hostname, installs Docker, enables the Docker service, and installs Docker Compose.

The `myserver` value is provided by the `templatefile` call in `main.tf`.

### Step 6: Define Outputs

Add the following to `outputs.tf`:

```hcl
output "instance_public_ip" {
  value = aws_instance.tfmyec2[*].public_ip
}

output "sec_gr_id" {
  value = aws_security_group.tf-sec-gr.id
}

output "instance_id" {
  value = aws_instance.tfmyec2[*].id
}
```

Outputs expose useful values from the module, such as instance IDs, public IP addresses, and the security group ID.

### Step 7: Create a Root Configuration That Calls the Module

Create a separate directory for the root configuration:

```bash
mkdir -p ~/terraform-modules/demo
cd ~/terraform-modules/demo

touch main.tf
```

Add the following to `main.tf`:

```hcl
provider "aws" {
  region = "us-east-1"
}

module "docker_instance" {
  source = "../ec2"

  key_name = "mykey"
}
```

Replace `mykey` with your actual EC2 key pair name.

Initialize and apply:

```bash
terraform init
terraform plan
terraform apply
```

Terraform loads the local module from `../ec2`.

After checking the created resources, remove the lab infrastructure when it is no longer needed:

```bash
terraform destroy
```

### Key Module Concepts

| Concept | Purpose |
|---|---|
| `main.tf` | Defines resources and data sources. |
| `variables.tf` | Declares configurable input values. |
| `outputs.tf` | Exposes selected values from the module. |
| `versions.tf` | Declares Terraform and provider requirements. |
| `source` | Specifies where Terraform loads a module from. |

---

## Part 2: Import Existing Resources

### What Is Terraform Import?

Terraform import connects an existing infrastructure resource to a Terraform resource address in state.

Importing does not mean Terraform created the resource. The resource must also have a corresponding Terraform configuration that describes how it should be managed.

After importing, review the plan carefully to identify differences between the existing resource and the configuration.

### Step 1: Create an Existing EC2 Instance

In the AWS console, create an EC2 instance for this exercise.

For example, the training exercise uses an Ubuntu 24.04 instance with the tag:

```text
Name = ubuntu-24.04
```

Record the instance ID from the AWS console. Use your own ID rather than a sample ID.

### Step 2: Create the Import Configuration

Create a working directory:

```bash
mkdir ~/terraform-import
cd ~/terraform-import

touch main.tf
```

Add a resource block that corresponds to the existing EC2 instance:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "tf-instances" {
  ami           = "REPLACE_WITH_EXISTING_AMI_ID"
  instance_type = "t3.micro"
  key_name      = "REPLACE_WITH_EXISTING_KEY_PAIR"

  tags = {
    Name = "ubuntu-24.04"
  }
}
```

Replace the AMI ID and key pair name with values that match your actual instance. Adjust the configuration to reflect the real resource.

### Step 3: Initialize Terraform and Import the Instance

Initialize the directory:

```bash
terraform init
```

Import the existing instance using its real ID:

```bash
terraform import \
  aws_instance.tf-instances \
  i-REPLACE_WITH_YOUR_INSTANCE_ID
```

The general syntax is:

```bash
terraform import RESOURCE_ADDRESS RESOURCE_ID
```

For this example:

- Resource address: `aws_instance.tf-instances`
- Resource ID: The actual EC2 instance ID from AWS

### Step 4: Verify the Imported Resource

List the resources tracked in state:

```bash
terraform state list
```

Review the state and the planned changes:

```bash
terraform plan
```

The resource should now be associated with the Terraform state. Carefully review the plan and update the configuration to match the existing infrastructure before applying changes.

**Important:** Import does not automatically guarantee that your configuration matches the resource. An incorrect configuration can lead to unexpected changes in a later plan or apply.

---

## Part 3: Import Methods

Terraform supports more than one workflow for importing resources. The exercises below introduce three approaches.

### Method 1: Classic CLI Import

The CLI import command associates an existing resource with a Terraform resource address.

```bash
terraform init
terraform import aws_instance.example RESOURCE_ID
terraform plan
```

Use this approach when you want to run the import operation directly from the terminal.

Remember:

- A matching resource block must exist in the configuration.
- Import updates Terraform state; it does not create the existing resource.
- You must review the resulting plan and ensure the configuration matches the real infrastructure.

### Method 2: Declarative Import Block

Terraform supports import blocks in configuration files. This approach is available in Terraform 1.5 and later.

For an existing EC2 instance, use an import block like this:

```hcl
import {
  to = aws_instance.example
  id = "REPLACE_WITH_EXISTING_INSTANCE_ID"
}

resource "aws_instance" "example" {
  ami           = "REPLACE_WITH_EXISTING_AMI_ID"
  instance_type = "t3.micro"

  # Add the configuration that matches the existing instance.
}
```

Replace the placeholder values with real values and complete the resource configuration.

Then run:

```bash
terraform init
terraform plan
terraform apply
```

The plan shows the proposed import and any other planned changes. Review it before applying.

Verify the state:

```bash
terraform state list
```

An import block can remain in the configuration as a record of the import operation or be removed after the import has been completed.

### Method 3: Generate Configuration During Import

Terraform also provides the `-generate-config-out` option for generating configuration for resources being imported. The training material describes this workflow as experimental, so check the documentation for your Terraform version before relying on it.

For this exercise, create a security group in AWS named `terraform-sg` and record its ID.

Add an import block to your configuration:

```hcl
import {
  to = aws_security_group.mysg
  id = "REPLACE_WITH_EXISTING_SECURITY_GROUP_ID"
}
```

Generate a configuration file:

```bash
terraform plan -generate-config-out=terraform-sg.tf
```

Inspect the generated `terraform-sg.tf` file and review the resulting configuration carefully.

Then run:

```bash
terraform plan
terraform apply
terraform state list
```

Generated configuration should be reviewed and adjusted before it is used as a long-term configuration.

---

## Important: Removing a Resource from Terraform State

There are situations where you want Terraform to stop managing a resource without deleting that resource from AWS.

Use `terraform state rm` for this purpose:

```bash
terraform state rm aws_security_group.mysg
```

Use the actual resource address from your configuration and state.

This operation:

- Removes the resource association from Terraform state.
- Does not send a delete request to AWS.
- Leaves the actual AWS resource in place.

**Do not delete the entire `terraform.tfstate` file as a way to remove one resource.** Doing so can disrupt Terraform's tracking of other resources.

Also note that removing a resource from state does not destroy it. If you later want Terraform to manage it again, you may need to import it.

---

## Cleanup

Before cleaning up, identify which resources were created for the lab and which existed before the exercise.

Inspect the plan before destroying resources:

```bash
terraform plan -destroy
```

Only destroy lab resources when you are certain they can be removed.

> **Warning:** Running `terraform destroy` on an imported resource can delete the actual AWS resource if Terraform manages it and the configuration requests its destruction. Importing does not protect a resource from deletion.

If the exercise used an existing EC2 instance or security group that must remain in AWS, do not destroy it. If you only want Terraform to stop managing it, consider `terraform state rm` after reviewing the consequences.

## Key Takeaways

- Modules organize reusable Terraform configurations.
- Input variables make modules configurable, and outputs expose useful values.
- A root module can call a local module or a module published in a registry.
- Import connects existing infrastructure to Terraform state.
- CLI import, import blocks, and generated configuration support different import workflows.
- Always compare the configuration with the real resource and review `terraform plan` before applying changes.
