// @vitest-environment node

import { beforeEach, describe, expect, it, vi } from "vitest";
import { AxiosHeaders, type InternalAxiosRequestConfig } from "axios";
import { AuthSessionMode } from "@/slices/authenticationSlice";

const API_BASE_URL = "https://psu-api.example.com/api";
const API_PUBLIC_BASE_URL = "https://public-psu-api.example.com/api";

const setup = async ({
  sessionMode = "authenticated",
  token = "test-token",
}: {
  sessionMode?: AuthSessionMode;
  token?: string | null;
} = {}) => {
  vi.resetModules();

  const requestUse = vi.fn();
  const responseUse = vi.fn();
  const resetAuthenticationAction = {
    type: "authentication/resetAuthentication",
  };
  const store = {
    getState: vi.fn(() => ({ authentication: { sessionMode, token } })),
    dispatch: vi.fn(),
  };
  const selectAuthentication = vi.fn(
    (state: {
      authentication: {
        sessionMode: AuthSessionMode;
        token?: string | null;
      };
    }) => {
      return state.authentication;
    },
  );
  const resetAuthentication = vi.fn(() => resetAuthenticationAction);

  vi.doMock("@/api/axios", () => ({
    default: {
      interceptors: {
        request: { use: requestUse },
        response: { use: responseUse },
      },
    },
  }));
  vi.doMock("@/store", () => ({
    store,
    selectAuthentication,
  }));
  vi.doMock("@/slices/authenticationSlice", () => ({
    resetAuthentication,
  }));
  vi.doMock("@/utils/env", () => ({
    API_BASE_URL,
    API_PUBLIC_BASE_URL,
  }));

  const { configureApiInterceptors } = await import("@/utils/axiosInterceptor");

  return {
    configureApiInterceptors,
    requestUse,
    resetAuthentication,
    responseUse,
    resetAuthenticationAction,
    store,
  };
};

const configure = async (auth?: {
  sessionMode?: AuthSessionMode;
  token?: string | null;
}) => {
  const context = await setup(auth);
  context.configureApiInterceptors();
  return context;
};

const runRequestInterceptor = (
  requestUse: ReturnType<typeof vi.fn>,
  config: Partial<InternalAxiosRequestConfig> = {},
) => {
  const requestInterceptor = requestUse.mock.calls[0][0];
  return requestInterceptor({
    headers: new AxiosHeaders(),
    ...config,
  } as InternalAxiosRequestConfig);
};

const runErrorInterceptor = (
  responseUse: ReturnType<typeof vi.fn>,
  status: number,
) => {
  const errorInterceptor = responseUse.mock.calls[0][1];
  const error = { response: { status } };
  return { error, promise: errorInterceptor(error) };
};

describe("configureApiInterceptors", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetModules();
  });

  it("registers the API interceptors once", async () => {
    const { configureApiInterceptors, requestUse, responseUse } = await setup();

    configureApiInterceptors();
    configureApiInterceptors();

    expect(requestUse).toHaveBeenCalledTimes(1);
    expect(responseUse).toHaveBeenCalledTimes(1);
  });

  it("uses the authenticated API when the user is authenticated with a token", async () => {
    const { requestUse } = await configure();
    const result = runRequestInterceptor(requestUse);

    expect(result.baseURL).toBe(API_BASE_URL);
    expect(result.headers.get("Authorization")).toBe("Bearer test-token");
  });

  it("uses the public API when the user continues as guest with a stale token", async () => {
    const { requestUse } = await configure({
      sessionMode: "guest",
      token: "stale-token",
    });
    const result = runRequestInterceptor(requestUse, {
      headers: new AxiosHeaders({
        Authorization: "Bearer stale-token",
      }),
    });

    expect(result.baseURL).toBe(`${API_PUBLIC_BASE_URL}/asa-go`);
    expect(result.headers.get("Authorization")).toBeUndefined();
  });

  it("uses the public API when the authenticated session has no token", async () => {
    const { requestUse } = await configure({ token: null });
    const result = runRequestInterceptor(requestUse);

    expect(result.baseURL).toBe(`${API_PUBLIC_BASE_URL}/asa-go`);
    expect(result.headers.get("Authorization")).toBeUndefined();
  });

  it("resets authentication on 401 responses", async () => {
    const { responseUse, resetAuthenticationAction, store } = await configure();
    const { error, promise } = runErrorInterceptor(responseUse, 401);

    await expect(promise).rejects.toBe(error);

    expect(store.dispatch).toHaveBeenCalledWith(resetAuthenticationAction);
  });

  it("does not reset authentication for non-401 responses", async () => {
    const { responseUse, store } = await configure();
    const { error, promise } = runErrorInterceptor(responseUse, 500);

    await expect(promise).rejects.toBe(error);

    expect(store.dispatch).not.toHaveBeenCalled();
  });
});
