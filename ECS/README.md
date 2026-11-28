# Amazon ECS Hands-on — Deploy a Containerized App with AWS Fargate

A practical, end-to-end introduction to **Amazon Elastic Container Service (ECS)**. You will build a small ToDo web app, package it as a Docker image, publish it to Amazon ECR, and run it as an ECS service on AWS Fargate.

> **Cost and safety:** ECS/Fargate tasks, public IPv4 addresses, load balancers, NAT gateways, ECR storage and CloudWatch Logs can incur charges. This lab uses a public Fargate task for simplicity. Restrict inbound traffic to your own IP, and delete all resources when finished.

## Learning objectives

- Explain ECS clusters, task definitions, tasks, services, capacity providers and launch types.
- Containerize and run the sample application locally.
- Publish a tagged image to Amazon ECR.
- Understand the ECS task execution role versus the application task role.
- Deploy and update a Fargate service with the AWS Console and AWS CLI.
- Configure networking, container health checks, logs and desired task count.
- Inspect service events and troubleshoot tasks.
- Clean up AWS resources safely.

## Repository layout

```text
ECS/
├── README.md
├── app/
│   ├── app.py
│   └── Dockerfile
├── cloudformation/
│   └── docker-host.yaml
└── ecs/
    ├── task-definition.json
    └── deploy.sh
```

## Architecture

```text
Developer
   |
   | docker build / push
   v
Amazon ECR (private image repository)
   |
   | ECS task execution role pulls image
   v
ECS Cluster
   |
   v
Fargate Service ---- desired count: 1+
   |
   v
Fargate Task [ToDo container :8080]
   |
   +---- CloudWatch Logs
   +---- Container health check
```

## Prerequisites

- An AWS account and an IAM identity permitted to create/manage ECR, ECS, IAM roles, EC2 networking and CloudWatch Logs.
- AWS CLI v2 configured locally: `aws configure` or (preferably) AWS IAM Identity Center / an assumed role.
- Docker Engine or Docker Desktop.
- `curl`, `jq`, and a shell compatible with Bash for the CLI lab.
- A VPC with public subnets and internet access for the simple public-task deployment.

Set the region once; examples use `us-east-1`:

```bash
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION="$AWS_REGION"
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
export ECR_REPOSITORY=ecs-todo
export IMAGE_TAG=v1
export IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"
```

Verify the identity and region before creating resources:

```bash
aws sts get-caller-identity
aws configure get region
```

## Part 1 — Build and test the sample application

The app is intentionally small: a browser-based ToDo list backed by a tiny in-memory API. Tasks reset when the container restarts; this is a teaching example, not a persistent production application.

From the repository root:

```bash
cd ECS/app
docker build -t ecs-todo:$IMAGE_TAG .
docker run --rm -d --name ecs-todo-local -p 8080:8080 ecs-todo:$IMAGE_TAG
curl -i http://localhost:8080/healthz
```

