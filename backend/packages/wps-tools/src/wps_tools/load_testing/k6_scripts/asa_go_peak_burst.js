// Replicates the highest observed hourly traffic peak on the ASA Go production API
// (18,000,000 requests in a single hour, per production analytics) as a sustained
// one-minute burst instead of spread across an hour -- a burst-capacity / rate-limiter
// resilience test, not a realistic traffic simulation.
//
// Target: https://psu.api.gov.bc.ca/api/asa-go/fba/fire-centre-info (production). A
// lightweight, parameter-free, read-only GET -- no path/query params, one cheap DB read,
// representative of what the mobile app calls on launch to populate its fire-centre picker.
//
// The gateway (openshift/aps/asa-go-gw-config.yaml) rate-limits to 100 requests/minute per
// SOURCE IP. This script's target rate is calibrated to that per-IP limit but attempts to reach
// the full 300,000 req/min peak (18,000,000 / 60) by fanning out across run_k6_test.py's
// --task-count does NOT work in this account: Prod-App-A/Prod-App-B have no Internet
// Gateway or NAT Gateway of their own, and route 0.0.0.0/0 through a Transit Gateway to a
// centralized landing-zone egress account (BCGOV LZA pattern). Every Fargate task, no
// matter how many, egresses through that same small, fixed set of NAT IPs -- task count
// does not multiply source-IP diversity here. Multi-region doesn't help either; this
// account is single-region (ca-west-1 isn't opted in).
//
// So: run this with a modest --task-count and treat whatever aggregate throughput
// actually gets through before 429s dominate as the real finding -- that ceiling reflects
// however many NAT IPs the centralized egress account uses, not something under our
// control from here. That's arguably the more useful result anyway: it validates whether
// the gateway's rate limiter actually holds up against realistic Fargate-originated load,
// rather than chasing a literal 300,000 req/min figure that isn't achievable from this VPC.
//
// Expect a real mix of 200s and 429s once the per-IP limit is hit -- that's the point.
// Checks report both separately rather than treating 429 as a failure.
import http from "k6/http";
import { Counter } from "k6/metrics";
import { check } from "k6";

const TARGET_URL = "https://psu.api.gov.bc.ca/api/asa-go/fba/fire-centre-info";

// Per-task target rate in requests/second. Defaults to ~100 req/min (the gateway's per-IP
// limit); override with TARGET_RPS to try a different per-task rate.
const TARGET_RPS = Number(__ENV.TARGET_RPS) || 100 / 60;

const rateLimited = new Counter("rate_limited_responses");

export const options = {
  scenarios: {
    peak_burst: {
      executor: "ramping-arrival-rate",
      startRate: 0,
      timeUnit: "1s",
      preAllocatedVUs: 20,
      maxVUs: 50,
      stages: [
        { target: TARGET_RPS, duration: "30s" }, // ramp up
        { target: TARGET_RPS, duration: "60s" }, // hold at peak for 1 minute
        { target: 0, duration: "15s" }, // ramp down
      ],
    },
  },
};

export default function peakBurst() {
  const res = http.get(TARGET_URL);
  if (res.status === 429) {
    rateLimited.add(1);
  }
  check(res, {
    "status is 200": (r) => r.status === 200,
    "status is 429 (rate limited)": (r) => r.status === 429,
  });
}
