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
    body += `Percentile Calculator: ${prBaseUrl}/\n`;
    body += `MoreCast: ${prBaseUrl}/morecast\n`;
    body += `C-Haines: ${prBaseUrl}/c-haines\n`;
    body += `FireBat: ${prBaseUrl}/fire-behaviour-calculator\n`;
    body += `FireBat bookmark: ${prBaseUrl}/fire-behaviour-calculator?s=264&f=o1a&c=6&w=undefined,s=322&f=c1&c=undefined&w=15.5\n`;
    body += `HFI Calculator: ${prBaseUrl}/hfi-calculator\n`;
    github.pulls.update({
      owner: context.repo.owner,
      repo: context.repo.repo,
      pull_number: prNum,
      body: body,
    });
  }
};
