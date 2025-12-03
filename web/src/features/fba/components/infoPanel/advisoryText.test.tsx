import {
  FireCentreHFIFuelStatsState,
  initialState as fuelStatsInitialState,
  getFireCentreHFIFuelStatsSuccess
} from '@/features/fba/slices/fireCentreHFIFuelStatsSlice'
import { initialState as runDatesInitialState } from '@/features/fba/slices/runDatesSlice'
import { initialState as fireCentreTPIStatsInitialState } from '@/features/fba/slices/fireCentreTPIStatsSlice'
import { createTestStore } from '@/test/testUtils'
import { render, screen, waitFor } from '@testing-library/react'
import { FireCenter, FireShape, FireShapeStatusDetail, FireZoneHFIStats } from 'api/fbaAPI'
import AdvisoryText, {
  getTopFuelsByArea,
  getTopFuelsByProportion,
  getZoneMinWindStatsText
} from 'features/fba/components/infoPanel/AdvisoryText'
import { initialState as provSummaryInitialState } from 'features/fba/slices/provincialSummarySlice'
import { cloneDeep } from 'lodash'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'
import { AdvisoryStatus } from '@/utils/constants'

const createDateTime = (year: number, month: number, day: number) => {
  return DateTime.fromObject({ year, month, day })
}

const preCoreSeasonForDate = createDateTime(2025, 5, 31)
const firstCoreSeasonDate = createDateTime(2025, 6, 1)
const lastCoreSeasonDate = createDateTime(2025, 9, 30)
const postCoreSeasonDate = createDateTime(2025, 10, 1)

const issueDate = DateTime.now()
const forDate = DateTime.now()

const mockFireCenter: FireCenter = {
  id: 1,
  name: 'Cariboo Fire Centre',
  stations: []
}

const mockFireZoneUnit: FireShape = {
  fire_shape_id: 20,
  mof_fire_zone_name: 'C2-Central Cariboo Fire Zone',
  mof_fire_centre_name: 'Cariboo Fire Centre',
  area_sqm: undefined
}

const mockAdvisoryFireZoneUnit: FireShape = {
  fire_shape_id: 18,
  mof_fire_zone_name: 'C4-100 Mile House Fire Zone',
  mof_fire_centre_name: 'Cariboo Fire Centre',
  area_sqm: undefined
}

const advisoryDetails: FireShapeStatusDetail[] = [
  {
    fire_shape_id: 18,
    status: AdvisoryStatus.ADVISORY,
    fire_shape_name: 'C4-100 Mile House Fire Zone',
    fire_centre_name: 'Cariboo Fire Centre'
  }
]

const warningDetails: FireShapeStatusDetail[] = [
  {
    fire_shape_id: 20,
    status: AdvisoryStatus.WARNING,
    fire_shape_name: 'C2-Central Cariboo Fire Zone',
    fire_centre_name: 'Cariboo Fire Centre'
  }
]

const noAdvisoryDetails: FireShapeStatusDetail[] = [
  {
    fire_shape_id: 20,
    status: null,
    fire_shape_name: 'C2-Central Cariboo Fire Zone',
    fire_centre_name: 'Cariboo Fire Centre'
  }
]

const initialHFIFuelStats = {
  'Cariboo Fire Centre': {
    '20': {
      fuel_area_stats: [
        {
          fuel_type: {
            fuel_type_id: 2,
            fuel_type_code: 'C-2',
            description: 'Boreal Spruce'
          },
          threshold: {
            id: 1,
            name: 'advisory',
            description: '4000 < hfi < 10000'
          },
          critical_hours: {
            start_time: 9,
            end_time: 13
          },
          area: 4000000000,
          fuel_area: 8000000000
        }
      ],
      min_wind_stats: [
        {
          threshold: {
            id: 1,
            name: 'advisory',
            description: '4000 < hfi < 10000'
          },
          min_wind_speed: 1
        },
        {
          threshold: {
            id: 2,
            name: 'warning',
            description: 'hfi > 1000'
          },
          min_wind_speed: 1
        }
      ]
    }
  }
}

