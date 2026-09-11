# CI/CD — GitHub Actions → Docker Hub → EC2 (SSM)

Pipeline file: `.github/workflows/deploy.yml`

```
push to main
   ↓
1. tests (pytest + vitest + next build)
   ↓
2. docker build  →  tag sahasnagar/cyberyukti:<short-sha> (+ latest)
   ↓
3. push to Docker Hub   (secrets: DOCKERHUB_USERNAME, DOCKERHUB_TOKEN)
   ↓
4. AWS auth via GitHub OIDC  (NO long-lived AWS keys)
   ↓
5. aws ssm send-command → EC2 runs a shell script:
      docker pull <sha-tag>
      keep old container as rollback target
      docker rm -f cyberyukti
      docker run ... (same flags as UserData)
      health check /api/health (inside the instance)
      on failure: restore previous image, re-check, mark deploy FAILED
```

## One-time setup

1. **Docker Hub secrets** (repo → Settings → Secrets and variables → Actions):
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN` (Docker Hub → Account Settings → Security → Access Token)

2. **AWS OIDC** (no long-lived keys):
   - Create an identity provider:
     ```bash
     aws iam create-open-id-connect-provider \
       --url https://token.actions.githubusercontent.com \
       --client-id-list sts.amazonaws.com \
       --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
     ```
   - Create a role named `cyberyukti-github-deploy` trusted by that provider,
     restricted to `repo:Sahas2711/CyberYukti:ref:refs/heads/main`, with
     permissions to: `cloudformation:DescribeStacks`,
     `ssm:SendCommand`, `ssm:GetCommandInvocation`,
     `ec2:DescribeInstances`, `iam:PassRole` (instance profile),
     `cloudformation:Get*`/`List*` as needed by the deploy script.
   - Put the role ARN in the repo secret `AWS_DEPLOY_ROLE_ARN`.

3. Push to `main`. The workflow runs automatically.

## Rollback behavior

The SSM deploy script on the instance:

1. Records the current running image (if any) as `$OLD_IMAGE`.
2. Starts the new container and polls `/api/health` (30 × 5 s).
3. If unhealthy: `docker rm -f` the new container, `docker run` `$OLD_IMAGE`,
   poll health again, then **exit non-zero** so `ssm send-command` fails and
   the GitHub Actions step turns red (deployment failure is visible).
4. If the old container also fails health check, the step still fails —
   honest failure, no silent success.

## What is NOT tested automatically (honesty section)

- The OIDC role trust/permission matrix is validated only on first real run.
- Scanner images inside the container are the app's own concern (semgrep/trivy
  installed in the image) and are not exercised by CI beyond build success.
