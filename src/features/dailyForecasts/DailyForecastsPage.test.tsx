import React from 'react'
import MockAdapter from 'axios-mock-adapter'
import { waitForElement, cleanup, fireEvent } from '@testing-library/react'

import { selectStations } from 'app/rootReducer'
import axios from 'api/axios'
import { renderWithRedux } from 'utils/testUtils'
import { DailyForecastsPage } from 'features/dailyForecasts/DailyForecastsPage'
import {
  mockStations,
  mockForecastsResponse,
  mockHourliesResponse
} from 'features/dailyForecasts/DailyForecastsPage.mock'

const mockAxios = new MockAdapter(axios)

afterEach(() => {
  mockAxios.reset()
  cleanup()
})

it('renders daily forecast page', async () => {
  const { getByText, getByTestId } = renderWithRedux(<DailyForecastsPage />)
  // before authenticated
  expect(getByText(/Signing in/i)).toBeInTheDocument()

  // Check if all the components are rendered after authenticated
  await waitForElement(() => getByText(/Predictive Services Unit/i))
  expect(getByText(/Daily Weather Forecast/i)).toBeInTheDocument()
  expect(getByTestId('weather-station-dropdown')).toBeInTheDocument()
})

it('renders weather stations dropdown with data', async () => {
  mockAxios.onGet('/stations/').replyOnce(200, { weather_stations: mockStations })

  const { getByText, getByTestId, store } = renderWithRedux(<DailyForecastsPage />)
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

it('renders daily forecast and hourly values in response to user inputs', async () => {
  mockAxios.onGet('/stations/').replyOnce(200, { weather_stations: mockStations })
  mockAxios.onPost('/forecasts/').replyOnce(200, mockForecastsResponse)
  mockAxios.onPost('/hourlies/').replyOnce(200, mockHourliesResponse)

  const { getByText, getByTestId } = renderWithRedux(<DailyForecastsPage />)

  // wait for authentication
  await waitForElement(() => getByText(/Predictive Services Unit/i))

  // Select a weather station
  fireEvent.click(getByTestId('weather-station-dropdown'))
  const station1 = await waitForElement(() =>
    getByText(`${mockStations[0].name} (${mockStations[0].code})`)
  )
  fireEvent.click(station1)

  // Send the request
  fireEvent.click(getByTestId('get-forecast-wx-button'))

  // Wait until the forecasts are fetched
  await waitForElement(() => getByTestId('daily-forecast-displays'))
  // Wait until the hourlies are fetched
  await waitForElement(() => getByTestId('hourly-readings-displays'))

  // Validate the correct request body
  // There should have been two requests, one for forecasts and one for hourlies.
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
