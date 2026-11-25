import { fireEvent, render, screen, within } from '@testing-library/react'
import type { ClimatologyRow } from '@/features/climatology/climatologyRows'
import { chooseComparedYears } from '@/features/climatology/comparedYears'
import ClimatologyReadout, { historyItems, readoutNotes, yearItems } from './ClimatologyReadout'

const row: ClimatologyRow = {
  time: Date.UTC(2026, 6, 12),
  count: 36,
  stationCount: 1,
  minimum: 15,
  p25: 22,
  median: 25,
  p75: 27,
  p90: 29.1,
  maximum: 35,
  value: 28.4,
  valueStationCount: 1,
  compared: { 2023: 31, 2017: 22.5 }
}
const comparedYears = chooseComparedYears([], [2023, 2021, 2017])

describe('yearItems', () => {
  it('has the selected year, then the years compared in their colours', () => {
    const items = yearItems(row, 'temperature', 2026, comparedYears)

    expect(items.map(item => `${item.label} ${item.value}`)).toEqual([
      '2026 28.4°C',
      '2023 31.0°C',
      // Nothing was observed that day in 2021.
      '2021 –',
      '2017 22.5°C'
    ])
    expect(items.slice(1).map(item => item.colour)).toEqual(comparedYears.map(each => each.colour))
  })

  it('keeps its rows on a day the selected year has no value', () => {
    const [first] = yearItems({ ...row, value: null, valueStationCount: null }, 'temperature', 2026, [])

    expect(first).toMatchObject({ label: '2026', value: '–' })
  })
})

describe('historyItems', () => {
  it('runs from the top band to the bottom, with the unit once in each', () => {
    expect(historyItems(row, 'temperature').map(item => `${item.label}: ${item.value}`)).toEqual([
      'Highest 10%: 29.1 to 35.0°C',
      '75th to 90th: 27.0 to 29.1°C',
      'Middle half: 22.0 to 27.0°C',
      'Median: 25.0°C',
      'Lowest 25%: 15.0 to 22.0°C'
    ])
  })
})

describe('readoutNotes', () => {
  it('counts the years of one station', () => {
    expect(readoutNotes(row, 2026)).toEqual(['36 years of record'])
  })

  it('counts the stations when several are combined', () => {
    expect(readoutNotes({ ...row, count: 72, stationCount: 2, valueStationCount: 2 }, 2026)).toEqual([
      '2026 is the mean of 2 stations',
      'History from 72 values at 2 stations'
    ])
  })

  it('does not describe a mean on a day the year has no value', () => {
    expect(readoutNotes({ ...row, stationCount: 2, value: null, valueStationCount: null }, 2026)).toHaveLength(1)
  })
})

describe('ClimatologyReadout', () => {
  const renderReadout = (highlightedYear: number | null = null) => {
    const onHighlight = vi.fn()
    render(
      <ClimatologyReadout
        row={row}
        variable="temperature"
        year={2026}
        comparedYears={comparedYears}
        highlightedYear={highlightedYear}
        onHighlight={onHighlight}
      />
    )
    return onHighlight
  }

  it('is a table of the day, with a row for each line and band', () => {
    renderReadout()

    const table = screen.getByRole('table', { name: 'Jul 12' })
    expect(within(table).getAllByRole('row')).toHaveLength(4 + 5)
    expect(within(table).getByRole('row', { name: '2023 31.0°C' })).toBeInTheDocument()
    expect(screen.getByText('36 years of record')).toBeInTheDocument()
  })

  it('highlights a compared year', () => {
    const onHighlight = renderReadout()

    fireEvent.click(screen.getByRole('button', { name: '2017' }))

    expect(onHighlight).toHaveBeenCalledWith(2017)
    // Only the compared years can be.
    expect(screen.getAllByRole('button')).toHaveLength(3)
  })

  it('stops highlighting the year chosen again', () => {
    const onHighlight = renderReadout(2017)
    const highlighted = screen.getByRole('button', { name: '2017' })
    expect(highlighted).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '2023' })).toHaveAttribute('aria-pressed', 'false')

    fireEvent.click(highlighted)

    expect(onHighlight).toHaveBeenCalledWith(null)
  })
})