describe('AdvisoryText', () => {
  const testStore = createTestStore({
    provincialSummary: {
      ...provSummaryInitialState,
      fireShapeAreaDetails: advisoryDetails
    }
  })

  const getInitialStore = () =>
    createTestStore({
      provincialSummary: {
        ...provSummaryInitialState,
        fireShapeAreaDetails: warningDetails
      }
    })

  const assertInitialState = () => {
    expect(screen.queryByTestId('advisory-message-advisory')).not.toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-min-wind-speeds')).not.toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-proportion')).toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-warning')).toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-wind-speed')).not.toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-slash')).not.toBeInTheDocument()
    expect(screen.queryByTestId('overnight-burning-text')).not.toBeInTheDocument()
  }

  it('should render the advisory text container', () => {
    const { getByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText issueDate={issueDate} forDate={forDate} />
      </Provider>
    )
    const advisoryText = getByTestId('advisory-text')
    expect(advisoryText).toBeInTheDocument()
  })

  it('should render default message when no fire center is selected', () => {
    const { getByTestId, queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText issueDate={issueDate} forDate={forDate} />
      </Provider>
    )
    const message = getByTestId('default-message')
    expect(message).toBeInTheDocument()
    const bulletinIssueDate = queryByTestId('bulletin-issue-date')
    expect(bulletinIssueDate).not.toBeInTheDocument()
  })

  it('should render default message when no fire zone unit is selected', () => {
    const { getByTestId, queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText issueDate={issueDate} forDate={forDate} selectedFireCenter={mockFireCenter} />
      </Provider>
    )
    const message = getByTestId('default-message')
    expect(message).toBeInTheDocument()
    const bulletinIssueDate = queryByTestId('bulletin-issue-date')
    expect(bulletinIssueDate).not.toBeInTheDocument()
  })

  it('should render no data message when the issueDate is invalid', () => {
    const { getByTestId, queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText issueDate={DateTime.invalid('test')} forDate={forDate} />
      </Provider>
    )
    const message = getByTestId('no-data-message')
    expect(message).toBeInTheDocument()
    const bulletinIssueDate = queryByTestId('bulletin-issue-date')
    expect(bulletinIssueDate).not.toBeInTheDocument()
  })

  it('should include fuel stats when their fuel area is above the 100 * 2000m * 2000m threshold', async () => {
    const store = getInitialStore()
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    assertInitialState()
    store.dispatch(getFireCentreHFIFuelStatsSuccess(initialHFIFuelStats))
    await waitFor(() => expect(screen.queryByTestId('advisory-message-warning')).toBeInTheDocument())
    await waitFor(() =>
      expect(screen.queryByTestId('advisory-message-warning')).toHaveTextContent(
        initialHFIFuelStats['Cariboo Fire Centre'][20].fuel_area_stats[0].fuel_type.fuel_type_code
      )
    )
  })

  it('should not include fuel stats when their fuel area is below the 100 * 2000m * 2000m threshold', async () => {
    const store = getInitialStore()
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    assertInitialState()
    let smallAreaStats = cloneDeep(initialHFIFuelStats)
    smallAreaStats['Cariboo Fire Centre'][20].fuel_area_stats[0].area = 10
    smallAreaStats['Cariboo Fire Centre'][20].fuel_area_stats[0].fuel_area = 100
    store.dispatch(getFireCentreHFIFuelStatsSuccess(smallAreaStats))

    await waitFor(() => expect(screen.queryByTestId('advisory-message-warning')).toBeInTheDocument())
    await waitFor(() =>
      expect(screen.queryByTestId('advisory-message-warning')).not.toHaveTextContent(
        initialHFIFuelStats['Cariboo Fire Centre'][20].fuel_area_stats[0].fuel_type.fuel_type_code
      )
    )
  })

  it('should render forDate as mmm/dd when different than issue date', () => {
    const issueDate = DateTime.fromObject({ year: 2021, month: 3, day: 24 })
    const forDate = DateTime.fromObject({ year: 2021, month: 3, day: 25 })
    const { queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    const bulletinIssueDate = queryByTestId('bulletin-issue-date')
    expect(bulletinIssueDate).toBeInTheDocument()
    expect(bulletinIssueDate).toHaveTextContent(
      `Issued on ${issueDate?.toLocaleString(DateTime.DATETIME_FULL)} for ${forDate.toLocaleString({ month: 'short', day: 'numeric' })}.`
    )
  })

  it('should render a no advisories message when there are no advisories/warnings', () => {
    const noAdvisoryStore = createTestStore({
      provincialSummary: {
        ...provSummaryInitialState
      }
    })
    const { queryByTestId } = render(
      <Provider store={noAdvisoryStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    const warningMessage = queryByTestId('advisory-message-warning')
    const advisoryMessage = queryByTestId('advisory-message-advisory')
    const proportionMessage = queryByTestId('advisory-message-proportion')
    const noAdvisoryMessage = queryByTestId('no-advisory-message')
    const zoneBulletinMessage = queryByTestId('fire-zone-unit-bulletin')
    const bulletinIssueDate = queryByTestId('bulletin-issue-date')
    expect(advisoryMessage).not.toBeInTheDocument()
    expect(warningMessage).not.toBeInTheDocument()
    expect(proportionMessage).not.toBeInTheDocument()
    expect(noAdvisoryMessage).toBeInTheDocument()
    expect(zoneBulletinMessage).toBeInTheDocument()
    expect(zoneBulletinMessage).toHaveTextContent(`${mockFireZoneUnit.mof_fire_zone_name}:`)
    expect(bulletinIssueDate).toBeInTheDocument()
    expect(bulletinIssueDate).toHaveTextContent(
      `Issued on ${issueDate?.toLocaleString(DateTime.DATETIME_FULL)} for today.`
    )
  })

  it('should render warning status', () => {
    const warningStore = createTestStore({
      provincialSummary: {
        ...provSummaryInitialState,
        fireShapeAreaDetails: warningDetails
      }
    })
    const { queryByTestId } = render(
      <Provider store={warningStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    const advisoryMessage = queryByTestId('advisory-message-advisory')
    const warningMessage = queryByTestId('advisory-message-warning')
    const proportionMessage = queryByTestId('advisory-message-proportion')
    const zoneBulletinMessage = queryByTestId('fire-zone-unit-bulletin')
    const bulletinIssueDate = queryByTestId('bulletin-issue-date')
    expect(advisoryMessage).not.toBeInTheDocument()
    expect(proportionMessage).toBeInTheDocument()
    expect(warningMessage).toBeInTheDocument()
    expect(zoneBulletinMessage).toBeInTheDocument()
    expect(zoneBulletinMessage).toHaveTextContent(`${mockFireZoneUnit.mof_fire_zone_name}:`)
    expect(bulletinIssueDate).toBeInTheDocument()
    expect(bulletinIssueDate).toHaveTextContent(
      `Issued on ${issueDate?.toLocaleString(DateTime.DATETIME_FULL)} for today.`
    )
    expect(screen.queryByTestId('advisory-message-wind-speed')).not.toBeInTheDocument()
  })

  it('should render advisory status', () => {
    const { queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockAdvisoryFireZoneUnit}
        />
      </Provider>
    )
    const advisoryMessage = queryByTestId('advisory-message-advisory')
    const warningMessage = queryByTestId('advisory-message-warning')
    const proportionMessage = queryByTestId('advisory-message-proportion')
    const zoneBulletinMessage = queryByTestId('fire-zone-unit-bulletin')
    const bulletinIssueDate = queryByTestId('bulletin-issue-date')
    expect(advisoryMessage).toBeInTheDocument()
    expect(proportionMessage).toBeInTheDocument()
    expect(warningMessage).not.toBeInTheDocument()
    expect(zoneBulletinMessage).toBeInTheDocument()
    expect(zoneBulletinMessage).toHaveTextContent(`${mockAdvisoryFireZoneUnit.mof_fire_zone_name}:`)
    expect(bulletinIssueDate).toBeInTheDocument()
    expect(bulletinIssueDate).toHaveTextContent(
      `Issued on ${issueDate?.toLocaleString(DateTime.DATETIME_FULL)} for today.`
    )
    expect(screen.queryByTestId('advisory-message-wind-speed')).not.toBeInTheDocument()
  })

  it('should render wind speed text and early fire behaviour text when fire zone unit is selected, based on wind speed & critical hours data', async () => {
    const store = getInitialStore()
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    assertInitialState()
    store.dispatch(getFireCentreHFIFuelStatsSuccess(initialHFIFuelStats))
    await waitFor(() => expect(screen.queryByTestId('advisory-message-wind-speed')).toBeInTheDocument())
    await waitFor(() => expect(screen.queryByTestId('early-advisory-text')).toBeInTheDocument())
    await waitFor(() => expect(screen.queryByTestId('overnight-burning-text')).not.toBeInTheDocument())
  })

  it('should render early advisory text and overnight burning text when critical hours go into the next day and start before 12', async () => {
    const store = getInitialStore()
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    assertInitialState()

    let overnightStats = cloneDeep(initialHFIFuelStats)
    overnightStats['Cariboo Fire Centre'][20].fuel_area_stats[0].critical_hours.end_time = 5

    store.dispatch(getFireCentreHFIFuelStatsSuccess(overnightStats))
    await waitFor(() => expect(screen.queryByTestId('early-advisory-text')).toBeInTheDocument())
    await waitFor(() => expect(screen.queryByTestId('overnight-burning-text')).toBeInTheDocument())
    await waitFor(() =>
      expect(screen.queryByTestId('overnight-burning-text')).toHaveTextContent(
        'and remain elevated into the overnight hours.'
      )
    )
  })

  it('should render only overnight burning text when critical hours go into the next day and start after 12', async () => {
    const store = getInitialStore()
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    assertInitialState()

    let overnightStats = cloneDeep(initialHFIFuelStats)
    overnightStats['Cariboo Fire Centre'][20].fuel_area_stats[0].critical_hours.end_time = 5
    overnightStats['Cariboo Fire Centre'][20].fuel_area_stats[0].critical_hours.start_time = 13

    store.dispatch(getFireCentreHFIFuelStatsSuccess(overnightStats))
    await waitFor(async () => expect(screen.queryByTestId('early-advisory-text')).not.toBeInTheDocument())
    await waitFor(async () => expect(screen.queryByTestId('overnight-burning-text')).toBeInTheDocument())
    await waitFor(() =>
      expect(screen.queryByTestId('overnight-burning-text')).toHaveTextContent(
        'Be prepared for fire behaviour to remain elevated into the overnight hours.'
      )
    )
  })

  it('should render critical hours missing message when critical hours start time is missing', () => {
    const store = createTestStore({
      provincialSummary: {
        ...provSummaryInitialState,
        fireShapeAreaDetails: advisoryDetails
      },
      fireCentreHFIFuelStats: {
        ...fuelStatsInitialState,
        ...missingCriticalHoursStartFuelStatsState.fireCentreHFIFuelStats
      }
    })
    const { queryByTestId } = render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockAdvisoryFireZoneUnit}
        />
      </Provider>
    )
    const advisoryMessage = queryByTestId('advisory-message-advisory')
    const criticalHoursMessage = queryByTestId('advisory-message-no-critical-hours')
    expect(advisoryMessage).toBeInTheDocument()
    expect(criticalHoursMessage).toBeInTheDocument()
  })

  it('should render critical hours missing message when critical hours end time is missing', () => {
    const store = createTestStore({
      provincialSummary: {
        ...provSummaryInitialState,
        fireShapeAreaDetails: advisoryDetails
      },
      fireCentreHFIFuelStats: {
        ...fuelStatsInitialState,
        ...missingCriticalHoursEndFuelStatsState.fireCentreHFIFuelStats
      }
    })
    const { queryByTestId } = render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockAdvisoryFireZoneUnit}
        />
      </Provider>
    )
    const advisoryMessage = queryByTestId('advisory-message-advisory')
    const criticalHoursMessage = queryByTestId('advisory-message-no-critical-hours')
    expect(advisoryMessage).toBeInTheDocument()
    expect(criticalHoursMessage).toBeInTheDocument()
  })

  it('should not render slash warning when critical hours duration is less than 12 hours', async () => {
    const store = getInitialStore()
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    assertInitialState()
    store.dispatch(getFireCentreHFIFuelStatsSuccess(initialHFIFuelStats))
    await waitFor(() => expect(screen.queryByTestId('advisory-message-slash')).not.toBeInTheDocument())
  })

  it('should render slash warning when critical hours duration is greater than 12 hours', async () => {
    const store = getInitialStore()
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    assertInitialState()

    let newHFIFuelStats = cloneDeep(initialHFIFuelStats)
    newHFIFuelStats['Cariboo Fire Centre'][20].fuel_area_stats[0].critical_hours.end_time = 22

    store.dispatch(getFireCentreHFIFuelStatsSuccess(newHFIFuelStats))
    await waitFor(() => expect(screen.queryByTestId('advisory-message-slash')).toBeInTheDocument())
  })

  const allInitialStates = {
    provincialSummary: provSummaryInitialState,
    fireCentreHFIFuelStats: fuelStatsInitialState,
    fireCentreTPIStats: fireCentreTPIStatsInitialState,
    runDates: runDatesInitialState
  }

  it.each(Object.keys(allInitialStates))('should render the loading indicator when %s is loading', async loadingKey => {
    const stateOverrides = Object.fromEntries(
      Object.entries(allInitialStates).map(([key, state]) => [key, { ...state, loading: key === loadingKey }])
    )

    const store = createTestStore(stateOverrides)
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    await waitFor(() => expect(screen.queryByTestId('advisory-text-loading')).toBeInTheDocument())
  })

  it('should not render the loading indicator when no ASA state is loading', async () => {
    const store = createTestStore({
      provincialSummary: { ...provSummaryInitialState, loading: false },
      fireCentreHFIFuelStats: { ...fuelStatsInitialState, loading: false },
      fireCentreTPIStats: { ...fireCentreTPIStatsInitialState, loading: false },
      runDates: { ...runDatesInitialState, loading: false }
    })
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    await waitFor(() => expect(screen.queryByTestId('advisory-text-loading')).not.toBeInTheDocument())
  })
})

