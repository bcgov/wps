import { vi } from "vitest";
import { useAppIsActive } from "@/hooks/useAppIsActive";
import { App } from "@capacitor/app";
import { act, renderHook } from "@testing-library/react";

vi.mock("@capacitor/app", () => {
  const listeners: { [key: string]: Array<(payload: unknown) => void> } = {};

  return {
    App: {
      addListener: (event: string, cb: (payload: unknown) => void) => {
        listeners[event] = listeners[event] || [];
        listeners[event].push(cb);
        return Promise.resolve({
          remove: () => {
            listeners[event] = listeners[event].filter((fn) => fn !== cb);
          },
        });
      },
      __emit: (event: string, payload: unknown) => {
        (listeners[event] || []).forEach((cb) => cb(payload));
      },
    },
  };
});

type AppStateChangePayload = { isActive: boolean };

const emitAppEvent = (event: string, payload: AppStateChangePayload): void => {
  (
    App as unknown as {
      __emit: (event: string, payload: AppStateChangePayload) => void;
    }
  ).__emit(event, payload);
};

describe("useAppIsActive", () => {
  it("should return true by default", () => {
    const { result } = renderHook(() => useAppIsActive());
    expect(result.current).toBe(true);
  });

  it("should update state on appStateChange", () => {
    const { result } = renderHook(() => useAppIsActive());

    act(() => {
      emitAppEvent("appStateChange", { isActive: false });
    });

    expect(result.current).toBe(false);

    act(() => {
      emitAppEvent("appStateChange", { isActive: true });
    });

    expect(result.current).toBe(true);
  });
});
