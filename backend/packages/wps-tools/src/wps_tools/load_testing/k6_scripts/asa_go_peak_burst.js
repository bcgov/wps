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
// SOURCE IP. This script's target rate is calibrated to that per-IP limit; reaching the full
// 300,000 req/min peak (18,000,000 / 60) means fanning out across many distinct source IPs,
// which is what ../deploy_k6_lambda.py's --concurrency and --regions are for (see
// ../README.md) -- each concurrent, non-VPC Lambda invocation is likely to land on
// a distinct IP from that region's shared pool, and each region in --regions has its own
// separate pool on top of that.
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
