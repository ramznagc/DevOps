# Kubernetes 01 — Install a Kubernetes Cluster on AWS EC2

<p align="left">
  <img src="https://img.shields.io/badge/Kubernetes-kubeadm-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes kubeadm" />
  <img src="https://img.shields.io/badge/Platform-Ubuntu-E95420?logo=ubuntu&logoColor=white" alt="Ubuntu" />
  <img src="https://img.shields.io/badge/Cloud-AWS%20EC2-FF9900?logo=amazonaws&logoColor=white" alt="AWS EC2" />
</p>

A hands-on guide to preparing Ubuntu EC2 instances, installing Kubernetes with **kubeadm** and **containerd**, joining worker nodes, and deploying an Nginx application.

> **Scope:** This README organizes the supplied lesson notes. Verify Kubernetes, Ubuntu, and package-repository versions against the official documentation before using the commands in a new environment.

## Learning objectives

By completing this lab, you will practise how to:

- Prepare Ubuntu instances for Kubernetes.
- Configure kernel modules, networking prerequisites, and containerd.
- Install `kubelet`, `kubeadm`, and `kubectl`.
- Initialize a control-plane node and configure Flannel networking.
- Join worker nodes to the cluster.
- Deploy and expose an Nginx Pod with a NodePort Service.
- Inspect and safely remove cluster resources and worker nodes.

## Lab architecture

| Component | Suggested lab configuration |
|---|---|
| Cloud platform | AWS EC2 |
| Operating system | Ubuntu 26.04 (as specified in the lesson notes) |
| Nodes | 1 control plane + 1 worker |
| Instance type | `t3a.medium` |
| CPU / memory | 2 vCPU / 4 GiB RAM |
| Storage | 20 GiB gp3 per instance |
| Container runtime | containerd |
| Cluster bootstrap | kubeadm |
| Pod network | Flannel |
| Example workload | Nginx |

Use private IP addresses for node-to-node communication. Replace all example values with the addresses and settings from your own AWS environment.

## Contents

