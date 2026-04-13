import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { retryWithBackoff } from "./retryWithBackoff";

describe("retryWithBackoff", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("resolves immediately when the operation succeeds on the first attempt", async () => {
    const op = vi.fn().mockResolvedValue("result");
    const result = await retryWithBackoff(op);
    expect(result).toBe("result");
    expect(op).toHaveBeenCalledTimes(1);
  });

  it("retries and resolves when the operation succeeds on a later attempt", async () => {
    const op = vi
      .fn()
      .mockRejectedValueOnce(new Error("fail"))
      .mockResolvedValueOnce("result");
    const promise = retryWithBackoff(op);
    await vi.advanceTimersByTimeAsync(1000);
    expect(await promise).toBe("result");
    expect(op).toHaveBeenCalledTimes(2);
  });

  it("throws after exhausting all retries", async () => {
    const op = vi.fn().mockRejectedValue(new Error("persistent"));
    const caught = retryWithBackoff(op, { maxRetries: 3 }).catch(
      (e) => e as Error,
    );
    await vi.advanceTimersByTimeAsync(7000); // 1000 + 2000 + 4000
    // @ts-expect-error - promise rejection type is intentionally coerced for test
    expect((await caught).message).toBe("persistent");
    expect(op).toHaveBeenCalledTimes(4); // 1 initial + 3 retries
  });

  it("does not retry before the delay elapses", async () => {
    const op = vi.fn().mockRejectedValue(new Error("fail"));
    const promise = retryWithBackoff(op, {
      maxRetries: 3,
      baseDelayMs: 1000,
    }).catch(() => {});
    await vi.advanceTimersByTimeAsync(999);
    expect(op).toHaveBeenCalledTimes(1); // still on first attempt, waiting for delay
    await vi.advanceTimersByTimeAsync(7000);
    await promise;
  });

  it("uses exponential backoff delays between retries", async () => {
    const op = vi.fn().mockRejectedValue(new Error("fail"));
    const promise = retryWithBackoff(op, {
      maxRetries: 3,
      baseDelayMs: 1000,
    }).catch(() => {});

    // After 1st failure, waits 1000ms before retry 1
    await vi.advanceTimersByTimeAsync(999);
    expect(op).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1); // 1000ms elapsed → retry 1
    expect(op).toHaveBeenCalledTimes(2);

    // After 2nd failure, waits 2000ms before retry 2
    await vi.advanceTimersByTimeAsync(1999);
    expect(op).toHaveBeenCalledTimes(2);
    await vi.advanceTimersByTimeAsync(1); // 2000ms elapsed → retry 2
    expect(op).toHaveBeenCalledTimes(3);

    // After 3rd failure, waits 4000ms before retry 3
    await vi.advanceTimersByTimeAsync(3999);
    expect(op).toHaveBeenCalledTimes(3);
    await vi.advanceTimersByTimeAsync(1); // 4000ms elapsed → retry 3
    expect(op).toHaveBeenCalledTimes(4);

    await promise;
  });

  it("uses custom baseDelayMs", async () => {
    const op = vi
      .fn()
      .mockRejectedValueOnce(new Error("fail"))
      .mockResolvedValueOnce("ok");
    const promise = retryWithBackoff(op, { baseDelayMs: 500 });
    await vi.advanceTimersByTimeAsync(499);
    expect(op).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);
    expect(await promise).toBe("ok");
    expect(op).toHaveBeenCalledTimes(2);
  });
});
