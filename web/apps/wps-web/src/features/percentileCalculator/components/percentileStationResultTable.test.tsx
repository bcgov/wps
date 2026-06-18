import { fireEvent, render, screen } from '@testing-library/react'
import type { StationSummaryResponse } from '@wps/api/percentileAPI'
import { describe, expect, it } from 'vitest'
import { PercentileStationResultTable } from './PercentileStationResultTable'

const makeStationResponse = (years: number[]): StationSummaryResponse => ({
  ffmc: 88.5,
  isi: 9.1,
  bui: 72.0,
  years,
  station: {
    code: 101,
    name: 'Test Station',
    lat: 49.0,
    long: -120.0,
    ecodivision_name: 'Montane Cordillera',
    core_season: { start_month: 5, start_day: 1, end_month: 9, end_day: 30 }
  }
})

describe('PercentileStationResultTable snackbar', () => {
  it('does not show warning when data covers the full time range', () => {
    const years = [2020, 2021, 2022, 2023, 2024]
    render(<PercentileStationResultTable stationResponse={makeStationResponse(years)} timeRange={5} />)

    expect(screen.queryByText(/Data only available for/)).not.toBeInTheDocument()
  })

  it('shows warning when fewer years of data are available than the time range', () => {
    const years = [2022, 2023, 2024]
    render(<PercentileStationResultTable stationResponse={makeStationResponse(years)} timeRange={10} />)

    expect(screen.getByText('Data only available for 3 of 10 years')).toBeInTheDocument()
  })

  it('re-shows the warning after dismissal when timeRange increases beyond available data', () => {
    const years = [2022, 2023, 2024]
    const { rerender } = render(
      <PercentileStationResultTable stationResponse={makeStationResponse(years)} timeRange={2} />
    )
    // 3 years >= timeRange=2 — no warning
    expect(screen.queryByText(/Data only available for/)).not.toBeInTheDocument()

    // Increase time range beyond available data — warning appears
    rerender(<PercentileStationResultTable stationResponse={makeStationResponse(years)} timeRange={5} />)
    expect(screen.getByText('Data only available for 3 of 5 years')).toBeInTheDocument()

    // User dismisses the snackbar
    fireEvent.click(screen.getByRole('button', { name: 'Close' }))

    // Slider increases time range further — warning re-opens
    rerender(<PercentileStationResultTable stationResponse={makeStationResponse(years)} timeRange={10} />)
    expect(screen.getByText('Data only available for 3 of 10 years')).toBeInTheDocument()
  })
})
