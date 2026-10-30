# Hands-on Docker-04: Docker Networking

## Overview

Docker networking allows containers to communicate with each other, connect to external networks, and expose application services to the host machine.

In this lesson, we explore Docker network types, the default bridge network, user-defined bridge networks, container-to-container communication, port publishing, host networking, and isolated containers.

## Learning Outcomes

By the end of this lesson, you will be able to:

- List available Docker networks.
- Create and inspect Docker networks.
- Connect containers to networks.
- Explain the default bridge network.
- Configure a user-defined bridge network.
- Test communication between containers.
- Understand container DNS resolution.
- Publish container ports to the host.
- Explain bridge, host, and none network modes.
- Remove Docker networks.

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Default Bridge Network](#2-default-bridge-network)
3. [User-Defined Bridge Network](#3-user-defined-bridge-network)
4. [Container Networking and Port Publishing](#4-container-networking-and-port-publishing)
5. [Host Network](#5-host-network)
6. [None Network](#6-none-network)
7. [Useful Docker Network Commands](#7-useful-docker-network-commands)
8. [Cleanup](#8-cleanup)
9. [Conclusion](#9-conclusion)

---

## 1. Prerequisites

Make sure Docker is installed and running.

Check the Docker version:

```bash
docker --version
```

Check whether the Docker service is running (on Linux systems using systemd):

```bash
sudo systemctl status docker
```

Check available Docker networks:

```bash
docker network ls
```

Docker commonly provides three built-in network types:

| Network | Description |
|---|---|
| `bridge` | Default network driver for standalone containers |
| `host` | Shares the host network namespace |
| `none` | Disables external container networking |

---

## 2. Default Bridge Network

The default bridge network is automatically available when Docker is installed. When a container is started without specifying a network, Docker normally connects it to this network.

### 2.1. List Docker Networks

```bash
docker network ls
```

You should see networks such as:

- `bridge`
- `host`
- `none`

### 2.2. Run Two Alpine Containers

Start two containers in detached mode:

```bash
docker container run -dit --name mycont1 alpine ash
docker container run -dit --name mycont2 alpine ash
```

**What does detached mode mean?**

The `-d` flag runs a container in the background. The `-i` flag keeps standard input open, while `-t` allocates a pseudo-terminal.

Check the running containers:

```bash
docker ps
```

### 2.3. Inspect the Default Bridge Network

```bash
docker network inspect bridge
```

The output includes information such as:

- Network ID
- Network driver
- Subnet and gateway
- Connected containers and their IP addresses

The default bridge network provides connectivity between containers connected to it.

### 2.4. Find a Container's IP Address

Inspect `mycont2`:

```bash
docker container inspect mycont2
```

To display only its IP address:

```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mycont2
```

### 2.5. Connect to a Container

Open a shell inside `mycont1`:

```bash
docker exec -it mycont1 sh
```

Check its network interfaces:

```sh
ip addr
```

If the `ip` command is unavailable, you can install the required networking tools in the container or inspect its network configuration from the Docker host.

### 2.6. Test Internet Connectivity

Inside `mycont1`, try:

```sh
ping -c 4 google.com
```

The Alpine image may not include `ping` by default. If necessary, install it:

```sh
apk add --no-cache iputils
```

Then try the ping command again.

### 2.7. Test Communication Between Containers

First, find the IP address of `mycont2`:

```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mycont2
```

Use the returned IP address inside `mycont1`:

```sh
ping -c 4 CONTAINER_IP
```

Replace `CONTAINER_IP` with the actual address returned by Docker.

On the default bridge network, containers can generally communicate using their IP addresses. Automatic container-name resolution is not provided in the same way as it is on user-defined networks.

Try the container name:

```sh
ping -c 4 mycont2
```

Name resolution may fail because the default bridge does not provide the same built-in DNS discovery available on user-defined bridge networks.

Exit the container:

```sh
exit
```

### 2.8. Stop and Remove Containers

```bash
docker container stop mycont1 mycont2
docker container rm mycont1 mycont2
```

---

## 3. User-Defined Bridge Network

A user-defined bridge network provides more flexibility than the default bridge network.

One important advantage is automatic DNS resolution between containers. Containers on the same user-defined network can communicate with each other using their names.

### 3.1. Create a User-Defined Network

Create a bridge network named `mynet`:

```bash
docker network create --driver bridge mynet
```

List the available networks:

```bash
docker network ls
```

Inspect the new network:

```bash
docker network inspect mynet
```

At this point, no containers should be connected to `mynet`.

### 3.2. Run Containers on Different Networks

Start two containers on `mynet`:

```bash
docker container run -dit --network mynet --name mycont1 alpine ash
docker container run -dit --network mynet --name mycont2 alpine ash
```

Start a third container on the default bridge:

```bash
docker container run -dit --name mycont3 alpine ash
```

Start a fourth container on the default bridge:

```bash
docker container run -dit --name mycont4 alpine ash
```

Connect the fourth container to `mynet` as well:

```bash
docker network connect mynet mycont4
```

The network layout is now:

| Container | Default bridge | `mynet` |
|---|---:|---:|
| `mycont1` | No | Yes |
| `mycont2` | No | Yes |
| `mycont3` | Yes | No |
| `mycont4` | Yes | Yes |

Check running containers:

```bash
docker container ls
```

### 3.3. Inspect the User-Defined Network

```bash
docker network inspect mynet
```

You should find:

- `mycont1`
- `mycont2`
- `mycont4`

Inspect the default bridge network:

```bash
docker network inspect bridge
```

You should find:

- `mycont3`
- `mycont4`

This demonstrates that a container can be connected to more than one Docker network.

### 3.4. Test Container Name Resolution

Open a shell inside `mycont1`:

```bash
docker exec -it mycont1 ash
```

Install ping if it is not available:

```sh
apk add --no-cache iputils
```

Ping the other containers connected to `mynet`:

```sh
ping -c 4 mycont2
ping -c 4 mycont4
```

Both should be reachable by their container names because they share the same user-defined network.

Now try to reach `mycont3` by name:

```sh
ping -c 4 mycont3
```

Name resolution should fail because `mycont3` is not connected to `mynet`.

Exit the container:

```sh
exit
```

### 3.5. Test Communication from a Container Connected to Two Networks

Open a shell inside `mycont4`:

```bash
docker exec -it mycont4 ash
```

Ping the containers on `mynet` by name:

```sh
ping -c 4 mycont1
ping -c 4 mycont2
```

Now find the IP address of `mycont3` from the Docker host:

```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mycont3
```

Use the returned IP address from inside `mycont4`:

```sh
ping -c 4 CONTAINER_IP
```

Replace `CONTAINER_IP` with the actual IP address of `mycont3`.

This works because `mycont4` is connected to both the default bridge and `mynet`. It can communicate with containers on either network, subject to network configuration and connectivity.

Exit the container:

```sh
exit
```

---

## 4. Container Networking and Port Publishing

Containers can run services that need to be accessed from outside the container.

Docker port publishing maps a port on the host machine to a port inside the container.

### 4.1. Run an Nginx Container with Port Publishing

Run an Nginx container:

```bash
docker container run --rm -d -p 8080:80 --name ng nginx
```

Explanation:

| Option | Description |
|---|---|
| `--rm` | Automatically removes the container when it stops |
| `-d` | Runs the container in the background |
| `-p 8080:80` | Maps host port `8080` to container port `80` |
| `--name ng` | Assigns the name `ng` to the container |

Open the following address in your browser:

```text
http://localhost:8080
```

You should see the Nginx welcome page.

Check the container:

```bash
docker ps
```

### 4.2. Stop the Nginx Container

```bash
docker container stop ng
```

Because the container was started with `--rm`, Docker automatically removes it after it stops.

Check the container list:

```bash
docker ps -a
```

The stopped Nginx container should no longer appear.

---

## 5. Host Network

The host network driver allows a container to share the host's network namespace.

Unlike bridge networking, host networking does not use the usual separate container IP address and port mapping model.

> **Note:** Host networking behaves differently depending on the operating system and Docker environment. The example below is intended for Linux Docker hosts. Docker Desktop may have different limitations.

### 5.1. Run Nginx with Host Networking

```bash
docker container run --rm -d --network host --name my_nginx nginx
```

With host networking, Nginx listens directly on the host's network interfaces.

The standard Nginx HTTP port is `80`, so open:

```text
http://localhost
```

No `-p` option is required for this host-network example.

### 5.2. Inspect the Container

```bash
docker inspect my_nginx
```

You can also open a shell inside the container:

```bash
docker exec -it my_nginx sh
```

On Debian-based Nginx images, you can install network tools if needed:

```sh
apt-get update
apt-get install -y net-tools
ifconfig
```

Exit the container:

```sh
exit
```

Stop the container:

```bash
docker container stop my_nginx
```

The container is automatically removed because it was started with `--rm`.

---

## 6. None Network

The `none` network driver disables external networking for a container.

A container using this network mode has only its loopback interface and cannot communicate with other containers or the internet through a Docker network.

### 6.1. Run an Alpine Container with No Network

```bash
docker container run --rm -it --network none --name nullcontainer alpine
```

Inspect its network interfaces:

```sh
ip addr
```

You should see the loopback interface (`lo`).

### 6.2. Test Connectivity

Try to ping an external domain:

```sh
ping -c 4 google.com
```

The command should fail because the container has no external network connection.

Exit the container:

```sh
exit
```

Because the container was started with `--rm`, Docker removes it automatically after it exits.

---

## 7. Useful Docker Network Commands

| Command | Description |
|---|---|
| `docker network ls` | Lists Docker networks |
| `docker network create mynet` | Creates a network |
| `docker network inspect mynet` | Displays network details |
| `docker network connect mynet container` | Connects a container to a network |
| `docker network disconnect mynet container` | Disconnects a container from a network |
| `docker network rm mynet` | Removes a network |
| `docker network prune` | Removes unused networks |
| `docker inspect container` | Displays container configuration, including network information |

---

## 8. Cleanup

Stop and remove the containers created in this lesson:

```bash
docker container rm -f mycont1 mycont2 mycont3 mycont4 2>/dev/null
```

Remove the user-defined network:

```bash
docker network rm mynet
```

Check the remaining networks:

```bash
docker network ls
```

**Important:** Docker will not remove a network while containers are still connected to it. Remove or disconnect those containers first.

---

## 9. Conclusion

In this lesson, we explored Docker networking and learned how containers communicate with each other and the outside world.

Key concepts covered:

- Docker's built-in network types: `bridge`, `host`, and `none`.
- The default bridge network and its limitations.
- Creating and inspecting user-defined bridge networks.
- Connecting multiple containers to the same network.
- Using container names for DNS-based communication on user-defined networks.
- Connecting one container to multiple networks.
- Publishing container ports with `-p`.
- Sharing the host network namespace with host networking.
- Isolating a container with the `none` network.
- Cleaning up containers and networks.

Understanding Docker networking is essential for building applications composed of multiple containers and managing communication between services.