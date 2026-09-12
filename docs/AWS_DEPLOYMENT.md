# AWS Deployment (EC2 + CloudFormation)

Real, minimal deployment: **one t3.micro EC2 instance running the
`sahasnagar/cyberyukti` Docker image**. No ALB, no RDS, no ECS, no NAT,
no SSH keys (SSM Session Manager only).

## Architecture

```
Internet ──► EC2 t3.micro (public subnet, SG: 80+8000 open, no SSH)
              └── Docker
                    └── cyberyukti (UI + API on ONE port; Dockerfile EXPOSE 8000)
                          └── semgrep/trivy run as in-container subprocesses
                              (no docker socket mount needed)
```

## What gets created

| Resource | Notes |
|---|---|
| VPC + 1 public subnet + IGW + route table | 10.0.0.0/16, AZ-a |
| Security group | Inbound 80/tcp + 8000/tcp only; **no 22** |
| 1× t3.micro EC2 (Amazon Linux 2023) | Docker installed via UserData |
| IAM role + instance profile | `AmazonSSMManagedInstanceCore` only |
| CloudFront/Lambda/RDS/etc. | **none** |

## Deploy

```bash
./scripts/deploy-aws.sh          # STACK_NAME=cyberyukti-demo IMAGE=sahasnagar/cyberyukti:latest
```

The script validates the template, creates/updates the stack, waits for
`stack-create-complete`, then polls `http://<public-ip>/api/health` until the
app actually answers (or tells you how to debug via SSM).

To deploy a different image tag (e.g. what CI pushed):

```bash
IMAGE=sahasnagar/cyberyukti:$(git rev-parse --short HEAD) ./scripts/deploy-aws.sh
```

## Access the app

- UI: `http://<public-ip>/`
- API docs: `http://<public-ip>/docs`
- Health: `http://<public-ip>/api/health`

## Shell access (no SSH)

```bash
aws ssm start-session --target <InstanceId>
# container logs:
sudo docker logs -f cyberyukti
# bootstrap log:
sudo tail -f /var/log/cyberyukti-bootstrap.log
```

## Rollback

The CI/CD pipeline (`.github/workflows/deploy.yml`) keeps the previous
container image on the instance. If the new container fails its health
check, the SSM deployment script re-runs the previous SHA tag and re-checks
health (see `docs/CI_CD.md`). To roll back manually:

```bash
aws ssm send-command --target <InstanceId> \
  --document-name AWS-RunShellScript \
  --parameters commands='["docker pull sahasnagar/cyberyukti:<old-sha> && docker rm -f cyberyukti && docker run -d --name cyberyukti --restart unless-stopped -p 80:8000 sahasnagar/cyberyukti:<old-sha>"]'
```

## Tear down (stop billing)

```bash
./scripts/destroy-aws.sh
```

## Honest test status

- Template validated with `aws cloudformation validate-template` (real, ap-south-1).
- Stack create/update + UserData bootstrap + health check: exercised via
  `scripts/deploy-aws.sh` (real AWS CLI calls; result depends on account
  permissions/free tier at the time you run it).
- The GitHub Actions OIDC deploy path requires repo secrets/role setup
  (see `docs/CI_CD.md`); it is **not** exercised until the first push to main.