const missingCriticalHoursStartFuelStatsState: FireCentreHFIFuelStatsState = {
  error: null,
  loading: false,
  fireCentreHFIFuelStats: {
    'Prince George Fire Centre': {
      '25': {
        fuel_area_stats: [
          {
            fuel_type: {
              fuel_type_id: 2,
              fuel_type_code: 'C-2',
              description: 'Boreal Spruce'
            },
            threshold: {
              id: 1,
              name: 'advisory',
              description: '4000 < hfi < 10000'
            },
            critical_hours: {
              start_time: undefined,
              end_time: 13
            },
            area: 4000,
            fuel_area: 8000
          }
        ],
        min_wind_stats: []
      }
    }
  }
}

const missingCriticalHoursEndFuelStatsState: FireCentreHFIFuelStatsState = {
  error: null,
  loading: false,
  fireCentreHFIFuelStats: {
    'Prince George Fire Centre': {
      '25': {
        fuel_area_stats: [
          {
            fuel_type: {
              fuel_type_id: 2,
              fuel_type_code: 'C-2',
              description: 'Boreal Spruce'
            },
            threshold: {
              id: 1,
              name: 'advisory',
              description: '4000 < hfi < 10000'
            },
            critical_hours: {
              start_time: 9,
              end_time: undefined
            },
            area: 4000,
            fuel_area: 8000
          }
        ],
        min_wind_stats: []
      }
    }
  }
}

