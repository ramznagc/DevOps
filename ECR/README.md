# Amazon ECR Hands-on — Build, Push, Pull and Manage Docker Images

A practical exercise for working with **Amazon Elastic Container Registry (ECR)**. You will provision a Docker host with Terraform, create private ECR repositories from the AWS Console and AWS CLI, then build, tag, push, pull and remove container images.

> **Scope:** This lab is designed for learning. Review AWS costs, permissions and network exposure before running it in a real account. The sample application repository and its dependencies are external to this repository.

## Learning objectives

By the end of this lab, you will be able to:

- Provision an Amazon Linux 2023 EC2 Docker host with Terraform.
- Explain ECR registries, repositories, image tags and image URIs.
- Create and configure private ECR repositories using the Console and AWS CLI.
- Authenticate Docker to ECR using an IAM instance role.
- Build a Docker image and push/pull it from ECR.
- Compare mutable and immutable image tags.
- Configure a repository lifecycle policy.
- Delete images and repositories safely.

## Repository contents

| File | Description |
|---|---|
| [ecr-ec2.tf](./ecr-ec2.tf) | Terraform configuration for the EC2 Docker host, security group and IAM role |

## Architecture

1. Terraform provisions an EC2 instance running Amazon Linux 2023.
2. The instance receives an IAM role with the ECR permissions needed for this lab.
3. Docker builds the sample ToDo application image.
4. The Docker CLI authenticates to the private ECR registry.
5. The image is tagged with the ECR repository URI and pushed.
6. The image can then be pulled and run from ECR.

## Prerequisites

- An AWS account and permissions to create EC2, IAM, security groups and ECR resources.
- Terraform CLI installed locally.
- An existing EC2 key pair in the AWS region you will use.
- The matching private key file available locally.
- AWS CLI installed locally if you want to inspect or clean up resources from your workstation.
- Docker installed on the EC2 host by the Terraform user data.

**Cost note:** EC2, EBS storage, public IPv4 addresses, ECR image storage and data transfer may incur charges. Delete the lab resources when finished.

## Part 1 — Provision the Docker host with Terraform

### 1. Configure variables

Create a `terraform.tfvars` file in this directory (do not commit private values):

```hcl
aws_region       = "us-east-1"
project_name     = "ecr-hands-on"
instance_type    = "t3.medium"
key_name         = "YOUR_EXISTING_KEY_PAIR_NAME"
ssh_allowed_cidr = "YOUR_PUBLIC_IP/32"
```

Replace the key pair name and SSH CIDR. **Do not leave SSH open to the whole internet**; use your public IP with a `/32` mask.

### 2. Initialize, review and apply

```bash
terraform init
terraform fmt -check
terraform validate
terraform plan
terraform apply
```

Save the outputs:

```bash
terraform output
```

### 3. Connect to EC2

Use the `ssh_command` output, substituting the local path to your private key:

```bash
ssh -i ~/.ssh/YOUR_KEY.pem ec2-user@<EC2_PUBLIC_IP>
```

Verify the tools:

```bash
docker --version
docker-compose --version
aws --version
```

If the Docker group membership was just applied, reconnect to the instance before running Docker without `sudo`.

### Terraform resources

- **AMI data source:** selects the latest Amazon Linux 2023 x86_64 image published by Amazon.
- **Security group:** allows HTTP on port 80 and SSH only from the configured CIDR.
- **IAM role and instance profile:** let the EC2 instance authenticate to ECR without storing access keys on the host.
- **EC2 instance:** installs Docker, AWS CLI and the Docker Compose standalone binary.
- **Outputs:** provide the public IP, application URL and SSH command.

The IAM policy is intended for this training workflow. For production, scope repository permissions to known repository ARNs and separate repository administration from image push/pull permissions.

## Part 2 — Create ECR repositories in the AWS Console

1. Open **Amazon Elastic Container Registry (ECR)** in the same region as the EC2 host.
2. Select **Private registry → Repositories → Create repository**.
3. Create the first repository:

   ```text
   student1-repo/todo-app
   ```

4. Review these settings:
   - **Visibility:** Private.
   - **Image tag mutability:** Mutable for the first exercise.
   - **Encryption:** AES-256 (default).
   - **Scan on push:** this lab turns it off to match the original exercise. For real workloads, enable image scanning and act on findings.
5. Create the repository and copy its URI.

An ECR image URI has this form:

```text
<AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com/<REPOSITORY>:<TAG>
```

Example:

```text
123456789012.dkr.ecr.us-east-1.amazonaws.com/student1-repo/todo-app:latest
```

The account ID and region above are placeholders; use the values shown in your AWS account.

### Repository naming and namespaces

Repository names can contain a namespace-like prefix. For example, `team-a/web-app` and `team-b/web-app` are distinct repositories in the same registry.

### Configure a lifecycle policy

A lifecycle policy expires images that match rules you define. In the repository view, open **Lifecycle Policy**, create a rule, and configure:

- Rule priority (for example, `1`).
- A clear description.
- Image status: tagged, untagged or any.
- Tag pattern/prefix if applicable.
- An age-based or image-count matching criterion.

Review the rule carefully before saving. Lifecycle actions are asynchronous; do not assume an image disappears immediately. Check the current ECR lifecycle policy documentation for evaluation timing and rule behavior.

## Part 3 — Authenticate Docker to ECR

Connect to the EC2 host. The attached instance role supplies temporary credentials to the AWS CLI; do not configure long-lived access keys on the instance.