Open [http://localhost:8080](http://localhost:8080), add a task, and verify that the list updates.

Stop the local container:

```bash
docker stop ecs-todo-local
```

The container listens on port **8080**. Keep this port consistent in the Dockerfile, ECS task definition, security group and service configuration.

## Part 2 — Create an ECR repository and push the image

Create a private repository:

```bash
aws ecr create-repository \
  --repository-name "$ECR_REPOSITORY" \
  --image-scanning-configuration scanOnPush=true \
  --image-tag-mutability IMMUTABLE \
  --region "$AWS_REGION"
```

Authenticate Docker to the registry. This command obtains a short-lived ECR login token; do not paste credentials into scripts or source control.

```bash
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin \
    "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
```

Tag and push:

```bash
docker tag "ecs-todo:$IMAGE_TAG" "$IMAGE_URI:$IMAGE_TAG"
docker push "$IMAGE_URI:$IMAGE_TAG"
aws ecr describe-images --repository-name "$ECR_REPOSITORY" \
  --query 'imageDetails[*].[imageTags,imageDigest,imagePushedAt]' --output table
```

For a new release, build and push a new immutable tag (for example, `v2`). Avoid reusing `latest` in deployments because immutable tags cannot be overwritten and versioned tags make rollbacks easier.

## Part 3 — Create ECS IAM roles

ECS uses two different task roles:

- **Task execution role**: used by the ECS/Fargate agent to pull private ECR images, publish logs, and retrieve supported startup secrets. Attach the AWS-managed `AmazonECSTaskExecutionRolePolicy`.
- **Task role**: credentials made available to application code inside the container when it calls AWS APIs. This sample app does not call AWS APIs, so no application task role is required.

Create the execution role in IAM:

1. Create a role for the **Elastic Container Service Task** trusted entity.
2. Attach `AmazonECSTaskExecutionRolePolicy`.
3. Name it `ecsTaskExecutionRole`.
4. Copy its ARN for the task definition.

The trust relationship must allow `ecs-tasks.amazonaws.com` to assume the role. Do not attach the execution role to the EC2 host or use administrator permissions as a shortcut.

## Part 4 — Deploy with the AWS Console

### Create a cluster

1. Open the [Amazon ECS console](https://console.aws.amazon.com/ecs/v2/clusters).
2. Choose **Create cluster**.
3. Enter `ecs-todo-cluster`.
4. Use the default networking/monitoring options and create the cluster. Fargate does not require you to provision or manage EC2 container instances.

### Register a task definition

1. Open **Task definitions → Create new task definition**.
2. Family: `ecs-todo`.
3. Launch type compatibility: AWS Fargate.
4. OS/Architecture: Linux/X86_64.
5. Network mode: `awsvpc`.
6. CPU: `0.25 vCPU`; Memory: `0.5 GB` (increase if your app needs more).
7. Container name: `ecs-todo`; image: the full `$IMAGE_URI:$IMAGE_TAG` URI.
8. Container port: `8080` / TCP.
9. Add the execution role created in Part 3.
10. Configure awslogs using log group `/ecs/ecs-todo`, region `$AWS_REGION`, stream prefix `ecs`. Create the log group first if needed:
   `aws logs create-log-group --log-group-name /ecs/ecs-todo`
11. Add a container health check: command `CMD-SHELL,curl -fsS http://localhost:8080/healthz || exit 1`, interval 30s, timeout 5s, retries 3, start period 10s.
12. Review and create the task definition.

### Create the service

1. Open `ecs-todo-cluster` and choose **Create → Service**.
2. Compute options: capacity provider strategy / Fargate.
3. Select the `ecs-todo` task definition family and its latest revision.
4. Service name: `ecs-todo-service`; desired tasks: `1`.
5. Select your VPC and public subnets.
6. For this learning lab only, enable **Auto-assign public IP**.
7. Select or create a security group that allows inbound TCP **8080 only from your public IP** (for example, `203.0.113.10/32`; replace this documentation address).
8. Create the service and wait until the task is **RUNNING** and the service is stable.
9. Open the task details, copy its public IP, and browse to `http://PUBLIC_IP:8080`.

For a production design, place tasks in private subnets and expose the service through an Application Load Balancer (ALB) or another managed ingress layer. Do not leave application ports open to the entire internet.

## Part 5 — Deploy with the AWS CLI

### Create the cluster and log group

```bash
aws ecs create-cluster --cluster-name ecs-todo-cluster
aws logs create-log-group --log-group-name /ecs/ecs-todo 2>/dev/null || true
```

### Prepare the task definition

Copy `ecs/task-definition.json` and replace the placeholders:

- `ACCOUNT_ID`: your AWS account ID.
- `REGION`: selected AWS region.
- `EXECUTION_ROLE_ARN`: ARN of `ecsTaskExecutionRole`.
- The image tag must exist in ECR.

Register it:

```bash
aws ecs register-task-definition --cli-input-json file://ecs/task-definition.json
```

### Create a service

Find your VPC and public subnet IDs:

```bash
aws ec2 describe-subnets --filters "Name=default-for-az,Values=true" \
  --query 'Subnets[*].[SubnetId,VpcId,AvailabilityZone]' --output table
```

Create a dedicated security group in the chosen VPC and allow TCP/8080 from your own public IP only. Then set these environment variables:

```bash
export ECS_CLUSTER=ecs-todo-cluster
export ECS_SERVICE=ecs-todo-service
export SUBNET_IDS=subnet-xxxxxxxx,subnet-yyyyyyyy
export SECURITY_GROUP_ID=sg-xxxxxxxx
```

Run the included deployment helper after reviewing it:

```bash
chmod +x ecs/deploy.sh
./ecs/deploy.sh
```

The helper creates or updates a Fargate service with public IP assignment. It does not create your VPC, subnets, security group, IAM role or ECR repository; those are explicit prerequisites. Check the service:

```bash
aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" \
  --query 'services[0].[status,runningCount,desiredCount,events[0].message]' --output table
aws ecs list-tasks --cluster "$ECS_CLUSTER" --service-name "$ECS_SERVICE"
```

## Part 6 — Release a new version

Make a small change in `app/app.py`, then build and push a new immutable image tag:

```bash
export IMAGE_TAG=v2
docker build -t "ecs-todo:$IMAGE_TAG" ./app
docker tag "ecs-todo:$IMAGE_TAG" "$IMAGE_URI:$IMAGE_TAG"
docker push "$IMAGE_URI:$IMAGE_TAG"
```

Update the task definition image to `$IMAGE_URI:v2`, register a new revision, then update the service:

```bash
aws ecs register-task-definition --cli-input-json file://ecs/task-definition.json
aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" \
  --task-definition ecs-todo
aws ecs wait services-stable --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE"
```

Check deployment status and service events in the ECS console or with `describe-services`. ECS performs a rolling deployment according to the service deployment configuration.

## Part 7 — Troubleshooting

| Symptom | What to inspect |
|---|---|
| Task stops immediately | ECS task **Stopped reason**, container exit code, CloudWatch logs |
| Cannot pull image | Image URI/tag, execution role trust and policy, ECR region/account |
| Task is pending | Subnet IP capacity, Fargate capacity, quotas, service events |
| App is unreachable | Public IP assignment, route to internet gateway, security group, port 8080 |
| Health check fails | Container port, `/healthz`, command availability, startup time |
| Service cannot stabilize | `aws ecs describe-services` events and stopped task details |

Useful commands:

```bash
aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE"
aws ecs list-tasks --cluster "$ECS_CLUSTER" --service-name "$ECS_SERVICE"
aws ecs describe-tasks --cluster "$ECS_CLUSTER" --tasks <TASK_ARN>
aws logs tail /ecs/ecs-todo --follow
```

## Part 8 — Clean up

Delete the service first, then the cluster and ECR image/repository:

```bash
aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" --desired-count 0
aws ecs delete-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE"
aws ecs delete-cluster --cluster "$ECS_CLUSTER"
aws ecr batch-delete-image --repository-name "$ECR_REPOSITORY" \
  --image-ids "$(aws ecr list-images --repository-name "$ECR_REPOSITORY" \
    --query 'imageIds[*]' --output json)" 2>/dev/null || true
aws ecr delete-repository --repository-name "$ECR_REPOSITORY" --force
aws logs delete-log-group --log-group-name /ecs/ecs-todo
```

Also remove the security group created for this lab. If you created a load balancer, target group, NAT gateway or other networking resources, delete those too. Check the AWS Billing console after cleanup.

## Optional — AWS Copilot

The source lesson includes AWS Copilot CLI as an alternative workflow. Treat Copilot as an optional/legacy path and verify its current maintenance and support status in the official AWS documentation before adopting it for a new project. The primary, reproducible deployment path in this repository is ECS + Fargate through the AWS Console and AWS CLI.

## Additional learning

- [Amazon ECS Developer Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html)
- [AWS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/userguide/what-is-fargate.html)
- [Amazon ECR User Guide](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html)
- [ECS task execution IAM role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)

---

*This lab is an educational example. Validate IAM permissions, networking, application behavior and cost controls in your own AWS environment before using the pattern in production.*
