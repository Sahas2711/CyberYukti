#!/usr/bin/env bash
###########################################################################
# update-ec2.sh — RUNS ON YOUR LAPTOP. Triggers the on-instance
# build+deploy (scripts/ec2-deploy.sh) on the EC2 box via SSM, waits for
# it, and streams the output. Run this after every push you want live.
#
# Usage:
#   ./scripts/update-ec2.sh                     # defaults below
#   BRANCH=main ./scripts/update-ec2.sh
#   INSTANCE_ID=i-xxx ./scripts/update-ec2.sh
#
# Env:
#   STACK_NAME   CloudFormation stack   (default: cyberyukti-demo)
#   INSTANCE_ID  EC2 id                 (default: auto from stack outputs)
#   BRANCH       branch to deploy       (default: github-dockerhub-analysis)
#   APP_PORT     host port              (default: 80)
###########################################################################
set -euo pipefail

STACK_NAME="${STACK_NAME:-cyberyukti-demo}"
REGION="${AWS_REGION:-$(aws configure get region 2>/dev/null || echo ap-south-1)}"
BRANCH="${BRANCH:-github-dockerhub-analysis}"
APP_PORT="${APP_PORT:-80}"

command -v aws >/dev/null || { echo "aws CLI not found" >&2; exit 1; }

INSTANCE_ID="${INSTANCE_ID:-$(aws --region "$REGION" cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='InstanceId'].OutputValue" --output text)}"

[ "$INSTANCE_ID" = "None" ] && { echo "no instance found for stack $STACK_NAME — run scripts/deploy-aws.sh first" >&2; exit 1; }

echo "==> Updating EC2 instance $INSTANCE_ID from branch '$BRANCH' (build + deploy on-instance)..."

# The deploy script lives in the repo, so fetch it straight from GitHub.
# (shellcheck disable=SC2086)
CMD_ID=$(aws --region "$REGION" ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --comment "CyberYukti build+deploy branch=$BRANCH" \
  --timeout-seconds 1800 \
  --parameters commands="[
    \"dnf install -y git curl >/dev/null 2>&1 || true\",
    \"mkdir -p /opt && curl -fsSL https://raw.githubusercontent.com/Sahas2711/CyberYukti/${BRANCH}/scripts/ec2-deploy.sh -o /opt/ec2-deploy.sh && chmod +x /opt/ec2-deploy.sh\",
    \"BRANCH='$BRANCH' APP_PORT='$APP_PORT' /opt/ec2-deploy.sh\"
  ]" \
  --query "Command.CommandId" --output text)

echo "==> SSM command: $CMD_ID (on-instance build takes ~5-10 min)"
echo "==> Watching..."

for i in $(seq 1 240); do
  STATUS=$(aws --region "$REGION" ssm get-command-invocation \
    --command-id "$CMD_ID" --instance-id "$INSTANCE_ID" \
    --query Status --output text 2>/dev/null || echo "Pending")
  case "$STATUS" in
    Success)
      echo "==> DEPLOY SUCCEEDED"
      aws --region "$REGION" ssm get-command-invocation --command-id "$CMD_ID" \
        --instance-id "$INSTANCE_ID" --query StandardOutputContent --output text | tail -15
      IP=$(aws --region "$REGION" cloudformation describe-stacks --stack-name "$STACK_NAME" \
        --query "Stacks[0].Outputs[?OutputKey=='PublicIP'].OutputValue" --output text)
      echo "==> http://$IP/  (docs: http://$IP/docs)"
      exit 0
      ;;
    Failed|Cancelled|TimedOut)
      echo "==> DEPLOY FAILED ($STATUS):"
      aws --region "$REGION" ssm get-command-invocation --command-id "$CMD_ID" \
        --instance-id "$INSTANCE_ID" \
        --query "{stderr:StandardErrorContent, stdout:StandardOutputContent}" --output text | tail -40
      exit 1
      ;;
    *) sleep 5 ;;
  esac
done

echo "timed out waiting for SSM command" >&2
exit 1
