# ARD-0011: Kubernetes for local container orchestration

## Status
Accepted

## Date
2026-08-08

## Context
The platform had grown to five owned services (three Python gRPC services, the FastAPI REST/demo app, and the C#/.NET Change Service) plus seven infrastructure dependencies (Postgres, Redis, RabbitMQ, Prometheus, Grafana, Jaeger, Nginx), the latter already running under `docker-compose`. The five owned services, however, ran directly on the host (via `watchmedo`/`dotnet run`), never as containers — there were no Dockerfiles for any of them.

The platform roadmap ([[enterprise_platform_vision]]) names Kubernetes as the next Infrastructure milestone after Prometheus/Grafana/Jaeger/RabbitMQ/Redis/Nginx, both for its own architectural value (declarative deployment, service discovery, self-healing) and as demonstrable, interview-relevant skill depth for the project's portfolio purpose.

## Decision
The full stack (12 workloads: 7 infrastructure + 5 owned services) is migrated to a local Kubernetes cluster, replacing `docker-compose` as the runtime for infrastructure and adding container images for the five services that previously only ran on the host.

- One Dockerfile per owned service (`Dockerfile.user_server`, `Dockerfile.cmdb_server`, `Dockerfile.incident_server`, `Dockerfile.fastapi`, `Dockerfile.changeservice`); the four Python ones use `uv` (ARD-0012), the C# one uses a multi-stage build (SDK image to `dotnet publish`, `aspnet` runtime image for the result).
- Manifests live in `k8s/`, one file per component, each a `Deployment` + `Service`. `Prometheus` and `Nginx` additionally get a `ConfigMap` (replacing docker-compose's bind-mounted config files, since Kubernetes pods can be rescheduled to any node and a host file path is meaningless there). Postgres gets a `PersistentVolumeClaim`.
- Credentials (`DATABASE_URL`, JWT `SECRET_KEY`, the .NET-format connection string) move into a single `Secret` (`k8s/app-secrets.yaml`), gitignored since the repository is public.
- All previously hardcoded `localhost:<port>` addresses between services (cross-service gRPC calls, Redis, RabbitMQ, the OTLP exporter) are converted to `os.getenv(..., "localhost:<port>")` (`Environment.GetEnvironmentVariable(...) ?? "localhost:<port>"` in C#), so the same code runs unchanged on the host (default) and in-cluster (overridden to the Kubernetes Service DNS name via the Deployment's `env:`).
- Cluster: Docker Desktop's built-in Kubernetes, using the **Kubeadm** provisioning method rather than the newer default **kind** method — see Alternatives.
- Database migrations (Alembic, EF Core) are applied to the cluster's Postgres via a temporary `kubectl port-forward`, since the `postgres` Service is only reachable from inside the cluster by default.

## Alternatives considered
- **Docker Desktop Kubernetes with the `kind` provisioning method** (the current default). Tried first; rejected — `kind` runs the cluster node in an isolated environment with its own image store, separate from the Docker daemon `docker build` uses. Locally built images (`imagePullPolicy: Never`) failed with `ErrImageNeverPull` even though `docker images` showed them present. Fixing this properly requires a local registry or `kind load docker-image`-style workarounds; switching to Kubeadm removes the problem at the root, since Kubeadm reuses the same Docker daemon as the CRI runtime.
- **minikube / standalone `kind` CLI.** Rejected — both are extra tools to install with the same or worse local-image friction as Docker Desktop's own `kind` method, no advantage over what Docker Desktop already provides once Kubeadm is selected.
- **Stay on `docker-compose`, don't containerize the owned services.** Rejected — doesn't advance the roadmap's Kubernetes milestone, doesn't produce portfolio-demonstrable Kubernetes skill, and leaves the five owned services as a permanent exception to "everything in this platform is a container," which would only get harder to justify as more services are added.
- **Terraform for provisioning.** Out of scope here — Terraform provisions infrastructure (cloud clusters, networks, managed databases); there is nothing to provision against a local Docker Desktop cluster. Becomes relevant if/when the platform moves to a real cloud-hosted cluster (AKS/EKS/GKE); a candidate future ARD, not part of this one.

## Consequences
- Declarative, reproducible deployment (`kubectl apply -f k8s/`) replaces manual process management (`watchmedo` per service, `docker-compose up` for infra) for anything running in the cluster.
- Service discovery is now DNS-based (`postgres`, `redis`, `user-server`, ...) instead of `localhost`-coupled, which is also what makes a future move to a real cloud cluster a manifest-reuse exercise rather than a rewrite.
- The local development inner loop changes: a code change to an owned service now requires `docker build` + `kubectl rollout restart`, rather than `watchmedo`'s instant on-save reload. `watchmedo` against `.venv`/`dotnet run` on the host remains available and unaffected for fast iteration; the container path is used for parity/integration testing and the eventual portfolio demo, not necessarily every edit-test cycle.
- Operational surface grows: Secrets and ConfigMaps are new concepts to maintain (e.g. `k8s/app-secrets.yaml` must be created manually on a fresh clone, since it's gitignored).
- A latent bug was surfaced (not introduced) by this migration: `grpc_clients/user_client.py` and `incident_client.py` created their `grpc.aio` channel at module-import time, before `uvicorn`'s event loop existed, causing `RuntimeError: ... attached to a different loop` under real concurrent use. Fixed by lazy channel initialization. This would have failed identically outside Kubernetes; the migration is simply what first exercised that code path end-to-end.
