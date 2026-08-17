// Replicates the highest observed hourly traffic peak on the ASA Go production API
// (18,000,000 requests in a single hour, per production analytics) as a sustained
// one-minute burst instead of spread across an hour -- a burst-capacity / rate-limiter
// resilience test, not a realistic traffic simulation.
//
// Each iteration replays the actual sequence of public (unauthenticated) GET requests the
// ASA Go mobile app makes on launch -- see mobile/asa-go/src/App.tsx (fetchFireCentres,
// fetchSFMSRunParameters, fetchAndCacheData) and mobile/asa-go/src/utils/dataSliceUtils.ts:
//   1. GET psu/fire-centres
//   2. GET fba/fire-centre-info
//   3. GET fba/latest-sfms-run-parameters/{today}/{tomorrow}
//   4. for each of today/tomorrow that has a run parameter:
//        GET fba/provincial-summary/{run_type}/{run_datetime}/{for_date}
//        GET fba/hfi-stats/{run_type}/{run_datetime}/{for_date}
//        GET fba/tpi-stats/{run_type}/{run_datetime}/{for_date}
//
// Target: https://psu.api.gov.bc.ca/api/asa-go (production).
//
// The gateway (openshift/aps/asa-go-gw-config.yaml) rate-limits to 100 requests/minute per
// SOURCE IP, across the whole /api/asa-go path (not per-endpoint). This script's target
// iteration rate is calibrated to that per-IP limit; reaching the full 300,000 req/min peak
// (18,000,000 / 60) means fanning out across many distinct source IPs, which is what
// ../deploy_k6_lambda.py's --concurrency and --regions are for (see ../README.md) -- each
// concurrent, non-VPC Lambda invocation is likely to land on a distinct IP from that region's
// shared pool, and each region in --regions has its own separate pool on top of that.
//
// Expect a real mix of 200s and 429s once the per-IP limit is hit -- that's the point.
// Checks report both separately rather than treating 429 as a failure.
import http from "k6/http";
import { Counter } from "k6/metrics";
import { check } from "k6";

const BASE_URL = "https://psu.api.gov.bc.ca/api/asa-go";

// Requests per simulated app launch, assuming both today and tomorrow have a run parameter
// (the common case in-season). Used only to calibrate the default iteration rate below.
const REQUESTS_PER_ITERATION = 9;

// Per-task target rate in iterations/second (one iteration == one simulated app launch).
// Defaults to the gateway's per-IP limit (100 req/min) divided by the requests each
// iteration makes, i.e. ~1 app launch per IP every ~54s; override with TARGET_RPS to try a
// different per-task rate.
const TARGET_RPS = Number(__ENV.TARGET_RPS) || 100 / 60 / REQUESTS_PER_ITERATION;

const rateLimited = new Counter("rate_limited_responses");

// ramping-arrival-rate's stages[].target must be an integer (k6 rejects the whole script at
// parse time otherwise). timeUnit is 60s so the default target becomes a small integer
// instead of rounding a sub-1 per-second target and drifting off the intended calibration.
const TARGET_PER_TIME_UNIT = Math.max(1, Math.round(TARGET_RPS * 60));

export const options = {
  scenarios: {
    peak_burst: {
      executor: "ramping-arrival-rate",
      startRate: 0,
      timeUnit: "60s",
      preAllocatedVUs: 20,
      maxVUs: 50,
      stages: [
        { target: TARGET_PER_TIME_UNIT, duration: "30s" }, // ramp up
        { target: TARGET_PER_TIME_UNIT, duration: "60s" }, // hold at peak for 1 minute
        { target: 0, duration: "15s" }, // ramp down
      ],
    },
  },
};

// ASA_GO_TIMEZONE (mobile/asa-go/src/utils/constants.ts) is a fixed UTC-7 offset, not a real
// (DST-aware) IANA zone -- matched here with plain UTC math rather than pulling in a
// timezone library.
function isoDatePacific(offsetDays) {
  const d = new Date(Date.now() - 7 * 60 * 60 * 1000 + offsetDays * 24 * 60 * 60 * 1000);
  return d.toISOString().slice(0, 10);
}

const TODAY_KEY = isoDatePacific(0);
const TOMORROW_KEY = isoDatePacific(1);

function get(path) {
  const res = http.get(`${BASE_URL}/${path}`, { tags: { name: path.split("/")[0] } });
  if (res.status === 429) {
    rateLimited.add(1);
  }
  check(res, {
    "status is 200": (r) => r.status === 200,
    "status is 429 (rate limited)": (r) => r.status === 429,
  });
  return res;
}

function fetchDayStats(runParameter) {
  if (!runParameter) {
    return;
  }
  const { run_type, run_datetime, for_date } = runParameter;
  const runTypeLower = run_type.toLowerCase();
  get(`fba/provincial-summary/${runTypeLower}/${encodeURI(run_datetime)}/${for_date}`);
  get(`fba/hfi-stats/${runTypeLower}/${run_datetime}/${for_date}`);
  get(`fba/tpi-stats/${runTypeLower}/${run_datetime}/${for_date}`);
}

export default function peakBurst() {
  get("psu/fire-centres");
  get("fba/fire-centre-info");

  const runParamsRes = get(`fba/latest-sfms-run-parameters/${TODAY_KEY}/${TOMORROW_KEY}`);
  let runParameters = {};
  if (runParamsRes.status === 200) {
    try {
      runParameters = runParamsRes.json("run_parameters") || {};
    } catch {
      runParameters = {};
    }
  }

  fetchDayStats(runParameters[TODAY_KEY]);
  fetchDayStats(runParameters[TOMORROW_KEY]);
}
