import { areaY, type ChartInteractionController, defineChart, lineY, ruleX } from '@tanstack/charts'
import { crosshair } from '@tanstack/charts/crosshair'
import { controlledSignal } from '@tanstack/charts/interaction/signal'
import { type ZoomXChange, type ZoomXWheelActivation, type ZoomXWindow, zoomX } from '@tanstack/charts/interaction/zoom'
import { decorative } from '@tanstack/charts/mark/decorative'
import { Chart } from '@tanstack/charts/react'
import { scaleLinear } from '@tanstack/charts/scales/linear'
import type { ClimatologyVariable } from '@wps/api/climatologyAPI'
import { type PointerEvent, useCallback, useMemo, useRef, useState } from 'react'
import {
  CLIMATOLOGY_VARIABLES,
  type ClimatologyRow,
  type DateWindow,
  formatDay,
  maxZoom,
  rowsExtent,
  rowsInWindow,
  valueExtent,
  windowTicks
} from '@/features/climatology/climatologyRows'
import ClimatologyReadout from '@/features/climatology/components/ClimatologyReadout'

// The bands run from cool through a neutral grey to warm, so the order reads without the
// legend, and adjacent bands stay apart for colour-blind readers.
export const BAND_COLOURS = {
  belowNormal: '#3987e5',
  normal: '#a9a89e',
  aboveNormal: '#eda100',
  extreme: '#e34948'
}
export const MEDIAN_COLOUR = '#52514e'
export const YEAR_COLOUR = '#0b0b0b'
const TODAY_COLOUR = '#898781'

export interface ClimatologyChartInput {
  rows: ClimatologyRow[]
  variable: ClimatologyVariable
  year: number
  // The dates shown. The rows outside it are not drawn, and the chart zooms and pans within the
  // rows' first to last day.
  dateWindow: DateWindow
  onDateWindowChange: (dateWindow: DateWindow) => void
  // Today as a time on the chart, or null to leave the marker out.
  today: number | null
  // The y axis' lowest and highest value, so that charts of several stations share one. By
  // default the rows' own, which zooming does not change.
  yDomain?: [number, number]
  // When the scroll wheel zooms: always over the plot, or only with Control or Command held,
  // which leaves the wheel to scroll a page of several charts.
  wheelZoom?: Extract<ZoomXWheelActivation, 'always' | 'modifier'>
}

export interface ClimatologyChartProps extends ClimatologyChartInput {
  // What the chart is of: a station's name, or a description of a group.
  title: string
  height?: number
}

/** The chart: percentile bands, the historical median and the selected year, by day. */
export const climatologyChartDefinition = ({
  rows,
  variable,
  dateWindow,
  onDateWindowChange,
  today,
  yDomain,
  wheelZoom = 'always'
}: ClimatologyChartInput) => {
  const { label, unit } = CLIMATOLOGY_VARIABLES[variable]
  const shown = rowsInWindow(rows, dateWindow)
  const extent = rowsExtent(rows) ?? dateWindow
  const ticks = windowTicks(dateWindow)
  const band = (lower: keyof ClimatologyRow, upper: keyof ClimatologyRow, fill: string) =>
    decorative(
      areaY(shown, {
        x: 'time',
        y1: row => row[lower],
        y2: row => row[upper],
        fill,
        fillOpacity: 0.85
      })
    )
  const todayShown = today !== null && today >= dateWindow.start && today <= dateWindow.end
  return defineChart({
    marks: [
      band('minimum', 'p25', BAND_COLOURS.belowNormal),
      band('p25', 'p75', BAND_COLOURS.normal),
      band('p75', 'p90', BAND_COLOURS.aboveNormal),
      band('p90', 'maximum', BAND_COLOURS.extreme),
      ...(todayShown
        ? [decorative(ruleX([today], { x: time => time, stroke: TODAY_COLOUR, strokeDasharray: '4 3' }))]
        : []),
      lineY(shown, { x: 'time', y: 'median', stroke: MEDIAN_COLOUR, strokeWidth: 1.5 }),
      lineY(shown, { x: 'time', y: 'value', stroke: YEAR_COLOUR, strokeWidth: 2.5 }),
      crosshair({ x: true, y: false })
    ],
    scales: {
      x: {
        scale: scaleLinear().domain([dateWindow.start, dateWindow.end]),
        axis: { ticks: { values: ticks.values, format: (time: number) => ticks.format(time) } }
      },
      y: {
        scale: scaleLinear().domain(yDomain ?? valueExtent(rows)),
        nice: true,
        grid: true,
        axis: { label: `${label} (${unit})` }
      }
    },
    // The rows either side of the window are drawn to reach its edges, and cut off there.
    clip: true,
    controls: [
      // The wheel zooms, dragging pans, plus and minus zoom from the keyboard and Home shows
      // every day again.
      zoomX({
        window: controlledSignal<ZoomXWindow<number>, ZoomXChange<number>>(
          { start: dateWindow.start, end: dateWindow.end },
          next => onDateWindowChange({ start: next.start, end: next.end })
        ),
        extent: [extent.start, extent.end],
        scaleExtent: [1, maxZoom(extent)],
        ariaLabel: 'Zoom and pan the dates shown',
        wheelActivation: wheelZoom,
        format: formatDay
      })
    ],
    // The pointer finds the day, wherever it is vertically. Its values are shown in a readout
    // above the chart, not a tooltip beside the pointer, which would cover the lines.
    focus: 'nearest-x',
    maxFocusDistance: Number.POSITIVE_INFINITY
  })
}

const ClimatologyChart = ({
  rows,
  variable,
  year,
  dateWindow,
  onDateWindowChange,
  today,
  yDomain,
  wheelZoom,
  title,
  height = 460
}: ClimatologyChartProps) => {
  const definition = useMemo(
    () =>
      climatologyChartDefinition({ rows, variable, year, dateWindow, onDateWindowChange, today, yDomain, wheelZoom }),
    [rows, variable, year, dateWindow, onDateWindowChange, today, yDomain, wheelZoom]
  )
  const [focused, setFocused] = useState<ClimatologyRow | null>(null)
  // The zoom control lies over the plot to catch drags and the wheel, so the chart under it
  // never sees the pointer. Its movement is passed on here so the readout still follows it.
  const interaction = useRef<ChartInteractionController | null>(null)
  const onPointerMove = useCallback((event: PointerEvent) => {
    const controller = interaction.current
    controller?.setControlledFocus(controller.resolvePointer(event.clientX, event.clientY))
  }, [])
  const onPointerLeave = useCallback(() => interaction.current?.setControlledFocus(null), [])
  const { label } = CLIMATOLOGY_VARIABLES[variable]
  return (
    <div>
      <ClimatologyReadout row={focused} variable={variable} year={year} />
      <div data-testid="climatology-chart-host" onPointerMove={onPointerMove} onPointerLeave={onPointerLeave}>
        <Chart
          definition={definition}
          height={height}
          ariaLabel={`${label} climatology for ${title}, ${year}`}
          ariaDescription={`Daily ${label.toLowerCase()} in ${year} against the range, median and percentiles of other years for each day of the year.`}
          onRender={context => {
            interaction.current = context.interaction as ChartInteractionController
          }}
          onFocusChange={point => setFocused(point ? (point.datum as ClimatologyRow) : null)}
        />
      </div>
    </div>
  )
}

export default ClimatologyChart
