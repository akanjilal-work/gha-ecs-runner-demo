# gha-ecs-runner-demo

A deliberately tiny app used to demonstrate the [`gha-ecs-runner`](https://github.com/akanjilal-work/gha-ecs-runner)
private build plane end to end. **The app is not the point — the pipeline is.**

A push (or a `workflow_dispatch` from the live demo's control API) runs
[`.github/workflows/build-and-push.yml`](.github/workflows/build-and-push.yml) on a
single-use, private **Fargate runner**:

1. **build** — rootless BuildKit builds [`app/`](app/) and pushes to Amazon ECR, then
   signs the image in-account with AWS KMS (transparency log disabled) and verifies it.
2. **deploy** — on its own ephemeral runner, runs an **independent `cosign verify`** as a
   gate, then registers a new task definition with the verified digest and rolls the
   ALB-fronted ECS service to it.

The running service ([`app/server.py`](app/server.py)) reports its own provenance — the
git SHA, build time, image digest, and whether its signature was verified — which is what
the live demo renders to prove the artifact in front of you was built privately and signed.

This repo is built and deployed only through that plane; nothing is built on a laptop.
