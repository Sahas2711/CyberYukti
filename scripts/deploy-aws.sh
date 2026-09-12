#!/usr/bin/env bash
###########################################################################
# deploy-aws.sh — create/update the CyberYukti CloudFormation stack and
# wait until the instance is up and the app passes its health check.
#
# Usage:
#   ./scripts/deploy-aws.sh                      # defaults below
#   STACK_NAME=cyberyukti IMAGE=sahasnagar/cyberyukti:latest ./scripts/deploy-aws.sh
#
# Requirements: AWS CLI v2 configured (SSO/keys/whatever), curl.
###########################################################################
set -euo pipefail

STACK_NAME="${STACK_NAME:-cyberyukti-demo}"
REGION="${AWS_REGION:-$(aws configure get region 2>/dev/null || echo ap-south-1)}"
IMAGE="${IMAGE:-sahasnagar/cyberyukti:latest}"
INSTANCE_TYPE="${INSTANCE_TYPE:-t3.micro}"
TEMPLATE="infra/cloudformation/cyberyukti-ec2.yaml"

command -v aws >/dev/null || { echo "aws CLI not found" >&2; exit 1; }
[ -f "$TEMPLATE" ] || { echo "template not found: $TEMPLATE (run from repo root)" >&2; exit 1; }

echo "==> Stack:      $STACK_NAME"
echo "==> Region:     $REGION"
echo "==> Image:      $IMAGE"
echo "==> Instance:   $INSTANCE_TYPE"

echo "==> Validating template..."
aws --region "$REGION" cloudformation validate-template \
  --template-body "file://$TEMPLATE" >/dev/null
echo "    template OK"

echo "==> Creating/updating stack (this takes ~3-5 min)..."
if aws --region "$REGION" cloudformation describe-stacks \
    --stack-name "$STACK_NAME" >/dev/null 2>&1; then
  aws --region "$REGION" cloudformation update-stack \
    --stack-name "$STACK_NAME" \
    --template-body "file://$TEMPLATE" \
    --parameters \
      ParameterKey=ContainerImage,ParameterValue="$IMAGE" \
      ParameterKey=InstanceType,ParameterValue="$INSTANCE_TYPE" \
    --capabilities CAPABILITY_NAMED_IAM >/dev/null
  WAIT="stack-update-complete"
else
  aws --region "$REGION" cloudformation create-stack \
    --stack-name "$STACK_NAME" \
    --template-body "file://$TEMPLATE" \
    --parameters \
      ParameterKey=ContainerImage,ParameterValue="$IMAGE" \
      ParameterKey=InstanceType,ParameterValue="$INSTANCE_TYPE" \
    --capabilities CAPABILITY_NAMED_IAM \
    --tags Key=project,Value=cyberyukti Key=ttl,Value=hackathon-demo >/dev/null
  WAIT="stack-create-complete"
fi

echo "==> Waiting for $WAIT ..."
aws --region "$REGION" cloudformation wait "$WAIT" --stack-name "$STACK_NAME" \
  || { echo "stack did not reach a complete state — check the console/events" >&2; exit 1; }

echo "==> Fetching outputs..."
INSTANCE_ID=$(aws --region "$REGION" cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='InstanceId'].OutputValue" --output text)
PUBLIC_IP=$(aws --region "$REGION" cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='PublicIP'].OutputValue" --output text)

echo "    Instance : $INSTANCE_ID"
echo "    Public IP: $PUBLIC_IP"

echo "==> Waiting for instance to bootstrap (Docker install + pull + health check)..."
echo "    (bootstrap log: aws ssm start-session --target $INSTANCE_ID, then tail /var/log/cyberyukti-bootstrap.log)"
for i in $(seq 1 40); do
  if curl -fsS --max-time 5 "http://$PUBLIC_IP/api/health" >/dev/null 2>&1; then
    echo "==> HEALTH CHECK PASSED: http://$PUBLIC_IP/  (docs: http://$PUBLIC_IP/docs)"
    exit 0
  fi
  echo "    attempt $i: app not up yet..."
  sleep 10
done

echo "WARNING: app did not answer /api/health within ~6-7 minutes." >&2
echo "Debug: aws --region $REGION ssm start-session --target $INSTANCE_ID" >&2
exit 1
