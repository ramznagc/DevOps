# Docker

## Overview

Docker is a platform that allows developers to build, package, and run applications in containers. Containers provide a consistent environment for applications and help simplify deployment across different systems.

This section contains hands-on Docker lessons covering installation, container management, data persistence, and networking.

## Learning Path

The lessons are organized to progress from Docker fundamentals to more advanced concepts.

### Lesson 01 – Docker Installation on EC2

Learn how to install Docker on an Amazon EC2 Linux instance and prepare the environment for working with containers.

Topics:
- Docker installation
- Docker service management
- Basic Docker configuration
- Running Docker on an EC2 instance

[Open Lesson 01 – Docker Installation on EC2](docker-01-installation-ec2/README.md)

### Lesson 02 – Docker Container Basic Operations

Learn the fundamental commands for managing Docker containers and images.

Topics:
- Running containers
- Listing containers
- Starting and stopping containers
- Removing containers
- Working with Docker images
- Executing commands inside containers

[Open Lesson 02 – Docker Container Basic Operations](docker-02-container-basic-operations/README.md)

### Lesson 03 – Handling Docker Volumes

Learn how Docker volumes provide persistent storage and allow data to be shared between containers.

Topics:
- Data persistence
- Creating and inspecting named volumes
- Sharing volumes between containers
- Read-only volume mounts
- Volume initialization behavior
- Bind mounts
- Anonymous volumes

[Open Lesson 03 – Handling Docker Volumes](docker-03-handling-volumes/README.md)

### Lesson 04 – Docker Networking

Learn how Docker containers communicate with each other and external networks.

Topics:
- Listing and inspecting Docker networks
- Default bridge network
- User-defined bridge networks
- Container-to-container communication
- Container name resolution
- Connecting containers to multiple networks
- Port publishing
- Host networking
- None networking

[Open Lesson 04 – Docker Networking](docker-04-networking/README.md)

---

## Repository Structure

```text
Docker/
│
├── README.md
│
├── docker-01-installation-ec2/
│   ├── README.md
│   ├── ec2-docker.tf
│   └── docker-installation-template.yml
│
├── docker-02-container-basic-operations/
│   └── README.md
│
├── docker-03-handling-volumes/
│   ├── README.md
│   └── images/
│       ├── same-vol-with-diff-con.png
│       ├── situation-1-and-2.png
│       ├── situation-3.png
│       └── situation-4.png
│
└── docker-04-networking/
    └── README.md
```

## Goals

By completing these lessons, you will gain practical experience with:

- Installing and configuring Docker
- Managing Docker images and containers
- Persisting application data with Docker volumes
- Sharing data between containers
- Configuring Docker networks
- Managing communication between containerized applications

