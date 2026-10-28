
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Find the latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-kernel-6.1-x86_64"]
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

# Allow SSH only from the configured trusted IP range
resource "aws_security_group" "docker_sg" {
  name        = "docker-ec2-security-group"
  description = "Allow SSH from a trusted IP address"

  ingress {
    description = "SSH from trusted IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "docker-ec2-security-group"
  }
}

# Create an EC2 instance and install Docker at startup
resource "aws_instance" "docker_machine" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.docker_sg.id]

  user_data = <<-EOF
    #!/bin/bash
    set -e
    dnf update -y
    dnf install -y docker
    systemctl enable --now docker
    usermod -aG docker ec2-user
  EOF

  tags = {
    Name = "Docker-Learning-EC2"
  }
}

variable "aws_region" {
  description = "AWS region in which to create the EC2 instance"
  type        = string
  default     = "eu-central-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_pair_name" {
  description = "Name of an existing EC2 key pair in the selected region"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "Trusted public IP address range allowed to SSH, e.g. 203.0.113.10/32"
  type        = string
}

output "instance_public_dns" {
  description = "Public DNS name of the Docker EC2 instance"
  value       = aws_instance.docker_machine.public_dns
}

output "instance_public_ip" {
  description = "Public IP address of the Docker EC2 instance"
  value       = aws_instance.docker_machine.public_ip
}
