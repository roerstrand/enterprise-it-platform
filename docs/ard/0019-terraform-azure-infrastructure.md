# ARD-0019: Terraform-provisioned Azure infrastructure (start of the AKS migration)

## Status
Proposed

## Date
2026-08-15

## Context
The platform runs on local Kubernetes today (ARD-0011). The roadmap's next step is migrating to a real cloud target (Azure Kubernetes Service) for portfolio/production realism, which first requires cloud infrastructure to exist: a place to push container images, and a way for CI (GitHub Actions) to authenticate to Azure without long-lived secrets sitting in repository settings.

## Decision
`terraform/main.tf` provisions the first slice of Azure infrastructure via the `azurerm`/`azuread` providers: a resource group (`enterprise-it-platform-rg`, Sweden Central), a Basic-tier Azure Container Registry (`enterpriseitplatformacr`), and a secretless GitHub Actions identity — an `azuread_application`/`azuread_service_principal` with an OIDC federated identity credential trusted only for `repo:roerstrand/enterprise-it-platform:ref:refs/heads/main`, granted the `AcrPush` role scoped to just the registry (not the subscription). Terraform state (`terraform.tfstate*`) and the downloaded provider binaries (`.terraform/`) are gitignored — this is a public repository, neither should enter history — while `.terraform.lock.hcl` (provider version pins) is committed, matching the intent of the lock file used elsewhere in the project (ARD-0012).

## Alternatives considered
- **A long-lived Service Principal secret stored as a GitHub Actions secret** — rejected; OIDC federation means no credential exists to leak, rotate, or expire — the trust relationship itself is the credential, scoped to a specific repo/branch.
- **ClickOps** (create the resource group/ACR manually in the Azure Portal) — rejected; contradicts documenting infrastructure decisions as code/ARDs in the first place, and isn't reproducible if the subscription needs to be rebuilt.
- **Provision AKS itself in this same pass** — deferred; this ARD covers only the registry and CI identity (roadmap step 8's first slice). AKS cluster provisioning and the GitHub Actions workflow that pushes the six service images are separate, not-yet-taken decisions.

## Consequences
- GitHub Actions can push images to ACR with no stored secret — verified manually by tagging/pushing the existing `user-server:local` image before wiring up the actual workflow.
- The `AcrPush` role is scoped to the registry only, not the resource group or subscription — a compromised workflow run can push/pull images but cannot provision or delete other Azure resources.
- Terraform state is local-only (no remote backend configured) — acceptable for a single-contributor project today, but means state isn't shared/lockable if this became a team workflow, and a lost local state file would require reconciling real Azure resources back into Terraform manually (`terraform import`).
- This is explicitly a partial migration (registry + CI identity only) — the services still run on local k8s (ARD-0011) until the AKS cluster itself and the corresponding GitHub Actions deploy workflow are added as follow-up decisions.
