# Kubernetes 07 — Amazon EKS and Cluster Autoscaler

This hands-on lesson creates an Amazon EKS cluster, configures local `kubectl` access, adds a managed worker node group, installs Cluster Autoscaler with IAM Roles for Service Accounts (IRSA), and demonstrates node scale-out with a sample workload.

> **Cost warning:** EKS control planes, EC2 worker nodes, load balancers, NAT gateways, public IPv4 addresses, and data transfer can incur AWS charges. Review [Amazon EKS pricing](https://aws.amazon.com/eks/pricing/) and delete lab resources when finished.

## Learning outcomes

- Create and inspect an EKS cluster
- Configure a kubeconfig context using AWS CLI
- Add a managed node group with a dedicated EC2 node IAM role
- Explain the difference between Pod autoscaling and node autoscaling
- Configure Cluster Autoscaler using IRSA and Auto Discovery
- Deploy a sample workload and observe pending Pods trigger node scale-out

## Repository contents

```text
kubernetes-07-eks-cluster-and-cluster-autoscaler/
├── README.md
├── iam/
│   └── cluster-autoscaler-policy.json
├── cluster-autoscaler/
│   └── cluster-autoscaler-deployment.yaml
└── sample-app/
    └── testing-cas.yaml
```

## Prerequisites

- An AWS account with permission to create EKS, EC2, IAM, VPC, Auto Scaling, and load-balancing resources
- An Amazon Linux 2023 EC2 administration host, or another supported workstation
- AWS CLI v2, `kubectl`, and `eksctl`
- An SSH key pair only if SSH access to worker nodes is explicitly needed
- A region selected for the entire exercise (examples below use `us-east-1`)

Do not place AWS access keys in source files or commit them to Git. Prefer an EC2 instance profile, AWS IAM Identity Center, or another supported short-lived credential mechanism. For an EC2 administration host, attach only the permissions needed for the lab.

### Install and verify tools

Install the AWS CLI by following the official instructions: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

Install `eksctl`: https://eksctl.io/installation/

Install a `kubectl` version compatible with your EKS Kubernetes version: https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html

Verify:

```bash
aws --version
eksctl version
kubectl version --client
aws sts get-caller-identity
aws configure get region
```

If using a profile, add `--profile YOUR_PROFILE` to AWS CLI commands or export `AWS_PROFILE`.

## Part 1 — Create the EKS cluster

You can create the cluster through the AWS Console or with `eksctl`. The CLI example is repeatable and keeps the cluster configuration visible in your terminal.

Choose a currently supported Kubernetes version in your target AWS Region. EKS version availability and support windows change; check the [EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html) page before creating the cluster.

Set variables:

```bash
export AWS_REGION=us-east-1
export CLUSTER_NAME=my-cluster
```

Create the cluster with a managed node group:

```bash
eksctl create cluster \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --version YOUR_SUPPORTED_K8S_VERSION \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 3 \
  --managed
```

Replace `YOUR_SUPPORTED_K8S_VERSION` with an EKS-supported minor version. The example uses a small managed node group for a lab; select instance types and capacity based on your workload and budget.

### What the cluster configuration means

- **Cluster service role:** allows the EKS control plane to manage AWS resources on your behalf. Use the EKS cluster IAM role guidance and the AWS-managed policy recommended by AWS.
- **VPC and subnets:** EKS networking and worker nodes live in a VPC. Production environments should use a deliberately designed VPC spanning multiple Availability Zones, with public/private subnet separation and appropriate routing.
- **Cluster endpoint access:** private-only access is preferable where practical. Public access should be restricted to trusted CIDR ranges. Public-and-private access is convenient for a lab but should not mean unrestricted public access.
- **Logging:** enable the control-plane log types needed for troubleshooting and security operations. CloudWatch Logs ingestion and retention may incur charges.
- **Secrets encryption:** EKS supports envelope encryption with AWS KMS for supported Kubernetes API data. Understand key policy, lifecycle, and cost before enabling it.

### Console-based alternative

In the AWS Console, open **Amazon EKS → Clusters → Create cluster**. Choose the cluster name and Kubernetes version, assign the EKS cluster IAM role, configure VPC/subnets and endpoint access, select desired control-plane log types, review, and create.

## Part 2 — Configure kubeconfig

Wait until the cluster status is `ACTIVE`:

```bash
aws eks describe-cluster \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --query 'cluster.status' \
  --output text
```

Write or update the current user's kubeconfig:

```bash
aws eks update-kubeconfig \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION"
```

This command obtains cluster connection details and configures an AWS IAM authenticator exec entry in `~/.kube/config`. It does not create Kubernetes users or grant access by itself; IAM authentication and EKS access entries/RBAC determine authorization.

Verify:

```bash
kubectl config current-context
kubectl get svc
kubectl get nodes
```

A cluster created without worker nodes may show no nodes. The `kubernetes` Service is the API service inside the cluster.

## Part 3 — Add a managed worker node group

The `eksctl create cluster` command above creates a managed node group already. If you created the control plane separately, add a managed node group:

```bash
eksctl create nodegroup \
  --cluster "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --name workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 3 \
  --managed
```

For a console-created node group, assign a dedicated node IAM role. AWS documents the required permissions in [Amazon EKS node IAM role](https://docs.aws.amazon.com/eks/latest/userguide/create-node-role.html). Common managed-node-group permissions include:

- `AmazonEKSWorkerNodePolicy` — worker nodes can connect to the EKS cluster and perform required worker-node operations.
- `AmazonEC2ContainerRegistryPullOnly` (preferred where available) or the documented ECR read-only permissions — allows nodes to pull images from ECR.
- VPC CNI permissions — allow the CNI component to manage networking resources. Prefer assigning these permissions to the VPC CNI add-on's own IAM role (IRSA or EKS Pod Identity) instead of broad node-role permissions.

For the node operating system, use an EKS-supported Amazon Linux 2023 or Bottlerocket AMI. **Do not select the old EKS-optimized Amazon Linux 2 AMI for a new cluster:** AWS stopped publishing EKS-optimized AL2 AMIs on November 26, 2025. See [AL2 AMI deprecation](https://docs.aws.amazon.com/eks/latest/userguide/eks-ami-deprecation-faqs.html).

Watch nodes:

```bash
kubectl get nodes --watch
```

The `t3.medium` example is a small general-purpose instance. Very small instance types can lack sufficient CPU/memory for system Pods and lab workloads. Check regional availability, quotas, and current pricing before choosing capacity.

## Part 4 — Configure Cluster Autoscaler

### What Cluster Autoscaler does

Cluster Autoscaler adjusts the size of supported node groups when Pods cannot be scheduled due to insufficient resources, and can remove underutilized nodes when their Pods can be safely moved.

It is different from Horizontal Pod Autoscaler (HPA):

- **HPA** changes the number of Pods for a workload.
- **Cluster Autoscaler** changes the number of worker nodes when scheduling demand requires more capacity.

For EKS managed node groups, Cluster Autoscaler works with the underlying EC2 Auto Scaling Groups. Its Kubernetes minor version must match the cluster's minor version. See the [AWS EKS best practices for Cluster Autoscaler](https://docs.aws.amazon.com/eks/latest/best-practices/cas.html).

### 4.1 Tag the node group Auto Scaling Group

Cluster Autoscaler Auto Discovery uses tags on the backing Auto Scaling Group. The required tags are:

```text
k8s.io/cluster-autoscaler/enabled = true
k8s.io/cluster-autoscaler/<CLUSTER_NAME> = owned
```

Replace `<CLUSTER_NAME>` with the exact EKS cluster name. Verify the ASG tags in the EC2 Auto Scaling console or with AWS CLI. Do not confuse these Auto Scaling Group tags with subnet tags used by load balancers.

### 4.2 Create the IAM policy

Review `iam/cluster-autoscaler-policy.json` and create an IAM policy named `ClusterAutoscalerPolicy`. The example grants the describe actions needed for discovery and includes mutation actions scoped by Auto Scaling Group resource tags. Adapt and validate the policy against the AWS documentation and your organization’s IAM standards.

### 4.3 Configure IRSA

IRSA allows a Kubernetes ServiceAccount to assume a specific IAM role through the cluster's OIDC provider. This avoids storing AWS access keys in the Cluster Autoscaler Pod.

Associate the OIDC provider:

```bash
eksctl utils associate-iam-oidc-provider \
  --cluster "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --approve
```

Create the IAM ServiceAccount (replace account/role/policy values as needed):

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/ClusterAutoscalerPolicy"

eksctl create iamserviceaccount \
  --cluster "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --namespace kube-system \
  --name cluster-autoscaler \
  --attach-policy-arn "$POLICY_ARN" \
  --approve
```

If the ServiceAccount already exists, inspect it before re-running the command. Do not create competing ServiceAccount resources from both eksctl and a separate manifest.

### 4.4 Deploy Cluster Autoscaler

Copy `cluster-autoscaler/cluster-autoscaler-deployment.yaml` and replace:

- `<CLUSTER_NAME>` with the EKS cluster name
- `<K8S_MINOR_VERSION>` with the cluster's Kubernetes major/minor version (for example, `1.XX`)
- `<CLUSTER_AUTOSCALER_PATCH_VERSION>` with a compatible Cluster Autoscaler patch release

The Cluster Autoscaler image version must match the Kubernetes cluster minor version. Do not use `latest`.

Apply the manifest:

```bash
kubectl apply -f cluster-autoscaler/cluster-autoscaler-deployment.yaml
kubectl -n kube-system rollout status deployment/cluster-autoscaler
kubectl -n kube-system logs deployment/cluster-autoscaler --tail=100
```

The manifest uses `serviceAccountName: cluster-autoscaler`. Confirm that the ServiceAccount has the expected IAM role annotation:

```bash
kubectl -n kube-system get serviceaccount cluster-autoscaler -o yaml
```

## Part 5 — Deploy the sample application and test scale-out

The sample manifest creates a namespace, a LoadBalancer Service, and a Deployment with three replicas. It includes CPU and memory requests so the scheduler can make meaningful placement decisions.

```bash
kubectl apply -f sample-app/testing-cas.yaml
kubectl -n my-namespace get pods,svc
kubectl -n my-namespace describe service container-info-svc
```

Wait for the LoadBalancer Service to receive an external hostname/address. AWS load balancer provisioning can take several minutes.

### Subnet discovery and tags

If the Service remains in `Pending`, inspect its events and the AWS load balancer controller/cloud provider prerequisites. EKS subnet discovery depends on appropriate subnet tags and network configuration.

Typical role tags:

- Public load balancer subnets: `kubernetes.io/role/elb = 1`
- Internal load balancer subnets: `kubernetes.io/role/internal-elb = 1`

Depending on the cluster and controller setup, cluster ownership tags may also be required:

- `kubernetes.io/cluster/<CLUSTER_NAME> = shared` or `owned`

Use the exact requirements for your load balancer controller and AWS configuration. See [EKS subnet discovery troubleshooting](https://repost.aws/knowledge-center/eks-vpc-subnet-discovery).

### Trigger a scale-out event

The managed node group's maximum size must be greater than its current size. In this lab it is set to 3. Increase the sample Deployment replicas:

```bash
kubectl -n my-namespace scale deployment/container-info-deploy --replicas=30
kubectl -n my-namespace get pods --watch
```

In another terminal:

```bash
kubectl get nodes --watch
kubectl -n kube-system logs deployment/cluster-autoscaler --follow
```

Inspect a Pending Pod:

```bash
kubectl -n my-namespace describe pod POD_NAME
```

Look at the scheduling events for insufficient CPU/memory or other constraints. When Cluster Autoscaler detects unschedulable Pods and a matching node group can scale, it increases the desired capacity. New EC2 instances take time to launch and join the cluster.

If scale-out does not occur, check:

- Node group maximum size and EC2 service quotas
- Auto Scaling Group discovery tags
- Cluster Autoscaler version compatibility
- IRSA trust relationship and IAM policy
- Pod resource requests and node allocatable capacity
- Node selectors, taints/tolerations, affinity, and topology constraints
- Cluster Autoscaler logs and Kubernetes events

## Cleanup — avoid ongoing AWS charges

Delete the sample workload and LoadBalancer Service first:

```bash
kubectl delete -f sample-app/testing-cas.yaml
```

Wait for the AWS load balancer to be deleted. Then remove Cluster Autoscaler:

```bash
kubectl delete -f cluster-autoscaler/cluster-autoscaler-deployment.yaml
eksctl delete iamserviceaccount \
  --cluster "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --namespace kube-system \
  --name cluster-autoscaler
```

Finally delete the EKS cluster and its managed node group:

```bash
eksctl delete cluster --name "$CLUSTER_NAME" --region "$AWS_REGION"
```

Check the AWS Console for leftover load balancers, NAT gateways, EBS volumes, Elastic IPs, and CloudWatch log groups. Delete only resources created for this lab and no longer needed.

## References

- [Amazon EKS pricing](https://aws.amazon.com/eks/pricing/)
- [EKS Kubernetes versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html)
- [Install kubectl for EKS](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html)
- [EKS node IAM role](https://docs.aws.amazon.com/eks/latest/userguide/create-node-role.html)
- [EKS Cluster Autoscaler best practices](https://docs.aws.amazon.com/eks/latest/best-practices/cas.html)
- [Cluster Autoscaler releases](https://github.com/kubernetes/autoscaler/releases)
- [EKS AL2 AMI deprecation](https://docs.aws.amazon.com/eks/latest/userguide/eks-ami-deprecation-faqs.html)
