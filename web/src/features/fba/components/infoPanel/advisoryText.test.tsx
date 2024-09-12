import { render } from '@testing-library/react'
import { DateTime } from 'luxon'
import AdvisoryText from 'features/fba/components/infoPanel/AdvisoryText'
import { FireCenter, FireShape, FireShapeAreaDetail } from 'api/fbaAPI'
import provincialSummarySlice, {
  initialState as provSummaryInitialState,
  ProvincialSummaryState
} from 'features/fba/slices/provincialSummarySlice'
import fireCentreHFIFuelStatsSlice, {
  initialState as fuelStatsInitialState,
  FireCentreHFIFuelStatsState
} from '@/features/fba/slices/fireCentreHFIFuelStatsSlice'
import { combineReducers, configureStore } from '@reduxjs/toolkit'
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

describe('AdvisoryText', () => {
  const testStore = buildTestStore({
    ...provSummaryInitialState,
    fireShapeAreaDetails: advisoryDetails
  })

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
    const { getByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText issueDate={issueDate} forDate={forDate} advisoryThreshold={advisoryThreshold} />
      </Provider>
    )
    const message = getByTestId('default-message')
    expect(message).toBeInTheDocument()
  })

  it('should render default message when no fire zone unit is selected', () => {
    const { getByTestId } = render(
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
  })

  it('should render no data message when the issueDate is invalid', () => {
    const { getByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText issueDate={DateTime.invalid('test')} forDate={forDate} advisoryThreshold={advisoryThreshold} />
      </Provider>
    )
    const message = getByTestId('no-data-message')
    expect(message).toBeInTheDocument()
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
    const noAdvisoryMessage = queryByTestId('no-advisory-message')
    expect(advisoryMessage).not.toBeInTheDocument()
    expect(warningMessage).not.toBeInTheDocument()
    expect(noAdvisoryMessage).toBeInTheDocument()
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
    expect(advisoryMessage).not.toBeInTheDocument()
    expect(warningMessage).toBeInTheDocument()
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
    expect(advisoryMessage).toBeInTheDocument()
    expect(warningMessage).not.toBeInTheDocument()
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
})

const missingCriticalHoursStartFuelStatsState: FireCentreHFIFuelStatsState = {
  error: null,
  fireCentreHFIFuelStats: {
    'Prince George Fire Centre': {
      '25': [
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
          area: 4000
        }
      ]
    }
  }
}

const missingCriticalHoursEndFuelStatsState: FireCentreHFIFuelStatsState = {
  error: null,
  fireCentreHFIFuelStats: {
    'Prince George Fire Centre': {
      '25': [
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
          area: 4000
        }
      ]
    }
  }
}
