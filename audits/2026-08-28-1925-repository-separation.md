# VDS Commercial Intelligence — Repository Separation Audit

**Timestamp:** 2026-08-28 19:25 Europe/Madrid  
**Scope:** repository/domain isolation after accidental CRM placement inside EU Funding Observatory demo  
**Result:** `PASS_WITH_WARNINGS`

## Checks

### 1. Demo main branch isolation — PASS
Verified `pinolissimo/eu-funding-observatory` branch `main` root after cleanup. The working tree contains demo/application assets (`site/`, `tests/`, `tools/`, deployment files, project README/release files) and **does not contain `commercial-intelligence/` or CRM root files**.

Cleanup commit: `ab237ea98d82d6b639ccd95e41a0cdb687b42b44`.

### 2. CRM tree preservation — PASS
The former `commercial-intelligence/` subtree was extracted unchanged as the root tree of branch `commercial-intelligence`.

Extraction commit: `3b662ca706da889c48b210bdfe47045d8815b9c6`.

Verified branch root contains CRM modules including:
- `README.md`
- `master-index.json`
- `CRM_ARCHITECTURE.md`
- `QA_AUDIT_STANDARD.md`
- `analytics/`
- `audits/`
- `campaigns/`
- `config/`
- `contacts/`
- `governance/`
- `italy/`
- `spain/`
- `opportunities/`
- `outreach/`
- `replies/`
- `research/`
- `reports/`
- `views/`
- `local-no-website/`

### 3. Dashboard isolation marking — PASS
CRM `README.md` now explicitly states that branch `commercial-intelligence` is the isolated commercial data store and branch `main` is forbidden for CRM writes.

### 4. Automation routing — PASS
The active commercial automations were updated to target branch `commercial-intelligence` at repository root only:
- VDS Partner Hunt
- VDS Reply Watch
- VDS QA Audit

Each automation explicitly forbids commercial writes to `main` and uses the branch-specific dashboard URL.

### 5. Data loss check — PASS
No CRM files were individually deleted before the subtree extraction. The isolated branch was created from the exact CRM tree object before removal from `main`, preserving the commercial working tree as it existed at extraction time. Git history also retains all prior commits.

## Warning / remaining architecture debt

The CRM is **not yet in a physically separate GitHub repository**. It is isolated in a dedicated branch of the demo repository because the authenticated GitHub connector available in this session exposes branch/file/commit operations but does not expose repository creation or rename.

Preferred final topology:

`pinolissimo/vds-commercial-intelligence` (private repository)

When such a repository exists, migrate branch `commercial-intelligence` root to it, verify content parity, update automations, and delete the temporary CRM branch from `eu-funding-observatory`.

## Non-regression gate
Future QA must treat either condition as CRITICAL FAIL:
1. CRM files reappear on `eu-funding-observatory/main`;
2. any commercial automation writes to `main`.

## Final assessment
The original domain-mixing error has been contained and the demo working tree is clean. Operational data is isolated and preserved. Physical repository separation remains the only unresolved infrastructure item due connector capability.
