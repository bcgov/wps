import { areaY, defineChart, lineY, ruleX } from '@tanstack/charts'
import { crosshair } from '@tanstack/charts/crosshair'
import { controlledSignal } from '@tanstack/charts/interaction/signal'
import { type ZoomXChange, type ZoomXWindow, zoomX } from '@tanstack/charts/interaction/zoom'
import { decorative } from '@tanstack/charts/mark/decorative'
import { Chart } from '@tanstack/charts/react'
import { scaleLinear } from '@tanstack/charts/scales/linear'
import { tooltip } from '@tanstack/charts/tooltip'
import type { ClimatologyVariable } from '@wps/api/climatologyAPI'
import { useMemo } from 'react'
import {
  CLIMATOLOGY_VARIABLES,
  type ClimatologyRow,
  type DateWindow,
  formatDay,
  formatValue,
  maxZoom,
  rowsExtent,
  rowsInWindow,
  valueExtent,
  windowTicks
} from '@/features/climatology/climatologyRows'

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
  year,
  dateWindow,
  onDateWindowChange,
  today,
  yDomain
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
      // Wheel zooms once the plot has focus, dragging pans, plus and minus zoom from the keyboard
      // and Home shows every day again.
      zoomX({
        window: controlledSignal<ZoomXWindow<number>, ZoomXChange<number>>(
          { start: dateWindow.start, end: dateWindow.end },
          next => onDateWindowChange({ start: next.start, end: next.end })
        ),
        extent: [extent.start, extent.end],
        scaleExtent: [1, maxZoom(extent)],
        ariaLabel: 'Zoom and pan the dates shown',
        format: formatDay
      })
    ],
    // The pointer finds the day, wherever it is vertically, and one tooltip describes it.
    focus: 'nearest-x',
    maxFocusDistance: Number.POSITIVE_INFINITY,
    tooltip: {
      use: tooltip,
      items: [
        { id: 'day', label: 'Day', text: point => formatDay(point.datum.time) },
        {
          id: 'value',
          label: `${year}`,
          text: point => (point.datum.value === null ? null : formatValue(point.datum.value, variable))
        },
        { id: 'median', label: 'Median', text: point => formatValue(point.datum.median, variable) },
        {
          id: 'normal',
          label: 'Normal (25th to 75th)',
          text: point => `${formatValue(point.datum.p25, variable)} to ${formatValue(point.datum.p75, variable)}`
        },
        { id: 'p90', label: '90th percentile', text: point => formatValue(point.datum.p90, variable) },
        {
          id: 'range',
          label: 'Lowest to highest',
          text: point =>
            `${formatValue(point.datum.minimum, variable)} to ${formatValue(point.datum.maximum, variable)}`
        },
        {
          id: 'value-stations',
          label: `Stations in ${year}`,
          text: point =>
            point.datum.valueStationCount !== null && point.datum.stationCount > 1
              ? `${point.datum.valueStationCount}`
              : null
        },
        {
          id: 'count',
          label: rows.some(row => row.stationCount > 1) ? 'Values in the distribution' : 'Years of record',
          text: point => `${point.datum.count}`
        },
        {
          id: 'stations',
          label: 'Stations in the distribution',
          text: point => (point.datum.stationCount > 1 ? `${point.datum.stationCount}` : null)
        }
      ]
    }
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
  title,
  height = 460
}: ClimatologyChartProps) => {
  const definition = useMemo(
    () => climatologyChartDefinition({ rows, variable, year, dateWindow, onDateWindowChange, today, yDomain }),
    [rows, variable, year, dateWindow, onDateWindowChange, today, yDomain]
  )
  const { label } = CLIMATOLOGY_VARIABLES[variable]
  return (
    <Chart
      definition={definition}
      height={height}
      ariaLabel={`${label} climatology for ${title}, ${year}`}
      ariaDescription={`Daily ${label.toLowerCase()} in ${year} against the range, median and percentiles of other years for each day of the year.`}
    />
  )
}

export default ClimatologyChart
