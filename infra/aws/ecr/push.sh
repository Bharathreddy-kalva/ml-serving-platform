#!/usr/bin/env bash
# Build and push backend image to ECR.
# Usage: ./infra/aws/ecr/push.sh [git-sha-or-tag]

set -euo pipefail

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_REGION:-us-east-1}
REPO="mlserving-backend"
TAG=${1:-latest}
REGISTRY="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "$REGISTRY"

docker build -t "$REPO:$TAG" backend/
docker tag "$REPO:$TAG" "$REGISTRY/$REPO:$TAG"
docker push "$REGISTRY/$REPO:$TAG"

echo "Pushed $REGISTRY/$REPO:$TAG"
