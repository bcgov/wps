import fireCentreHFIFuelStatsSlice, {
  FireCentreHFIFuelStatsState,
  initialState as fuelStatsInitialState,
  getFireCentreHFIFuelStatsSuccess
} from '@/features/fba/slices/fireCentreHFIFuelStatsSlice'
import { combineReducers, configureStore } from '@reduxjs/toolkit'
import { render, screen, waitFor } from '@testing-library/react'
import { FireCenter, FireShape, FireShapeAreaDetail, FireZoneHFIStats } from 'api/fbaAPI'
import AdvisoryText, {
  getTopFuelsByArea,
  getTopFuelsByProportion,
  getZoneMinWindStatsText
} from 'features/fba/components/infoPanel/AdvisoryText'
import provincialSummarySlice, {
  ProvincialSummaryState,
  initialState as provSummaryInitialState
} from 'features/fba/slices/provincialSummarySlice'
import { cloneDeep } from 'lodash'
import { DateTime } from 'luxon'
import { Provider } from 'react-redux'

const buildTestStore = (
  provincialSummaryInitialState: ProvincialSummaryState,
  fuelStatsInitialState?: FireCentreHFIFuelStatsState
) => {
  const rootReducer = combineReducers({
    provincialSummary: provincialSummarySlice,
    fireCentreHFIFuelStats: fireCentreHFIFuelStatsSlice
  })
  const testStore = configureStore({
    reducer: rootReducer,
    preloadedState: {
      provincialSummary: provincialSummaryInitialState,
      fireCentreHFIFuelStats: fuelStatsInitialState
    }
  })
  return testStore
}

const issueDate = DateTime.now()
const forDate = DateTime.now()
const advisoryThreshold = 20

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

const advisoryDetails: FireShapeAreaDetail[] = [
  {
    fire_shape_id: 18,
    threshold: 1,
    combustible_area: 11014999365,
    elevated_hfi_area: 4158676298,
    elevated_hfi_percentage: 37,
    fire_shape_name: 'C4-100 Mile House Fire Zone',
    fire_centre_name: 'Cariboo Fire Centre'
  },
  {
    fire_shape_id: 18,
    threshold: 2,
    combustible_area: 11014999365,
    elevated_hfi_area: 2079887078,
    elevated_hfi_percentage: 18,
    fire_shape_name: 'C4-100 Mile House Fire Zone',
    fire_centre_name: 'Cariboo Fire Centre'
  }
]

const warningDetails: FireShapeAreaDetail[] = [
  {
    fire_shape_id: 20,
    threshold: 1,
    combustible_area: 11836638228,
    elevated_hfi_area: 3716282050,
    elevated_hfi_percentage: 31,
    fire_shape_name: 'C2-Central Cariboo Fire Zone',
    fire_centre_name: 'Cariboo Fire Centre'
  },
  {
    fire_shape_id: 20,
    threshold: 2,
    combustible_area: 11836638228,
    elevated_hfi_area: 2229415672,
    elevated_hfi_percentage: 21,
    fire_shape_name: 'C2-Central Cariboo Fire Zone',
    fire_centre_name: 'Cariboo Fire Centre'
  }
]

const noAdvisoryDetails: FireShapeAreaDetail[] = [
  {
    fire_shape_id: 20,
    threshold: 1,
    combustible_area: 11836638228,
    elevated_hfi_area: 3716282050,
    elevated_hfi_percentage: 10,
    fire_shape_name: 'C2-Central Cariboo Fire Zone',
    fire_centre_name: 'Cariboo Fire Centre'
  },
  {
    fire_shape_id: 20,
    threshold: 2,
    combustible_area: 11836638228,
    elevated_hfi_area: 2229415672,
    elevated_hfi_percentage: 2,
    fire_shape_name: 'C2-Central Cariboo Fire Zone',
    fire_centre_name: 'Cariboo Fire Centre'
  }
]

