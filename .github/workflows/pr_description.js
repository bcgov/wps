/* This module us used by a github workflow to check the PR description for test links, and add them
if found to be missing.
*/
module.exports = async ({ github, context }) => {
  const prNum = context.payload.pull_request.number;
  const pr = await github.pulls.get({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: prNum,
  });
  const prBaseUrl = `https://wps-pr-${prNum}.apps.silver.devops.gov.bc.ca`;
  if (pr.data.body === null || !pr.data.body.includes(prBaseUrl)) {
    // If the body doesn't already contain some test links, we create a few.
    let body = pr.data.body === null ? "" : pr.data.body;
    body += "\n# Test Links:\n";
    body += `[Percentile Calculator](${prBaseUrl}/){:target="_blank" rel="noopener"}\n`;
    body += `[MoreCast](${prBaseUrl}/morecast){:target="_blank" rel="noopener"}\n`;
    body += `[C-Haines](${prBaseUrl}/c-haines){:target="_blank" rel="noopener"}\n`;
    body += `[FireBat](${prBaseUrl}/fire-behaviour-calculator){:target="_blank" rel="noopener"}\n`;
    body += `[FireBat bookmark](${prBaseUrl}/fire-behaviour-calculator?s=266&f=c5&c=NaN&w=20,s=286&f=c7&c=NaN&w=16,s=1055&f=c7&c=NaN&w=NaN,s=305&f=c7&c=NaN&w=NaN,s=344&f=c5&c=NaN&w=NaN,s=346&f=c7&c=NaN&w=NaN,s=328&f=c7&c=NaN&w=NaN,s=1399&f=c7&c=NaN&w=NaN,s=334&f=c7&c=NaN&w=NaN,s=1082&f=c3&c=NaN&w=NaN,s=388&f=c7&c=NaN&w=NaN,s=309&f=c7&c=NaN&w=16,s=306&f=c7&c=NaN&w=NaN,s=1029&f=c7&c=NaN&w=NaN,s=298&f=c7&c=NaN&w=NaN,s=1108&f=c5&c=NaN&w=NaN,s=836&f=c7&c=NaN&w=NaN#state=2ec784ca-c46a-49d0-b2b3-1cf32a9015a2&session_state=7d9447c8-db66-4661-b4cb-03d2ac0d1d8f&code=32292df4-2bdf-4f90-a4a8-c8dbcda682a9.7d9447c8-db66-4661-b4cb-03d2ac0d1d8f.2b63f390-f3dc-43ae-89f2-016453863476){:target="_blank" rel="noopener"}\n`;
    body += `[HFI Calculator](${prBaseUrl}/hfi-calculator){:target="_blank" rel="noopener"}\n`;
    github.pulls.update({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNum,
      body: body,
    });
  }
};
