import { readFileSync } from "fs";

const main = async () => {
  const ev = JSON.parse(readFileSync(process.env.GITHUB_EVENT_PATH, "utf8"));
  const prNum = ev.pull_request.number;
  console.log(`PR number is ${prNum}`);
};

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
