import { render, screen } from '@testing-library/react'
import ClimatologyLegend from './ClimatologyLegend'

describe('ClimatologyLegend', () => {
  it('names the selected year, the median and each percentile band', () => {
    render(<ClimatologyLegend year={2026} />)

    const labels = screen.getAllByRole('listitem').map(item => item.textContent)
    expect(labels).toEqual([
      '2026',
      'Historical median',
      'Extreme (90th percentile and above)',
      'Above normal (75th to 90th)',
      'Normal (25th to 75th)',
      'Below normal (lowest to 25th)'
    ])
  })
})
