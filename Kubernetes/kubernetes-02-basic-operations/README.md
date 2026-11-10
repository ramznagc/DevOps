# Kubernetes 02 — Basic Operations

<p align="left">
  <img src="https://img.shields.io/badge/Kubernetes-Basic%20Operations-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes Basic Operations" />
  <img src="https://img.shields.io/badge/Level-Beginner-2ea44f" alt="Beginner" />
  <img src="https://img.shields.io/badge/Platform-Ubuntu%2022.04-E95420?logo=ubuntu&logoColor=white" alt="Ubuntu 22.04" />
</p>

A hands-on lesson covering everyday Kubernetes operations: inspecting cluster resources, working with Pods, ReplicaSets and Deployments, using namespaces, and performing Deployment updates and rollbacks.

## Learning objectives

By completing this lesson, you will practise how to:

- Inspect nodes and discover Kubernetes API resources.
- Create, inspect, and delete Pods.
- Create and manage ReplicaSets and Deployments.
- Read container logs and execute commands inside containers.
- Scale Deployments and observe ReplicaSet behaviour.
- Create and work with namespaces.
- Perform rolling updates and roll back a Deployment to an earlier revision.

## Lab environment

| Component | Lesson configuration |
|---|---|
| Operating system | Ubuntu 22.04 |
| Cluster | 1 control-plane node + 1 worker node |
| Cluster setup | CloudFormation template referenced in the original lesson |
| Practice alternative | [Killercoda Kubernetes playgrounds](https://killercoda.com/playgrounds) |

> **Template note:** The original lesson references `cfn-template-to-create-k8s-cluster.yml`, but that template was not included with the supplied lesson file. Add the template to this folder before using the CloudFormation-based setup. The worker is described as joining automatically after the control-plane node is ready.

## Contents

1. [Set up the Kubernetes cluster](#1-set-up-the-kubernetes-cluster)
2. [Basic Kubernetes operations](#2-basic-kubernetes-operations)
   - [Cluster and API resource discovery](#cluster-and-api-resource-discovery)
   - [Pods](#pods)
   - [ReplicaSets](#replicasets)
   - [Deployments](#deployments)
3. [Namespaces](#3-namespaces)
4. [Deployment rolling updates and rollbacks](#4-deployment-rolling-updates-and-rollbacks)

---

## 1. Set up the Kubernetes cluster

Use the CloudFormation template described in the original lesson to launch two Ubuntu 22.04 nodes: one control plane and one worker. Once the control-plane node is running, the worker is expected to join the cluster automatically.

If you cannot create the lab environment, use the [Killercoda playgrounds](https://killercoda.com/playgrounds).

Verify the cluster:

```bash
kubectl cluster-info
kubectl get nodes
```

Both nodes should appear in the node list. Continue when the cluster is ready.

## 2. Basic Kubernetes operations

### Cluster and API resource discovery

List the API resources supported by the cluster:

```bash
kubectl api-resources
```

Some common resource names and short names:

| Resource | Short name |
|---|---|
| deployments | `deploy` |
| events | `ev` |
| endpoints | `ep` |
| nodes | `no` |
| pods | `po` |
| services | `svc` |

Get help for kubectl:

```bash
kubectl help
```

Read the field documentation for Nodes and list the cluster nodes:

```bash
kubectl explain nodes
kubectl get nodes
```

### Pods

Read the Pod API documentation:

```bash
kubectl explain pods
```

Create a file named `mypod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: nginx
spec:
  containers:
    - name: mynginx
      image: nginx
      ports:
        - containerPort: 80
```

Create and inspect the Pod:

```bash
kubectl create -f mypod.yaml
kubectl get pods
kubectl get pods -o wide
kubectl describe pod nginx-pod
kubectl get pod nginx-pod -o yaml
```

Delete the Pod using either command:

```bash
kubectl delete -f mypod.yaml
# Or:
kubectl delete pod nginx-pod
```

### ReplicaSets

Read the ReplicaSet API documentation:

```bash
kubectl explain replicaset
```

Create a file named `myreplicaset.yaml`:

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: nginx-rs
  labels:
    environment: dev
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: mynginx
          image: nginx
          ports:
            - containerPort: 80
```

The selector must match the labels on the Pod template.

Apply and inspect the ReplicaSet:

```bash
kubectl apply -f myreplicaset.yaml
kubectl get replicaset
kubectl get pods -o wide
kubectl describe replicaset nginx-rs
```

Delete it:

```bash
kubectl delete replicaset nginx-rs
```

### Deployments

Read the Deployment API documentation:

```bash
kubectl explain deployments
```

Create a file named `mydeployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    environment: dev
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx
          ports:
            - containerPort: 80
```

Apply and inspect the Deployment:

```bash
kubectl apply -f mydeployment.yaml
kubectl get deployments
kubectl get pods -o wide
kubectl describe deployment nginx-deployment
kubectl get rs
```

Read container logs. Replace `<pod-name>` and `<container-name>` with actual names:

```bash
kubectl logs <pod-name>
# For a multi-container Pod:
kubectl logs <pod-name> -c <container-name>
```

Execute commands inside a container:

```bash
kubectl exec <pod-name> -- date
kubectl exec <pod-name> -- cat /usr/share/nginx/html/index.html
```

Open an interactive shell:

```bash
kubectl exec -it <pod-name> -- bash
```

Inspect ReplicaSets:

```bash
kubectl get rs
kubectl describe rs <replicaset-name>
```

Scale the Deployment to five replicas:

```bash
kubectl scale deployment nginx-deployment --replicas=5
kubectl get deployment nginx-deployment
kubectl get pods
```

You can also change `spec.replicas` in `mydeployment.yaml` and apply the file again:

```bash
kubectl apply -f mydeployment.yaml
```

Delete one Pod managed by the Deployment and observe that the controller creates a replacement:

```bash
kubectl delete pod <pod-name>
kubectl get pods
```

Delete the Deployment when finished:

```bash
kubectl delete deployment nginx-deployment
```

## 3. Namespaces

Namespaces provide a way to organize resources into separate virtual clusters backed by the same physical cluster.

List the namespaces:

```bash
kubectl get namespaces
```

The lesson introduces these default namespaces:

| Namespace | Purpose |
|---|---|
| `default` | Default namespace for resources when no namespace is specified. |
| `kube-system` | Holds objects created by the Kubernetes system. |
| `kube-public` | Readable by all clients; reserved for resources intended to be publicly visible across the cluster. |
| `kube-node-lease` | Holds Lease objects used by nodes to send heartbeats. |

Create a file named `my-namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mynamespace
```

Create the namespace from the YAML file:

```bash
kubectl apply -f my-namespace.yaml
```

Alternatively, create it directly:

```bash
kubectl create namespace mynamespace
```

Create Deployments in different namespaces:

```bash
kubectl create deployment mynginx --image=nginx
kubectl create deployment myapache --image=httpd -n=mynamespace
```

List Deployments in the default namespace and in `mynamespace`:

```bash
kubectl get deployments
kubectl get deployments -n mynamespace
```

List Deployments across all namespaces:

```bash
kubectl get deployments --all-namespaces -o wide
```

Delete the namespace (this also deletes the namespaced resources inside it):

```bash
kubectl delete namespace mynamespace
```

## 4. Deployment rolling updates and rollbacks

This exercise demonstrates Deployment revisions by updating a container image, inspecting rollout history, and rolling back to an earlier revision.

### 4.1 Create the initial Deployment

Create a working directory and move into it:

```bash
mkdir deployment-lesson
cd deployment-lesson
```

Create `mydeploy.yaml` with the initial image version `1.0`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mydeploy
  labels:
    app: myapp
  annotations:
    kubernetes.io/change-cause: "Initial deployment using ondiacademy/ondiaweb:1.0"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp
  minReadySeconds: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
        - name: mycontainer
          image: ondiacademy/ondiaweb:1.0
          ports:
            - containerPort: 80
```

Apply the manifest and inspect the Deployment, ReplicaSets, and Pods using the `app=myapp` label:

```bash
kubectl apply -f mydeploy.yaml
kubectl get deploy,rs,po -l app=myapp
kubectl describe deployment mydeploy
```

### 4.2 Inspect rollout history

View the Deployment's revision history:

```bash
kubectl rollout history deployment mydeploy
kubectl rollout history deployment mydeploy --revision=1
```

### 4.3 Update the container image to version 2.0

```bash
kubectl set image deployment/mydeploy mycontainer=ondiacademy/ondiaweb:2.0
kubectl annotate deployment mydeploy kubernetes.io/change-cause="Updated mycontainer to ondiacademy/ondiaweb:2.0" --overwrite
```

Inspect the rollout and revisions:

```bash
kubectl rollout history deployment mydeploy
kubectl rollout history deployment mydeploy --revision=1
kubectl rollout history deployment mydeploy --revision=2
kubectl get deploy,rs,po -l app=myapp
```

### 4.4 Update the image using kubectl edit

Open the Deployment for editing:

```bash
kubectl edit deployment/mydeploy
```

Change the container image to `ondiacademy/ondiaweb:3.0` and update the change-cause annotation. Save and close the editor.

Alternatively, set the image directly:

```bash
kubectl set image deployment/mydeploy mycontainer=ondiacademy/ondiaweb:3.0
kubectl annotate deployment mydeploy kubernetes.io/change-cause="Updated mycontainer to ondiacademy/ondiaweb:3.0" --overwrite
```

Inspect the history and resources again:

```bash
kubectl rollout history deployment mydeploy
kubectl rollout history deployment mydeploy --revision=1
kubectl rollout history deployment mydeploy --revision=2
kubectl rollout history deployment mydeploy --revision=3
kubectl get deploy,rs,po -l app=myapp
```

### 4.5 Roll back to revision 1

Roll back the Deployment:

```bash
kubectl rollout undo deployment mydeploy --to-revision=1
```

Inspect the rollout history and resources:

```bash
kubectl rollout history deployment mydeploy
kubectl get deploy,rs,po -l app=myapp
```

The original lesson demonstrates that a rollback creates a new revision in the history; revision numbers therefore change as you update and roll back. Inspect the actual revision details in your cluster rather than assuming revision numbers will be identical in every run.

You can also inspect a specific revision:

```bash
kubectl rollout history deployment mydeploy --revision=<revision-number>
```

### 4.6 Clean up

Delete the Deployment:

```bash
kubectl delete deployment mydeploy
```

---

## Useful command summary

| Task | Command |
|---|---|
| List nodes | `kubectl get nodes` |
| List Pods | `kubectl get pods -o wide` |
| List Deployments | `kubectl get deployments` |
| List ReplicaSets | `kubectl get rs` |
| Describe a resource | `kubectl describe <resource> <name>` |
| Read Pod logs | `kubectl logs <pod-name>` |
| Execute a command in a Pod | `kubectl exec <pod-name> -- <command>` |
| Scale a Deployment | `kubectl scale deployment <name> --replicas=<count>` |
| List namespaces | `kubectl get namespaces` |
| View rollout history | `kubectl rollout history deployment <name>` |
| Undo a rollout | `kubectl rollout undo deployment <name>` |

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [ReplicaSets](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)
- [Killercoda Kubernetes Playgrounds](https://killercoda.com/playgrounds)

---

<p align="center"><i>Hands-on Kubernetes learning lab — Kubernetes 02</i></p>
