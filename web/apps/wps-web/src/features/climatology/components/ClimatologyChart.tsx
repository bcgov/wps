import { Box } from '@mui/material'
import { areaY, type ChartInteractionController, defineChart, lineY, ruleX } from '@tanstack/charts'
import { crosshair } from '@tanstack/charts/crosshair'
import { controlledSignal } from '@tanstack/charts/interaction/signal'
import { type ZoomXChange, type ZoomXWheelActivation, type ZoomXWindow, zoomX } from '@tanstack/charts/interaction/zoom'
import { decorative } from '@tanstack/charts/mark/decorative'
import { Chart } from '@tanstack/charts/react'
import { scaleLinear } from '@tanstack/charts/scales/linear'
import type { ClimatologyVariable } from '@wps/api/climatologyAPI'
import { sortBy } from 'lodash'
import { type PointerEvent, useCallback, useMemo, useRef, useState } from 'react'
import {
  axisLabel,
  CLIMATOLOGY_VARIABLES,
  type ClimatologyRow,
  type DateWindow,
  formatDay,
  latestRow,
  maxZoom,
  rowsExtent,
  rowsInWindow,
  valueExtent,
  windowTicks
} from '@/features/climatology/climatologyRows'
import type { ComparedYear } from '@/features/climatology/comparedYears'
import ClimatologyReadout from '@/features/climatology/components/ClimatologyReadout'
import { BAND_COLOURS, MEDIAN_COLOUR, YEAR_COLOUR } from '@/features/climatology/components/climatologyColours'

const TODAY_COLOUR = '#898781'
// The percentiles the bands run between.
type BandEdge = 'minimum' | 'p25' | 'p75' | 'p90' | 'maximum'
// How much of a compared year's line shows while another is highlighted.
export const DIMMED_OPACITY = 0.2

export interface ClimatologyChartInput {
  rows: ClimatologyRow[]
  variable: ClimatologyVariable
  year: number
  // The dates shown. The rows outside it are not drawn, and the chart zooms and pans within the
  // rows' first to last day.
  dateWindow: DateWindow
  onDateWindowChange: (dateWindow: DateWindow) => void
  // The years drawn beside the selected one.
  comparedYears: ComparedYear[]
  // The compared year to make stand out, or null to draw them all alike.
  highlightedYear: number | null
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
  onHighlight: (year: number | null) => void
  height?: number
}

/** The chart: percentile bands, the historical median and the selected year, by day. */
export const climatologyChartDefinition = ({
  rows,
  variable,
  dateWindow,
  onDateWindowChange,
  comparedYears,
  highlightedYear,
  today,
  yDomain,
  wheelZoom = 'always'
}: ClimatologyChartInput) => {
  const shown = rowsInWindow(rows, dateWindow)
  const extent = rowsExtent(rows) ?? dateWindow
  const ticks = windowTicks(dateWindow)
  const band = (lower: BandEdge, upper: BandEdge, fill: string) =>
    decorative(
      areaY(shown, {
        x: 'time',
        y1: row => row[lower],
        y2: row => row[upper],
        fill,
        // The shades are light already, and an area is mostly transparent by default.
        fillOpacity: 1
      })
    )
  const todayShown = today !== null && today >= dateWindow.start && today <= dateWindow.end
  return defineChart({
    marks: [
      band('minimum', 'p25', BAND_COLOURS.lowest),
      band('p25', 'p75', BAND_COLOURS.middle),
      band('p75', 'p90', BAND_COLOURS.high),
      band('p90', 'maximum', BAND_COLOURS.highest),
      ...(todayShown
        ? [decorative(ruleX([today], { x: time => time, stroke: TODAY_COLOUR, strokeDasharray: '4 3' }))]
        : []),
      lineY(shown, { x: 'time', y: 'median', stroke: MEDIAN_COLOUR, strokeWidth: 1.5 }),
      // Pointing at a day finds its median, which every day has, so these need no points. The
      // highlighted year is last, on top of the others.
      ...sortBy(comparedYears, each => each.year === highlightedYear).map(({ year, colour }) =>
        decorative(
          lineY(shown, {
            x: 'time',
            y: row => row.compared[year] ?? null,
            stroke: colour,
            strokeWidth: year === highlightedYear ? 2.5 : 1.5,
            strokeOpacity: highlightedYear === null || year === highlightedYear ? 1 : DIMMED_OPACITY
          })
        )
      ),
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
        axis: { label: axisLabel(variable) }
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
    // beside the chart, not a tooltip beside the pointer, which would cover the lines.
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
  comparedYears,
  highlightedYear,
  today,
  yDomain,
  wheelZoom,
  title,
  onHighlight,
  height = 460
}: ClimatologyChartProps) => {
  const definition = useMemo(
    () =>
      climatologyChartDefinition({
        rows,
        variable,
        year,
        dateWindow,
        onDateWindowChange,
        comparedYears,
        highlightedYear,
        today,
        yDomain,
        wheelZoom
      }),
    [rows, variable, year, dateWindow, onDateWindowChange, comparedYears, highlightedYear, today, yDomain, wheelZoom]
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
  const row = focused ?? latestRow(rows, dateWindow)
  return (
    // The readout goes under the chart where there is no room beside it.
    <Box sx={{ display: 'flex', flexWrap: 'wrap', columnGap: 2, alignItems: 'flex-start' }}>
      <Box
        data-testid="climatology-chart-host"
        onPointerMove={onPointerMove}
        onPointerLeave={onPointerLeave}
        sx={{ flex: '1 1 480px', minWidth: 0 }}
      >
        <Chart
          definition={definition}
          height={height}
          ariaLabel={`${label} climatology for ${title}, ${year}`}
          ariaDescription={`Daily ${label.toLowerCase()} in ${[year, ...comparedYears.map(each => each.year)].join(', ')} against the range, median and percentiles of other years for each day of the year.`}
          onRender={context => {
            interaction.current = context.interaction as ChartInteractionController
          }}
          onFocusChange={point => setFocused(point ? (point.datum as ClimatologyRow) : null)}
        />
      </Box>
      {row && (
        <ClimatologyReadout
          row={row}
          variable={variable}
          year={year}
          comparedYears={comparedYears}
          highlightedYear={highlightedYear}
          onHighlight={onHighlight}
        />
      )}
    </Box>
  )
}

export default ClimatologyChart
