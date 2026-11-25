import { createChartScene } from '@tanstack/charts'
import { fireEvent, render, screen, within } from '@testing-library/react'
import type { ClimatologyRow, DateWindow } from '@/features/climatology/climatologyRows'
import { chooseComparedYears } from '@/features/climatology/comparedYears'
import ClimatologyChart, { climatologyChartDefinition, DIMMED_OPACITY } from './ClimatologyChart'

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
  valueStationCount: value === null ? null : 1,
  compared: {}
})

const rows = [row(1, 20), row(2, 21), row(3, null), row(4, null)]
const everyDay: DateWindow = { start: Date.UTC(2026, 6, 1), end: Date.UTC(2026, 6, 4) }
const input = {
  rows,
  variable: 'temperature' as const,
  year: 2026,
  dateWindow: everyDay,
  onDateWindowChange: vi.fn(),
  comparedYears: [],
  highlightedYear: null,
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

  describe('with compared years', () => {
    const comparedYears = chooseComparedYears([], [2023, 2017])
    const compared = rows.map(each => ({ ...each, compared: { 2023: 30, 2017: 10 } }))
    const lineOf = (highlightedYear: number | null, year: number) => {
      const { colour } = comparedYears.find(each => each.year === year) ?? { colour: '' }
      const lines: { stroke?: string; strokeOpacity?: number; strokeWidth?: number }[] = []
      JSON.stringify(scene({ rows: compared, comparedYears, highlightedYear }), (_, value) => {
        if (value?.stroke === colour) {
          lines.push(value)
        }
        return value
      })
      return lines[0]
    }

    it('draws a line for each in its colour, behind the points of the selected year', () => {
      expect(lineOf(null, 2023)).toBeDefined()
      expect(lineOf(null, 2017)).toBeDefined()
      // The lines are not pointed at: pointing at the day reads them out.
      expect(scene({ rows: compared, comparedYears }).points).toHaveLength(6)
    })

    it('dims the others while one is highlighted', () => {
      expect(JSON.stringify(lineOf(2023, 2017))).toContain(`${DIMMED_OPACITY}`)
      expect(JSON.stringify(lineOf(2023, 2023))).not.toContain(`${DIMMED_OPACITY}`)
    })
  })

  it('accepts a marker for today', () => {
    expect(() => scene({ today: Date.UTC(2026, 6, 2) })).not.toThrow()
  })
})

describe('ClimatologyChart', () => {
  it('renders a chart named for the station, variable and year', () => {
    render(<ClimatologyChart {...input} title="AFTON" onHighlight={vi.fn()} />)

    expect(screen.getByRole('img', { name: 'Temperature climatology for AFTON, 2026' })).toBeInTheDocument()
  })

  it('shows the latest day the year has a value for until a day is stepped to from the keyboard', async () => {
    render(<ClimatologyChart {...input} title="AFTON" onHighlight={vi.fn()} />)
    const readout = within(screen.getByTestId('climatology-readout'))
    // Nothing is observed yet on July 3 and 4.
    expect(readout.getByRole('table', { name: 'Jul 2' })).toBeInTheDocument()
    expect(readout.getByRole('row', { name: '2026 21.0°C' })).toBeInTheDocument()
    const chart = screen.getByRole('img', { name: /Temperature climatology/ })

    chart.focus()
    fireEvent.keyDown(chart, { key: 'ArrowRight' })

    expect(await readout.findByRole('table', { name: 'Jul 1' })).toBeInTheDocument()
    expect(readout.getByRole('row', { name: '2026 20.0°C' })).toBeInTheDocument()
    expect(readout.getByRole('row', { name: 'Median 18.0°C' })).toBeInTheDocument()
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
        onHighlight={vi.fn()}
      />
    )

    fireEvent.keyDown(screen.getByLabelText('Zoom and pan the dates shown'), { key: '+' })

    expect(onDateWindowChange).toHaveBeenCalledTimes(1)
    const [{ start, end }] = onDateWindowChange.mock.calls[0]
    expect(start).toBeGreaterThan(days[0])
    expect(end).toBeLessThan(days[days.length - 1])
  })

  it('uses the y axis it is given, so several charts share one', () => {
    const { scales } = scene({ yDomain: [-10, 40] })

    expect(scales.y?.domain).toEqual([-10, 40])
  })

  it.each([
    ['always', /Use a vertical wheel to zoom/],
    ['modifier', /Hold Control or Command while using a vertical wheel/]
  ] as const)('zooms with the wheel %s', (wheelZoom, instructions) => {
    render(<ClimatologyChart {...input} wheelZoom={wheelZoom} title="AFTON" onHighlight={vi.fn()} />)

    expect(screen.getByLabelText('Zoom and pan the dates shown')).toHaveAccessibleDescription(instructions)
  })
})
