# Docker-02: Docker Container Basic Operations 🐳

## 📌 Overview

This hands-on lab introduces the basic operations used to manage Docker containers, including running, listing, starting, stopping, inspecting, and removing containers.

## 🎯 Learning Objectives

By completing this lab, you will learn how to:

- Explore Docker command help.
- Run an interactive Ubuntu container.
- List running and stopped containers.
- Understand container IDs, names, and statuses.
- Start and stop containers.
- Execute commands inside a running container.
- Inspect container configuration.
- Remove containers safely.

## 🧰 Prerequisites

- Docker installed and running on a Linux machine.
- Terminal access with permission to run Docker commands.
- Basic Linux command-line knowledge.

> This lab can be completed on an existing Docker host. No new AWS resources are required.

## 1. Explore Docker Help

Display the available Docker commands:

```bash
docker help
```

Get help for a specific command:

```bash
docker run --help
```

## 2. Check the Docker Service

On Linux systems using `systemd`, check the service status:

```bash
sudo systemctl status docker
```

## 3. Run an Interactive Ubuntu Container

Start an Ubuntu container with an interactive Bash shell:

```bash
docker run -it ubuntu bash
```

Inside the container, check the operating system:

```bash
cat /etc/os-release
```

Check the current shell:

```bash
echo "$0"
```

Update the package lists:

```bash
apt-get update
```

Create a file in the home directory:

```bash
cd ~
touch myfile.txt
ls -l myfile.txt
```

Install Vim and open the file:

```bash
apt-get install -y vim
vim myfile.txt
```

Inside Vim, press `i` to enter insert mode and type:

```text
Hello from the Ubuntu Container
```

Press `Esc`, type `:wq`, and press Enter to save and exit.

Leave the container:

```bash
exit
```

## 4. List Containers

List all containers, including stopped containers:

```bash
docker ps -a
```

Equivalent command:

```bash
docker container ls -a
```

List only running containers:

```bash
docker ps
```

Important fields:

- **CONTAINER ID:** Unique identifier for the container.
- **IMAGE:** Image used to create the container.
- **COMMAND:** Command executed when the container starts.
- **STATUS:** Current container state.
- **NAMES:** Container name.

## 5. Create a Named Container

Create a second Ubuntu container named `mycont`:

```bash
docker run -it --name mycont ubuntu bash
```

Exit the container shell:

```bash
exit
```

List all containers again:

```bash
docker ps -a
```

The container remains listed even when it is stopped.

## 6. Start and Stop Containers

Start a container using its actual ID:

```bash
docker start CONTAINER_ID
```

Stop a running container:

```bash
docker stop CONTAINER_ID
```

Start the named container:

```bash
docker start mycont
```

Check running containers:

```bash
docker ps
```

Replace `CONTAINER_ID` with the ID displayed in your own terminal. Container IDs vary between environments.

## 7. Execute Commands Inside a Running Container

Open an interactive shell in `mycont`:

```bash
docker exec -it mycont bash
```

Create a test file:

```bash
touch ~/container-test.txt
ls -l ~/container-test.txt
```

Exit the shell:

```bash
exit
```

**Note:** Exiting a shell opened with `docker exec` normally exits only that shell; it does not stop the container's main process.

## 8. Inspect a Container

Display detailed container information:

```bash
docker inspect mycont
```

For easier reading, use `less`:

```bash
docker inspect mycont | less
```

Press `q` to exit `less`.

## 9. Remove Containers

Check the container list:

```bash
docker ps -a
```

Stop `mycont` if it is running:

```bash
docker stop mycont
```

Remove it:

```bash
docker rm mycont
```

Remove another container by its actual ID:

```bash
docker rm CONTAINER_ID
```

Verify the result:

```bash
docker ps -a
```

> **Warning:** Removing a container deletes its writable layer. Data stored only in that layer may be lost. Use Docker volumes for data that needs to persist independently of a container.

## 🔐 Best Practices

- Use meaningful container names.
- Check container status before stopping or removing it.
- Use real IDs from your own environment rather than example IDs.
- Remember that stopped containers still exist until removed.
- Use volumes for persistent data.
- Remove only containers you created for this lab.

## 🧹 Cleanup

List containers before cleaning up:

```bash
docker ps -a
```

Stop and remove only the containers created for this exercise. The Ubuntu image may be kept for future labs.

## ✅ Summary

In this lab, we explored Docker help, launched interactive Ubuntu containers, listed and inspected containers, managed their lifecycle, executed commands inside running containers, and removed containers.

---

*Part of my DevOps Learning Portfolio.*
