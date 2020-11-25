import React from 'react'
import MockAdapter from 'axios-mock-adapter'
import {
  waitForElementToBeRemoved,
  waitForElement,
  cleanup,
  fireEvent
} from '@testing-library/react'

import axios from 'api/axios'
import { selectStations } from 'app/rootReducer'
import { renderWithRedux } from 'utils/testUtils'
import { WEATHER_STATION_MAP_LINK, FWI_VALUES_DECIMAL } from 'utils/constants'
import { NOT_AVAILABLE } from 'utils/strings'
import PercentileCalculatorPage from 'features/percentileCalculator/pages/PercentileCalculatorPage'
import {
  mockStations,
  mockPercentilesResponse,
  mockNullPercentilesResponse
} from 'features/percentileCalculator/pages/PercentileCalculatorPage.mock'

const mockAxios = new MockAdapter(axios)

afterEach(() => {
  mockAxios.reset()
  cleanup()
})

it('renders FWI calculator page', async () => {
  const { getByText, getByTestId, store } = renderWithRedux(<PercentileCalculatorPage />)

  // Check if all the components are rendered
  expect(getByText(/Percentile Calculator/i)).toBeInTheDocument()
  expect(selectStations(store.getState()).stations).toEqual([])
  expect(getByTestId('weather-station-dropdown')).toBeInTheDocument()
  expect(getByTestId('time-range-slider')).toBeInTheDocument()
  expect(getByTestId('percentile-textfield')).toBeInTheDocument()

  // Map link tests
  expect(getByTestId('launch-map-link').closest('a')).toHaveAttribute(
    'href',
    WEATHER_STATION_MAP_LINK
  )
  fireEvent.click(getByTestId('launch-map-link'))
})

it('renders weather stations dropdown with data', async () => {
  mockAxios.onGet('/stations/').replyOnce(200, { weather_stations: mockStations })

  const { getByText, getByTestId, store } = renderWithRedux(<PercentileCalculatorPage />)

  expect(selectStations(store.getState()).stations).toEqual([])
  fireEvent.click(getByTestId('weather-station-dropdown'))

  const [station1] = await waitForElement(() => [
    getByText(`${mockStations[0].name} (${mockStations[0].code})`),
    getByText(`${mockStations[1].name} (${mockStations[1].code})`)
  ])

  fireEvent.click(station1)
  expect(selectStations(store.getState()).stations).toEqual(mockStations)
})

it('renders error message when fetching stations failed', async () => {
  mockAxios.onGet('/stations/').replyOnce(404)

  const { getByText, queryByText, store } = renderWithRedux(<PercentileCalculatorPage />)

  expect(queryByText(/Error occurred/i)).not.toBeInTheDocument()
  expect(selectStations(store.getState()).error).toBeNull()

  await waitForElement(() => getByText(/Error occurred/i))

  expect(selectStations(store.getState()).error).toBeTruthy()
})

it('renders time range slider with selecting the range', async () => {
  const { getByTestId } = renderWithRedux(<PercentileCalculatorPage />)
  const sliderWrapper = getByTestId('time-range-slider')
  const timeRangeSliderInput = sliderWrapper.children[1].children[2]

  expect(sliderWrapper).toBeInTheDocument()
  fireEvent.change(timeRangeSliderInput, {
    target: { value: 20 }
  })
  expect(timeRangeSliderInput.getAttribute('value')).toEqual('20')
})

it('renders percentiles result in response to user inputs', async () => {
  mockAxios.onGet('/stations/').replyOnce(200, { weather_stations: mockStations })
  mockAxios.onPost('/percentiles/').replyOnce(200, mockPercentilesResponse)

  const { store, getByText, getByTestId, queryByTestId } = renderWithRedux(
    <PercentileCalculatorPage />
  )

  // Select a weather station
  fireEvent.click(getByTestId('weather-station-dropdown'))
  const [station0] = await waitForElement(() => [
    getByText(`${mockStations[0].name} (${mockStations[0].code})`),
    getByText(`${mockStations[1].name} (${mockStations[1].code})`)
  ])
  fireEvent.click(station0)

  // Send the request
  fireEvent.click(getByTestId('calculate-percentiles-button'))

  // Test things before getting the result
  expect(store.getState().percentiles.result).toBeNull()
  expect(queryByTestId('percentile-documentation-card')).not.toBeInTheDocument()

  // Wait until the calculation is fetched
  await waitForElement(() => getByTestId('percentile-result-tables'))

  // Validate the correct request body
  expect(mockAxios.history.post.length).toBe(1)
  expect(mockAxios.history.post[0].data).toBe(
    JSON.stringify({
      stations: [1],
      percentile: 90,
      year_range: { start: 2010, end: 2019 }
    })
  )

  // Check if mean values are rendered
  expect(store.getState().percentiles.result).toEqual(mockPercentilesResponse)
  getByTestId('percentile-mean-result-table')
  const {
    mean_values: { ffmc, bui, isi }
  } = mockPercentilesResponse
  expect(getByTestId('percentile-mean-result-ffmc').textContent).toBe(
    ffmc?.toFixed(FWI_VALUES_DECIMAL)
  )
  expect(getByTestId('percentile-mean-result-bui').textContent).toBe(
    bui?.toFixed(FWI_VALUES_DECIMAL)
  )
  expect(getByTestId('percentile-mean-result-isi').textContent).toBe(
    isi?.toFixed(FWI_VALUES_DECIMAL)
  )

  // Check if the documentation is rendered
  getByTestId('percentile-documentation-card')

  // Test for the case where mean values are null
  mockAxios.onPost('/percentiles/').replyOnce(200, mockNullPercentilesResponse)
  fireEvent.click(getByTestId('calculate-percentiles-button'))
  await waitForElement(() => getByTestId('percentile-result-tables'))
  expect(getByTestId('percentile-mean-result-ffmc').textContent).toBe(NOT_AVAILABLE)
  expect(getByTestId('percentile-mean-result-bui').textContent).toBe(NOT_AVAILABLE)
  expect(getByTestId('percentile-mean-result-isi').textContent).toBe(NOT_AVAILABLE)

  // Test for the case where network error occurs
  mockAxios.onPost('/percentiles/').replyOnce(404)
  fireEvent.click(getByTestId('calculate-percentiles-button'))
  await waitForElementToBeRemoved(() => queryByTestId('percentile-result-tables'))
})
