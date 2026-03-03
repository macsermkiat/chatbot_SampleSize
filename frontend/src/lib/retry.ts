/**
 * Fetch wrapper with exponential backoff for Render cold-start resilience.
 *
 * Retries on network errors and 502/503/504 (server not ready).
 * Never retries 4xx client errors.
 */

interface RetryOptions {
  /** Max number of attempts (including the first). Default: 3 */
  maxAttempts?: number;
  /** Initial delay in ms before the first retry. Default: 1000 */
  initialDelayMs?: number;
  /** Multiplier applied to delay after each retry. Default: 2 */
  backoffMultiplier?: number;
}

const RETRYABLE_STATUS_CODES = new Set([502, 503, 504]);

const DEFAULT_OPTIONS: Required<RetryOptions> = {
  maxAttempts: 3,
  initialDelayMs: 1000,
  backoffMultiplier: 2,
};

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function fetchWithRetry(
  input: RequestInfo | URL,
  init?: RequestInit,
  options?: RetryOptions,
): Promise<Response> {
  const { maxAttempts, initialDelayMs, backoffMultiplier } = {
    ...DEFAULT_OPTIONS,
    ...options,
  };

  let lastError: unknown;
  let delay = initialDelayMs;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const response = await fetch(input, init);

      if (RETRYABLE_STATUS_CODES.has(response.status) && attempt < maxAttempts) {
        await sleep(delay);
        delay = delay * backoffMultiplier;
        continue;
      }

      return response;
    } catch (error) {
      // Network error (server unreachable, DNS failure, etc.)
      lastError = error;

      if (attempt < maxAttempts) {
        await sleep(delay);
        delay = delay * backoffMultiplier;
        continue;
      }
    }
  }

  throw lastError;
}
