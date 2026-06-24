import { fireEvent, render } from '@testing-library/react'
import { RunType } from '@wps/api/fbaAPI'
import { vi } from 'vitest'
import ActualForecastControl from './ActualForecastControl'

describe('ActualForecastControl', () => {
  const mockSetRunType = vi.fn()

  it('should render the radio button selector with the correct default', () => {
    const { getByTestId } = render(<ActualForecastControl runType={RunType.FORECAST} setRunType={mockSetRunType} />)
    const forecastButton = getByTestId('forecast-radio')
    expect(forecastButton).toBeChecked()
  })

  it('should call setRunType with the correct value when a radio button is selected', () => {
    const { getByTestId, rerender } = render(
      <ActualForecastControl runType={RunType.FORECAST} setRunType={mockSetRunType} />
    )
    fireEvent.click(getByTestId('actual-radio'))
    expect(mockSetRunType).toHaveBeenCalledWith(RunType.ACTUAL)
    expect(mockSetRunType).toHaveBeenCalledTimes(1)

    rerender(<ActualForecastControl runType={RunType.ACTUAL} setRunType={mockSetRunType} />)
    fireEvent.click(getByTestId('forecast-radio'))
    expect(mockSetRunType).toHaveBeenCalledTimes(2)
    expect(mockSetRunType).toHaveBeenCalledWith(RunType.FORECAST)
  })
})
