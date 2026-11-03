
# Docker-06: Docker Compose Operations

## Overview

This hands-on project demonstrates how to use Docker Compose to build and run a multi-container application.

A Python Flask web application communicates with a Redis service to maintain a page visit counter.

Docker Compose manages both services using a single configuration file.

## Learning Objectives

- Understand Docker Compose
- Understand Compose YAML configuration
- Define and manage multiple services
- Build Docker images using Docker Compose
- Connect Flask and Redis containers
- Manage application containers
- Understand container dependencies
- Rebuild images after application changes

## Technologies

- Docker
- Docker Compose
- Python
- Flask
- Redis
- Alpine Linux
- YAML

## Project Structure

```text
docker-06-compose-operations/
├── app.py
├── Dockerfile
├── compose.yml
├── requirements.txt
└── README.md
```

## 1. Check Docker and Docker Compose

Check Docker version:

```bash
docker --version
```

Check Docker Compose version:

```bash
docker compose version
```

Docker Desktop for Windows includes Docker Compose.

## 2. Build and Start the Application

Build the Flask application image and start both services:

```bash
docker compose up --build
```

Docker Compose performs the following operations:

1. Builds the Flask application image.
2. Pulls the Redis image if it is not available locally.
3. Creates the required network.
4. Starts the Redis and Flask containers.

Open the application in your browser:

```text
http://localhost:5000
```

Refresh the page several times.

The visit counter should increase with each request.

## 3. Run Containers in Detached Mode

Stop the foreground process with `Ctrl+C`.

Start the services in detached mode:

```bash
docker compose up -d
```

Check running containers:

```bash
docker compose ps
```

View service logs:

```bash
docker compose logs
```

View logs for the web service:

```bash
docker compose logs web
```

## 4. Inspect Docker Compose Configuration

Display the resolved Compose configuration:

```bash
docker compose config
```

List images used by the Compose project:

```bash
docker compose images
```

Check running containers:

```bash
docker ps
```

## 5. Update the Flask Application

Open `app.py` and change the response inside the `hello()` function:

```python
return f"Hello World! This is the updated application. Visit count: {count}\n"
```

Save the file.

Run:

```bash
docker compose up -d
```

Because the application code is copied into the image during the build process, the existing image must be rebuilt for the change to appear.

Rebuild and restart the services:

```bash
docker compose up -d --build
```

Refresh the browser:

```text
http://localhost:5000
```

The updated message should now appear.

## 6. Stop and Remove Containers

Stop and remove the Compose services:

```bash
docker compose down
```

Check whether containers have been removed:

```bash
docker ps -a
```

List available images:

```bash
docker image ls
```

By default, `docker compose down` removes the containers and the Compose network, but keeps the images and named volumes.

## 7. Useful Docker Compose Commands

| Command | Description |
|---|---|
| `docker compose up` | Build and start services |
| `docker compose up -d` | Start services in detached mode |
| `docker compose up --build` | Rebuild images and start services |
| `docker compose ps` | List Compose containers |
| `docker compose logs` | Display service logs |
| `docker compose images` | List project images |
| `docker compose config` | Display resolved configuration |
| `docker compose down` | Stop and remove services |

## Key Takeaways

- Docker Compose simplifies multi-container application management.
- Compose files define services and their configurations.
- Flask can communicate with Redis using the service name as its hostname.
- Docker Compose creates a network for service communication.
- Image rebuilding is required when application code is copied into an image during the build.
- Multiple containers can be managed with a single command.

## Project Status

Completed as a hands-on Docker Compose learning exercise and included in my DevOps portfolio.
This project demonstrates multi-container application orchestration using Docker Compose, Flask, and Redis.
