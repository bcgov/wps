import {
  FireCenter,
  FireShape,
  FireShapeAreaDetail,
  RunType,
} from "@/api/fbaAPI";
import AdvisoryText from "@/components/report/AdvisoryText";
import fireCentreHFIFuelStatsSlice, {
  FireCentreHFIFuelStatsState,
  initialState as fuelStatsInitialState,
  getFireCentreHFIFuelStatsSuccess,
} from "@/slices/fireCentreHFIFuelStatsSlice";
import provincialSummarySlice, {
  ProvincialSummaryState,
  initialState as provSummaryInitialState,
} from "@/slices/provincialSummarySlice";
import runParameterSlice, {
  initialState as runParameterInitialState,
  RunParameterState,
} from "@/slices/runParameterSlice";
import { combineReducers, configureStore } from "@reduxjs/toolkit";
import { render, screen, waitFor } from "@testing-library/react";
import { cloneDeep } from "lodash";
import { DateTime } from "luxon";
import { Provider } from "react-redux";

const advisoryThreshold = 20;
const TEST_FOR_DATE = "2025-07-14";
const TEST_RUN_DATETIME = "2025-07-13";
const EXPECTED_FOR_DATE = DateTime.fromISO(TEST_FOR_DATE).toLocaleString({
  month: "short",
  day: "numeric",
});
const EXPECTED_RUN_DATETIME = DateTime.fromISO(
  TEST_RUN_DATETIME
).toLocaleString(DateTime.DATETIME_FULL);

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

const initialHFIFuelStats = {
  "Cariboo Fire Centre": {
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
  },
};

const runParameterTestState = {
  ...runParameterInitialState,
  forDate: TEST_FOR_DATE,
  runDatetime: TEST_RUN_DATETIME,
  runType: RunType.FORECAST,
};

const buildTestStore = (
  provincialSummaryInitialState: ProvincialSummaryState,
  runParameterInitialState: RunParameterState,
  fuelStatsInitialState?: FireCentreHFIFuelStatsState
) => {
  const rootReducer = combineReducers({
    provincialSummary: provincialSummarySlice,
    runParameter: runParameterSlice,
    fireCentreHFIFuelStats: fireCentreHFIFuelStatsSlice,
  });
  const testStore = configureStore({
    reducer: rootReducer,
    preloadedState: {
      provincialSummary: provincialSummaryInitialState,
      runParameter: runParameterInitialState,
      fireCentreHFIFuelStats: fuelStatsInitialState,
    },
  });
  return testStore;
};

