import { areaY, defineChart, lineY, ruleX } from '@tanstack/charts'
import { crosshair } from '@tanstack/charts/crosshair'
import { decorative } from '@tanstack/charts/mark/decorative'
import { Chart } from '@tanstack/charts/react'
import { scaleLinear } from '@tanstack/charts/scales/linear'
import { tooltip } from '@tanstack/charts/tooltip'
import type { ClimatologyVariable } from '@wps/api/climatologyAPI'
import { useMemo } from 'react'
import {
  CLIMATOLOGY_VARIABLES,
  type ClimatologyRow,
  formatDay,
  formatMonth,
  formatValue
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
  // The times the x axis is labelled at: the first day of each month shown.
  monthTicks: number[]
  // Today as a time on the chart, or null to leave the marker out.
  today: number | null
}

export interface ClimatologyChartProps extends ClimatologyChartInput {
  stationName: string
}

/** The chart: percentile bands, the historical median and the selected year, by day. */
export const climatologyChartDefinition = ({ rows, variable, year, monthTicks, today }: ClimatologyChartInput) => {
  const { label, unit } = CLIMATOLOGY_VARIABLES[variable]
  const band = (lower: keyof ClimatologyRow, upper: keyof ClimatologyRow, fill: string) =>
    decorative(
      areaY(rows, {
        x: 'time',
        y1: row => row[lower],
        y2: row => row[upper],
        fill,
        fillOpacity: 0.85
      })
    )
  return defineChart({
    marks: [
      band('minimum', 'p25', BAND_COLOURS.belowNormal),
      band('p25', 'p75', BAND_COLOURS.normal),
      band('p75', 'p90', BAND_COLOURS.aboveNormal),
      band('p90', 'maximum', BAND_COLOURS.extreme),
      ...(today === null
        ? []
        : [decorative(ruleX([today], { x: time => time, stroke: TODAY_COLOUR, strokeDasharray: '4 3' }))]),
      lineY(rows, { x: 'time', y: 'median', stroke: MEDIAN_COLOUR, strokeWidth: 1.5 }),
      lineY(rows, { x: 'time', y: 'value', stroke: YEAR_COLOUR, strokeWidth: 2.5 }),
      crosshair({ x: true, y: false })
    ],
    scales: {
      x: {
        scale: scaleLinear,
        axis: { ticks: { values: monthTicks, format: (time: number) => formatMonth(time) } }
      },
      y: {
        scale: scaleLinear,
        nice: true,
        grid: true,
        axis: { label: `${label} (${unit})` }
      }
    },
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
        { id: 'count', label: 'Years of record', text: point => `${point.datum.count}` }
      ]
    }
  })
}

const ClimatologyChart = ({ rows, variable, year, monthTicks, today, stationName }: ClimatologyChartProps) => {
  const definition = useMemo(
    () => climatologyChartDefinition({ rows, variable, year, monthTicks, today }),
    [rows, variable, year, monthTicks, today]
  )
  const { label } = CLIMATOLOGY_VARIABLES[variable]
  return (
    <Chart
      definition={definition}
      height={460}
      ariaLabel={`${label} climatology for ${stationName}, ${year}`}
      ariaDescription={`Daily ${label.toLowerCase()} in ${year} against the range, median and percentiles of other years for each day of the year.`}
    />
  )
}

export default ClimatologyChart
