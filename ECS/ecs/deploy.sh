#!/usr/bin/env bash
set -Eeuo pipefail

: "${AWS_REGION:?Set AWS_REGION}"
: "${AWS_ACCOUNT_ID:?Set AWS_ACCOUNT_ID}"
: "${SUBNET_IDS:?Set comma-separated SUBNET_IDS}"
: "${SECURITY_GROUP_ID:?Set SECURITY_GROUP_ID}"

CLUSTER="${ECS_CLUSTER:-ecs-todo-cluster}"
SERVICE="${ECS_SERVICE:-ecs-todo-service}"
TASK_FAMILY="${TASK_FAMILY:-ecs-todo}"
TASK_FILE="${TASK_FILE:-ecs/task-definition.json}"

echo "Registering task definition from $TASK_FILE"
aws ecs register-task-definition --cli-input-json "file://$TASK_FILE" >/dev/null

if aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].status' --output text 2>/dev/null | grep -q ACTIVE; then
  echo "Updating existing ECS service..."
  aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" \
    --task-definition "$TASK_FAMILY" >/dev/null
else
  echo "Creating ECS Fargate service..."
  aws ecs create-service \
    --cluster "$CLUSTER" \
    --service-name "$SERVICE" \
    --task-definition "$TASK_FAMILY" \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" >/dev/null
fi

aws ecs wait services-stable --cluster "$CLUSTER" --services "$SERVICE"
aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
  --query 'services[0].[status,runningCount,desiredCount]' --output table
echo "Deployment is stable. Retrieve the task public IP from ECS task details."
