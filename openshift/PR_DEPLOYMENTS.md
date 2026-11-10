# PR dev deployments

PRs normally deploy automatically. Before provisioning, both deployment workflows
check requested memory in dev's `compute-long-running-quota`. A new environment
requires 20Gi of headroom. An environment with a fully ready main application
deployment requires 8Gi for its update. Review these constants in
`openshift/scripts/check_dev_capacity.py` when dev resource requests change.

If memory is insufficient, the workflow adds `skip-dev-deploy` and explains the
shortage in its job summary. Existing resources remain. Remove the label to retry.
Adding the label yourself also pauses future deployments. Image builds and tests
continue while deployment is paused. Weather retains its existing path filter.

The label never deletes resources. To free resources without closing a PR, use
the existing manual Cleanup workflow with its PR number. This performs full cleanup,
including database data, images, and backups. Closing a PR also requests full cleanup.

Deployment and cleanup workflows share a concurrency group to avoid overlapping
runs. The memory check is conservative. Scheduled jobs can consume capacity after
it runs, and other resource shortages remain ordinary deployment errors.

Create the repository label once before enabling these workflows:

```bash
gh label create skip-dev-deploy --repo bcgov/wps --color fbca04 --description "Pause dev deployment; remove to retry"
```
