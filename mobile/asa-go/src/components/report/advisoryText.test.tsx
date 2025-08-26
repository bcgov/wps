import {
  FireCenter,
  FireShape,
  FireShapeAreaDetail,
  FireZoneHFIStatsDictionary,
  RunParameter,
  RunType,
} from "@/api/fbaAPI";
import AdvisoryText from "@/components/report/AdvisoryText";
import dataSlice, {
  DataState,
  initialState as dataInitialState,
} from "@/slices/dataSlice";
import runParametersSlice, {
  initialState as runParametersInitialState,
  RunParametersState,
} from "@/slices/runParametersSlice";
import { combineReducers, configureStore } from "@reduxjs/toolkit";
import { render, screen, waitFor } from "@testing-library/react";
import { cloneDeep } from "lodash";
import { DateTime } from "luxon";
import { Provider } from "react-redux";
import { Mock, vi } from "vitest";

// Mock hooks
vi.mock("@/hooks/useRunParameterForDate", () => ({
  useRunParameterForDate: vi.fn(),
}));
vi.mock(import("@/hooks/dataHooks"), async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useFilteredHFIStatsForDate: vi.fn(),
  };
});
import { useRunParameterForDate } from "@/hooks/useRunParameterForDate";
import { useFilteredHFIStatsForDate } from "@/hooks/dataHooks";

const advisoryThreshold = 20;
const TEST_FOR_DATE = "2025-07-14";
const TEST_FOR_DATE_LUXON = DateTime.fromISO(TEST_FOR_DATE);
const TEST_RUN_DATETIME = "2025-07-13";
const EXPECTED_FOR_DATE = DateTime.fromISO(TEST_FOR_DATE).toLocaleString({
  month: "short",
  day: "numeric",
});
const EXPECTED_RUN_DATETIME = DateTime.fromISO(
  TEST_RUN_DATETIME
).toLocaleString(DateTime.DATETIME_FULL);

const testRunParameter: RunParameter = {
  for_date: TEST_FOR_DATE,
  run_datetime: TEST_RUN_DATETIME,
  run_type: RunType.FORECAST,
};

const mockFireCenter: FireCenter = {
  id: 1,
  name: "Cariboo Fire Centre",
  stations: [],
};

const mockFireZoneUnit: FireShape = {
  fire_shape_id: 20,
  mof_fire_zone_name: "C2-Central Cariboo Fire Zone",
  mof_fire_centre_name: "Cariboo Fire Centre",
  area_sqm: undefined,
};

const mockAdvisoryFireZoneUnit: FireShape = {
  fire_shape_id: 18,
  mof_fire_zone_name: "C4-100 Mile House Fire Zone",
  mof_fire_centre_name: "Cariboo Fire Centre",
  area_sqm: undefined,
};

const advisoryDetails: FireShapeAreaDetail[] = [
  {
    fire_shape_id: 18,
    threshold: 1,
    combustible_area: 11014999365,
    elevated_hfi_area: 4158676298,
    elevated_hfi_percentage: 37,
    fire_shape_name: "C4-100 Mile House Fire Zone",
    fire_centre_name: "Cariboo Fire Centre",
  },
  {
    fire_shape_id: 18,
    threshold: 2,
    combustible_area: 11014999365,
    elevated_hfi_area: 2079887078,
    elevated_hfi_percentage: 18,
    fire_shape_name: "C4-100 Mile House Fire Zone",
    fire_centre_name: "Cariboo Fire Centre",
  },
];

const warningDetails: FireShapeAreaDetail[] = [
  {
    fire_shape_id: 20,
    threshold: 1,
    combustible_area: 11836638228,
    elevated_hfi_area: 3716282050,
    elevated_hfi_percentage: 31,
    fire_shape_name: "C2-Central Cariboo Fire Zone",
    fire_centre_name: "Cariboo Fire Centre",
  },
  {
    fire_shape_id: 20,
    threshold: 2,
    combustible_area: 11836638228,
    elevated_hfi_area: 2229415672,
    elevated_hfi_percentage: 21,
    fire_shape_name: "C2-Central Cariboo Fire Zone",
    fire_centre_name: "Cariboo Fire Centre",
  },
];

