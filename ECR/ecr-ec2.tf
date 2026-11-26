# ECR hands-on EC2 host
# Creates an Amazon Linux 2023 instance with Docker, AWS CLI and an EC2 role
# for managing Amazon ECR. Restrict SSH ingress before applying.

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region used for the EC2 host and ECR exercises."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix used for resource names and tags."
  type        = string
  default     = "ecr-hands-on"
}

variable "instance_type" {
  description = "EC2 instance type for the Docker host."
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "Name of an existing EC2 key pair in the selected region."
  type        = string
}

variable "ssh_allowed_cidr" {
  description = "CIDR allowed to connect over SSH. Set this to your public IP /32."
  type        = string
  default     = "0.0.0.0/0"
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_security_group" "docker_host" {
  name        = "${var.project_name}-sg"
  description = "HTTP demo access and restricted SSH access"

  ingress {
    description = "HTTP ToDo demo"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH - restrict to your public IP /32"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

resource "aws_iam_role" "ecr_host" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

# ECR authorization tokens require Resource="*". The remaining permissions
# are scoped to ECR actions needed by this educational create/push/pull lab.
resource "aws_iam_role_policy" "ecr_access" {
  name = "${var.project_name}-ecr-policy"
  role = aws_iam_role.ecr_host.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "GetECRAuthorizationToken"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Sid    = "ManageECRRepositoriesAndImages"
        Effect = "Allow"
        Action = [
          "ecr:CreateRepository",
          "ecr:DescribeRepositories",
          "ecr:DeleteRepository",
          "ecr:PutImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchDeleteImage",
          "ecr:DescribeImages",
          "ecr:ListImages",
          "ecr:PutLifecyclePolicy",
          "ecr:GetLifecyclePolicy",
          "ecr:DeleteLifecyclePolicy"
        ]
        Resource = "arn:aws:ecr:${var.aws_region}:*:repository/*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ecr_host" {
  name = "${var.project_name}-instance-profile"
  role = aws_iam_role.ecr_host.name
}

resource "aws_instance" "docker_host" {
  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.instance_type
  key_name                    = var.key_name
  vpc_security_group_ids      = [aws_security_group.docker_host.id]
  iam_instance_profile        = aws_iam_instance_profile.ecr_host.name
  associate_public_ip_address = true

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    encrypted   = true
    volume_type = "gp3"
    volume_size = 20
  }

  user_data = <<-EOF
    #!/bin/bash
    set -eux
    dnf update -y
    dnf install -y docker awscli
    systemctl enable --now docker
    usermod -aG docker ec2-user
    curl -fsSL https://github.com/docker/compose/releases/download/v2.26.0/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
  EOF

  tags = {
    Name = "${var.project_name}-docker-host"
  }
}

output "instance_public_ip" {
  description = "Public IPv4 address of the Docker host."
  value       = aws_instance.docker_host.public_ip
}

output "application_url" {
  description = "URL used to test the sample ToDo application."
  value       = "http://${aws_instance.docker_host.public_ip}"
}

output "ssh_command" {
  description = "SSH command for connecting to the Docker host."
  value       = "ssh -i <private-key.pem> ec2-user@${aws_instance.docker_host.public_ip}"
}
