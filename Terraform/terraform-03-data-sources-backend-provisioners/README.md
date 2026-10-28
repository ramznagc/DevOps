# Hands-on Terraform 03: Data Sources, Remote Backend, and Provisioners

This hands-on session explores how to retrieve existing infrastructure information with Terraform data sources, store Terraform state remotely using an Amazon S3 backend, and execute actions with provisioners.

## Learning Outcomes

By the end of this session, you will be able to:

- Use Terraform data sources to retrieve existing AWS resources.
- Configure an Amazon S3 remote backend for Terraform state.
- Understand state storage and state locking.
- Use `local-exec`, `remote-exec`, and `file` provisioners.

## Session Outline

- [Part 1: Terraform Data Sources](#part-1-terraform-data-sources)
- [Part 2: Remote State and S3 Backend](#part-2-remote-state-and-s3-backend)
- [Part 3: Terraform Provisioners](#part-3-terraform-provisioners)
- [Cleanup](#cleanup)

---

## Part 1: Terraform Data Sources

### What Are Data Sources?

Terraform data sources allow you to retrieve information about existing resources or external data and use it elsewhere in your configuration.

In this exercise, we will look up an existing Amazon Machine Image (AMI) and use its ID when creating an EC2 instance.

### Step 1: Prepare an AMI

1. Open the AWS Management Console.
2. Select an existing EC2 instance.
3. Create an image from the instance and name it `my-ami`.
4. Wait until the image is available.

### Step 2: Create the Terraform Configuration

Create a working directory and a configuration file:

```bash
mkdir tf-data
cd tf-data
touch main.tf
```

Add the following configuration to `main.tf`:

```hcl
provider "aws" {
  region = "us-east-1"
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.0.0"
    }
  }
}

locals {
  mytag = "local-name"
}

data "aws_ami" "tf_ami" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

variable "ec2_type" {
  default = "t2.micro"
}

resource "aws_instance" "tf-ec2" {
  ami           = data.aws_ami.tf_ami.id
  instance_type = var.ec2_type
  key_name      = "mykey"

  tags = {
    Name = "${local.mytag}-this is from my-ami"
  }
}
```

**Before running the configuration:**

- Replace `mykey` with your EC2 key pair name.
- Ensure your AWS credentials are configured.
- Make sure the AMI lookup matches the image you created in the selected region.

### Step 3: Initialize, Plan, and Apply

```bash
terraform init
terraform plan
terraform apply
```

Review the execution plan and confirm the changes when prompted.

After the instance is created, check its AMI ID in the AWS console.

### Step 4: Clean Up

```bash
terraform destroy
```

Review the destruction plan before confirming.

**Key takeaway:** A data source retrieves information about an existing object. In this example, `data.aws_ami.tf_ami.id` supplies the AMI ID used by the EC2 resource.

---

## Part 2: Remote State and S3 Backend

### What Is a Backend?

A Terraform backend determines where Terraform stores its state and how state operations are handled. By default, Terraform uses the local backend and stores state in the working directory.

A remote backend allows state to be stored outside the local working directory. In this session, we will use Amazon S3.

### Step 1: Create an S3 Bucket for State

Create a separate directory for the backend configuration:

```bash
mkdir ~/s3-backend
cd ~/s3-backend
touch backend.tf
```

Add the following configuration to `backend.tf`:

```hcl
provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "tf-remote-state" {
  bucket        = "tf-remote-s3-bucket-changehere"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "versioning_backend_s3" {
  bucket = aws_s3_bucket.tf-remote-state.id

  versioning_configuration {
    status = "Enabled"
  }
}
```

Replace the example bucket name with a globally unique name.

Initialize and create the bucket:

```bash
terraform init
terraform plan
terraform apply
```

The bucket is configured with versioning enabled.

> **Important:** `force_destroy = true` is used here for a lab exercise. It can allow Terraform to delete a bucket even when it contains objects. Avoid this setting for a state bucket that contains important state history.

### Step 2: Configure the S3 Backend

Return to the `tf-data` directory:

```bash
cd ~/tf-data
```

Add a `terraform` block to `main.tf` with the S3 backend configuration. Replace the bucket value with the actual bucket name created in the previous step.

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.0.0"
    }
  }

  backend "s3" {
    bucket       = "tf-remote-s3-bucket-changehere"
    key          = "env/dev/tf-remote-backend.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
```

The backend block belongs inside the top-level `terraform` block. If your file already has a `terraform` block, update that block rather than creating a duplicate.

The settings mean:

- `bucket`: The S3 bucket used to store the state.
- `key`: The object path where the state is stored.
- `region`: The AWS region containing the bucket.
- `encrypt`: Enables server-side encryption for the stored state.
- `use_lockfile`: Enables S3 lock-file-based state locking.

### Step 3: Migrate Local State to S3

First, try running:

```bash
terraform apply
```

Then initialize the working directory again:

```bash
terraform init
```

Terraform may prompt you to migrate the existing local state to the configured S3 backend. Review the prompt and confirm the migration if it is appropriate.

Run the command again:

```bash
terraform plan
```

Open the S3 console and verify that the state object exists at the configured key.

### Step 4: Observe State Locking

Add a test S3 resource to the configuration:

```hcl
resource "aws_s3_bucket" "tf-test-1" {
  bucket = "replace-with-a-unique-test-bucket-name"
}
```

Apply the configuration:

```bash
terraform plan
terraform apply
```

For the locking exercise, use a separate test resource or a controlled change. Open two terminals in the same Terraform working directory and try to run state-changing operations close together.

With supported locking configured, Terraform can prevent conflicting operations while a state lock is held. The second operation may need to wait or fail with a lock-related message.

Do not force-unlock a state unless you have confirmed that no active operation holds the lock.

### Step 5: Clean Up Backend Resources

After confirming that you no longer need the lab resources, clean up the infrastructure carefully.

```bash
terraform destroy
```

Destroy the resources managed by the `tf-data` configuration first. Then, from the backend configuration directory, review the plan and destroy the backend resources only when you are certain the state is no longer needed:

```bash
cd ~/s3-backend
terraform plan -destroy
terraform destroy
```

**Important:** Destroying the S3 backend bucket can permanently remove remote state and its history. Do not delete a state bucket while other configurations still depend on it.

If you created an AMI and snapshot for this exercise, review and remove them separately from the AWS console when they are no longer required.

---

## Part 3: Terraform Provisioners

### What Are Provisioners?

Provisioners execute actions on the local machine or a remote resource as part of Terraform resource operations.

This session covers three provisioner types:

| Provisioner | Purpose |
|---|---|
| `local-exec` | Executes a command on the machine running Terraform. |
| `remote-exec` | Executes commands on a remote resource after connecting to it. |
| `file` | Copies a file or content from the machine running Terraform to a remote resource. |

Provisioners are useful for specific setup tasks, but they should not be the default solution for server configuration. Prefer provider-native features or dedicated configuration-management tools where appropriate.

### Step 1: Prepare the SSH Key

For the remote connection exercise, make the required private key available to the machine running Terraform and ensure the remote EC2 instance can be reached over SSH.

For example, a key file's permissions can be restricted with:

```bash
chmod 400 ~/mykey.pem
```

Use the correct key path, key pair name, and EC2 username for your environment.

### Step 2: Create the Configuration

Create the working directory:

```bash
mkdir ~/provisioners
cd ~/provisioners
touch main.tf
```

Add the following configuration to `main.tf`:

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

resource "aws_instance" "instance" {
  ami                    = "ami-09e6f87a47903347c"
  instance_type          = "t2.micro"
  key_name               = "mykey"
  vpc_security_group_ids = [aws_security_group.tf-sec-gr.id]

  tags = {
    Name = "terraform-instance-with-provisioner"
  }

  provisioner "local-exec" {
    command = "echo http://${self.public_ip} > public_ip.txt"
  }

  connection {
    type        = "ssh"
    host        = self.public_ip
    user        = "ec2-user"
    private_key = file(pathexpand("~/mykey.pem"))
  }

  provisioner "remote-exec" {
    inline = [
      "sudo dnf -y install httpd",
      "sudo systemctl enable httpd",
      "sudo systemctl start httpd"
    ]
  }

  provisioner "file" {
    content     = self.public_ip
    destination = "/home/ec2-user/my_public_ip.txt"
  }
}

resource "aws_security_group" "tf-sec-gr" {
  name = "tf-provisioner-sg"

  tags = {
    Name = "tf-provisioner-sg"
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

**Before running the configuration:**

- Verify that the AMI is available in `us-east-1` and is compatible with the commands in the remote script.
- Replace `mykey` with your EC2 key pair name.
- Make sure the private key path is correct.
- Ensure the EC2 instance has network access and that SSH is allowed from your IP address.

For a safer setup, restrict SSH ingress to your own IP instead of allowing `0.0.0.0/0`.

### Step 3: Initialize and Apply

```bash
terraform init
terraform plan
terraform apply
```

Review the plan before approving it.

After provisioning completes, inspect the results:

- `local-exec` writes the instance's public IP to `public_ip.txt` on the machine running Terraform.
- `remote-exec` installs and starts Apache HTTP Server on the EC2 instance.
- `file` writes the public IP to `/home/ec2-user/my_public_ip.txt` on the remote instance.

If the remote connection fails, check the SSH key, username, security group, route configuration, and instance readiness.

### Step 4: Clean Up

```bash
terraform destroy
```

Review the plan before confirming so that you understand which resources will be removed.

---

## Cleanup Checklist

Before finishing the session:

- [ ] Review and destroy the EC2 instances created for the exercises.
- [ ] Remove test S3 buckets and objects that are no longer required.
- [ ] Keep or remove the remote state bucket only after confirming that no configuration depends on it.
- [ ] Remove unused AMIs and snapshots created during the lab.
- [ ] Verify that no unintended AWS resources remain.

## Key Takeaways

- Data sources retrieve information that Terraform can use in other configuration blocks.
- Remote backends store Terraform state outside the local working directory.
- S3 versioning and state locking help protect state history and coordinate operations.
- Provisioners can run local commands, remote commands, and file transfers.
- Always review plans and clean up lab resources to avoid unnecessary AWS costs.
