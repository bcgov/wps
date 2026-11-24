import { fireEvent, render, screen } from '@testing-library/react'
import { chooseComparedYears } from '@/features/climatology/comparedYears'
import ClimatologyLegend from './ClimatologyLegend'

describe('ClimatologyLegend', () => {
  const renderLegend = (overrides = {}) => {
    const onHighlight = vi.fn()
    render(
      <ClimatologyLegend
        yearLabel="2026 (mean of stations)"
        comparedYears={[]}
        highlightedYear={null}
        onHighlight={onHighlight}
        {...overrides}
      />
    )
    return onHighlight
  }
  const comparedYears = chooseComparedYears([], [2023, 2017])

  it('names the line of the selected year, the median and each percentile band', () => {
    renderLegend()

    const labels = screen.getAllByRole('listitem').map(item => item.textContent)
    expect(labels).toEqual([
      '2026 (mean of stations)',
      'Historical median',
      'Highest 10%',
      '75th to 90th percentile',
      'Middle half (25th to 75th)',
      'Lowest 25%'
    ])
  })

  it('names the compared years after the selected one', () => {
    renderLegend({ comparedYears })

    const labels = screen.getAllByRole('listitem').map(item => item.textContent)
    expect(labels.slice(0, 4)).toEqual(['2026 (mean of stations)', '2023', '2017', 'Historical median'])
  })

  it('highlights a compared year', () => {
    const onHighlight = renderLegend({ comparedYears })

    fireEvent.click(screen.getByRole('button', { name: '2017' }))

    expect(onHighlight).toHaveBeenCalledWith(2017)
  })

  it('stops highlighting the year chosen again', () => {
    const onHighlight = renderLegend({ comparedYears, highlightedYear: 2017 })
    const highlighted = screen.getByRole('button', { name: '2017' })
    expect(highlighted).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '2023' })).toHaveAttribute('aria-pressed', 'false')

    fireEvent.click(highlighted)

    expect(onHighlight).toHaveBeenCalledWith(null)
  })
})
