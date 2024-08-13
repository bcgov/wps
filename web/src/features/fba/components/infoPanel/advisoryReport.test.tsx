import React from 'react'
import AdvisoryReport from 'features/fba/components/infoPanel/AdvisoryReport'
import { render } from '@testing-library/react'
import { DateTime } from 'luxon'
import { FireCenter } from 'api/fbaAPI'
import provincialSummarySlice, {
  initialState,
  ProvincialSummaryState
} from 'features/fba/slices/provincialSummarySlice'
import { combineReducers, configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'

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

const issueDate = DateTime.now()
const forDate = DateTime.now()
const advisoryThreshold = 20

const mockFireCenter: FireCenter = {
  id: 1,
  name: 'Fire Center 1',
  stations: []
}

describe('AdvisoryReport', () => {
  const testStore = buildTestStore({
    ...initialState
  })
  it('should render', () => {
    const { getByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryReport
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
        />
      </Provider>
    )
    const advisoryReport = getByTestId('advisory-report')
    expect(advisoryReport).toBeInTheDocument()
  })
  it('should render the first bulletin tab', () => {
    const { getByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryReport
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
        />
      </Provider>
    )
    const tabPanel = getByTestId('tabpanel-0')
    expect(tabPanel).toBeInTheDocument()
  })
  it('should render advisoryText as children', () => {
    const { getByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryReport
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
        />
      </Provider>
    )
    const advisoryText = getByTestId('advisory-text')
    expect(advisoryText).toBeInTheDocument()
  })
})
