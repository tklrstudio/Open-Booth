# Decision: GitHub Actions VPS Deployment for Open Booth

**Created:** 2026-03-11
**Decision Status:** Proposed
**Decision ID:** DEC-OB-2026-03-11-001
**Workspace:** Open-Booth
**Branch:** Operations

---

## Problem

Open Booth is deployed to the VPS manually. The portfolio now has a standard VPS deployment pattern via GitHub Actions (see `.living-systems/docs/standards/VPS_DEPLOYMENT.md`). Open Booth should align with this standard.

**Current state:**
Manual deployment following `docs/VPS_SETUP.md`. No automation, no audit trail.

---

## Decision

**Deploy Open Booth via GitHub Actions using the portfolio VPS deployment standard.**

- Triggers on push to `main` when `client/` or `scripts/` change, or manual dispatch
- rsync `client/` to `/opt/openbooth/client/` and `scripts/` to `/opt/openbooth/scripts/`
- Restart `openbooth.service`
- No pip install needed (zero external dependencies)

**Scope:**
- Adds `.github/workflows/deploy.yml`
- No changes to the application code
- VPS one-time setup (systemd, nginx) remains manual

---

## Execution Checklist

- [x] Create `.github/workflows/deploy.yml`
- [ ] Add `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_KEY` secrets to the GitHub repo
- [ ] Test end-to-end deploy
- [ ] Update `docs/VPS_SETUP.md` to reference automated deployment

---

## Related

**Standard:** `.living-systems/docs/standards/VPS_DEPLOYMENT.md`
**Related:** DEC-OB-2026-03-11-026 (open-brain deployment — same standard)

---

**End of Decision Record**
