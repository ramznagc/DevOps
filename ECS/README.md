# Amazon ECS Hands-on — Deploy a Containerized ToDo App on AWS Fargate

This lab takes a small Flask application from source code to a running Amazon ECS service. You will build and test the container locally, publish it to Amazon ECR, then deploy it to ECS on AWS Fargate.

> **Cost and safety:** ECS Fargate, an Application Load Balancer, NAT gateways, public IPv4 addresses, ECR storage, and CloudWatch Logs may incur charges. Use a dedicated lab account, review the resources created, and complete the cleanup section. Never commit AWS credentials, account-specific ARNs, subnet IDs, or security-group IDs.

## What you will build

```text
Browser
  |
  | HTTP :80
  v
Application Load Balancer
  |
  v
ECS Service (desired count: 1)
  |
  v
Fargate Task ---- pulls image ----> Amazon ECR
  |
  +---- logs ----------------------> CloudWatch Logs
```

The sample app is intentionally small: add and complete ToDo items, view a health endpoint, and see a version string. It stores data in process memory, so items are not durable and may disappear when a task is replaced. This is a container/ECS learning exercise, not a production data architecture.

## Learning objectives

By the end, you should be able to:

- Explain the relationship between an ECS cluster, task definition, task, and service.
- Build a Docker image and publish versioned tags to a private ECR repository.
- Distinguish the task execution role from the application task role.
- Deploy an ECS Fargate service with `awsvpc` networking.
- Expose an HTTP application through an Application Load Balancer.
- Inspect deployment state, container health, and CloudWatch logs.
- Roll out a new image and clean up AWS resources safely.

## Repository layout

```text
ECS/
├── README.md
├── app/
│   ├── app.py
│   └── templates/
│       └── index.html
├── Dockerfile
├── .dockerignore
├── requirements.txt
└── task-definition.template.json
```

## Prerequisites

- An AWS account and a configured AWS CLI v2 profile.
- Docker Engine.
- An IAM identity allowed to create/use ECR and ECS resources, pass the ECS task roles, and create or configure networking and load-balancing resources.
- A VPC with at least two subnets in different Availability Zones for an Application Load Balancer. For a public-facing lab, use public subnets with internet routing.
- An ECS task security group that permits inbound application traffic from the ALB security group only.
- An ALB security group that permits inbound HTTP from your test IP (or a suitably restricted CIDR).

Set the region once; use the same region throughout:

```bash
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION="$AWS_REGION"
export APP_NAME=ecs-todo
export ECR_REPOSITORY="$APP_NAME"
export ECS_CLUSTER="$APP_NAME-cluster"
export ECS_SERVICE="$APP_NAME-service"
export TASK_FAMILY="$APP_NAME-task"
export IMAGE_TAG=v1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY"
```

Confirm your identity and region:

```bash
aws sts get-caller-identity
aws configure get region
```

## Part 1 — Explore and run the application locally

The app source is in this folder. It uses Flask and listens on port `8080`.

```bash
cd ECS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/app.py
```

Open `http://localhost:8080`. Check health in another terminal:

```bash
curl -i http://localhost:8080/health
```

Stop the local server with `Ctrl+C`.

## Part 2 — Build and test the Docker image

```bash
docker build -t "$APP_NAME:$IMAGE_TAG" .
docker run --rm -d --name ecs-todo-local -p 8080:8080 "$APP_NAME:$IMAGE_TAG"
curl -i http://localhost:8080/health
docker logs ecs-todo-local
docker stop ecs-todo-local
```

The image runs as a non-root user and includes a Docker health check. The ECS task definition also declares a container health check; ECS health checks are evaluated inside the container.

## Part 3 — Create an ECR repository and push the image

Create a private repository (skip creation if it already exists):

```bash
aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" >/dev/null 2>&1 || \
  aws ecr create-repository \
    --repository-name "$ECR_REPOSITORY" \
    --image-tag-mutability IMMUTABLE \
    --image-scanning-configuration scanOnPush=true
```

