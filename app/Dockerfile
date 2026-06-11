# syntax=docker/dockerfile:1
#
# Tiny, rootless image for the demo backend. No third-party packages, so there
# is nothing to scan but the base, and the build is fast on the ephemeral
# runner. Built by rootless BuildKit on the private Fargate runner -- never on a
# laptop, never with a Docker daemon.

FROM public.ecr.aws/docker/library/python:3.12-slim

# Build-time provenance -> baked into the image so the running service can
# report what it was built from. The runner passes these via --opt build-arg.
ARG GIT_SHA=dev
ARG BUILT_AT=unknown
ENV GIT_SHA=${GIT_SHA} \
    BUILT_AT=${BUILT_AT} \
    PORT=8080 \
    PYTHONUNBUFFERED=1

# Non-root runtime user.
RUN useradd -m -u 10001 app
USER app
WORKDIR /home/app

COPY --chown=app:app server.py /home/app/server.py

EXPOSE 8080
# Container-level healthcheck (the ALB also checks /healthz independently).
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz').status==200 else 1)" || exit 1

ENTRYPOINT ["python", "/home/app/server.py"]
