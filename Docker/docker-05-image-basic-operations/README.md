
# Docker-05: Docker Image Basic Operations

## Overview

This project demonstrates basic Docker image operations and the process of building, running, tagging, and publishing Docker images.

A simple Python Flask application is packaged into two different Docker images to compare Ubuntu-based and Alpine-based container environments.

## Learning Objectives

- Understand Docker images and image layers
- List, pull, inspect, and remove Docker images
- Understand Docker Hub and image tags
- Build Docker images using Dockerfiles
- Run containers in detached mode
- Map host ports to container ports
- Tag and push images to Docker Hub
- Compare Ubuntu and Alpine-based image sizes

## Technologies

- Docker
- Docker Hub
- Python
- Flask
- Ubuntu
- Alpine Linux

## Project Structure

```text
Docker-05-Image-Basic-Operations/
├── Dockerfile
├── Dockerfile-alpine
├── welcome.py
└── README.md
```

## 1. Basic Docker Image Operations

Check Docker version:

```bash
docker --version
```

List available images:

```bash
docker image ls
```

Pull Ubuntu image:

```bash
docker image pull ubuntu
```

Pull a specific Ubuntu version:

```bash
docker image pull ubuntu:22.04
```

Inspect an image:

```bash
docker image inspect ubuntu
docker image inspect ubuntu:22.04
```

Search for images:

```bash
docker search ubuntu
```

Run Ubuntu interactively:

```bash
docker run -it ubuntu
```

Inside the container:

```bash
cat /etc/os-release
exit
```

## 2. Building the Ubuntu-Based Image

Build the image using the Ubuntu-based Dockerfile:

```bash
docker build -t YOUR_DOCKERHUB_USERNAME/flask-app:1.0 -f Dockerfile .
```

List the generated images:

```bash
docker image ls
```

Run the container:

```bash
docker run -d --name welcome-ubuntu -p 8080:80 YOUR_DOCKERHUB_USERNAME/flask-app:1.0
```

Open the application in your browser:

```text
http://localhost:8080
```

Check running containers:

```bash
docker ps
```

View container logs:

```bash
docker logs welcome-ubuntu
```

## 3. Building the Alpine-Based Image

Build the Alpine-based image:

```bash
docker build -t YOUR_DOCKERHUB_USERNAME/flask-app:2.0 -f Dockerfile-alpine .
```

List the images:

```bash
docker image ls
```

Compare image sizes:

```bash
docker image ls YOUR_DOCKERHUB_USERNAME/flask-app
```

Run the Alpine-based container:

```bash
docker run -d --name welcome-alpine -p 8081:80 YOUR_DOCKERHUB_USERNAME/flask-app:2.0
```

Open the application:

```text
http://localhost:8081
```

Check running containers:

```bash
docker ps
```

## 4. Comparing Docker Images

The project uses two different base images:

| Image | Base Image | Tag |
|---|---|---|
| Ubuntu version | ubuntu:24.04 | 1.0 |
| Alpine version | python:3.12-alpine | 2.0 |

Compare their actual sizes with:

```bash
docker image ls YOUR_DOCKERHUB_USERNAME/flask-app
```

The Alpine-based image is expected to be smaller because Alpine is a minimal Linux distribution.

Actual image sizes depend on the image versions and installed dependencies.

## 5. Publishing Images to Docker Hub

Log in to Docker Hub:

```bash
docker login
```

Push the Ubuntu-based image:

```bash
docker push YOUR_DOCKERHUB_USERNAME/flask-app:1.0
```

Push the Alpine-based image:

```bash
docker push YOUR_DOCKERHUB_USERNAME/flask-app:2.0
```

Replace `YOUR_DOCKERHUB_USERNAME` with your own Docker Hub username before running these commands.

## 6. Managing Image Tags

Tag the Alpine image as latest:

```bash
docker image tag YOUR_DOCKERHUB_USERNAME/flask-app:2.0 YOUR_DOCKERHUB_USERNAME/flask-app:latest
```

Push the latest tag:

```bash
docker push YOUR_DOCKERHUB_USERNAME/flask-app:latest
```

## 7. Cleaning Up

Stop the running containers:

```bash
docker stop welcome-ubuntu welcome-alpine
```

Remove the containers:

```bash
docker rm welcome-ubuntu welcome-alpine
```

List local images:

```bash
docker image ls
```

Remove the project images if they are no longer needed:

```bash
docker image rm YOUR_DOCKERHUB_USERNAME/flask-app:1.0
docker image rm YOUR_DOCKERHUB_USERNAME/flask-app:2.0
docker image rm YOUR_DOCKERHUB_USERNAME/flask-app:latest
```

## Key Takeaways

- Docker images package applications and their dependencies.
- Dockerfiles define how images are built.
- Image tags help identify different versions.
- Docker Hub provides a registry for sharing images.
- Alpine-based images can reduce image size.
- Containers provide isolated environments for applications.

## Project Status

Completed as a hands-on Docker learning project and included in my DevOps portfolio.
