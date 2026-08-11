import { fireEvent, render, screen } from '@testing-library/react'
import { RunType } from '@wps/api/runType'
import RunTypeDropdown from './RunTypeDropdown'

describe('RunTypeDropdown', () => {
  it('shows actuals and forecasts', () => {
    render(<RunTypeDropdown selectedRunType={RunType.ACTUAL} setSelectedRunType={vi.fn()} />)

    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Source' }))

    expect(screen.getByRole('option', { name: 'Actual' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Forecast' })).toBeInTheDocument()
  })

  it('updates the selected run type', () => {
    const setSelectedRunType = vi.fn()
    render(<RunTypeDropdown selectedRunType={RunType.ACTUAL} setSelectedRunType={setSelectedRunType} />)

    fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Source' }))
    fireEvent.click(screen.getByRole('option', { name: 'Forecast' }))

    expect(setSelectedRunType).toHaveBeenCalledWith(RunType.FORECAST)
  })
})
