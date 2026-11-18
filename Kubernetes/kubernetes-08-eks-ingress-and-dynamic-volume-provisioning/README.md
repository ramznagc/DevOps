# Hands-on EKS-02: Ingress and Dynamic Volume Provisioning

This lesson combines Amazon EKS cluster administration, Kubernetes Ingress routing, and persistent storage backed by Amazon EBS.

> **Important — controller lifecycle:** The original lab uses the community `ingress-nginx` controller to teach Ingress and the `rewrite-target` annotation. The Kubernetes project retired ingress-nginx on March 24, 2026. It no longer receives releases, bug fixes, or security updates. Keep this controller only for an isolated learning environment; do not introduce it into a new production cluster. For new deployments, evaluate a maintained Ingress controller or the Kubernetes Gateway API. See the [Kubernetes retirement announcement](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/) and the [archived project notice](https://github.com/kubernetes/ingress-nginx).

## Learning outcomes

By the end of this hands-on lesson, you will be able to:

- Install and use `kubectl` and `eksctl` on Amazon Linux 2023.
- Create and manage an Amazon EKS cluster.
- Explain Ingress resources and Ingress controllers.
- Route requests by URL path and hostname.
- Explain how the NGINX `rewrite-target` annotation changes the path sent to a backend.
- Configure the Amazon EBS CSI driver and dynamically provision persistent storage with a StorageClass and PVC.

## Outline

1. Install `kubectl` and `eksctl`.
2. Create an EKS cluster.
3. Configure Ingress routing and hostname-based virtual hosting.
4. Configure dynamic EBS volume provisioning.

## Prerequisites

- An AWS account and an IAM identity with permissions to create EKS, EC2, IAM, CloudFormation, and EBS resources.
- AWS CLI configured, or an appropriate IAM role attached to the management instance.
- An Amazon Linux 2023 EC2 instance for the command-line exercises.
- A supported Kubernetes version and an EKS cluster in a region with sufficient capacity.
- Basic familiarity with Pods, Deployments, Services, and YAML.

**Cost reminder:** EKS control planes, EC2 worker nodes, load balancers, and EBS volumes can incur charges. Complete the cleanup steps and verify that no billable resources remain.

---

## Part 1 — Install kubectl and eksctl

### Install kubectl on Amazon Linux 2023

Launch an Amazon Linux 2023 EC2 instance, connect over SSH, and update packages:

```bash
sudo dnf update -y
```

Install the EKS-vended `kubectl` binary using the current version and download instructions in the [AWS EKS kubectl documentation](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html). The version-specific download URL in the original classroom notes can become stale, so use the current AWS instructions rather than pinning an old dated URL.

After downloading the binary:

```bash
chmod +x ./kubectl
mkdir -p "$HOME/bin"
install -m 0755 ./kubectl "$HOME/bin/kubectl"
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/bin:$PATH"
kubectl version --client
```

### Install eksctl

Download and install the latest Linux AMD64 release:

```bash
ARCH=amd64
PLATFORM=$(uname -s)_$ARCH
curl --fail --silent --show-error --location \
  "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_${PLATFORM}.tar.gz" \
  | tar xz -C /tmp
sudo install -m 0755 /tmp/eksctl /usr/local/bin/eksctl
eksctl version
```

Official instructions: [Installing or upgrading eksctl](https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html#installing-eksctl).

---

## Part 2 — Create an EKS cluster

Configure AWS credentials if the instance does not already use an attached IAM role:

```bash
aws configure
aws sts get-caller-identity
```

Choose a Kubernetes version currently supported by EKS in your target region. The following example follows the original lesson's region, cluster name, and worker-node sizing; adjust the version and instance type to current regional availability:

```bash
export AWS_REGION=us-east-1
export CLUSTER_NAME=cw-cluster

eksctl create cluster \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --version 1.34 \
  --zones us-east-1a,us-east-1b,us-east-1c \
  --node-type t3a.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 3
```

The cluster creation process can take several minutes. Check the cluster and worker nodes:

```bash
eksctl get cluster --region "$AWS_REGION"
kubectl get nodes -o wide
kubectl get pods -A
```

### Optional — enable SSH access to managed nodes

If SSH access is required for the classroom exercise, create a key pair first:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/eks-node-key
```

Then create a cluster with an SSH key:

```bash
eksctl create cluster \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --version 1.34 \
  --zones us-east-1a,us-east-1b,us-east-1c \
  --nodegroup-name my-nodes \
  --node-type t3a.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 3 \
  --ssh-access \
  --ssh-public-key ~/.ssh/eks-node-key.pub \
  --managed
```

Use SSH access only when it is needed, and restrict the node security group's inbound SSH source to trusted addresses. Review the available options with:

```bash
eksctl create cluster --help
```

You can inspect the EKS cluster in the AWS console and the CloudFormation stacks created by `eksctl`.

---

## Part 3 — Ingress

### 3.1 Understand Ingress

A Kubernetes Service provides a stable endpoint for a set of Pods. An Ingress resource describes HTTP(S) routing rules from outside the cluster to Services. An **Ingress controller** watches Ingress resources and implements those rules. Creating an Ingress resource alone does not provide a working entry point; a compatible controller must be installed and configured.

Read the [Kubernetes Ingress documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/).

### 3.2 Controller note for this historical lab

The original exercise installs ingress-nginx using the cloud-provider manifest. The original notes called this a bare-metal installation, but the URL uses the `provider/cloud` manifest. These are different deployment environments.

The ingress-nginx project was retired on March 24, 2026. The following installation command is retained only to explain the original lab and reproduce it in a disposable, isolated environment; it is **not** a recommendation for a new or production cluster:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.14.3/deploy/static/provider/cloud/deploy.yaml
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

Wait until the controller Pods are ready. The controller Service may take a few minutes to receive an external address in a cloud environment. For a new deployment, select a currently maintained controller or Gateway API implementation instead.

### 3.3 Deploy the ClarusShop application

The original lab uses two application backends:

- `storefront-service` serves the storefront at `/`.
- `account-service` serves the account page.

The manifests are in the `ingress/` directory. Apply them:

```bash
kubectl apply -f ingress/
kubectl get deployments,pods,services
```

The Services are `ClusterIP` because they are internal backends reached through the Ingress controller. The controller provides the external entry point.

### 3.4 Path-based routing

The sample Ingress sends requests for `/` to the storefront and requests for `/account` to the account service:

```bash
kubectl apply -f ingress/ingress.yaml
kubectl get ingress
kubectl describe ingress clarusshop-ingress
```

Find the controller's external address:

```bash
kubectl get svc -n ingress-nginx
```

Use the external address shown for the controller Service:

```bash
curl http://<INGRESS-ADDRESS>/
curl http://<INGRESS-ADDRESS>/account
```

The exact address and response depend on the cloud environment and application image versions.

### 3.5 Host-based routing

An Ingress rule can also select a backend by HTTP Host header. The example in `ingress/virtual-hosting/ingress.yaml` routes:

- `nginx.example.test` to the NGINX Service.
- `apache.example.test` to the Apache Service.

Create the two sample backends and apply the Ingress:

```bash
kubectl run mynginx --image=nginx --port=80 --expose
kubectl run myapache --image=httpd --port=80 --expose
kubectl apply -f ingress/virtual-hosting/ingress.yaml
kubectl get pods,services,ingress
```

For a quick local test, send the Host header directly:

```bash
curl -H 'Host: nginx.example.test' http://<INGRESS-ADDRESS>/
curl -H 'Host: apache.example.test' http://<INGRESS-ADDRESS>/
```

For real DNS access, create DNS records for hostnames in a domain you control, pointing them to the controller's external address. The example domain `example.test` is reserved for testing and is not publicly resolvable.

### 3.6 Rewrite-target annotation lab

The separate `ingress-rewrite-target-annotation/` directory contains a focused two-stage exercise:

1. **Without the annotation:** the account backend exposes `/account`, so a request to `/account` is served successfully without rewriting.
2. **With the annotation:** change the account image to the variant that serves its page at `/`. The incoming request still matches `/account`, so the controller rewrites the backend request path to `/`.

The key annotation is:

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
```

Apply the sample manifests and Ingress from that directory as described in its README. The annotation is controller-specific; it is not a built-in Kubernetes Ingress field.

**Important:** This simplified rewrite rule sends matching requests to the backend root. More complex applications with nested paths may need capture groups and a more specific rewrite rule. Verify the exact behavior with the controller version used in the lab.

---

## Part 4 — Dynamic Volume Provisioning with Amazon EBS

### 4.1 Amazon EBS CSI driver

The Amazon EBS Container Storage Interface (CSI) driver allows EKS workloads to request persistent EBS volumes through Kubernetes storage objects. An EBS volume is an Availability Zone-scoped block device and is typically mounted by one node at a time with `ReadWriteOnce`.

The EBS CSI driver must be available in the cluster. Follow AWS's current instructions for [managing the Amazon EBS CSI driver as an EKS add-on](https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html).

### 4.2 Associate an IAM OIDC provider

Set the cluster variables:

```bash
export AWS_REGION=us-east-1
export CLUSTER_NAME=cw-cluster
```

Associate the IAM OIDC provider (if it is not already associated):

```bash
eksctl utils associate-iam-oidc-provider \
  --region "$AWS_REGION" \
  --cluster "$CLUSTER_NAME" \
  --approve
```

### 4.3 Create the EBS CSI driver IAM role

The controller needs AWS permissions to manage EBS volumes. Create a role for the driver's service account and attach the AWS-managed `AmazonEBSCSIDriverPolicy` policy:

```bash
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster "$CLUSTER_NAME" \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --role-only \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --region "$AWS_REGION" \
  --approve
```

### 4.4 Install the EBS CSI add-on

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

eksctl create addon \
  --name aws-ebs-csi-driver \
  --cluster "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --service-account-role-arn "arn:aws:iam::${ACCOUNT_ID}:role/AmazonEKS_EBS_CSI_DriverRole" \
  --force
```

Check the controller and node Pods:

```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver
kubectl get storageclass
```

If the add-on already exists, inspect its configuration and update it instead of blindly creating a duplicate.

### 4.5 Create a StorageClass

A StorageClass describes how a volume should be dynamically provisioned. This lesson uses the EBS CSI provisioner and `WaitForFirstConsumer`. The latter delays volume binding/provisioning until a Pod using the claim is scheduled, allowing Kubernetes to select a compatible Availability Zone.

The example uses `gp3`, the general-purpose SSD volume type:

```bash
kubectl apply -f storage/storage-class.yaml
kubectl get storageclass
kubectl describe storageclass ebs-gp3
```

### 4.6 Create a PersistentVolumeClaim

A PersistentVolumeClaim (PVC) is a request for storage. Apply the 1 GiB claim:

```bash
kubectl apply -f storage/claim.yaml
kubectl get pvc
```

With `WaitForFirstConsumer`, the PVC may remain `Pending` until a Pod references it. This is expected.

### 4.7 Mount the claim in a Pod

Apply the Pod manifest:

```bash
kubectl apply -f storage/pod.yaml
kubectl get pod test-aws
kubectl get pv,pvc
```

After the Pod is running, inspect the mounted filesystem:

```bash
kubectl exec -it test-aws -- df -h
```

The EBS volume should be mounted at `/usr/share/nginx/html`. You can also write a test file and verify that it remains on the mounted volume while the claim exists:

```bash
kubectl exec test-aws -- sh -c 'echo persistent-data > /usr/share/nginx/html/test.txt'
kubectl exec test-aws -- cat /usr/share/nginx/html/test.txt
```

### 4.8 Cleanup

Delete the workload first, then the PVC, and finally the StorageClass:

```bash
kubectl delete -f storage/pod.yaml
kubectl delete -f storage/claim.yaml
kubectl delete -f storage/storage-class.yaml
```

Check the PV and PVC states:

```bash
kubectl get pv,pvc
```

The StorageClass in this lesson uses `reclaimPolicy: Delete`; deleting the PVC normally causes the dynamically provisioned EBS volume to be deleted after it is released. Verify this in the EC2 **Volumes** console before assuming cleanup is complete. If you change the reclaim policy to `Retain`, you must manage the retained volume separately.

Delete the cluster when all exercises are complete:

```bash
eksctl get cluster --region "$AWS_REGION"
eksctl delete cluster "$CLUSTER_NAME" --region "$AWS_REGION"
```

Also verify that no unattached EBS volumes, load balancers, or other billable resources remain.

---

## Repository layout

```text
kubernetes-08-eks-ingress-and-dynamic-volume-provisioning/
├── README.md
├── ingress/
│   ├── account-deployment.yaml
│   ├── account-service.yaml
│   ├── ingress.yaml
│   ├── storefront-deployment.yaml
│   ├── storefront-service.yaml
│   └── virtual-hosting/
│       └── ingress.yaml
├── ingress-rewrite-target-annotation/
│   ├── README.md
│   ├── ing.yaml
│   └── k8s/
│       ├── account-deploy.yaml
│       ├── account-service.yaml
│       ├── storefront-deploy.yaml
│       └── storefront-service.yaml
└── storage/
    ├── claim.yaml
    ├── pod.yaml
    └── storage-class.yaml
```

## References

- [Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Ingress NGINX retirement announcement](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/)
- [Amazon EKS — install kubectl](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html)
- [Amazon EKS — eksctl](https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html)
- [Amazon EKS — Amazon EBS CSI driver add-on](https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html)
