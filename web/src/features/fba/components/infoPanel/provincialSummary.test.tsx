import { Provider } from 'react-redux'
import { render } from '@testing-library/react'
import ProvincialSummary, { NO_DATA_MESSAGE } from 'features/fba/components/infoPanel/ProvincialSummary'
import provincialSummarySlice, {
  initialState,
  ProvincialSummaryState
} from 'features/fba/slices/provincialSummarySlice'
import { combineReducers, configureStore } from '@reduxjs/toolkit'
import { FireShapeStatusDetail } from 'api/fbaAPI'
import { AdvisoryStatus } from '@/utils/constants'

const buildTestStore = (initialState: ProvincialSummaryState) => {
  const rootReducer = combineReducers({ provincialSummary: provincialSummarySlice })
  const testStore = configureStore({
    reducer: rootReducer,
    preloadedState: {
      provincialSummary: initialState
    }
  })
  return testStore
}

describe('ProvincialSummary', () => {
  it('should render', () => {
    const testStore = buildTestStore({
      ...initialState
    })
    const { getByTestId } = render(
      <Provider store={testStore}>
        <ProvincialSummary />
      </Provider>
    )
    const provincialSummary = getByTestId('provincial-summary')
    expect(provincialSummary).toBeInTheDocument()
  })
  it('should have no data message when provincial summary has no data', () => {
    const testStore = buildTestStore({
      ...initialState
    })
    const { getByTestId } = render(
      <Provider store={testStore}>
        <ProvincialSummary />
      </Provider>
    )
    const noDataMessage = getByTestId('provincial-summary-no-data')
    expect(noDataMessage).toBeInTheDocument()
    expect(noDataMessage).toHaveTextContent(NO_DATA_MESSAGE)
  })
  it('should render fireCenterInfo component as children', () => {
    const fireShapeStatusDetails: FireShapeStatusDetail[] = [
      {
        fire_shape_id: 1,
        fire_shape_name: 'foo',
        fire_centre_name: 'fizz',
        status: AdvisoryStatus.ADVISORY
      }
    ]
    const testStore = buildTestStore({
      ...initialState,
      fireShapeStatusDetails: fireShapeStatusDetails
    })
    const { getByTestId } = render(
      <Provider store={testStore}>
        <ProvincialSummary />
      </Provider>
    )
    const fireCentreInfo = getByTestId('fire-centre-info')
    expect(fireCentreInfo).toBeInTheDocument()
  })
})
