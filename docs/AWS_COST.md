# AWS Cost (10-hour hackathon demo)

Region: ap-south-1. Prices below are **approximate list prices** — verify
current pricing yourself; nothing here is a guarantee.

## What runs

| Resource | ~Price (ap-south-1) | 10 h cost |
|---|---|---|
| t3.micro EC2 | ~$0.0104/h | **~$0.10** |
| EBS gp3 root 8 GB | ~$0.096/GB-month | ~$0.003 |
| Public IPv4 | ~$0.005/h (non-free-tier) | ~$0.05 |
| Data transfer in | free | $0 |
| Data transfer out (demo traffic) | first 100 GB free | ~$0 |
| CloudFormation | free | $0 |
| SSM Session Manager / send-command | free | $0 |
| IAM / OIDC provider | free | $0 |

**Total: roughly $0.10–0.20 for a 10-hour demo** if the account is past
free tier; **$0** if the account is within the 12-month free tier
(750 h/month t3.micro/t2.micro + 30 GB EBS + 100 GB egress).

Why so low: no ALB (~$0.0225/h + LCU), no NAT gateway (~$0.056/h + data),
no RDS, no EKS/ECS/Fargate, no CloudFront. The stack is one EC2 instance
plus free control-plane resources.

## Cost safety rails

- `scripts/destroy-aws.sh` deletes the whole stack in one command — run it
  when the demo ends; billing stops when the instance terminates.
- The stack carries a `ttl=hackathon-demo` tag for easy identification.
- The IAM role has no billing or broad `*:*` permissions.
- Nothing in the stack creates recurring services (no RDS snapshots,
  no Elastic IPs are allocated, no S3 buckets).

## What could still cost money (honesty section)

- Forgetting to tear down: a t3.micro left running 24/7 for a month is
  ~$7.50 (or free within free tier).
- Pulling large scanner DBs (trivy) counts as **data transfer in** — free;
  pushing results out stays under the 100 GB free egress for any demo scale.
- If a **t4g.micro** is chosen instead, prices differ slightly (ARM build
  of the image would be required — not set up; keep t3.micro x86_64).
