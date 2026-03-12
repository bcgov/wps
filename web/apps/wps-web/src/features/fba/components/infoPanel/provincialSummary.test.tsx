import { Provider } from 'react-redux'
import { render } from '@testing-library/react'
import ProvincialSummary, { NO_DATA_MESSAGE } from 'features/fba/components/infoPanel/ProvincialSummary'
import provincialSummarySlice, { initialState } from 'features/fba/slices/provincialSummarySlice'
import { combineReducers } from '@reduxjs/toolkit'
import { FireShapeStatusDetail } from 'api/fbaAPI'
import { AdvisoryStatus } from '@/utils/constants'
import { createTestStore } from '@/test/testUtils'

const provincialSummaryReducer = combineReducers({ provincialSummary: provincialSummarySlice })

describe('ProvincialSummary', () => {
  it('should render', () => {
    const testStore = createTestStore({ provincialSummary: { ...initialState } }, provincialSummaryReducer)
    const { getByTestId } = render(
      <Provider store={testStore}>
        <ProvincialSummary />
      </Provider>
    )
    const provincialSummary = getByTestId('provincial-summary')
    expect(provincialSummary).toBeInTheDocument()
  })
  it('should have no data message when provincial summary has no data', () => {
    const testStore = createTestStore({ provincialSummary: { ...initialState } }, provincialSummaryReducer)
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
    const testStore = createTestStore(
      { provincialSummary: { ...initialState, fireShapeStatusDetails } },
      provincialSummaryReducer
    )
    const { getByTestId } = render(
      <Provider store={testStore}>
        <ProvincialSummary />
      </Provider>
    )
    const fireCentreInfo = getByTestId('fire-centre-info')
    expect(fireCentreInfo).toBeInTheDocument()
  })
})