Authenticate Docker to ECR and push the image:

```bash
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker tag "$APP_NAME:$IMAGE_TAG" "$ECR_URI:$IMAGE_TAG"
docker push "$ECR_URI:$IMAGE_TAG"
aws ecr describe-images --repository-name "$ECR_REPOSITORY"
```

Use a new tag for every release when the repository is immutable (for example, `v2`, `v3`). Avoid relying on `latest` for repeatable deployments.

## Part 4 — Prepare ECS IAM roles

Create or verify these IAM roles before deploying:

1. **Task execution role** — trusted by `ecs-tasks.amazonaws.com`, with the `AmazonECSTaskExecutionRolePolicy` managed policy. ECS/Fargate uses it to pull private ECR images and publish logs to CloudWatch.
2. **Task role** — trusted by `ecs-tasks.amazonaws.com`; grant only the AWS API permissions the application itself needs. This sample app calls no AWS APIs, so a task role is not required.

The role ARN for the execution role is referenced by the task definition. The role must exist in the same AWS account. Your deployment identity also needs `iam:PassRole` for the role.

## Part 5 — Create the ECS cluster

```bash
aws ecs create-cluster --cluster-name "$ECS_CLUSTER"
aws ecs describe-clusters --clusters "$ECS_CLUSTER"
```

For Fargate, you do not need to provision or manage EC2 container instances.

## Part 6 — Register the task definition

Copy the template and replace the placeholders. The template uses Fargate, `awsvpc`, 0.25 vCPU, 0.5 GiB memory, port 8080, and CloudWatch Logs.

```bash
export EXECUTION_ROLE_ARN=arn:aws:iam::$ACCOUNT_ID:role/ecsTaskExecutionRole
export LOG_GROUP="/ecs/$APP_NAME"

aws logs create-log-group --log-group-name "$LOG_GROUP" 2>/dev/null || true

sed \
  -e "s|TASK_FAMILY|$TASK_FAMILY|g" \
  -e "s|ACCOUNT_ID|$ACCOUNT_ID|g" \
  -e "s|AWS_REGION|$AWS_REGION|g" \
  -e "s|ECR_REPOSITORY|$ECR_REPOSITORY|g" \
  -e "s|IMAGE_TAG|$IMAGE_TAG|g" \
  -e "s|EXECUTION_ROLE_ARN|$EXECUTION_ROLE_ARN|g" \
  -e "s|LOG_GROUP|$LOG_GROUP|g" \
  task-definition.template.json > task-definition.json

aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs describe-task-definition --task-definition "$TASK_FAMILY"
```

The generated `task-definition.json` contains account-specific values; do not commit it.

## Part 7 — Deploy an ECS Fargate service

Choose your own networking values from your VPC. Do not copy example subnet or security-group IDs from another account.

```bash
export SUBNET_1=subnet-xxxxxxxx
export SUBNET_2=subnet-yyyyyyyy
export TASK_SECURITY_GROUP=sg-xxxxxxxx
export TARGET_GROUP_ARN=arn:aws:elasticloadbalancing:$AWS_REGION:$ACCOUNT_ID:targetgroup/your-target/xxxxxxxx
```

Create an Application Load Balancer and target group (or use an existing ALB). For Fargate with `awsvpc`, the target group target type must be **ip**, and its protocol/port must match the app (HTTP/8080). Configure the ALB listener to forward to this target group.

Create the ECS service:

```bash
aws ecs create-service \
  --cluster "$ECS_CLUSTER" \
  --service-name "$ECS_SERVICE" \
  --task-definition "$TASK_FAMILY" \
  --desired-count 1 \
  --launch-type FARGATE \
  --health-check-grace-period-seconds 60 \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$TASK_SECURITY_GROUP],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=$APP_NAME,containerPort=8080"
```

