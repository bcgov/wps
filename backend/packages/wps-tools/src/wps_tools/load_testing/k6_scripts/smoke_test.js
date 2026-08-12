// Smoke test for the Distributed Load Testing on AWS pipeline itself.
// Hits k6's own public test site (test.k6.io, run by Grafana for exactly this
// purpose) rather than any real target. A script that makes zero HTTP calls
// won't work here: Taurus/BZT's k6 CSV exporter only captures request-level
// metrics, so a request-free script produces an empty results.csv and BZT
// reports the whole run as failed even when k6 itself succeeds.
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 1,
  duration: "10s",
};

export default function smokeTest() {
  const res = http.get("https://test.k6.io/");
  check(res, { "status is 200": (r) => r.status === 200 });
  sleep(1);
}
