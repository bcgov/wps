import { createChartScene } from '@tanstack/charts'
import { fireEvent, render, screen } from '@testing-library/react'
import type { ClimatologyRow } from '@/features/climatology/climatologyRows'
import ClimatologyTimeline, { climatologyTimelineDefinition } from './ClimatologyTimeline'

const DAY = 24 * 60 * 60 * 1000
const FIRST = Date.UTC(2026, 3, 1)

const rows: ClimatologyRow[] = Array.from({ length: 60 }, (_, index) => ({
  time: FIRST + index * DAY,
  count: 30,
  minimum: 5,
  p25: 12,
  median: 18,
  p75: 24,
  p90: 28,
  maximum: 35,
  value: index < 30 ? 20 : null
}))

const window = { start: FIRST + 10 * DAY, end: FIRST + 20 * DAY }

describe('climatologyTimelineDefinition', () => {
  it('always spans every day, whatever the chart above shows', () => {
    const definition = climatologyTimelineDefinition({
      rows,
      year: 2026,
      dateWindow: window,
      onDateWindowChange: vi.fn()
    })

    const { scales } = createChartScene(definition, { width: 800, height: 110 })

    expect(scales.x?.domain).toEqual([FIRST, FIRST + 59 * DAY])
  })
})

describe('ClimatologyTimeline', () => {
  const renderTimeline = (onDateWindowChange = vi.fn()) => {
    render(<ClimatologyTimeline rows={rows} year={2026} dateWindow={window} onDateWindowChange={onDateWindowChange} />)
    return onDateWindowChange
  }

  it('has a start and an end handle on the dates shown', () => {
    renderTimeline()

    expect(screen.getByRole('slider', { name: 'First date shown' })).toHaveAttribute('aria-valuetext', 'Apr 11')
    expect(screen.getByRole('slider', { name: 'Last date shown' })).toHaveAttribute('aria-valuetext', 'Apr 21')
  })

  it('moves the dates shown when a handle moves', () => {
    const onDateWindowChange = renderTimeline()

    fireEvent.keyDown(screen.getByRole('slider', { name: 'Last date shown' }), { key: 'ArrowRight' })

    expect(onDateWindowChange).toHaveBeenCalledWith({ start: window.start, end: window.end + DAY })
  })

  it('keeps at least a week shown when the handles close in', () => {
    const onDateWindowChange = vi.fn()
    render(
      <ClimatologyTimeline
        rows={rows}
        year={2026}
        dateWindow={{ start: window.start, end: window.start + 7 * DAY }}
        onDateWindowChange={onDateWindowChange}
      />
    )

    fireEvent.keyDown(screen.getByRole('slider', { name: 'Last date shown' }), { key: 'ArrowLeft' })

    const [{ start, end }] = onDateWindowChange.mock.calls[0]
    expect(end - start).toBe(7 * DAY)
  })
})
