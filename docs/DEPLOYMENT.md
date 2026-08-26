# Deployment and Operations

## Recommended production target

The included `render.yaml` defines a Docker web service, managed PostgreSQL, persistent disk mounted at `/var/data`, generated JWT secret, and `/api/health` checks.

## Required hosted-model secrets

A deployed container cannot reach the developer laptop’s Ollama instance. Configure an OpenAI-compatible provider:

```text
LLM_API_BASE=https://provider.example/v1
LLM_API_KEY=<secret>
LLM_MODEL=<provider-model-id>
```

Never commit `.env` or expose these values to the browser.

## Render Blueprint rollout

1. Push the repository to GitHub.
2. In Render, choose **New → Blueprint**.
3. Select `Samik123Mit/unibot-resume-agent`.
4. Review the PostgreSQL and persistent-disk plans in `render.yaml`.
5. Enter the hosted-model secret values.
6. Apply the blueprint.
7. Wait for `/api/health` to become healthy.
8. Complete the production smoke test from [TESTING.md](TESTING.md).
9. Replace the pending live-link line in `README.md` with the verified URL.

## Local PostgreSQL verification

```powershell
Copy-Item .env.example .env
docker compose up --build
```

## Rollback

1. Roll back the web service to the previous healthy image/commit.
2. Do not roll back PostgreSQL independently unless a migration requires it.
3. Retain the PDF disk; database records reference revision paths.
4. Re-run health and tenant-isolation checks.

## Backup policy

- Daily PostgreSQL backups.
- Daily persistent-disk snapshot or migration to versioned object storage.
- Coordinated retention so database revisions never point to expired files.

## Production checklist

- [ ] Hosted model credentials configured.
- [ ] PostgreSQL connection healthy.
- [ ] `JWT_SECRET` generated, not default.
- [ ] Persistent `UPLOAD_DIR` mounted.
- [ ] HTTPS enabled.
- [ ] CI green on deployed commit.
- [ ] PDF upload/edit/download smoke test passed.
- [ ] Reset and undo verified.
- [ ] Live link updated in README.