- [1. Prepare all nodes](#1-prepare-all-nodes)
- [2. Install and configure containerd](#2-install-and-configure-containerd)
- [3. Install Kubernetes packages](#3-install-kubernetes-packages)
- [4. Initialize the control plane](#4-initialize-the-control-plane)
- [5. Join the worker node](#5-join-the-worker-node)
- [6. Deploy Nginx](#6-deploy-nginx)
- [7. Remove a worker node](#7-remove-a-worker-node)
- [8. Troubleshooting notes](#8-troubleshooting-notes)
- [References](#references)

---

## 1. Prepare all nodes

Run the preparation steps on **both** EC2 instances.

### 1.1 Configure security groups

Create separate security groups for the control-plane and worker nodes. Restrict SSH (port 22) to your trusted IP address. Allow Kubernetes node traffic only from the required cluster nodes or security groups; do not expose etcd or internal control-plane ports to the public internet.

#### Control-plane node

| Protocol | Port | Purpose |
|---|---:|---|
| TCP | 6443 | Kubernetes API server |
| TCP | 2379–2380 | etcd client/server API |
| TCP | 10250 | Kubelet API |
| TCP | 10257 | kube-controller-manager |
| TCP | 10259 | kube-scheduler |
| TCP | 22 | SSH administration |
| UDP | 8472 | Flannel VXLAN (when using this backend) |

#### Worker node

| Protocol | Port | Purpose |
|---|---:|---|
| TCP | 10250 | Kubelet API |
| TCP | 10256 | kube-proxy |
| TCP | 30000–32767 | NodePort Services |
| TCP | 22 | SSH administration |
| UDP | 8472 | Flannel VXLAN (when using this backend) |

Check the [Kubernetes ports and protocols reference](https://kubernetes.io/docs/reference/networking/ports-and-protocols/) and the networking plugin's documentation for requirements that apply to your selected versions and configuration.

### 1.2 Set hostnames

Choose the appropriate hostname on each instance.

**Control plane:**

```bash
sudo hostnamectl set-hostname kube-master
```

**Worker:**

```bash
sudo hostnamectl set-hostname kube-worker
```

### 1.3 Disable swap (if required)

The original lesson notes mark this step as unnecessary for the AWS instances used in the exercise and include it for physical servers/workstations. Follow the requirements for your Kubernetes version and environment.

```bash
free -m
sudo swapoff -a
```

If you need swap disabled persistently, review `/etc/fstab` and comment out the relevant swap entry carefully.

### 1.4 Load kernel modules and configure networking

```bash
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

sudo sysctl --system
```

Verify the modules and sysctl values:

```bash
lsmod | grep br_netfilter
lsmod | grep overlay

sysctl net.bridge.bridge-nf-call-iptables \
       net.bridge.bridge-nf-call-ip6tables \
       net.ipv4.ip_forward
```

---

## 2. Install and configure containerd

The lab uses containerd as the container runtime.

### 2.1 Add Docker's package repository

The lesson uses Docker's Ubuntu repository to install the containerd package.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt-get update
```

### 2.2 Install and enable containerd

```bash
sudo apt-get install -y containerd.io
sudo systemctl enable --now containerd
sudo systemctl status containerd
```

### 2.3 Configure the systemd cgroup driver

The kubelet and container runtime should use the same cgroup driver. The lesson configures containerd to use `systemd`.

```bash
sudo containerd config default | \
  sudo tee /etc/containerd/config.toml >/dev/null

sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' \
  /etc/containerd/config.toml

sudo systemctl restart containerd
sudo systemctl enable containerd
```

### 2.4 Optional: install nerdctl

`nerdctl` provides a Docker-compatible command-line experience for containerd. It is optional for this Kubernetes lab.

See the [nerdctl releases](https://github.com/containerd/nerdctl/releases) page and choose a release appropriate for your system. The lesson notes use version 2.0.3:

```bash
wget https://github.com/containerd/nerdctl/releases/download/v2.0.3/nerdctl-full-2.0.3-linux-amd64.tar.gz
sudo tar xvf nerdctl-full-2.0.3-linux-amd64.tar.gz -C /usr/local
```

Example test:

```bash
sudo nerdctl run -d --name redis redis:alpine
sudo nerdctl container ls
```

---

## 3. Install Kubernetes packages

Run on **all nodes**.

The supplied lesson notes configure the Kubernetes v1.37 apt repository. Confirm that this version is intended for your lab before installation.

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.37/deb/Release.key | \
  sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.37/deb/ /' | \
  sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

---

## 4. Initialize the control plane

Run these commands on **kube-master only**.

### 4.1 Pull the required images

```bash
sudo kubeadm config images pull
```

### 4.2 Initialize the cluster

Replace the placeholder with the control-plane instance's **private IP address**.

```bash
sudo kubeadm init \
  --apiserver-advertise-address=<CONTROL_PLANE_PRIVATE_IP> \
  --pod-network-cidr=10.244.0.0/16
```

The lesson uses Flannel, which is configured here with the `10.244.0.0/16` Pod network CIDR.

### 4.3 Configure kubectl for the current user

Run the commands printed by kubeadm after a successful initialization. The usual setup shown in the lesson is:

```bash
mkdir -p "$HOME/.kube"
sudo cp -i /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
```

### 4.4 Install Flannel networking

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

Check the control-plane node and system Pods:

```bash
kubectl get nodes
kubectl get pods -A
kubectl get namespaces
kubectl get pods -n kube-system -o wide
kubectl get services
```

---

## 5. Join the worker node

On the **control-plane node**, generate a fresh join command:

```bash
sudo kubeadm token create --print-join-command
```

Copy the generated command securely and run it with `sudo` on the **worker node**. A join command contains a temporary bootstrap token and cluster CA hash; do not commit real values to GitHub.

This repository includes a reusable helper file: [join-script.sh](../kubernetes-01-installation-ec2/join-script.sh).

After joining, return to the control plane and verify:

```bash
kubectl get nodes
kubectl get nodes -o wide
```

---

## 6. Deploy Nginx

Run these commands from a machine configured with the cluster's kubeconfig.

### 6.1 Check the cluster

```bash
kubectl get nodes
kubectl get pods
kubectl get pods -A -o wide
```

### 6.2 Create an Nginx Pod

```bash
kubectl run nginx-server --image=nginx --port=80
kubectl get pods -o wide
```

### 6.3 Expose Nginx using NodePort

```bash
kubectl expose pod nginx-server --port=80 --type=NodePort
kubectl get service -o wide
```

Find the assigned NodePort in the service output. If you want to test it from outside AWS, ensure the worker's security group permits that specific NodePort from your trusted source IP. Avoid opening the full NodePort range to the public internet.

### 6.4 Clean up the test workload

```bash
kubectl delete service nginx-server
kubectl delete pod nginx-server
kubectl get pods
```

---

## 7. Remove a worker node

Run the drain and delete commands on the **control plane**:

```bash
kubectl get nodes
kubectl cordon kube-worker
kubectl drain kube-worker --ignore-daemonsets --delete-emptydir-data
kubectl delete node kube-worker
```

Then run on the **worker node**:

```bash
sudo kubeadm reset -f
```

The original lesson also lists optional cleanup commands for a worker that needs to rejoin. Use them only when troubleshooting and after confirming the impact on that node:

```bash
sudo rm -rf /etc/cni/net.d
sudo rm -rf "$HOME/.kube"
sudo systemctl daemon-reload
sudo systemctl restart kubelet
sudo ss -lntp | grep 10250
```

To rejoin, generate a **new** join command on the control plane and run it on the worker.

---

## 8. Troubleshooting notes

### Cgroup driver mismatch

The kubelet and container runtime must use a compatible, matching cgroup driver. This lab configures containerd with:

```toml
SystemdCgroup = true
```

Check the containerd configuration and service status if the node does not become Ready:

```bash
grep -n "SystemdCgroup" /etc/containerd/config.toml
sudo systemctl status containerd
sudo systemctl status kubelet
```

### Useful inspection commands

```bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl describe node <NODE_NAME>
kubectl get events -A --sort-by=.metadata.creationTimestamp
sudo journalctl -u kubelet -n 100 --no-pager
```

---

## References

- [Install kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)
- [Create a cluster with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/)
- [Container runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)
- [Kubernetes ports and protocols](https://kubernetes.io/docs/reference/networking/ports-and-protocols/)
- [Kubernetes network add-ons](https://kubernetes.io/docs/concepts/cluster-administration/addons/)
- [Kubernetes reference](https://kubernetes.io/docs/reference/)
- [Docker Engine installation on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Flannel](https://github.com/flannel-io/flannel)
- [nerdctl releases](https://github.com/containerd/nerdctl/releases)

---

<p align="center">
  <i>Hands-on Kubernetes learning lab — Kubernetes 01</i>
</p>
