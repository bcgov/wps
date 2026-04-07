const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

interface RetryOptions {
  maxRetries?: number;
  baseDelayMs?: number;
}

export async function retryWithBackoff<T>(
  op: () => Promise<T>,
  { maxRetries = 3, baseDelayMs = 250 }: RetryOptions = {},
): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    if (attempt > 0) {
      await sleep(baseDelayMs * Math.pow(2, attempt - 1));
    }
    try {
      return await op();
    } catch (e) {
      lastError = e;
    }
  }
  throw lastError;
}