describe("AdvisoryText", () => {
  const testStore = buildTestStore(
    {
      ...provSummaryInitialState,
      fireShapeAreaDetails: advisoryDetails,
    },
    runParameterInitialState
  );

  const getInitialStore = () =>
    buildTestStore(
      {
        ...provSummaryInitialState,
        fireShapeAreaDetails: warningDetails,
      },
      runParameterTestState
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
    ).not.toBeInTheDocument();
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
        ...provSummaryInitialState,
        fireShapeAreaDetails: advisoryDetails,
      },
      { ...runParameterInitialState, forDate: TEST_FOR_DATE }
    );
    const { getByTestId, queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={undefined}
          advisoryThreshold={advisoryThreshold}
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
        ...provSummaryInitialState,
        fireShapeAreaDetails: advisoryDetails,
      },
      {
        ...runParameterInitialState,
        runDatetime: TEST_RUN_DATETIME,
      }
    );
    const { getByTestId, queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={undefined}
          advisoryThreshold={advisoryThreshold}
        />
      </Provider>
    );
    const message = getByTestId("no-data-message");
    expect(message).toBeInTheDocument();
    const bulletinIssueDate = queryByTestId("bulletin-issue-date");
    expect(bulletinIssueDate).not.toBeInTheDocument();
  });

  it("should include fuel stats when their fuel area is above the 100 * 2000m * 2000m threshold", async () => {
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    );
    assertInitialState();
    store.dispatch(getFireCentreHFIFuelStatsSuccess(initialHFIFuelStats));
    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-warning")
      ).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-warning")
      ).toHaveTextContent(
        initialHFIFuelStats["Cariboo Fire Centre"][20].fuel_area_stats[0]
          .fuel_type.fuel_type_code
      )
    );
  });

  it("should not include fuel stats when their fuel area is below the 100 * 2000m * 2000m threshold", async () => {
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    );
    assertInitialState();
    const smallAreaStats = cloneDeep(initialHFIFuelStats);
    smallAreaStats["Cariboo Fire Centre"][20].fuel_area_stats[0].area = 10;
    smallAreaStats[
      "Cariboo Fire Centre"
    ][20].fuel_area_stats[0].fuel_area = 100;
    store.dispatch(getFireCentreHFIFuelStatsSuccess(smallAreaStats));

    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-warning")
      ).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-warning")
      ).not.toHaveTextContent(
        initialHFIFuelStats["Cariboo Fire Centre"][20].fuel_area_stats[0]
          .fuel_type.fuel_type_code
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
        />
      </Provider>
    );
    const bulletinIssueDate = queryByTestId("bulletin-issue-date");
    expect(bulletinIssueDate).toBeInTheDocument();
    expect(bulletinIssueDate).toHaveTextContent(
      `Issued on ${EXPECTED_RUN_DATETIME} for ${EXPECTED_FOR_DATE}.`
    );
  });

  it("should render a no advisories message when there are no advisories/warnings", () => {
    const noAdvisoryStore = buildTestStore(
      {
        ...provSummaryInitialState,
        fireShapeAreaDetails: noAdvisoryDetails,
      },
      runParameterTestState
    );
    const { queryByTestId } = render(
      <Provider store={noAdvisoryStore}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
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
    const warningStore = buildTestStore(
      {
        ...provSummaryInitialState,
        fireShapeAreaDetails: warningDetails,
      },
      runParameterTestState
    );
    const { queryByTestId } = render(
      <Provider store={warningStore}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
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
    const advisoryStore = buildTestStore(
      {
        ...provSummaryInitialState,
        fireShapeAreaDetails: advisoryDetails,
      },
      runParameterTestState
    );
    const { queryByTestId } = render(
      <Provider store={advisoryStore}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockAdvisoryFireZoneUnit}
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
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    );
    assertInitialState();
    store.dispatch(getFireCentreHFIFuelStatsSuccess(initialHFIFuelStats));
    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-wind-speed")
      ).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(screen.queryByTestId("early-advisory-text")).toBeInTheDocument()
    );
    await waitFor(() =>
      expect(
        screen.queryByTestId("overnight-burning-text")
      ).not.toBeInTheDocument()
    );
  });

  it("should render early advisory text and overnight burning text when critical hours go into the next day and start before 12", async () => {
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    );
    assertInitialState();

    const overnightStats = cloneDeep(initialHFIFuelStats);
    overnightStats[
      "Cariboo Fire Centre"
    ][20].fuel_area_stats[0].critical_hours.end_time = 5;

    store.dispatch(getFireCentreHFIFuelStatsSuccess(overnightStats));
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
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    );
    assertInitialState();

    const overnightStats = cloneDeep(initialHFIFuelStats);
    overnightStats[
      "Cariboo Fire Centre"
    ][20].fuel_area_stats[0].critical_hours.end_time = 5;
    overnightStats[
      "Cariboo Fire Centre"
    ][20].fuel_area_stats[0].critical_hours.start_time = 13;

    store.dispatch(getFireCentreHFIFuelStatsSuccess(overnightStats));
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
        ...provSummaryInitialState,
        fireShapeAreaDetails: advisoryDetails,
      },
      runParameterTestState,
      {
        ...fuelStatsInitialState,
        fireCentreHFIFuelStats:
          missingCriticalHoursStartFuelStatsState.fireCentreHFIFuelStats,
      }
    );
    const { queryByTestId } = render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockAdvisoryFireZoneUnit}
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
        ...provSummaryInitialState,
        fireShapeAreaDetails: advisoryDetails,
      },
      runParameterTestState,
      {
        ...fuelStatsInitialState,
        fireCentreHFIFuelStats:
          missingCriticalHoursEndFuelStatsState.fireCentreHFIFuelStats,
      }
    );
    const { queryByTestId } = render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockAdvisoryFireZoneUnit}
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
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    );
    assertInitialState();
    store.dispatch(getFireCentreHFIFuelStatsSuccess(initialHFIFuelStats));
    await waitFor(() =>
      expect(
        screen.queryByTestId("advisory-message-slash")
      ).not.toBeInTheDocument()
    );
  });

  it("should render slash warning when critical hours duration is greater than 12 hours", async () => {
    const store = getInitialStore();
    render(
      <Provider store={store}>
        <AdvisoryText
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    );
    assertInitialState();

    const newHFIFuelStats = cloneDeep(initialHFIFuelStats);
    newHFIFuelStats[
      "Cariboo Fire Centre"
    ][20].fuel_area_stats[0].critical_hours.end_time = 22;

    store.dispatch(getFireCentreHFIFuelStatsSuccess(newHFIFuelStats));
    await waitFor(() =>
      expect(screen.queryByTestId("advisory-message-slash")).toBeInTheDocument()
    );
  });
});

const missingCriticalHoursStartFuelStatsState: FireCentreHFIFuelStatsState = {
  error: null,
  fireCentreHFIFuelStats: {
    "Prince George Fire Centre": {
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
};

const missingCriticalHoursEndFuelStatsState: FireCentreHFIFuelStatsState = {
  error: null,
  fireCentreHFIFuelStats: {
    "Prince George Fire Centre": {
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
};