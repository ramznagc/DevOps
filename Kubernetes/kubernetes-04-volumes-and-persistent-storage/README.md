# Kubernetes 04 — Volumes and Persistent Storage

<p>
  <img src="https://img.shields.io/badge/Kubernetes-Storage-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes Storage" />
  <img src="https://img.shields.io/badge/Topics-PV%20%7C%20PVC%20%7C%20EmptyDir-0A7B83" alt="Persistent storage topics" />
</p>

A hands-on lesson about Kubernetes storage, data persistence, PersistentVolumes (PVs), PersistentVolumeClaims (PVCs), `emptyDir`, and StorageClasses.

## Learning objectives

By completing this lesson, you will practise how to:

- Explain why applications need persistent storage.
- Create and inspect PersistentVolumes and PersistentVolumeClaims.
- Understand how a PVC binds to a suitable PV.
- Mount persistent storage in a Pod.
- Explore the lifecycle of an `emptyDir` volume.
- Use a StorageClass and dynamic volume provisioning.

## Lesson outline

1. [Prepare the Kubernetes cluster](#1-prepare-the-kubernetes-cluster)
2. [Create and use a PersistentVolume](#2-create-and-use-a-persistentvolume)
3. [Explore PV and PVC binding](#3-explore-pv-and-pvc-binding)
4. [Use an emptyDir volume](#4-use-an-emptydir-volume)
5. [Explore StorageClasses and dynamic provisioning](#5-explore-storageclasses-and-dynamic-provisioning)
6. [Clean up](#6-clean-up)

---

## 1. Prepare the Kubernetes cluster

The source lesson uses an Ubuntu 22.04 cluster with one control-plane node and one worker node. It references a CloudFormation template from the previous lesson.

> **Template note:** The referenced `cfn-template-to-create-k8s-cluster.yml` was not included with the uploaded lesson file. Use your existing cluster or a Kubernetes practice environment such as [Killercoda](https://killercoda.com/playgrounds).

Check that the cluster is available:

```bash
kubectl cluster-info
kubectl get nodes
```

## 2. Create and use a PersistentVolume

### 2.1 Understand Kubernetes volumes

Read the [Kubernetes Volumes documentation](https://kubernetes.io/docs/concepts/storage/volumes/) and inspect the PersistentVolume API:

```bash
kubectl explain persistentvolume
```

A PersistentVolume (PV) is a cluster storage resource. A PersistentVolumeClaim (PVC) is a request for storage made by a user or workload. A Pod can mount storage through a PVC rather than depending directly on a Pod's temporary filesystem.

### 2.2 Prepare data on the worker node

Connect to the worker node used for this lab and create a directory with a sample web page:

```bash
mkdir -p "$HOME/pv-data"
echo "Welcome to Kubernetes persistence volume lesson" > "$HOME/pv-data/index.html"
ls -l "$HOME/pv-data"
pwd
```

The source lesson uses this path:

```text
/home/ubuntu/pv-data
```

Use the actual absolute path on your worker node in the PV manifest below.

> **Important — hostPath is node-local:** A `hostPath` volume refers to a path on one specific Kubernetes node. It is not shared storage across the cluster. The Pod must run on the same node that contains the data directory. The sample manifest from the lesson does not specify node affinity, so verify the Pod's node placement before testing. For production and multi-node workloads, prefer an appropriate network or cloud storage provisioner.

### 2.3 Create a PersistentVolume

On a machine configured with `kubectl`, create `ondia-pv.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: ondia-pv-vol
  labels:
    type: local
spec:
  storageClassName: manual
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /home/ubuntu/pv-data
```

Apply the manifest and inspect the PV:

```bash
kubectl apply -f ondia-pv.yaml
kubectl get pv ondia-pv-vol
kubectl describe pv ondia-pv-vol
```

Before a claim is bound, the PV should be available for a matching claim.

### 2.4 Create a PersistentVolumeClaim

Inspect the PVC API:

```bash
kubectl explain persistentvolumeclaim
```

Create `ondia-pv-claim.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ondia-pv-claim
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

Apply and check the claim:

```bash
kubectl apply -f ondia-pv-claim.yaml
kubectl get pvc ondia-pv-claim
kubectl get pv ondia-pv-vol
```

Kubernetes looks for a PV that satisfies the PVC's requested storage, access mode, and StorageClass. When a matching PV is found, the claim and volume are bound.

### 2.5 Mount the claim in a Pod

Create `ondia-pod.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ondia-pod
  labels:
    app: ondia-web
spec:
  volumes:
    - name: ondia-pv-storage
      persistentVolumeClaim:
        claimName: ondia-pv-claim
  containers:
    - name: ondia-pv-container
      image: nginx
      ports:
        - containerPort: 80
          name: http-server
      volumeMounts:
        - mountPath: /usr/share/nginx/html
          name: ondia-pv-storage
```

Apply the manifest and inspect placement:

```bash
kubectl apply -f ondia-pod.yaml
kubectl get pod ondia-pod -o wide
```

Make sure the Pod is running on the worker node where you created `/home/ubuntu/pv-data`. If it is scheduled elsewhere, the hostPath may not contain the expected data.

Open a shell in the container and read the page:

```bash
kubectl exec -it ondia-pod -- /bin/bash
```

Inside the container:

```bash
curl http://localhost/
```

### 2.6 Verify that the data is persistent

On the worker node that hosts the directory, change the page:

```bash
echo "Kubernetes Rocks!!!!" > "$HOME/pv-data/index.html"
```

Then read it again from the Nginx container:

```bash
kubectl exec ondia-pod -- cat /usr/share/nginx/html/index.html
```

The updated content should be visible because the container is mounting the host directory through the PV and PVC.

### 2.7 Expose the Pod (optional)

The source lesson exposes the Pod using a NodePort Service:

```bash
kubectl expose pod ondia-pod --port=80 --type=NodePort
kubectl get services
```

Use the assigned NodePort and the appropriate node address to test it:

```text
http://<NODE_PUBLIC_IP>:<NODE_PORT>
```

Only open the required port to a trusted source in your cloud security group.

## 3. Explore PV and PVC binding

This exercise demonstrates how Kubernetes matches a claim to an available volume.

Create a working directory:

```bash
mkdir -p pvc-bound
cd pvc-bound
```

### 3.1 Create two PersistentVolumes

Create `pv-3g.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-3g
  labels:
    type: local
spec:
  storageClassName: manual
  capacity:
    storage: 3Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /home/ubuntu/pv-data
```

Create `pv-6g.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-6g
  labels:
    type: local
spec:
  storageClassName: manual
  capacity:
    storage: 6Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /home/ubuntu/pv-data
```

Apply both:

```bash
kubectl apply -f pv-3g.yaml
kubectl apply -f pv-6g.yaml
kubectl get pv
```

### 3.2 Request 2Gi of storage

Create `pv-claim-2g.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pv-claim-2g
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 2Gi
```

Apply and inspect:

```bash
kubectl apply -f pv-claim-2g.yaml
kubectl get pv,pvc
```

The lesson expects the 2Gi claim to bind to the 3Gi PV. A claim can bind to a PV with capacity greater than or equal to the requested capacity, provided the other requirements match.

### 3.3 Request 7Gi of storage

Create `pv-claim-7g.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pv-claim-7g
spec:
  storageClassName: manual
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 7Gi
```

Apply it:

```bash
kubectl apply -f pv-claim-7g.yaml
kubectl get pv,pvc
```

Observe the statuses:

- The 2Gi claim can bind to a suitable available PV.
- The 7Gi claim remains `Pending` because neither available PV has enough capacity.
- The 6Gi PV remains `Available` if it has not been claimed.

This demonstrates that a PVC is not bound merely because a PV exists; the PV must satisfy the claim.

## 4. Use an emptyDir volume

An `emptyDir` volume is created when a Pod is assigned to a node.

- It starts empty.
- It remains available to containers in that Pod while the Pod remains on the node.
- Data survives a container crash and restart within the same Pod.
- Data is permanently deleted when the Pod is removed from the node.

Create a directory:

```bash
mkdir -p emptydir
cd emptydir
```

Create `nginx.yaml`:

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
      image: nginx:1.19
      ports:
        - containerPort: 80
      volumeMounts:
        - mountPath: /test
          name: emptydir-test
  volumes:
    - name: emptydir-test
      emptyDir: {}
```

Apply and inspect:

```bash
kubectl apply -f nginx.yaml
kubectl get pod nginx-pod
kubectl exec -it nginx-pod -- bash
```

Inside the container, create a file:

```bash
mkdir -p /test
echo "Hello World" > /test/hello.txt
cat /test/hello.txt
```

### Observe the emptyDir lifecycle

A container restart inside the same Pod does not normally remove the `emptyDir` data. However, deleting the Pod and creating a replacement Pod creates a new `emptyDir`, so the old data is lost.

The source lesson suggests deleting the running container directly with `ctr` to demonstrate a container restart. This is a low-level runtime operation and can be disruptive; it is not the recommended way to manage Kubernetes workloads. If you perform that experiment, first identify the correct container and understand the impact. For normal operations, use Kubernetes APIs and observe Pod/container restart behavior through:

```bash
kubectl describe pod nginx-pod
kubectl get pod nginx-pod
```

Finally, delete the Pod:

```bash
kubectl delete pod nginx-pod
```

## 5. Explore StorageClasses and dynamic provisioning

A StorageClass describes a class of storage and can be used by a provisioner to create storage dynamically when a PVC requests it.

### 5.1 Inspect available StorageClasses

```bash
kubectl get storageclass
kubectl describe storageclass
```

The source lesson uses a StorageClass named `local-path`. This class is not guaranteed to exist in every cluster. Continue with the following manifests only if your cluster has a compatible `local-path` StorageClass and provisioner.

### 5.2 Create a PVC

Create `sc-pv-claim.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sc-pv-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 3Gi
  storageClassName: local-path
```

Apply and inspect:

```bash
kubectl apply -f sc-pv-claim.yaml
kubectl get pv,pvc
```

Depending on the provisioner, the claim may remain `Pending` until a Pod requests it. Some StorageClasses use delayed binding (for example, `WaitForFirstConsumer`).

### 5.3 Create a Pod that uses the claim

Create `pod-with-dynamic-storage.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-sc
  labels:
    app: web-nginx
spec:
  containers:
    - name: test-sc
      image: nginx:latest
      ports:
        - containerPort: 80
      volumeMounts:
        - mountPath: /usr/share/nginx/html
          name: aws-pd
  volumes:
    - name: aws-pd
      persistentVolumeClaim:
        claimName: sc-pv-claim
```

Apply the Pod and inspect the resources:

```bash
kubectl apply -f pod-with-dynamic-storage.yaml
kubectl get pods
kubectl get pv,pvc
```

If dynamic provisioning is configured correctly, the provisioner creates a PV for the PVC and the claim becomes `Bound`. The source lesson notes that its local-path provisioner stores data under `/opt/local-path-provisioner` on the worker node; the actual path depends on the provisioner's configuration.

## 6. Clean up

Remove the resources created in this lesson. Run commands only for resources that you created:

```bash
kubectl delete service ondia-pod --ignore-not-found
kubectl delete pod ondia-pod --ignore-not-found
kubectl delete pvc ondia-pv-claim --ignore-not-found
kubectl delete pv ondia-pv-vol --ignore-not-found

kubectl delete -f pv-claim-2g.yaml --ignore-not-found
kubectl delete -f pv-claim-7g.yaml --ignore-not-found
kubectl delete -f pv-3g.yaml --ignore-not-found
kubectl delete -f pv-6g.yaml --ignore-not-found

kubectl delete pod nginx-pod --ignore-not-found
kubectl delete pod test-sc --ignore-not-found
kubectl delete pvc sc-pv-claim --ignore-not-found
```

> **Storage warning:** Deleting a PVC or PV can affect access to stored data. Reclaim behavior depends on the PV's reclaim policy and the storage provisioner. Review the resources and backup any data you need before cleanup.

## Quick command reference

| Task | Command |
|---|---|
| Explain PersistentVolumes | `kubectl explain pv` |
| List PersistentVolumes | `kubectl get pv` |
| Explain PersistentVolumeClaims | `kubectl explain pvc` |
| List claims | `kubectl get pvc` |
| List PVs and PVCs | `kubectl get pv,pvc` |
| Inspect StorageClasses | `kubectl get storageclass` |
| Inspect a Pod's mounts/events | `kubectl describe pod <POD_NAME>` |
| Read a file in a container | `kubectl exec <POD_NAME> -- cat <PATH>` |

## References

- [Kubernetes Volumes](https://kubernetes.io/docs/concepts/storage/volumes/)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [StorageClasses](https://kubernetes.io/docs/concepts/storage/storage-classes/)
- [Configure a Pod to Use a PersistentVolumeClaim](https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/)

---

<p align="center"><i>Hands-on Kubernetes learning lab — Kubernetes 04</i></p>
