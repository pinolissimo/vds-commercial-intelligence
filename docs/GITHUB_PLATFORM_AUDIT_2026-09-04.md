# GitHub Platform Audit — VDS Commercial Intelligence

Audit date: 2026-09-04 (Europe/Madrid)

## Executive decision

Keep GitHub as the only infrastructure/control plane around the existing VDS acquisition tasks. Do not move or rewrite the working production task architecture. Use GitHub only where it improves reliability, observability, deployment, security or maintenance without reducing acquisition quality.

## USE — already implemented

### GitHub Actions
**Decision: KEEP / CORE INFRASTRUCTURE.**

Used for:
- high-frequency public/employer-direct discovery fanout;
- semantic gate and source/territory optimization;
- disposable Command Center projections;
- AI Command interpretation through OpenAI Responses API;
- Command Center QA;
- GitHub Pages build/deployment.

Reliability controls already present:
- workflow concurrency groups;
- `cancel-in-progress: false` for AI commands and discovery where loss would be unsafe;
- collision-safe refresh/rebuild/retry before canonical writes;
- production and dashboard workflows separated;
- recovery projection workflow kept manual to avoid redundant minutes.

### GitHub Pages
**Decision: USE for the static Command Center shell only.**

The Pages artifact contains UI assets only. CRM JSON, contacts, replies and outbound records remain in the private repository and are read through the GitHub REST API after authenticated browser access.

The OpenAI key is never published. First-access setup encrypts it locally with the repository Actions public key and writes only the encrypted value to GitHub Actions Secrets.

One-time prerequisite: the repository Pages site must be enabled with `Source = GitHub Actions`. `actions/configure-pages` cannot self-enable a previously disabled Pages site when it only has the workflow `GITHUB_TOKEN`; the official action requires a separate PAT/GitHub App token with Pages/administration rights for enablement.

GitHub Pages availability note: public repositories are supported on GitHub Free; private-repository Pages requires GitHub Pro, Team, Enterprise Cloud or Enterprise Server. This repository must remain private because it contains operational CRM data.

### Repository Actions Secrets
**Decision: USE.**

`OPENAI_API_KEY` is stored only as a repository Actions Secret. The Command Center first-access flow uses the official Actions public-key endpoint + LibSodium `crypto_box_seal` and never stores the plaintext OpenAI key in browser storage, JSON, workflow inputs or Pages.

### Fine-grained personal access token
**Decision: USE only as a session credential for the private Command Center.**

Least-privilege target:
- resource owner: `pinolissimo`;
- repository access: only `vds-commercial-intelligence`;
- Contents: read;
- Actions: write;
- Secrets: write;
- suggested expiry: 90 days.

The dashboard stores this token only in `sessionStorage`, not `localStorage`. A GitHub-supported prefilled token-creation template is provided by the UI; the owner must still select only this repository in GitHub's form.

### Dependabot version updates
**Decision: KEEP. Already configured.**

`.github/dependabot.yml` monitors the `github-actions` ecosystem weekly and groups maintenance updates. Dependabot version updates are available for all GitHub repositories and are the right low-maintenance supply-chain control for the Actions dependencies used here.

### GitHub repository history + pull requests + QA
**Decision: KEEP.**

Use feature branches for Command Center architectural changes, CI before merge, and canonical Git history as the audit trail. Production task changes remain deliberate and separate from UI changes.

## IMPORTANT CONTINUITY RISK — Actions minutes

The repository is private, so ordinary GitHub-hosted Action jobs consume the plan's included minutes. Current GitHub documentation lists:
- GitHub Free: 2,000 minutes/month;
- GitHub Pro: 3,000 minutes/month;
- GitHub Team: 3,000 minutes/month;
- 10 GB Actions cache per repository on these plans.

GitHub rounds billable execution of each private-repository hosted job up to the next whole minute.

A measured high-frequency discovery job on 2026-09-04 ran from approximately 11:04:36Z to 11:05:22Z. Even though this is under one minute, it is therefore one billable minute. At the current `*/10` schedule, a continuously running single-job discovery workflow has a theoretical floor of about:

`6 jobs/hour × 24 × 30 = 4,320 billable job-minutes/month`

before counting other private-repository workflows.

