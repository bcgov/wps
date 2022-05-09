/* This module us used by a github workflow to check the PR description for test links, and add them
if found to be missing.
*/
module.exports = async ({ github, context }) => {
  const prNum = context.payload.pull_request.number;
  const pr = await github.rest.pulls.get({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: prNum,
  });
  const prBaseUrl = `https://wps-pr-${prNum}.apps.silver.devops.gov.bc.ca`;
  if (pr.data.body === null || !pr.data.body.includes(prBaseUrl)) {
    // If the body doesn't already contain some test links, we create a few.
    let body = pr.data.body === null ? "" : pr.data.body;
    body += "\n# Test Links:\n";
    body += `[Percentile Calculator](${prBaseUrl}/)\n`;
    body += `[MoreCast](${prBaseUrl}/morecast)\n`;
    body += `[C-Haines](${prBaseUrl}/c-haines)\n`;
    body += `[FireBat](${prBaseUrl}/fire-behaviour-calculator)\n`;
    body += `[FireBat bookmark](${prBaseUrl}/fire-behaviour-calculator?s=266&f=c5&c=NaN&w=20,s=286&f=c7&c=NaN&w=16,s=1055&f=c7&c=NaN&w=NaN,s=305&f=c7&c=NaN&w=NaN,s=344&f=c5&c=NaN&w=NaN,s=346&f=c7&c=NaN&w=NaN,s=328&f=c7&c=NaN&w=NaN,s=1399&f=c7&c=NaN&w=NaN,s=334&f=c7&c=NaN&w=NaN,s=1082&f=c3&c=NaN&w=NaN,s=388&f=c7&c=NaN&w=NaN,s=309&f=c7&c=NaN&w=16,s=306&f=c7&c=NaN&w=NaN,s=1029&f=c7&c=NaN&w=NaN,s=298&f=c7&c=NaN&w=NaN,s=836&f=c7&c=NaN&w=NaN)\n`;
    body += `[Fire Behaviour Advisory](${prBaseUrl}/fire-behaviour-advisory)\n`;
    body += `[HFI Calculator](${prBaseUrl}/hfi-calculator)\n`;
    body += `[FWI Calculator](${prBaseUrl}/fwi-calculator)\n`;
    github.rest.pulls.update({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNum,
      body: body,
    });
  }
};