const fireZoneFuelStats: FireZoneHFIStats = {
  fuel_area_stats: [
    {
      fuel_type: {
        fuel_type_id: 2,
        fuel_type_code: 'C-2',
        description: 'Boreal Spruce'
      },
      threshold: {
        id: 1,
        name: 'advisory',
        description: '4000 < hfi < 10000'
      },
      critical_hours: {
        start_time: 10.0,
        end_time: 21.0
      },
      area: 500,
      fuel_area: 1000
    },
    {
      fuel_type: {
        fuel_type_id: 2,
        fuel_type_code: 'C-2',
        description: 'Boreal Spruce'
      },
      threshold: {
        id: 2,
        name: 'warning',
        description: '4000 < hfi < 10000'
      },
      critical_hours: {
        start_time: 10.0,
        end_time: 21.0
      },
      area: 400,
      fuel_area: 1000
    },
    {
      fuel_type: {
        fuel_type_id: 9,
        fuel_type_code: 'S-1',
        description: 'Slash'
      },
      threshold: {
        id: 1,
        name: 'advisory',
        description: '4000 < hfi < 10000'
      },
      critical_hours: {
        start_time: 10.0,
        end_time: 21.0
      },
      area: 300,
      fuel_area: 1000
    },
    {
      fuel_type: {
        fuel_type_id: 4,
        fuel_type_code: 'M-1/M-2',
        description: 'mixed'
      },
      threshold: {
        id: 1,
        name: 'advisory',
        description: '4000 < hfi < 10000'
      },
      critical_hours: {
        start_time: 10.0,
        end_time: 21.0
      },
      area: 50,
      fuel_area: 100
    }
  ],
  min_wind_stats: []
}