Set the region and retrieve the registry account ID:

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
```

Authenticate Docker:

```bash
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"
```

A successful login prints `Login Succeeded`. ECR authorization tokens are temporary; authenticate again when the token expires.

## Part 4 — Build and run the sample ToDo application

The original training exercise uses a sample Node.js ToDo application archive. Download it onto the EC2 instance:

```bash
curl -fL \
  https://github.com/awsdevopsteam/jenkins-first-project/raw/master/to-do-app-nodejs.tar \
  -o to-do-app-nodejs.tar

tar -xvf to-do-app-nodejs.tar
cd to-do-app-nodejs
```

> **Dependency note:** the original exercise used Node.js 12, which is end-of-life. For a maintained application, update the Dockerfile to a currently supported Node.js LTS release and verify compatibility with the project's dependencies before building. The Dockerfile below uses Node.js 20 as an example; it may require dependency updates in this legacy sample.

Create a `Dockerfile`:

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY . .
RUN yarn install --production
EXPOSE 3000
CMD ["node", "/app/src/index.js"]
```

Build the image:

```bash
docker build -t todo-app:latest .
docker image ls
```

Run it locally and test the application at the EC2 public IP:

```bash
docker run --name todo-local -d -p 80:3000 todo-app:latest
docker ps
```

Open `http://<EC2_PUBLIC_IP>` in your browser. Then stop and remove the local container:

```bash
docker stop todo-local
docker rm todo-local
```

## Part 5 — Tag and push the image to ECR

Set the repository name and image URI:

```bash
export REPOSITORY=student1-repo/todo-app
export IMAGE_URI="$ECR_REGISTRY/$REPOSITORY:latest"
```

Tag and push:

```bash
docker tag todo-app:latest "$IMAGE_URI"
docker push "$IMAGE_URI"
```

Refresh the repository in the ECR Console and inspect the image tag and digest.

## Part 6 — Pull and run the image from ECR

Remove the local image to demonstrate that the next run uses the registry copy:

```bash
docker image rm "$IMAGE_URI" todo-app:latest
docker pull "$IMAGE_URI"
docker run --name todo-from-ecr -d -p 80:3000 "$IMAGE_URI"
```

Test the application again, then clean up:

```bash
docker stop todo-from-ecr
docker rm todo-from-ecr
```

## Part 7 — Update an image and understand tag mutability

1. Change the sample application's UI text in `src/static/js/app.js`.
2. Rebuild the image:

   ```bash
   docker build -t todo-app:latest .
   ```

3. Push the updated image using the same `latest` tag:

   ```bash
   docker tag todo-app:latest "$IMAGE_URI"
   docker push "$IMAGE_URI"
   ```

4. Pull and run the updated image, then verify the browser output.

A **mutable** tag can be moved to point to a different image digest. An **immutable** tag cannot be overwritten while that tag exists. Prefer unique version tags (for example, `1.0.1` or a Git commit SHA) for traceable releases; do not rely on `latest` as a release identifier.

## Part 8 — Create a second repository with AWS CLI

Create a repository configured for immutable tags:

```bash
aws ecr create-repository \
  --repository-name student2-repo/todo-app \
  --image-scanning-configuration scanOnPush=false \
  --image-tag-mutability IMMUTABLE \
  --region "$AWS_REGION"
```

Set its URI, tag the local image and push it:

```bash
export REPOSITORY_2=student2-repo/todo-app
export IMAGE_URI_2="$ECR_REGISTRY/$REPOSITORY_2:1.0.0"

docker tag todo-app:latest "$IMAGE_URI_2"
docker push "$IMAGE_URI_2"
```

Because this repository uses immutable tags, pushing another image with the already-used `1.0.0` tag will fail. Use a new version tag for each subsequent image.

## Part 9 — Pull, run and delete images

Remove local copies and confirm that the image is no longer present:

```bash
docker image ls
docker image rm todo-app:latest "$IMAGE_URI_2"
docker image ls
```

Pull and run the image from the second repository:

```bash
docker pull "$IMAGE_URI_2"
docker run --name todo-v1 -d -p 80:3000 "$IMAGE_URI_2"
```

Test `http://<EC2_PUBLIC_IP>`, then stop and remove the container:

```bash
docker stop todo-v1
docker rm todo-v1
```

Delete the image tag and repository using AWS CLI:

```bash
aws ecr batch-delete-image \
  --repository-name "$REPOSITORY_2" \
  --image-ids imageTag=1.0.0 \
  --region "$AWS_REGION"

aws ecr delete-repository \
  --repository-name "$REPOSITORY_2" \
  --force \
  --region "$AWS_REGION"
```

You can also delete the first repository and its images from the ECR Console. Deleting a repository with images requires deleting the images first or choosing the force option in the CLI.

## Part 10 — Clean up AWS resources

From the directory containing the Terraform configuration:

```bash
terraform destroy
```

Before destroying the EC2 host, make sure you have deleted any ECR repositories and images you created. ECR repositories are not managed by this Terraform configuration and will remain until you delete them separately.

## Troubleshooting

| Symptom | Checks |
|---|---|
| `AccessDeniedException` | Confirm the EC2 instance profile is attached and the role has the required ECR permissions. |
| `no basic auth credentials` | Run the ECR Docker login command again for the correct region and registry. |
| `repository does not exist` | Verify the account ID, region and repository name. |
| Push rejected for immutable tag | Push with a new, unused tag. |
| Cannot connect over SSH | Check the key pair, instance state and `ssh_allowed_cidr` security-group rule. |
| Application is unreachable | Check container status, port mapping, application logs and the security-group HTTP rule. |

Useful diagnostics:

```bash
aws sts get-caller-identity
aws ecr describe-repositories --region "$AWS_REGION"
docker logs <CONTAINER_NAME>
```

---

**Lab complete:** You have provisioned a Docker host, created ECR repositories through both the Console and CLI, and practiced building, tagging, pushing, pulling, running and deleting container images.