const fireCentreHFIFuelStats = {
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
          area: 4000,
          fuel_area: 8000
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
  const testStore = buildTestStore({
    ...provSummaryInitialState,
    fireShapeAreaDetails: advisoryDetails
  })

  const getInitialStore = () =>
    buildTestStore({
      ...provSummaryInitialState,
      fireShapeAreaDetails: warningDetails
    })

  const assertInitialState = () => {
    expect(screen.queryByTestId('advisory-message-advisory')).not.toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-min-wind-speeds')).not.toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-proportion')).toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-warning')).toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-wind-speed')).not.toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-early-low-wind')).not.toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-overnight')).not.toBeInTheDocument()
  }

  it('should render the advisory text container', () => {
    const { getByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText issueDate={issueDate} forDate={forDate} advisoryThreshold={advisoryThreshold} />
      </Provider>
    )
    const advisoryText = getByTestId('advisory-text')
    expect(advisoryText).toBeInTheDocument()
  })

  it('should render default message when no fire center is selected', () => {
    const { getByTestId, queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText issueDate={issueDate} forDate={forDate} advisoryThreshold={advisoryThreshold} />
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
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
        />
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
        <AdvisoryText issueDate={DateTime.invalid('test')} forDate={forDate} advisoryThreshold={advisoryThreshold} />
      </Provider>
    )
    const message = getByTestId('no-data-message')
    expect(message).toBeInTheDocument()
    const bulletinIssueDate = queryByTestId('bulletin-issue-date')
    expect(bulletinIssueDate).not.toBeInTheDocument()
  })

  it('should render forDate as mmm/dd when different than issue date', () => {
    const issueDate = DateTime.fromObject({ year: 2021, month: 3, day: 24 })
    const forDate = DateTime.fromObject({ year: 2021, month: 3, day: 25 })
    const { queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
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
    const noAdvisoryStore = buildTestStore({
      ...provSummaryInitialState,
      fireShapeAreaDetails: noAdvisoryDetails
    })
    const { queryByTestId } = render(
      <Provider store={noAdvisoryStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
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
    const warningStore = buildTestStore({
      ...provSummaryInitialState,
      fireShapeAreaDetails: warningDetails
    })
    const { queryByTestId } = render(
      <Provider store={warningStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
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
    expect(screen.queryByTestId('advisory-message-early-low-wind')).not.toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-overnight')).not.toBeInTheDocument()
  })

  it('should render advisory status', () => {
    const { queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
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
    expect(screen.queryByTestId('advisory-message-early-low-wind')).not.toBeInTheDocument()
    expect(screen.queryByTestId('advisory-message-overnight')).not.toBeInTheDocument()
  })

  it('should render wind speed text and early fire behaviour text when fire zone unit is selected, based on wind speed & critical hours data', async () => {
    const store = getInitialStore()
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    assertInitialState()

    store.dispatch(getFireCentreHFIFuelStatsSuccess(fireCentreHFIFuelStats))

    await waitFor(() => expect(screen.queryByTestId('advisory-message-wind-speed')).toBeInTheDocument())
    await waitFor(() => expect(screen.queryByTestId('advisory-message-early-low-wind')).toBeInTheDocument())
    await waitFor(() =>
      expect(screen.queryByTestId('advisory-message-early-low-wind')).toHaveTextContent(
        'Pay close attention to minor increases in wind speed and be prepared for increasing fire behaviour early in the day'
      )
    )
    await waitFor(() => expect(screen.queryByTestId('advisory-message-overnight')).not.toBeInTheDocument())
  })

  it('should render wind speed text without early fire behaviour text when fire zone unit is selected, based on wind speed & critical hours data', async () => {
    const store = getInitialStore()
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    assertInitialState()

    let noEarlyStats = cloneDeep(fireCentreHFIFuelStats)
    noEarlyStats['Cariboo Fire Centre'][20].fuel_area_stats[0].critical_hours.start_time = 13

    store.dispatch(getFireCentreHFIFuelStatsSuccess(noEarlyStats))

    await waitFor(() => expect(screen.queryByTestId('advisory-message-wind-speed')).toBeInTheDocument())
    await waitFor(() => expect(screen.queryByTestId('advisory-message-early-low-wind')).toBeInTheDocument())
    await waitFor(() =>
      expect(screen.queryByTestId('advisory-message-early-low-wind')).toHaveTextContent(
        'Pay close attention to minor increases in wind speed'
      )
    )
    await waitFor(() => expect(screen.queryByTestId('advisory-message-overnight')).not.toBeInTheDocument())
  })

  it('should render overnight burning text when critical hours go into the next day', async () => {
    const store = getInitialStore()
    render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockFireZoneUnit}
        />
      </Provider>
    )
    assertInitialState()

    let overnightStats = cloneDeep(fireCentreHFIFuelStats)
    overnightStats['Cariboo Fire Centre'][20].fuel_area_stats[0].critical_hours.end_time = 5

    store.dispatch(getFireCentreHFIFuelStatsSuccess(overnightStats))

    await waitFor(() => expect(screen.queryByTestId('advisory-message-overnight')).toBeInTheDocument())
  })

  it('should render critical hours missing message when critical hours start time is missing', () => {
    const store = buildTestStore(
      {
        ...provSummaryInitialState,
        fireShapeAreaDetails: advisoryDetails
      },
      {
        ...fuelStatsInitialState,
        fireCentreHFIFuelStats: missingCriticalHoursStartFuelStatsState.fireCentreHFIFuelStats
      }
    )
    const { queryByTestId } = render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
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
    const store = buildTestStore(
      {
        ...provSummaryInitialState,
        fireShapeAreaDetails: advisoryDetails
      },
      {
        ...fuelStatsInitialState,
        fireCentreHFIFuelStats: missingCriticalHoursEndFuelStatsState.fireCentreHFIFuelStats
      }
    )
    const { queryByTestId } = render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
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

  it('should render wind speed missing message when wind speed is missing', () => {
    const store = buildTestStore(
      {
        ...provSummaryInitialState,
        fireShapeAreaDetails: advisoryDetails
      },
      {
        ...fuelStatsInitialState,
        fireCentreHFIFuelStats: missingCriticalHoursEndFuelStatsState.fireCentreHFIFuelStats
      }
    )
    const { queryByTestId } = render(
      <Provider store={store}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
          selectedFireZoneUnit={mockAdvisoryFireZoneUnit}
        />
      </Provider>
    )
    const advisoryMessage = queryByTestId('advisory-message-advisory')
    const windSpeedMissingMessage = queryByTestId('advisory-message-no-wind-speed')
    expect(advisoryMessage).toBeInTheDocument()
    expect(windSpeedMissingMessage).toBeInTheDocument()
  })
})

const missingCriticalHoursStartFuelStatsState: FireCentreHFIFuelStatsState = {
  error: null,
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
      area: 90,
      fuel_area: 100
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
  it('should return the top fuels by area, correctly handling both advisory and warning hfi pixels', () => {
    const result = getTopFuelsByArea(fireZoneFuelStats)
    // should return the fuel records that cumulatively sum to > 75% of the total hfi area
    expect(result).toEqual(fireZoneFuelStats.fuel_area_stats.slice(0, 2))
  })
})

describe('getTopFuelsByProportion', () => {
  it('should return the top fuels by proportion of their fuel area', () => {
    const result = getTopFuelsByProportion(fireZoneFuelStats.fuel_area_stats)
    // should return the fuel records that cumulatively sum to > 90% of their own fuel area
    expect(result).toEqual(fireZoneFuelStats.fuel_area_stats.slice(0, 3))
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

  it('should return specific text when both min wind speeds are 0', () => {
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
        min_wind_speed: 0
      }
    ])
    expect(result).toBeUndefined()
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
    expect(result).toEqual(`if winds exceed 1 km/h`)
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
    expect(result).toEqual(`if winds exceed 1 km/h`)
  })
})
