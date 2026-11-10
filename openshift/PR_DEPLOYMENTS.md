# PR dev deployments

Tests and image builds run without a label, subject to the existing path filters.

Add `deploy-dev` to deploy a PR and update its environment on subsequent commits.
Remove it to stop future deployments. Already-triggered runs may still deploy.

Removing the label retains the environment. Close the PR or run Cleanup manually
with its PR number to delete its resources, including database data, images, and backups.

Create the repository label once before enabling these workflows:

```bash
gh label create deploy-dev --repo bcgov/wps --color 0e8a16 --description "Deploy this PR to dev and update it on subsequent commits"
```