**Decision: DO NOT slow the motor automatically.** Acquisition throughput is the business priority and the user explicitly requires the search engine not to stop. Instead:
- preserve the 10-minute cadence;
- keep unnecessary projection work folded into discovery instead of a second scheduled workflow;
- keep recovery workflow manual;
- treat Actions quota/billing exhaustion or workflow disabling as a CRITICAL availability incident in the Watchdog;
- owner should ensure adequate Actions quota/billing configuration if continuous 10-minute operation is required.

Pages and Dependabot GitHub-hosted standard runner usage are documented as free and do not need to be optimized away.

## DO NOT USE — evaluated and rejected

### GitHub Models
**Decision: DO NOT USE.**

GitHub retired GitHub Models completely on 2026-07-30. The playground, model catalog, inference API and BYOK are no longer available to any customer. OpenAI Responses API remains the Command Center AI layer.

### GitHub Spark
**Decision: DO NOT USE.**

GitHub announced retirement of Spark on github.com in August 2026; new app creation is no longer a viable foundation. The VDS Command Center remains a normal static web application + Actions architecture.

### Codespaces as production compute
**Decision: DO NOT USE for runtime.**

Codespaces is useful for interactive development, not a durable scheduler/backend. It adds no production advantage over the existing Actions architecture.

### GitHub Packages / Container Registry
**Decision: DO NOT USE now.**

There is no container/package distribution need in this GitHub-only design. Adding a package lifecycle would increase maintenance and storage without improving acquisition output.

### OIDC
**Decision: DO NOT USE now.**

OIDC is valuable when GitHub Actions must authenticate to an external cloud. The owner explicitly chose GitHub-only infrastructure, so there is no external cloud trust relationship to establish.

### Issues / Projects as the operational CRM or command queue
**Decision: DO NOT USE.**

The canonical JSON event/state model already supports deterministic deduplication, worker routing and projections. Mirroring operational state into Issues/Projects would create dual-write and reconciliation risk.

### Actions artifacts as canonical data storage
**Decision: DO NOT USE.**

Canonical operational data belongs in versioned repository JSON/JSONL. Artifacts are ephemeral build outputs and would weaken discoverability/auditability while consuming storage.

### CodeQL / advanced secret scanning as an assumed free private-repo control
**Decision: DO NOT DESIGN AROUND IT.**

Advanced private-repository security availability depends on plan/organization licensing. The current project instead relies on minimal permissions, CSP, local runtime assets, deterministic CI, Dependabot for Actions, secret non-publication tests and GitHub Actions Secrets. Advanced GitHub security features can be added later if the account plan provides them, but they are not a dependency of the architecture.

## Architecture decision summary

```text
Existing VDS production tasks       = authoritative execution engine
GitHub private repository           = canonical state / audit / CRM data
GitHub Actions                       = serverless compute + scheduling + AI command runner
GitHub Pages                         = static UI shell only
GitHub REST API                      = authenticated private data/control transport
GitHub Actions Secret               = OPENAI_API_KEY vault
OpenAI Responses API                = command interpretation / analysis
Dependabot                           = GitHub Actions dependency maintenance
Command bridge pending/processed    = idempotent overlay into existing workers
Watchdog                             = acquisition + bridge availability monitoring
```

## Final invariant

No GitHub feature is allowed to become a new mandatory dependency for the acquisition core unless its failure mode is isolated from normal discovery, qualification, deduplication, route verification and sending. The Command Center may fail closed; the production acquisition engine must continue its normal cycle.

## Official references reviewed

- GitHub Models retirement (2026-07-30): https://github.blog/changelog/2026-07-30-github-models-is-now-retired/
- GitHub Spark retirement notice: https://github.blog/changelog/2026-08-04-upcoming-deprecation-of-github-spark-on-github-com/
- GitHub Actions billing and included usage: https://docs.github.com/en/billing/concepts/product-billing/github-actions
- Viewing Actions job execution/billable rounding: https://docs.github.com/en/actions/how-tos/monitor-workflows/view-job-execution-time
- GitHub Pages availability: https://docs.github.com/en/pages/getting-started-with-github-pages
- Dependabot version updates: https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-version-updates
- Fine-grained PAT prefill templates: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- Fine-grained PAT permissions: https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens
