// Replicates the highest observed hourly traffic peak on the ASA Go production API
// (18,000,000 requests in a single hour, per production analytics) as a sustained
// one-minute burst instead of spread across an hour -- a burst-capacity / rate-limiter
// resilience test, not a realistic traffic simulation.
//
// Each iteration replays the actual sequence of public (unauthenticated) requests the
// ASA Go mobile app makes on launch -- see mobile/asa-go/src/App.tsx (fetchFireCentres,
// fetchSFMSRunParameters, fetchAndCacheData, initSubscriptions) and
// mobile/asa-go/src/utils/dataSliceUtils.ts:
//   1. GET psu/fire-centres
//   2. GET fba/fire-centre-info
//   3. GET fba/latest-sfms-run-parameters/{today}/{tomorrow}
//   4. for each of today/tomorrow that has a run parameter:
//        GET fba/provincial-summary/{run_type}/{run_datetime}/{for_date}
//        GET fba/hfi-stats/{run_type}/{run_datetime}/{for_date}
//        GET fba/tpi-stats/{run_type}/{run_datetime}/{for_date}
//   5. once per synthetic device (VU): POST device/register, then every iteration:
//      GET device/notification-settings, and occasionally (~10% of iterations):
//      POST device/notification-settings. `device/unregister` is never called -- it's unused
//      anywhere in the shipped app, so calling it here wouldn't be representative traffic.
//      register/update-settings write real rows to the DeviceToken/NotificationSettings
//      tables (register creates a row; nothing ever deletes it), so every device/token here
//      is a synthetic, clearly-tagged "k6-loadtest-..." value, never a real device, and rows
//      still accumulate across runs, just far more slowly than one-per-iteration. Periodically
//      clean up rows with device_id LIKE 'k6-loadtest-%'.
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
// Expect a real mix of 200s and 429s once the per-IP limit is hit -- that's the point. Both
// count as a pass on the single merged check below; only a genuine error (5xx, timeout,
// connection failure) trips the checks threshold and makes k6 exit non-zero.
import http from "k6/http";
import { Counter } from "k6/metrics";
import { check } from "k6";
import exec from "k6/execution";

const BASE_URL = "https://psu.api.gov.bc.ca/api/asa-go";

// Average requests per simulated app launch, assuming both today and tomorrow have a run
// parameter (the common case in-season): 9 read requests, plus the device lifecycle below,
// which is mostly just 1 (GET settings, every iteration) since register only fires once per
// VU and update-settings only ~10% of the time. Only used to calibrate the
// default iteration rate below, where being off by a request or two doesn't matter.
const REQUESTS_PER_ITERATION = 10;

// TARGET_RPS is actual HTTP requests/second (matches deploy_k6_lambda.py's --target-rps,
// which is documented and forwarded as requests/second). Defaults to the gateway's
// per-IP limit (100 req/min = 1.667 req/s); override with TARGET_RPS/--target-rps to try a
// different rate.
const TARGET_RPS = Number(__ENV.TARGET_RPS) || 100 / 60;
const TARGET_ITERATIONS_PER_SECOND = TARGET_RPS / REQUESTS_PER_ITERATION;

const rateLimited = new Counter("rate_limited_responses");

// ramping-arrival-rate's stages[].target must be an integer (k6 rejects the whole script at
// parse time otherwise). timeUnit is 60s so the default target becomes a small integer
// instead of rounding a sub-1 per-second target and drifting off the intended calibration.
// (Default: 1.667/10*60 = 10 iterations/60s, 10 req/iteration * 10 iterations/min =
// 100 req/min, matching the gateway limit.)
const TARGET_PER_TIME_UNIT = Math.max(1, Math.round(TARGET_ITERATIONS_PER_SECOND * 60));

export const options = {
  // "checks" here is the single merged check below (200 or 429 both count as a pass) -- a
  // real error (5xx, timeout, connection failure) is neither, so this is what actually makes
  // k6 exit non-zero on a genuine problem instead of silently succeeding.
  thresholds: {
    checks: ["rate>0.99"],
  },
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

function checkResponse(res) {
  if (res.status === 429) {
    rateLimited.add(1);
  }
  // A single check, not two -- "200" and "429" as separate checks are mutually exclusive by
  // construction (any given response can only match one), so every response would always
  // fail exactly one of them and the pass rate could never read as healthy even when
  // everything is working exactly as expected.
  check(res, {
    "status is 200 or 429 (rate limited)": (r) => r.status === 200 || r.status === 429,
  });
  return res;
}

function get(path) {
  return checkResponse(http.get(`${BASE_URL}/${path}`, { tags: { name: path.split("/")[0] } }));
}

function post(path, body) {
  const res = http.post(`${BASE_URL}/${path}`, JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    tags: { name: path.split("/")[0] },
  });
  return checkResponse(res);
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

// A real device registers only once per FCM token (registerDevice in pushNotificationSlice.ts
// bails out if the token hasn't changed) and then reads its notification settings on every
// launch (initSubscriptions, dispatched unconditionally in App.tsx) -- it does NOT
// register/update-settings/unregister on every single launch. Calling all four every
// iteration would overweight writes relative to real traffic and, worse, permanently
// accumulate one new synthetic DeviceToken row per iteration for the whole burst.
//
// Modeled here as: register once per synthetic "device" (VU) -- these module-scope `let`s
// are re-initialized once when k6 starts a VU, then persist across that VU's iterations, the
// same shape as a real device keeping the same token across launches -- then GET settings on
// every iteration, matching every real launch. `unregisterToken` is unused anywhere in the
// app (confirmed via grep) so it's deliberately never called here; a load test invoking a
// dead endpoint isn't representative traffic. Settings updates are user-driven (a zone
// subscription toggle), not launch-triggered, so only a small fraction of iterations send one.
let vuDeviceId = null;
let vuToken = null;

const UPDATE_SETTINGS_PROBABILITY = 0.1; // rough stand-in for "occasional user action", not a measured production ratio

function deviceLifecycle() {
  if (vuDeviceId === null) {
    const uniquePart = `${exec.vu.idInTest}-${Date.now()}`;
    vuDeviceId = `k6-loadtest-${uniquePart}`;
    vuToken = `k6-loadtest-token-${uniquePart}`;
    post("device/register", {
      platform: "android",
      token: vuToken,
      device_id: vuDeviceId,
      user_id: null,
    });
  }

  get(`device/notification-settings?device_id=${vuDeviceId}`);

  if (Math.random() < UPDATE_SETTINGS_PROBABILITY) { // NOSONAR -- not a security context: only decides whether to send an optional load-test request, nothing cryptographic or security-sensitive
    // Empty list is the only fire_zone_source_ids value guaranteed valid without looking up
    // a real zone id (it's a foreign key to Shape.source_identifier) -- still exercises the
    // endpoint's read/delete path.
    post("device/notification-settings", { device_id: vuDeviceId, fire_zone_source_ids: [] });
  }
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

  deviceLifecycle();
}
