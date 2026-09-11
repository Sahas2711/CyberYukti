#!/usr/bin/env bash
###########################################################################
# destroy-aws.sh — delete the CyberYukti CloudFormation stack so all
# hackathon resources (EC2, EIP-less public IP, SG, VPC resources, IAM
# role/profile) are terminated immediately and billing stops.
#
# Usage:
#   ./scripts/destroy-aws.sh                    # STACK_NAME=cyberyukti-demo
#   STACK_NAME=other ./scripts/destroy-aws.sh
###########################################################################
set -euo pipefail

STACK_NAME="${STACK_NAME:-cyberyukti-demo}"
REGION="${AWS_REGION:-$(aws configure get region 2>/dev/null || echo ap-south-1)}"

command -v aws >/dev/null || { echo "aws CLI not found" >&2; exit 1; }

if ! aws --region "$REGION" cloudformation describe-stacks \
    --stack-name "$STACK_NAME" >/dev/null 2>&1; then
  echo "stack '$STACK_NAME' does not exist in $REGION — nothing to do"
  exit 0
fi

echo "==> Deleting stack '$STACK_NAME' in $REGION (terminates the EC2 instance)..."
aws --region "$REGION" cloudformation delete-stack --stack-name "$STACK_NAME"

echo "==> Waiting for deletion (2-4 minutes)..."
if aws --region "$REGION" cloudformation wait stack-delete-complete \
    --stack-name "$STACK_NAME" 2>/dev/null; then
  echo "==> Stack deleted. All resources terminated, billing stopped."
else
  echo "WARNING: deletion incomplete — check for failed resources in the console." >&2
  exit 1
fi
