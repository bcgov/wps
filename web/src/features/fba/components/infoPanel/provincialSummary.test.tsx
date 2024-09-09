
import { Provider } from 'react-redux'
import { render } from '@testing-library/react'
import ProvincialSummary, { NO_DATA_MESSAGE } from 'features/fba/components/infoPanel/ProvincialSummary'
import provincialSummarySlice, {
  initialState,
  ProvincialSummaryState
} from 'features/fba/slices/provincialSummarySlice'
import { combineReducers, configureStore } from '@reduxjs/toolkit'
import { FireShapeAreaDetail } from 'api/fbaAPI'

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
        <ProvincialSummary advisoryThreshold={20} />
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
        <ProvincialSummary advisoryThreshold={20} />
      </Provider>
    )
    const noDataMessage = getByTestId('provincial-summary-no-data')
    expect(noDataMessage).toBeInTheDocument()
    expect(noDataMessage).toHaveTextContent(NO_DATA_MESSAGE)
  })
  it('should render fireCenterInfo component as children', () => {
    const fireShapeAreaDetails: FireShapeAreaDetail[] = [
      {
        fire_shape_id: 1,
        fire_shape_name: 'foo',
        fire_centre_name: 'fizz',
        combustible_area: 2,
        threshold: 1,
        elevated_hfi_area: 100,
        elevated_hfi_percentage: 0
      }
    ]
    const testStore = buildTestStore({
      ...initialState,
      fireShapeAreaDetails
    })
    const { getByTestId } = render(
      <Provider store={testStore}>
        <ProvincialSummary advisoryThreshold={20} />
      </Provider>
    )
    const fireCentreInfo = getByTestId('fire-centre-info')
    expect(fireCentreInfo).toBeInTheDocument()
  })
})
