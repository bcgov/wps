import React from 'react'
import MockAdapter from 'axios-mock-adapter'
import { waitForElement, cleanup, fireEvent } from '@testing-library/react'

import axios from 'api/axios'
import { selectStationsReducer } from 'app/rootReducer'
import { renderWithRedux } from 'utils/testUtils'
import { WEATHER_STATION_MAP_LINK } from 'utils/constants'
import { FWICalculatorPage } from 'features/fwiCalculator/FWICalculatorPage'

const mockAxios = new MockAdapter(axios)

import {
  mockStations,
  mockPercentilesResponse
} from 'features/fwiCalculator/FWICalculatorPage.mock'

afterEach(() => {
  mockAxios.reset()
  cleanup()
})

it('renders FWI calculator page', async () => {
  const { getByText, getByTestId, store } = renderWithRedux(
    <FWICalculatorPage />
  )

  // Check if all the components are rendered
  expect(getByText(/FWI calculator/i)).toBeInTheDocument()
  expect(selectStationsReducer(store.getState()).stations).toEqual([])
  expect(getByTestId('weather-station-dropdown')).toBeInTheDocument()
  expect(getByTestId('time-range-slider')).toBeInTheDocument()
  expect(getByTestId('percentile-textfield')).toBeInTheDocument()

  // Map icon tests
  expect(getByTestId('map-icon')).toBeInTheDocument()
  window.open = jest.fn()
  fireEvent.click(getByTestId('map-icon'))
  expect(window.open).toBeCalledWith(WEATHER_STATION_MAP_LINK, '_blank')
})

it('renders weather stations dropdown with data', async () => {
  mockAxios
    .onGet('/stations')
    .replyOnce(200, { weather_stations: mockStations })

  const { getByText, getByTestId, store } = renderWithRedux(
    <FWICalculatorPage />
  )

  expect(selectStationsReducer(store.getState()).stations).toEqual([])
  fireEvent.click(getByTestId('weather-station-dropdown'))

  const [station1] = await waitForElement(() => [
    getByText(`${mockStations[0].name} (${mockStations[0].code})`),
    getByText(`${mockStations[1].name} (${mockStations[1].code})`)
  ])

  fireEvent.click(station1)
  expect(selectStationsReducer(store.getState()).stations).toEqual(mockStations)
})

it('renders error message when fetching stations failed', async () => {
  mockAxios.onGet('/stations').replyOnce(404)

  const { getByText, queryByText, store } = renderWithRedux(
    <FWICalculatorPage />
  )

  expect(queryByText(/404/i)).not.toBeInTheDocument()
  expect(selectStationsReducer(store.getState()).error).toBeNull()

  await waitForElement(() => getByText(/404/i))

  expect(selectStationsReducer(store.getState()).error).toBeTruthy()
})

it('renders time range slider with selecting the range', async () => {
  const { getByTestId } = renderWithRedux(<FWICalculatorPage />)
  const sliderWrapper = getByTestId('time-range-slider')
  const timeRangeSliderInput = sliderWrapper.children[1].children[2]

  expect(sliderWrapper).toBeInTheDocument()
  fireEvent.change(timeRangeSliderInput, {
    target: { value: 20 }
  })
  expect(timeRangeSliderInput.getAttribute('value')).toEqual('20')
})

it('renders percentiles result when clicking on the calculate button', async () => {
  mockAxios
    .onGet('/stations')
    .replyOnce(200, { weather_stations: mockStations })
  mockAxios.onPost('/percentiles').replyOnce(200, mockPercentilesResponse)

  const { getByText, getByTestId, store, queryByTestId } = renderWithRedux(
    <FWICalculatorPage />
  )

  // Select a weather station
  fireEvent.click(getByTestId('weather-station-dropdown'))
  const station1 = await waitForElement(() =>
    getByText(`${mockStations[0].name} (${mockStations[0].code})`)
  )
  fireEvent.click(station1)

  // Send the request
  fireEvent.click(getByTestId('calculate-percentiles-button'))

  // Test things before getting the result
  expect(store.getState().percentiles.result).toBeNull()
  expect(queryByTestId('percentile-documentation-card')).not.toBeInTheDocument()

  // Wait until the calculation is fetched
  await waitForElement(() => getByTestId('percentile-result-tables'))

  // Check if the correct request body has been included
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
  getByText(mockPercentilesResponse.mean_values.FFMC.toFixed(1).toString())
  getByText(mockPercentilesResponse.mean_values.BUI.toFixed(1).toString())
  getByText(mockPercentilesResponse.mean_values.ISI.toFixed(1).toString())

  // Check if the documentation is rendered
  expect(getByTestId('percentile-documentation-card')).toBeInTheDocument()
})
