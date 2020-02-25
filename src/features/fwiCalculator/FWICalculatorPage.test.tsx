import React from 'react'
import MockAdapter from 'axios-mock-adapter'
import { waitForElement, cleanup, fireEvent } from '@testing-library/react'

import axios from 'api/axios'
import App from 'app/App'
import { selectStationsReducer } from 'app/rootReducer'
import { renderWithRedux } from 'utils/testUtils'
import { timeRangeOptions } from 'features/fwiCalculator/components/TimeRangeDropdown'

const mockAxios = new MockAdapter(axios)
const mockStations = [
  { code: 1, name: 'Station 1' },
  { code: 2, name: 'Station 2' }
]

afterEach(() => {
  mockAxios.reset()
  cleanup()
})

it('renders FWI calculator page', async () => {
  mockAxios.onGet('/stations').reply(200, { weather_stations: mockStations })

  const { getByText, getByTestId, store } = renderWithRedux(<App />)
  const pageTitle = getByText(/FWI calculator/i)
  expect(pageTitle).toBeInTheDocument()
  expect(selectStationsReducer(store.getState()).stations).toEqual([])

  expect(getByTestId('weather-station-dropdown')).toBeInTheDocument()

  fireEvent.click(getByTestId('weather-station-dropdown'))
  const [station1] = await waitForElement(() => [
    getByText('Station 1(1)'),
    getByText('Station 2(2)')
  ])
  fireEvent.click(station1)

  expect(selectStationsReducer(store.getState()).stations).toEqual(mockStations)

  //Time range dropdown test
  expect(getByTestId('time-range-dropdown')).toBeInTheDocument()

  //fireEvent.click(getByTestId('time-range-dropdown'))

  //const timeRange1 = await waitForElement(() => getByText(timeRangeOptions[0]))

  //fireEvent.click(timeRange1)

  //Percentile textfield test
  expect(getByTestId('percentile-textfield')).toBeInTheDocument()
})

it('renders error message when fetching stations failed', async () => {
  mockAxios.onGet('/stations').reply(404)

  const { getByText, queryByText, store } = renderWithRedux(<App />)

  expect(queryByText(/404/i)).not.toBeInTheDocument()
  expect(selectStationsReducer(store.getState()).error).toBeNull()

  await waitForElement(() => getByText(/404/i))
  expect(selectStationsReducer(store.getState()).error).toBeTruthy()
})