const noAdvisoryDetails: FireShapeAreaDetail[] = [
  {
    fire_shape_id: 20,
    threshold: 1,
    combustible_area: 11836638228,
    elevated_hfi_area: 3716282050,
    elevated_hfi_percentage: 10,
    fire_shape_name: "C2-Central Cariboo Fire Zone",
    fire_centre_name: "Cariboo Fire Centre",
  },
  {
    fire_shape_id: 20,
    threshold: 2,
    combustible_area: 11836638228,
    elevated_hfi_area: 2229415672,
    elevated_hfi_percentage: 2,
    fire_shape_name: "C2-Central Cariboo Fire Zone",
    fire_centre_name: "Cariboo Fire Centre",
  },
];

const mockFireZoneHFIStatsDictionary: FireZoneHFIStatsDictionary = {
  "20": {
    fuel_area_stats: [
      {
        fuel_type: {
          fuel_type_id: 2,
          fuel_type_code: "C-2",
          description: "Boreal Spruce",
        },
        threshold: {
          id: 1,
          name: "advisory",
          description: "4000 < hfi < 10000",
        },
        critical_hours: {
          start_time: 9,
          end_time: 13,
        },
        area: 4000000000,
        fuel_area: 8000000000,
      },
    ],
    min_wind_stats: [
      {
        threshold: {
          id: 1,
          name: "advisory",
          description: "4000 < hfi < 10000",
        },
        min_wind_speed: 1,
      },
      {
        threshold: {
          id: 2,
          name: "warning",
          description: "hfi > 1000",
        },
        min_wind_speed: 1,
      },
    ],
  },
};

const missingCriticalHoursStartDataState: Partial<DataState> = {
  hfiStats: {
    [TEST_FOR_DATE]: {
      runParameter: testRunParameter,
      data: {
        25: {
          fuel_area_stats: [
            {
              fuel_type: {
                fuel_type_id: 2,
                fuel_type_code: "C-2",
                description: "Boreal Spruce",
              },
              threshold: {
                id: 1,
                name: "advisory",
                description: "4000 < hfi < 10000",
              },
              critical_hours: {
                start_time: undefined,
                end_time: 13,
              },
              area: 4000,
              fuel_area: 8000,
            },
          ],
          min_wind_stats: [],
        },
      },
    },
  },
};

const missingCriticalHoursEndDataState: Partial<DataState> = {
  hfiStats: {
    [TEST_FOR_DATE]: {
      runParameter: testRunParameter,
      data: {
        "25": {
          fuel_area_stats: [
            {
              fuel_type: {
                fuel_type_id: 2,
                fuel_type_code: "C-2",
                description: "Boreal Spruce",
              },
              threshold: {
                id: 1,
                name: "advisory",
                description: "4000 < hfi < 10000",
              },
              critical_hours: {
                start_time: 9,
                end_time: undefined,
              },
              area: 4000,
              fuel_area: 8000,
            },
          ],
          min_wind_stats: [],
        },
      },
    },
  },
};

const runParametersTestState = {
  ...runParametersInitialState,
  [TEST_FOR_DATE]: {
    for_date: TEST_FOR_DATE,
    run_datetime: TEST_RUN_DATETIME,
    run_type: RunType.FORECAST,
  },
};

const runParametersTestStateNoRunDateTimeState = {
  ...runParametersInitialState,
  [TEST_FOR_DATE]: {
    for_date: TEST_FOR_DATE,
    run_type: RunType.FORECAST,
  },
};

const runParametersTestStateNoForDateState = {
  ...runParametersInitialState,
  [TEST_FOR_DATE]: {
    run_datetime: TEST_RUN_DATETIME,
    run_type: RunType.FORECAST,
  },
};

