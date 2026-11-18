import { createChartScene } from '@tanstack/charts'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { ClimatologyRow, DateWindow } from '@/features/climatology/climatologyRows'
import ClimatologyChart, { climatologyChartDefinition } from './ClimatologyChart'

const DAY = 24 * 60 * 60 * 1000

const row = (day: number, value: number | null): ClimatologyRow => ({
  time: Date.UTC(2026, 6, day),
  count: 30,
  minimum: 5,
  p25: 12,
  median: 18,
  p75: 24,
  p90: 28,
  maximum: 35,
  value,
  stationCount: 1,
  valueStationCount: value === null ? null : 1
})

const rows = [row(1, 20), row(2, 21), row(3, null), row(4, null)]
const everyDay: DateWindow = { start: Date.UTC(2026, 6, 1), end: Date.UTC(2026, 6, 4) }
const input = {
  rows,
  variable: 'temperature' as const,
  year: 2026,
  dateWindow: everyDay,
  onDateWindowChange: vi.fn(),
  today: null
}

const scene = (overrides = {}) =>
  createChartScene(climatologyChartDefinition({ ...input, ...overrides }), { width: 800, height: 460 })

describe('climatologyChartDefinition', () => {
  it('lets a reader point at every day of the median and every observed day of the year', () => {
    const { points } = scene()

    // Four days of median, and the two days the year has a value for. The bands are not
    // pointed at: one tooltip describes the whole day.
    expect(points).toHaveLength(6)
    expect(points.filter(point => point.yValue === 18)).toHaveLength(4)
    expect(points.map(point => point.yValue).filter(value => value !== 18)).toEqual([20, 21])
  })

  it('spans the dates shown on x and the lowest to highest values on y', () => {
    const { scales } = scene()

    expect(scales.x?.domain).toEqual([everyDay.start, everyDay.end])
    expect(scales.y?.domain).toEqual([5, 35])
  })

  it('draws the days of a narrower window, and the day either side to reach its edges', () => {
    const days = Array.from({ length: 30 }, (_, index) => row(index + 1, 20))
    const window = { start: Date.UTC(2026, 6, 10), end: Date.UTC(2026, 6, 20) }

    const { points, scales } = scene({ rows: days, dateWindow: window })

    expect(scales.x?.domain).toEqual([window.start, window.end])
    // Days 9 to 21, each with a median and a value.
    expect(points).toHaveLength(13 * 2)
    // Zooming in does not rescale the y axis.
    expect(scales.y?.domain).toEqual([5, 35])
  })

  it('still draws with no observations in the year', () => {
    const { points } = scene({ rows: rows.map(each => ({ ...each, value: null })) })

    expect(points).toHaveLength(4)
  })

  it('accepts a marker for today', () => {
    expect(() => scene({ today: Date.UTC(2026, 6, 2) })).not.toThrow()
  })
})

describe('ClimatologyChart', () => {
  it('renders a chart named for the station, variable and year', () => {
    render(<ClimatologyChart {...input} title="AFTON" />)

    expect(screen.getByRole('img', { name: 'Temperature climatology for AFTON, 2026' })).toBeInTheDocument()
  })

  it('describes a day in the readout above the chart when stepped to from the keyboard', async () => {
    render(<ClimatologyChart {...input} title="AFTON" />)
    const readout = screen.getByTestId('climatology-readout')
    expect(readout).toHaveTextContent('Point at a day on the chart')
    const chart = screen.getByRole('img', { name: /Temperature climatology/ })

    chart.focus()
    fireEvent.keyDown(chart, { key: 'ArrowRight' })

    await waitFor(() => expect(readout).toHaveTextContent('Jul 1'))
    expect(readout).toHaveTextContent('2026 20.0°C')
    expect(readout).toHaveTextContent('Median 18.0°C')
    expect(readout).toHaveTextContent('Normal 12.0°C to 24.0°C')
    expect(readout).toHaveTextContent('90th percentile 28.0°C')
    expect(readout).toHaveTextContent('Lowest to highest 5.0°C to 35.0°C')
    expect(readout).toHaveTextContent('Years of record 30')
    // No tooltip floats over the chart.
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('zooms in from the keyboard', () => {
    const days = Array.from({ length: 60 }, (_, index) => Date.UTC(2026, 3, 1) + index * DAY)
    const onDateWindowChange = vi.fn()
    render(
      <ClimatologyChart
        {...input}
        rows={days.map(time => ({ ...row(1, 20), time }))}
        dateWindow={{ start: days[0], end: days[days.length - 1] }}
        onDateWindowChange={onDateWindowChange}
        title="AFTON"
      />
    )

    fireEvent.keyDown(screen.getByLabelText('Zoom and pan the dates shown'), { key: '+' })

    expect(onDateWindowChange).toHaveBeenCalledTimes(1)
    const [{ start, end }] = onDateWindowChange.mock.calls[0]
    expect(start).toBeGreaterThan(days[0])
    expect(end).toBeLessThan(days[days.length - 1])
  })

  it('counts the stations in the readout when several are combined', async () => {
    const group = rows.map(each => ({
      ...each,
      count: 60,
      stationCount: 2,
      valueStationCount: each.value === null ? null : 2
    }))
    render(<ClimatologyChart {...input} rows={group} title="Kamloops Fire Centre" />)
    const chart = screen.getByRole('img', { name: /Temperature climatology/ })

    chart.focus()
    fireEvent.keyDown(chart, { key: 'ArrowRight' })

    const readout = screen.getByTestId('climatology-readout')
    await waitFor(() => expect(readout).toHaveTextContent('2026 20.0°C (2 stations)'))
    expect(readout).toHaveTextContent('Drawn from 60 values at 2 stations')
  })

  it('uses the y axis it is given, so several charts share one', () => {
    const { scales } = scene({ yDomain: [-10, 40] })

    expect(scales.y?.domain).toEqual([-10, 40])
  })

  it.each([
    ['always', /Use a vertical wheel to zoom/],
    ['modifier', /Hold Control or Command while using a vertical wheel/]
  ] as const)('zooms with the wheel %s', (wheelZoom, instructions) => {
    render(<ClimatologyChart {...input} wheelZoom={wheelZoom} title="AFTON" />)

    expect(screen.getByLabelText('Zoom and pan the dates shown')).toHaveAccessibleDescription(instructions)
  })
})
