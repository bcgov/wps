import { describe, expect, it } from "vitest";
import reducer, { updateNetworkStatus } from "./networkStatusSlice";

describe("networkStatusSlice", () => {
  describe("updateNetworkStatus", () => {
    it.each([
      { connectionType: "wifi", connected: true },
      { connectionType: "cellular", connected: true },
      { connectionType: "none", connected: false },
      { connectionType: "unknown", connected: false },
    ] as const)(
      "sets connected=$connected when connectionType=$connectionType",
      ({ connectionType, connected }) => {
        const state = reducer(
          undefined,
          updateNetworkStatus({ connected: true, connectionType }),
        );
        expect(state.networkStatus.connected).toBe(connected);
        expect(state.networkStatus.connectionType).toBe(connectionType);
      },
    );
  });
});
