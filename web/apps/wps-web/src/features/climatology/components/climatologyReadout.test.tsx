import { render, screen } from '@testing-library/react'
import type { ClimatologyRow } from '@/features/climatology/climatologyRows'
import ClimatologyReadout, { readoutItems } from './ClimatologyReadout'

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
  value: null,
  valueStationCount: null
}

describe('readoutItems', () => {
  it('leaves out the year on a day it has no value', () => {
    expect(readoutItems(row, 'temperature', 2026).map(item => item.label)).toEqual([
      'Median',
      'Normal',
      '90th percentile',
      'Lowest to highest',
      'Years of record'
    ])
  })

  it('leads with the year when it has a value', () => {
    const [first] = readoutItems({ ...row, value: 28.4, valueStationCount: 1 }, 'temperature', 2026)

    expect(first).toEqual({ label: '2026', value: '28.4°C' })
  })
})

describe('ClimatologyReadout', () => {
  it('says how to see a day before one is pointed at', () => {
    render(<ClimatologyReadout row={null} variable="temperature" year={2026} />)

    expect(screen.getByTestId('climatology-readout')).toHaveTextContent('Point at a day on the chart')
  })

  it('shows the day pointed at and its values', () => {
    render(<ClimatologyReadout row={row} variable="relative_humidity" year={2026} />)

    expect(screen.getByTestId('climatology-readout')).toHaveTextContent('Jul 12Median 25%Normal 22% to 27%')
  })
})
