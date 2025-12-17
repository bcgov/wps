import { renderHook } from "@testing-library/react";
import { useFireCentreDetails } from "./useFireCentreDetails";
import { FireCenter, RunParameter, RunType } from "api/fbaAPI";
import { Provider } from "react-redux";
import { DateTime } from "luxon";
import { AdvisoryStatus } from "@/utils/constants";
import { createTestStore } from "@/testUtils";

describe("useFireCentreDetails", () => {
  it("returns grouped and sorted fire shape details for a selected fire center", () => {
    const testDate = DateTime.fromISO("2025-08-25");
    const mockFireCenter: FireCenter = {
      id: 1,
      name: "Test Centre",
      stations: [],
    };

    const mockProvincialSummaries = [
      {
        fire_shape_id: 2,
        fire_shape_name: "Zone B",
        fire_centre_name: "Test Centre",
        status: AdvisoryStatus.ADVISORY,
      },
      {
        fire_shape_id: 1,
        fire_shape_name: "Zone A",
        fire_centre_name: "Test Centre",
        status: AdvisoryStatus.WARNING,
      },
    ];

    const mockRunParameter: RunParameter = {
      for_date: "2025-08-25",
      run_datetime: "2025-08-25T12:00:00Z",
      run_type: RunType.FORECAST,
    };

    const store = createTestStore({
      data: {
        provincialSummaries: {
          "2025-08-25": {
            data: mockProvincialSummaries,
            runParameter: mockRunParameter,
          },
        },
        loading: false,
        error: null,
        lastUpdated: null,
        tpiStats: {},
        hfiStats: {},
      },
    });

    const { result } = renderHook(
      () => useFireCentreDetails(mockFireCenter, testDate),
      {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      }
    );

    expect(result.current).toEqual([
      {
        fire_shape_id: 1,
        fire_shape_name: "Zone A",
        fire_centre_name: "Test Centre",
        status: AdvisoryStatus.WARNING,
      },
      {
        fire_shape_id: 2,
        fire_shape_name: "Zone B",
        fire_centre_name: "Test Centre",
        status: AdvisoryStatus.ADVISORY,
      },
    ]);
  });

  it("returns an empty array if no fire center is selected", () => {
    const testDate = DateTime.fromISO("2025-08-25");
    const store = createTestStore();

    const { result } = renderHook(
      () => useFireCentreDetails(undefined, testDate),
      {
        wrapper: ({ children }) => (
          <Provider store={store}>{children}</Provider>
        ),
      }
    );

    expect(result.current).toEqual([]);
  });
});