describe('getTopFuelsByArea', () => {
  it('should return the top fuels by area before start of core season, correctly handling both advisory and warning hfi pixels', () => {
    const result = getTopFuelsByArea(fireZoneFuelStats, preCoreSeasonForDate)
    // should return the fuel records that cumulatively sum to > 75% of the total hfi area
    expect(result).toEqual(fireZoneFuelStats.fuel_area_stats.slice(0, 3))
  })
  it('should return the top fuels by area from start of core season, correctly handling both advisory and warning hfi pixels', () => {
    const result = getTopFuelsByArea(fireZoneFuelStats, firstCoreSeasonDate)
    // should return the fuel records that cumulatively sum to > 75% of the total hfi area
    expect(result).toEqual([...fireZoneFuelStats.fuel_area_stats.slice(0, 2)])
  })
  it('should return the top fuels by area until end of core season, correctly handling both advisory and warning hfi pixels', () => {
    const result = getTopFuelsByArea(fireZoneFuelStats, lastCoreSeasonDate)
    // should return the fuel records that cumulatively sum to > 75% of the total hfi area
    expect(result).toEqual(fireZoneFuelStats.fuel_area_stats.slice(0, 2))
  })
  it('should return the top fuels by area after end of core season, correctly handling both advisory and warning hfi pixels', () => {
    const result = getTopFuelsByArea(fireZoneFuelStats, postCoreSeasonDate)
    // should return the fuel records that cumulatively sum to > 75% of the total hfi area
    expect(result).toEqual(fireZoneFuelStats.fuel_area_stats.slice(0, 3))
  })
})

