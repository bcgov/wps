import React from 'react'
import { render } from '@testing-library/react'
import { DateTime } from 'luxon'
import AdvisoryText from 'features/fba/components/infoPanel/AdvisoryText'
import { FireCenter, FireShapeAreaDetail } from 'api/fbaAPI'
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
  name: 'Cariboo Fire Centre',
  stations: []
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
    ...initialState,
    fireShapeAreaDetails: advisoryDetails
  })

  it('should render the advisory text container', () => {
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

  it('should render no data message when the issueDate is invalid selected', () => {
    const { getByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText issueDate={DateTime.invalid('test')} forDate={forDate} advisoryThreshold={advisoryThreshold} />
      </Provider>
    )
    const message = getByTestId('no-data-message')
    expect(message).toBeInTheDocument()
  })

  it('should only render advisory status if there is only advisory data', () => {
    const { queryByTestId } = render(
      <Provider store={testStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
        />
      </Provider>
    )
    const advisoryMessage = queryByTestId('advisory-message-advisory')
    const warningMessage = queryByTestId('advisory-message-warning')
    expect(advisoryMessage).toBeInTheDocument()
    expect(warningMessage).not.toBeInTheDocument()
  })

  it('should only render warning status if there is only warning data', () => {
    const warningStore = buildTestStore({
      ...initialState,
      fireShapeAreaDetails: warningDetails
    })
    const { queryByTestId } = render(
      <Provider store={warningStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
        />
      </Provider>
    )
    const warningMessage = queryByTestId('advisory-message-warning')
    const advisoryMessage = queryByTestId('advisory-message-advisory')
    expect(advisoryMessage).not.toBeInTheDocument()
    expect(warningMessage).toBeInTheDocument()
  })

  it('should render both warning and advisory text if data for both exists', () => {
    const warningAdvisoryStore = buildTestStore({
      ...initialState,
      fireShapeAreaDetails: warningDetails.concat(advisoryDetails)
    })
    const { queryByTestId } = render(
      <Provider store={warningAdvisoryStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
        />
      </Provider>
    )
    const warningMessage = queryByTestId('advisory-message-warning')
    const advisoryMessage = queryByTestId('advisory-message-advisory')
    expect(advisoryMessage).toBeInTheDocument()
    expect(warningMessage).toBeInTheDocument()
  })

  it('should render a no advisories message when there are no advisories/warnings', () => {
    const noAdvisoryStore = buildTestStore({
      ...initialState,
      fireShapeAreaDetails: noAdvisoryDetails
    })
    const { queryByTestId } = render(
      <Provider store={noAdvisoryStore}>
        <AdvisoryText
          issueDate={issueDate}
          forDate={forDate}
          advisoryThreshold={advisoryThreshold}
          selectedFireCenter={mockFireCenter}
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
})