This example assumes the tasks run in private subnets with a route to ECR/CloudWatch through NAT or the appropriate VPC endpoints. If you use public subnets for a temporary lab, set `assignPublicIp=ENABLED` and ensure the subnet route table has an internet-gateway route. Keep the task security group inbound rule limited to TCP/8080 from the ALB security group.

Wait for the service to stabilize:

```bash
aws ecs wait services-stable --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE"
aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE"
```

Find the ALB DNS name in the EC2 Load Balancers console or with:

```bash
aws elbv2 describe-load-balancers --query 'LoadBalancers[].DNSName' --output text
```

Open `http://<ALB-DNS-NAME>` in a browser. The ALB target group should show healthy targets.

## Part 8 — Observe tasks, logs, and health

```bash
aws ecs list-tasks --cluster "$ECS_CLUSTER" --service-name "$ECS_SERVICE"
aws ecs describe-tasks --cluster "$ECS_CLUSTER" --tasks <TASK_ARN>
aws logs tail "$LOG_GROUP" --follow
```

Troubleshooting checklist:

- **CannotPullContainerError:** verify the image URI/tag, ECR repository region, execution role, and network path to ECR.
- **Task stops immediately:** inspect stopped reason and container exit code with `describe-tasks`; review CloudWatch logs.
- **ALB target unhealthy:** verify target type is `ip`, target port is 8080, app binds to `0.0.0.0`, health check path is `/health`, and task security group allows traffic from the ALB security group.
- **Service cannot place tasks:** verify subnet IP capacity, Fargate platform support, task CPU/memory combination, and subnet egress.

## Part 9 — Release an application update

Build and push a new immutable tag:

```bash
export IMAGE_TAG=v2
docker build -t "$APP_NAME:$IMAGE_TAG" .
docker tag "$APP_NAME:$IMAGE_TAG" "$ECR_URI:$IMAGE_TAG"
docker push "$ECR_URI:$IMAGE_TAG"
```

Render a new task definition revision using the updated `IMAGE_TAG`, then register it:

```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs update-service \
  --cluster "$ECS_CLUSTER" \
  --service "$ECS_SERVICE" \
  --task-definition "$TASK_FAMILY" \
  --force-new-deployment
aws ecs wait services-stable --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE"
```

For a real release workflow, keep task-definition revisions immutable and deploy the exact revision returned by `register-task-definition`. The ECS service performs a rolling deployment according to its deployment configuration.

## Part 10 — Cleanup

Delete resources in dependency order. The commands below remove the ECS service and cluster; they do **not** delete the ALB, target group, security groups, log group, IAM roles, or ECR repository.

```bash
aws ecs update-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE" --desired-count 0
aws ecs delete-service --cluster "$ECS_CLUSTER" --service "$ECS_SERVICE"
aws ecs delete-cluster --cluster "$ECS_CLUSTER"
```

Then, in the EC2 and VPC consoles (or using the corresponding ELB/VPC CLI commands), delete the ALB, listener, target group, and lab-only security groups after confirming they are not shared. Remove the log group if no longer needed:

```bash
aws logs delete-log-group --log-group-name "$LOG_GROUP"
```

Delete the ECR repository and all its images only if you no longer need them:

```bash
aws ecr delete-repository --repository-name "$ECR_REPOSITORY" --force
```

Delete lab-only IAM roles only after confirming no other workload uses them.

## Notes on the original training material

- The original lab's fixed subnet/security-group IDs and account placeholders are replaced with explicit variables; IDs are account- and VPC-specific.
- The sample listens on port 8080, so the Dockerfile, task definition, target group, and security-group rules use the same port consistently.
- The original Copilot section is not used as the primary deployment path. This lab uses the ECS AWS CLI directly so each AWS resource and setting is visible and reproducible. Check the current AWS Copilot project status and documentation before starting a new Copilot-based workflow.
- The app uses in-memory storage; use a database or persistent external service for durable application data.

## Further reading

- [Amazon ECS documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html)
- [Fargate task networking](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-networking.html)
- [ECS task execution IAM role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)
- [Amazon ECR user guide](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html)