const buildTestStore = (
  dataInitialState: DataState,
  runParametersInitialState: RunParametersState
) => {
  const rootReducer = combineReducers({
    data: dataSlice,
    runParameters: runParametersSlice,
  });
  const testStore = configureStore({
    reducer: rootReducer,
    preloadedState: {
      data: dataInitialState,
      runParameters: runParametersInitialState,
    },
  });
  return testStore;
};

describe("AdvisoryText", () => {
  const testStore = buildTestStore(
    {
      ...dataInitialState,
      provincialSummaries: {
        [TEST_FOR_DATE]: {
          runParameter: testRunParameter,
          data: advisoryDetails,
        },
      },
    },
    runParametersInitialState
  );

  const getInitialStore = () =>
    buildTestStore(
      {
        ...dataInitialState,
        provincialSummaries: {
          [TEST_FOR_DATE]: {
            runParameter: testRunParameter,
            data: warningDetails,
          },
        },
      },
      runParametersTestState
    );

  const assertInitialState = () => {
    expect(
      screen.queryByTestId("advisory-message-advisory")
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("advisory-message-min-wind-speeds")
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("advisory-message-proportion")
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("advisory-message-warning")
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("advisory-message-wind-speed")
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("advisory-message-slash")
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("overnight-burning-text")
    ).not.toBeInTheDocument();
  };

  it("should render the advisory text container", () => {
    const { getByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          selectedFireCenter={undefined}
          selectedFireZoneUnit={undefined}
          advisoryThreshold={advisoryThreshold}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const advisoryText = getByTestId("advisory-text");
    expect(advisoryText).toBeInTheDocument();
  });

  it("should render default message when no fire center is selected", () => {
    const { getByTestId, queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          selectedFireCenter={undefined}
          selectedFireZoneUnit={undefined}
          advisoryThreshold={advisoryThreshold}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const message = getByTestId("default-message");
    expect(message).toBeInTheDocument();
    const bulletinIssueDate = queryByTestId("bulletin-issue-date");
    expect(bulletinIssueDate).not.toBeInTheDocument();
  });

  it("should render a no data message when no fire zone unit is selected", () => {
    const { getByTestId, queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={undefined}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const message = getByTestId("no-data-message");
    expect(message).toBeInTheDocument();
    const bulletinIssueDate = queryByTestId("bulletin-issue-date");
    expect(bulletinIssueDate).not.toBeInTheDocument();
  });

  it("should render no data message when the runDatetime is null", () => {
    const testStore = buildTestStore(
      {
        ...dataInitialState,
        provincialSummaries: {
          [TEST_FOR_DATE]: {
            runParameter: testRunParameter,
            data: advisoryDetails,
          },
        },
      },
      runParametersTestStateNoRunDateTimeState
    );
    const { getByTestId, queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={undefined}
          advisoryThreshold={advisoryThreshold}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const message = getByTestId("no-data-message");
    expect(message).toBeInTheDocument();
    const bulletinIssueDate = queryByTestId("bulletin-issue-date");
    expect(bulletinIssueDate).not.toBeInTheDocument();
  });

  it("should render no data message when the forDate is null", () => {
    const testStore = buildTestStore(
      {
        ...dataInitialState,
        provincialSummaries: {
          [TEST_FOR_DATE]: {
            runParameter: testRunParameter,
            data: advisoryDetails,
          },
        },
      },
      runParametersTestStateNoForDateState
    );
    const { getByTestId, queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={undefined}
          advisoryThreshold={advisoryThreshold}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const message = getByTestId("no-data-message");
    expect(message).toBeInTheDocument();
    const bulletinIssueDate = queryByTestId("bulletin-issue-date");
    expect(bulletinIssueDate).not.toBeInTheDocument();
  });

  it("should include fuel stats when their fuel area is above the 100 * 2000m * 2000m threshold", async () => {
    (useRunParameterForDate as Mock).mockReturnValue(testRunParameter);
    (useFilteredHFIStatsForDate as Mock).mockReturnValue(
      mockFireZoneHFIStatsDictionary
    );
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    screen.debug();
    assertInitialState();
    // act(() => store.dispatch(getDataSuccess(initialDataStateWithHFIFuelStats)));
    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-warning")
      ).toBeInTheDocument()
    );

    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-warning")
      ).toHaveTextContent(
        mockFireZoneHFIStatsDictionary[20].fuel_area_stats[0].fuel_type
          .fuel_type_code
      )
    );
  });

  it("should not include fuel stats when their fuel area is below the 100 * 2000m * 2000m threshold", async () => {
    (useRunParameterForDate as Mock).mockReturnValue(testRunParameter);
    (useFilteredHFIStatsForDate as Mock).mockReturnValue({});
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );

    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-warning")
      ).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-warning")
      ).not.toHaveTextContent(
        mockFireZoneHFIStatsDictionary[20].fuel_area_stats[0].fuel_type
          .fuel_type_code
      )
    );
  });

  it("should render forDate as mmm/dd when different than issue date", () => {
    const { queryByTestId } = render(
      <Provider store={getInitialStore()}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const bulletinIssueDate = queryByTestId("bulletin-issue-date");
    expect(bulletinIssueDate).toBeInTheDocument();
    expect(bulletinIssueDate).toHaveTextContent(
      `Issued on ${EXPECTED_RUN_DATETIME} for ${EXPECTED_FOR_DATE}.`
    );
  });

  it("should render forDate as 'today' when forDate parameter matches today's date", () => {
    const todayRunParameter = cloneDeep(testRunParameter);
    (useRunParameterForDate as Mock).mockReturnValue({
      ...todayRunParameter,
      for_date: DateTime.now().toISODate(),
    });
    (useFilteredHFIStatsForDate as Mock).mockReturnValue({});
    const store = buildTestStore(
      {
        ...dataInitialState,
        provincialSummaries: {
          [TEST_FOR_DATE]: {
            runParameter: testRunParameter,
            data: advisoryDetails,
          },
        },
      },
      runParametersTestStateNoForDateState
    );
    const { queryByTestId } = render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const bulletinIssueDate = queryByTestId("bulletin-issue-date");
    expect(bulletinIssueDate).toBeInTheDocument();
    expect(bulletinIssueDate).toHaveTextContent(
      `Issued on ${EXPECTED_RUN_DATETIME} for today.`
    );
  });

  it("should render a no advisories message when there are no advisories/warnings", () => {
    (useRunParameterForDate as Mock).mockReturnValue(testRunParameter);
    (useFilteredHFIStatsForDate as Mock).mockReturnValue({});
    const noAdvisoryStore = buildTestStore(
      {
        ...dataInitialState,
        provincialSummaries: {
          [TEST_FOR_DATE]: {
            runParameter: testRunParameter,
            data: noAdvisoryDetails,
          },
        },
      },
      runParametersTestState
    );
    const { queryByTestId } = render(
      <Provider store={noAdvisoryStore}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const warningMessage = queryByTestId("advisory-message-warning");
    const advisoryMessage = queryByTestId("advisory-message-advisory");
    const proportionMessage = queryByTestId("advisory-message-proportion");
    const noAdvisoryMessage = queryByTestId("no-advisory-message");
    const zoneBulletinMessage = queryByTestId("fire-zone-unit-bulletin");
    const bulletinIssueDate = queryByTestId("bulletin-issue-date");
    expect(advisoryMessage).not.toBeInTheDocument();
    expect(warningMessage).not.toBeInTheDocument();
    expect(proportionMessage).not.toBeInTheDocument();
    expect(noAdvisoryMessage).toBeInTheDocument();
    expect(zoneBulletinMessage).toBeInTheDocument();
    expect(zoneBulletinMessage).toHaveTextContent(
      `${mockFireZoneUnit.mof_fire_zone_name}:`
    );
    expect(bulletinIssueDate).toBeInTheDocument();
    expect(bulletinIssueDate).toHaveTextContent(
      `Issued on ${EXPECTED_RUN_DATETIME} for ${EXPECTED_FOR_DATE}.`
    );
  });

  it("should render warning status", () => {
    const warningStore = getInitialStore();
    const { queryByTestId } = render(
      <Provider store={warningStore}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const advisoryMessage = queryByTestId("advisory-message-advisory");
    const warningMessage = queryByTestId("advisory-message-warning");
    const proportionMessage = queryByTestId("advisory-message-proportion");
    const zoneBulletinMessage = queryByTestId("fire-zone-unit-bulletin");
    const bulletinIssueDate = queryByTestId("bulletin-issue-date");
    expect(advisoryMessage).not.toBeInTheDocument();
    expect(proportionMessage).toBeInTheDocument();
    expect(warningMessage).toBeInTheDocument();
    expect(zoneBulletinMessage).toBeInTheDocument();
    expect(zoneBulletinMessage).toHaveTextContent(
      `${mockFireZoneUnit.mof_fire_zone_name}:`
    );
    expect(bulletinIssueDate).toBeInTheDocument();
    expect(bulletinIssueDate).toHaveTextContent(
      `Issued on ${EXPECTED_RUN_DATETIME} for ${EXPECTED_FOR_DATE}.`
    );
    expect(
      screen.queryByTestId("advisory-message-wind-speed")
    ).not.toBeInTheDocument();
  });

  it("should render advisory status", () => {
    const { queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockAdvisoryFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const advisoryMessage = queryByTestId("advisory-message-advisory");
    const warningMessage = queryByTestId("advisory-message-warning");
    const proportionMessage = queryByTestId("advisory-message-proportion");
    const zoneBulletinMessage = queryByTestId("fire-zone-unit-bulletin");
    const bulletinIssueDate = queryByTestId("bulletin-issue-date");
    expect(advisoryMessage).toBeInTheDocument();
    expect(proportionMessage).toBeInTheDocument();
    expect(warningMessage).not.toBeInTheDocument();
    expect(zoneBulletinMessage).toBeInTheDocument();
    expect(zoneBulletinMessage).toHaveTextContent(
      `${mockAdvisoryFireZoneUnit.mof_fire_zone_name}:`
    );
    expect(bulletinIssueDate).toBeInTheDocument();
    expect(bulletinIssueDate).toHaveTextContent(
      `Issued on ${EXPECTED_RUN_DATETIME} for ${EXPECTED_FOR_DATE}.`
    );
    expect(
      screen.queryByTestId("advisory-message-wind-speed")
    ).not.toBeInTheDocument();
  });

  it("should render wind speed text and early fire behaviour text when fire zone unit is selected, based on wind speed & critical hours data", async () => {
    (useRunParameterForDate as Mock).mockReturnValue(testRunParameter);
    (useFilteredHFIStatsForDate as Mock).mockReturnValue(
      mockFireZoneHFIStatsDictionary
    );
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-wind-speed")
      ).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(
        screen.queryByTestId("overnight-burning-text")
      ).not.toBeInTheDocument()
    );
  });

  it("should render early advisory text and overnight burning text when critical hours go into the next day and start before 12", async () => {
    (useRunParameterForDate as Mock).mockReturnValue(testRunParameter);
    const filteredStatsNextDay = cloneDeep(mockFireZoneHFIStatsDictionary);
    filteredStatsNextDay[20].fuel_area_stats[0].critical_hours.end_time = 5;
    (useFilteredHFIStatsForDate as Mock).mockReturnValue(filteredStatsNextDay);
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    await waitFor(() =>
      expect(screen.queryByTestId("early-advisory-text")).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(screen.queryByTestId("overnight-burning-text")).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(screen.queryByTestId("overnight-burning-text")).toHaveTextContent(
        "and remain elevated into the overnight hours."
      )
    );
  });

  it("should render only overnight burning text when critical hours go into the next day and start after 12", async () => {
    (useRunParameterForDate as Mock).mockReturnValue(testRunParameter);
    const filteredStatsNextDay = cloneDeep(mockFireZoneHFIStatsDictionary);
    filteredStatsNextDay[20].fuel_area_stats[0].critical_hours.end_time = 5;
    filteredStatsNextDay[20].fuel_area_stats[0].critical_hours.start_time = 13;
    (useFilteredHFIStatsForDate as Mock).mockReturnValue(filteredStatsNextDay);
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    await waitFor(async () =>
      expect(
        screen.queryByTestId("early-advisory-text")
      ).not.toBeInTheDocument()
    );
    await waitFor(async () =>
      expect(screen.queryByTestId("overnight-burning-text")).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(screen.queryByTestId("overnight-burning-text")).toHaveTextContent(
        "Be prepared for fire behaviour to remain elevated into the overnight hours."
      )
    );
  });

  it("should render critical hours missing message when critical hours start time is missing", () => {
    const store = buildTestStore(
      {
        ...dataInitialState,
        hfiStats: {
          [TEST_FOR_DATE]: {
            runParameter: testRunParameter,
            data: missingCriticalHoursStartDataState,
          },
        },
        provincialSummaries: {
          [TEST_FOR_DATE]: {
            runParameter: testRunParameter,
            data: advisoryDetails,
          },
        },
      },
      runParametersTestState
    );
    const { queryByTestId } = render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockAdvisoryFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const advisoryMessage = queryByTestId("advisory-message-advisory");
    const criticalHoursMessage = queryByTestId(
      "advisory-message-no-critical-hours"
    );
    expect(advisoryMessage).toBeInTheDocument();
    expect(criticalHoursMessage).toBeInTheDocument();
  });

  it("should render critical hours missing message when critical hours end time is missing", () => {
    const store = buildTestStore(
      {
        ...dataInitialState,
        hfiStats: {
          [TEST_FOR_DATE]: {
            runParameter: testRunParameter,
            data: missingCriticalHoursEndDataState,
          },
        },
        provincialSummaries: {
          [TEST_FOR_DATE]: {
            runParameter: testRunParameter,
            data: advisoryDetails,
          },
        },
      },
      runParametersTestState
    );
    const { queryByTestId } = render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockAdvisoryFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    const advisoryMessage = queryByTestId("advisory-message-advisory");
    const criticalHoursMessage = queryByTestId(
      "advisory-message-no-critical-hours"
    );
    expect(advisoryMessage).toBeInTheDocument();
    expect(criticalHoursMessage).toBeInTheDocument();
  });

  it("should not render slash warning when critical hours duration is less than 12 hours", async () => {
    (useRunParameterForDate as Mock).mockReturnValue(testRunParameter);
    (useFilteredHFIStatsForDate as Mock).mockReturnValue(
      mockFireZoneHFIStatsDictionary
    );
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-slash")
      ).not.toBeInTheDocument()
    );
  });

  it("should render slash warning when critical hours duration is greater than 12 hours", async () => {
    (useRunParameterForDate as Mock).mockReturnValue(testRunParameter);
    const filteredCriticalHoursStats = cloneDeep(
      mockFireZoneHFIStatsDictionary
    );
    filteredCriticalHoursStats[20].fuel_area_stats[0].critical_hours.end_time = 22;
    (useFilteredHFIStatsForDate as Mock).mockReturnValue(
      filteredCriticalHoursStats
    );
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
          date={TEST_FOR_DATE_LUXON}
        />
      </Provider>
    );
    await waitFor(() =>
      expect(screen.queryByTestId("advisory-message-slash")).toBeInTheDocument()
    );
  });
});
