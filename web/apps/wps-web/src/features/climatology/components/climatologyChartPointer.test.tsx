import { fireEvent, render, screen } from '@testing-library/react'
import type { ClimatologyRow } from '@/features/climatology/climatologyRows'
import ClimatologyChart from './ClimatologyChart'

// The chart is replaced by one that hands over a stand-in interaction controller, because jsdom
// does not lay the chart out and so cannot place a pointer on it. A real browser covers that.
const interaction = {
  clientToScene: vi.fn(),
  resolvePointer: vi.fn((clientX: number, clientY: number) => ({ at: [clientX, clientY] })),
  setControlledFocus: vi.fn()
}

vi.mock('@tanstack/charts/react', () => ({
  Chart: ({ onRender }: { onRender: (context: { interaction: typeof interaction }) => void }) => {
    onRender({ interaction })
    return <div data-testid="chart" />
  }
}))

const row: ClimatologyRow = {
  time: Date.UTC(2026, 6, 1),
  count: 30,
  stationCount: 1,
  minimum: 5,
  p25: 12,
  median: 18,
  p75: 24,
  p90: 28,
  maximum: 35,
  value: 20,
  valueStationCount: 1,
  compared: {}
}

describe('ClimatologyChart pointer', () => {
  it('passes the pointer through the zoom control to the chart, so its tooltip follows', () => {
    render(
      <ClimatologyChart
        rows={[row]}
        variable="temperature"
        year={2026}
        dateWindow={{ start: row.time, end: row.time + 1 }}
        onDateWindowChange={vi.fn()}
        comparedYears={[]}
        highlightedYear={null}
        today={null}
        title="AFTON"
      />
    )
    const host = screen.getByTestId('climatology-chart-host')

    // Pointer events reach the host from whatever lies on the plot, the zoom control included.
    fireEvent.pointerMove(screen.getByTestId('chart'), { clientX: 120, clientY: 80 })

    expect(interaction.resolvePointer).toHaveBeenCalledWith(120, 80)
    expect(interaction.setControlledFocus).toHaveBeenLastCalledWith({ at: [120, 80] })

    fireEvent.pointerLeave(host)

    expect(interaction.setControlledFocus).toHaveBeenLastCalledWith(null)
  })
})
