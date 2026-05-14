import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const rateLimited = new Counter('rate_limited');
const upstreamErrors = new Counter('upstream_errors');

const BASE_URL = 'https://psu.api.gov.bc.ca/api/asa-go';

export const options = {
  scenarios: {
    rate_limit_check: {
      executor: 'constant-vus',
      vus: 1,
      duration: '3m',
      startTime: '0s',
      tags: { scenario: 'rate_limit_check' },
    },
    upstream_saturation: {
      executor: 'ramping-vus',
      startVUs: 1,
      startTime: '4m', // 3m test + 1m buffer after rate_limit_check
      stages: [
        { duration: '2m', target: 10 },
        { duration: '3m', target: 30 },
        { duration: '3m', target: 50 },
        { duration: '2m', target: 0 },
      ],
      tags: { scenario: 'upstream_saturation' },
    },
  },
  thresholds: {
    // rate_limit_check passes when Kong actually rate-limits us (proves the limit works)
    'http_req_failed{scenario:rate_limit_check}': ['rate>0.1'],
    'rate_limited{scenario:rate_limit_check}': ['count>0'],
    // upstream_saturation: 10s p95 is a safety net only — goal is measurement, not pass/fail
    'http_req_duration{scenario:upstream_saturation}': ['p(95)<10000'],
  },
};

export function setup() {
  const today = new Date().toISOString().split('T')[0];

  const boundsRes = http.get(`${BASE_URL}/sfms-run-bounds`);
  if (boundsRes.status !== 200) {
    throw new Error(`setup: /sfms-run-bounds returned ${boundsRes.status}: ${boundsRes.body}`);
  }

  const runRes = http.get(`${BASE_URL}/latest-sfms-run-datetime/${today}`);
  if (runRes.status !== 200) {
    throw new Error(
      `setup: /latest-sfms-run-datetime/${today} returned ${runRes.status}: ${runRes.body}`
    );
  }

  const runData = JSON.parse(runRes.body);
  if (!runData.run_parameter) {
    throw new Error(`setup: no run_parameter available for ${today} — run may not have processed yet`);
  }

  const { run_type, run_datetime } = runData.run_parameter;
  // run_datetime is ISO 8601 e.g. "2025-08-26T15:01:47.340947Z" — colons must be percent-encoded in URL paths
  return {
    runType: run_type,
    runDatetime: encodeURIComponent(run_datetime),
    forDate: today,
  };
}

function recordResponse(res) {
  if (res.status === 429) {
    rateLimited.add(1);
  } else if (res.status >= 500) {
    upstreamErrors.add(1);
  }
  check(res, {
    'X-RateLimit-Limit-Minute header present': (r) =>
      r.headers['X-Ratelimit-Limit-Minute'] !== undefined,
    'X-RateLimit-Remaining-Minute header present': (r) =>
      r.headers['X-Ratelimit-Remaining-Minute'] !== undefined,
  });
}

function runRequests(data) {
  const headers = { Accept: 'application/json' };
  const urls = [
    `${BASE_URL}/fire-centre-info`,
    `${BASE_URL}/sfms-run-bounds`,
    `${BASE_URL}/provincial-summary/${data.runType}/${data.runDatetime}/${data.forDate}`,
    `${BASE_URL}/hfi-stats/${data.runType}/${data.runDatetime}/${data.forDate}`,
  ];

  for (const url of urls) {
    const res = http.get(url, { headers });
    recordResponse(res);
  }
}

export default function (data) {
  runRequests(data);
}