describe('getTopFuelsByProportion', () => {
  it('should return the top fuels by proportion of their fuel area', () => {
    const result = getTopFuelsByProportion(fireZoneFuelStats.fuel_area_stats)
    // should return the fuel records that cumulatively sum to > 90% of their own fuel area
    expect(result).toEqual(fireZoneFuelStats.fuel_area_stats.slice(0, 2))
  })
})

describe('getZoneMinWindStats', () => {
  it('should return the minimum wind speed', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 1
      },
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 2
      }
    ])
    expect(result).toEqual(`if winds exceed 1 km/h`)
  })
  it('should return the minimum wind speed when they are the same', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 1
      },
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 1
      }
    ])
    expect(result).toEqual(`if winds exceed 1 km/h`)
  })
  it('should return just advisory min wind speed', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 1
      }
    ])
    expect(result).toEqual(`if winds exceed 1 km/h`)
  })

  it('should return just warning min wind speed', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 1
      }
    ])
    expect(result).toEqual(`if winds exceed 1 km/h`)
  })

  it('should return specific text when both min wind speeds are 0 or round to 0', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 0.1
      },
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 0
      }
    ])
    expect(result).toEqual('if winds exceed 0 km/h')
  })
  it('should return specific text when only advisory min wind speed is 0', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 0
      },
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 1
      }
    ])
    expect(result).toEqual(`if winds exceed 0 km/h`)
  })
  it('should return specific text when only warning min wind speed is 0', () => {
    const result = getZoneMinWindStatsText([
      {
        threshold: {
          id: 1,
          name: 'advisory',
          description: '4000 < hfi < 10000'
        },
        min_wind_speed: 1
      },
      {
        threshold: {
          id: 2,
          name: 'warning',
          description: 'hfi > 1000'
        },
        min_wind_speed: 0
      }
    ])
    expect(result).toEqual(`if winds exceed 0 km/h`)
  })
})
