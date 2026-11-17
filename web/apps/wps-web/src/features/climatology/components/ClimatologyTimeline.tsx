import { areaY, defineChart, lineY } from '@tanstack/charts'
import { type BrushRange, type BrushXChange, brushX } from '@tanstack/charts/interaction/brush'
import { controlledSignal } from '@tanstack/charts/interaction/signal'
import { decorative } from '@tanstack/charts/mark/decorative'
import { Chart } from '@tanstack/charts/react'
import { scaleLinear } from '@tanstack/charts/scales/linear'
import { useMemo } from 'react'
import {
  type ClimatologyRow,
  type DateWindow,
  formatDay,
  rowsExtent,
  snapToRows,
  widenWindow,
  windowTicks
} from '@/features/climatology/climatologyRows'
import { BAND_COLOURS, MEDIAN_COLOUR, YEAR_COLOUR } from '@/features/climatology/components/ClimatologyChart'

export interface ClimatologyTimelineProps {
  rows: ClimatologyRow[]
  year: number
  // The dates the chart above shows. The timeline marks them with a start and an end handle.
  dateWindow: DateWindow
  onDateWindowChange: (dateWindow: DateWindow) => void
}

/** A compact view of every day, with handles that choose the dates the chart above shows. */
export const climatologyTimelineDefinition = ({ rows, dateWindow, onDateWindowChange }: ClimatologyTimelineProps) => {
  const extent = rowsExtent(rows) ?? dateWindow
  const ticks = windowTicks(extent)
  const range = snapToRows(dateWindow, rows)
  return defineChart({
    marks: [
      decorative(areaY(rows, { x: 'time', y1: 'p25', y2: 'p75', fill: BAND_COLOURS.normal, fillOpacity: 0.6 })),
      decorative(lineY(rows, { x: 'time', y: 'median', stroke: MEDIAN_COLOUR, strokeWidth: 1 })),
      lineY(rows, { x: 'time', y: 'value', stroke: YEAR_COLOUR, strokeWidth: 1.5 })
    ],
    scales: {
      x: {
        scale: scaleLinear().domain([extent.start, extent.end]),
        axis: { ticks: { values: ticks.values, format: (time: number) => ticks.format(time) } }
      },
      y: { scale: scaleLinear, nice: true, axis: false }
    },
    clip: true,
    // The handles are the only thing to interact with: no point focus or tooltip.
    focus: false,
    controls: [
      brushX({
        range: controlledSignal<BrushRange<number>, BrushXChange<number>>(range, next =>
          // The chart above follows the handles as they are dragged.
          onDateWindowChange(widenWindow({ start: next.start, end: next.end }, extent))
        ),
        values: rows.map(row => row.time),
        format: formatDay,
        ariaLabel: 'Dates shown',
        startAriaLabel: 'First date shown',
        endAriaLabel: 'Last date shown',
        // Slim neutral bars mark the start and end, and a light wash the dates between them.
        handleSize: 8,
        handleStyle: { fill: MEDIAN_COLOUR, stroke: MEDIAN_COLOUR },
        selectionStyle: { fill: BAND_COLOURS.belowNormal, fillOpacity: 0.12, stroke: BAND_COLOURS.belowNormal }
      })
    ]
  })
}

const ClimatologyTimeline = ({ rows, year, dateWindow, onDateWindowChange }: ClimatologyTimelineProps) => {
  const definition = useMemo(
    () => climatologyTimelineDefinition({ rows, year, dateWindow, onDateWindowChange }),
    [rows, year, dateWindow, onDateWindowChange]
  )
  return (
    <Chart
      definition={definition}
      height={110}
      ariaLabel={`Timeline of ${year}`}
      ariaDescription="Drag the handles to choose the dates the chart shows."
    />
  )
}

export default ClimatologyTimeline
