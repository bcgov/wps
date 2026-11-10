# PR dev deployments

PRs do not deploy to dev by default. Add the `deploy-dev` label to request a
deployment. Subsequent commits update the environment while the label remains.
Tests and image builds run for relevant PRs regardless of the label. Weather
retains its existing path filter.

Both deployment workflows use the labels recorded in the event that triggered
the run. Unrelated label additions do not start builds or provisioning. Developers
choose which PRs consume dev capacity, and quota shortages remain ordinary
deployment errors.

Remove `deploy-dev` to stop future deployments. Already-triggered runs may still
deploy after label removal, PR closure, or a newer commit. Existing environments
remain. Add the label again to redeploy.

The label never deletes resources. To free resources without closing a PR, use
the existing manual Cleanup workflow with its PR number. This performs full cleanup,
including database data, images, and backups. Closing a PR also requests full cleanup.

Create the repository label once before enabling these workflows:

```bash
gh label create deploy-dev --repo bcgov/wps --color 0e8a16 --description "Deploy this PR to dev and update it on subsequent commits"
```
