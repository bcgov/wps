import React from 'react'
import MockAdapter from 'axios-mock-adapter'
import { waitForElement, cleanup, fireEvent } from '@testing-library/react'

import { selectStations } from 'app/rootReducer'
import axios from 'api/axios'
import { renderWithRedux } from 'utils/testUtils'
import FireWeatherPage from 'features/fireWeather/pages/FireWeatherPage'
import {
  mockStations,
  mockModelsResponse,
  mockReadingsResponse
} from 'features/fireWeather/pages/FireWeatherPage.mock'

const mockAxios = new MockAdapter(axios)

afterEach(() => {
  mockAxios.reset()
  cleanup()
})

it('renders fire weather page', async () => {
  const { getByText, getByTestId } = renderWithRedux(<FireWeatherPage />)
  // before authenticated
  expect(getByText(/Signing in/i)).toBeInTheDocument()

  // Check if all the components are rendered after authenticated
  await waitForElement(() => getByText(/Predictive Services Unit/i))
  expect(getByText(/Daily Weather Model/i)).toBeInTheDocument()
  expect(getByTestId('weather-station-dropdown')).toBeInTheDocument()
})

it('renders weather stations dropdown with data', async () => {
  mockAxios.onGet('/stations/').replyOnce(200, { weather_stations: mockStations })

  const { getByText, getByTestId, store } = renderWithRedux(<FireWeatherPage />)
  expect(selectStations(store.getState()).stations).toEqual([])

  // wait for authentication
  await waitForElement(() => getByText(/Predictive Services Unit/i))

  fireEvent.click(getByTestId('weather-station-dropdown'))

  const [station1] = await waitForElement(() => [
    getByText(`${mockStations[0].name} (${mockStations[0].code})`),
    getByText(`${mockStations[1].name} (${mockStations[1].code})`)
  ])

  fireEvent.click(station1)
  expect(selectStations(store.getState()).stations).toEqual(mockStations)
})

it('renders daily model and hourly values in response to user inputs', async () => {
  mockAxios.onGet('/stations/').replyOnce(200, { weather_stations: mockStations })
  mockAxios.onPost('/forecasts/').replyOnce(200, mockModelsResponse)
  mockAxios.onPost('/hourlies/').replyOnce(200, mockReadingsResponse)

  const { getByText, getByTestId } = renderWithRedux(<FireWeatherPage />)

  // wait for authentication
  await waitForElement(() => getByText(/Predictive Services Unit/i))

  // Select a weather station
  fireEvent.click(getByTestId('weather-station-dropdown'))
  const station1 = await waitForElement(() =>
    getByText(`${mockStations[0].name} (${mockStations[0].code})`)
  )
  fireEvent.click(station1)

  // Send the request
  fireEvent.click(getByTestId('get-wx-data-button'))

  // Wait until all the displays show up
  await waitForElement(() => getByTestId('daily-models-display'))
  await waitForElement(() => getByTestId('hourly-readings-display'))
  await waitForElement(() => getByTestId('weather-graph-by-station'))

  // Validate the correct request body
  // There should have been two requests, one for models and one for hourly readings.
  expect(mockAxios.history.post.length).toBe(2)
  // Each of those request should ask for a station
  mockAxios.history.post.forEach(post => {
    expect(post.data).toBe(
      JSON.stringify({
        stations: [1]
      })
    )
  })
})
