import { render } from '@testing-library/react'
import store from 'app/store'
import ResetForecastButton, { resetForecastRows } from 'features/moreCast2/components/ResetForecastButton'
import { buildValidActualRow, buildValidForecastRow } from 'features/moreCast2/rowFilters.test'
import { DateTime } from 'luxon'
import React from 'react'
import { Provider } from 'react-redux'

const TEST_DATE = DateTime.now()

describe('SaveForecastButton', () => {
  it('should render the button as enabled', () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton enabled={true} label="test" allRows={[]} setAllRows={jest.fn()} />
      </Provider>
    )

    const manageStationsButton = getByTestId('reset-forecast-button')
    expect(manageStationsButton).toBeInTheDocument()
    expect(manageStationsButton).toBeEnabled()
  })
  it('should render the button as disabled', () => {
    const { getByTestId } = render(
      <Provider store={store}>
        <ResetForecastButton enabled={false} label="test" allRows={[]} setAllRows={jest.fn()} />
      </Provider>
    )

    const manageStationsButton = getByTestId('reset-forecast-button')
    expect(manageStationsButton).toBeInTheDocument()
    expect(manageStationsButton).toBeDisabled()
  })
  it('should reset the forecast rows to their initial load state', () => {
    const mockRowData = [
      buildValidForecastRow(111, TEST_DATE.plus({ days: 1 }), 'MANUAL'),
      buildValidForecastRow(222, TEST_DATE.plus({ days: 1 }), 'MANUAL'),
      buildValidActualRow(222, TEST_DATE.minus({ days: 1 }))
    ]

    const resetRows = resetForecastRows(mockRowData)

    expect(resetRows[0].tempForecast?.value).toBe(NaN)
    expect(resetRows[0].rhForecast?.value).toBe(NaN)
    expect(resetRows[0].windSpeedForecast?.value).toBe(NaN)
    expect(resetRows[0].precipForecast?.value).toBe(0)
  })
  it('should not reset rows with submitted forecasts or actuals', () => {
    const mockRowData = [
      buildValidForecastRow(111, TEST_DATE.plus({ days: 1 }), 'FORECAST'),
      buildValidForecastRow(222, TEST_DATE.plus({ days: 1 }), 'FORECAST'),
      buildValidActualRow(222, TEST_DATE.minus({ days: 1 }))
    ]

    const resetRows = resetForecastRows(mockRowData)

    expect(resetRows).toEqual(mockRowData)
  })
})
