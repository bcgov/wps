import { createChartScene } from '@tanstack/charts'
import { fireEvent, render, screen } from '@testing-library/react'
import type { ClimatologyRow } from '@/features/climatology/climatologyRows'
import ClimatologyChart, { climatologyChartDefinition } from './ClimatologyChart'

const row = (day: number, value: number | null): ClimatologyRow => ({
  time: Date.UTC(2026, 6, day),
  count: 30,
  minimum: 5,
  p25: 12,
  median: 18,
  p75: 24,
  p90: 28,
  maximum: 35,
  value
})

const rows = [row(1, 20), row(2, 21), row(3, null), row(4, null)]
const input = { rows, variable: 'temperature' as const, year: 2026, monthTicks: [Date.UTC(2026, 6, 1)], today: null }

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

  it('spans the days on x and the lowest to highest values on y', () => {
    const { scales } = scene()

    expect(scales.x?.domain).toEqual([Date.UTC(2026, 6, 1), Date.UTC(2026, 6, 4)])
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
    render(<ClimatologyChart {...input} stationName="AFTON" />)

    expect(screen.getByRole('img', { name: 'Temperature climatology for AFTON, 2026' })).toBeInTheDocument()
  })

  it('describes a day in a tooltip when stepped to from the keyboard', async () => {
    render(<ClimatologyChart {...input} stationName="AFTON" />)
    const chart = screen.getByRole('img', { name: /Temperature climatology/ })

    chart.focus()
    fireEvent.keyDown(chart, { key: 'ArrowRight' })

    const tooltip = await screen.findByRole('status')
    expect(tooltip).toHaveTextContent('DayJul 1')
    expect(tooltip).toHaveTextContent('202620.0°C')
    expect(tooltip).toHaveTextContent('Median18.0°C')
    expect(tooltip).toHaveTextContent('Normal (25th to 75th)12.0°C to 24.0°C')
    expect(tooltip).toHaveTextContent('90th percentile28.0°C')
    expect(tooltip).toHaveTextContent('Lowest to highest5.0°C to 35.0°C')
    expect(tooltip).toHaveTextContent('Years of record30')
  })
})
