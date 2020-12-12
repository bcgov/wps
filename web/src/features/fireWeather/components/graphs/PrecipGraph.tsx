import React, { useRef, useEffect, useMemo } from 'react'
import * as d3 from 'd3'
import { makeStyles } from '@material-ui/core/styles'
import moment from 'moment'

import { ObservedValue } from 'api/observationAPI'
import * as d3Utils from 'utils/d3'
import { formatDateInPDT } from 'utils/date'
import { NoonForecastValue } from 'api/forecastAPI'
import { ModelValue } from 'api/modelAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import { PDT_UTC_OFFSET } from 'utils/constants'

const observedPrecipColor = '#a50b41'
const accumObservedPrecipColor = observedPrecipColor
const forecastPrecipColor = '#fb0058'
const accumForecastPrecipColor = forecastPrecipColor
const gdpsPrecipColor = '#32e7e7'
const accumGDPSPrecipColor = gdpsPrecipColor
const hrdpsPrecipColor = '#a017c2'
const accumHRDPSPrecipColor = hrdpsPrecipColor
const rdpsPrecipColor = '#026200'
const accumRDPSPrecipColor = rdpsPrecipColor


const useStyles = makeStyles({
  root: {
    paddingBottom: 15,

    '& .yAxisLabel': {
      textAnchor: 'middle',
      font: '9px sans-serif'
    },

    '& .tooltip': {
      pointerEvents: 'none',
      font: '8.5px sans-serif',

      '&--hidden': {
        display: 'none'
      }
    },

    '& .tooltipCursor': {
      strokeWidth: 1,
      stroke: 'gray',
      strokeDasharray: '1,1',
      opacity: 0
    },

    '& .precipLine': {
      '&__observed': {
        strokeWidth: 2.5,
        stroke: observedPrecipColor
      },

      '&__forecast': {
        strokeWidth: 2.5,
        stroke: forecastPrecipColor
      },

      '&__gdps': {
        strokeWidth: 2.5,
        stroke: gdpsPrecipColor
      },

      '&__rdps': {
        strokeWidth: 2.5,
        stroke: rdpsPrecipColor
      },

      '&__hrdps': {
        strokeWidth: 2.5,
        stroke: hrdpsPrecipColor
      },

      '&--hidden': {
        visibility: 'hidden'
      }
    },

    '& .accumPrecipLine': {
      '&__observed': {
        stroke: accumObservedPrecipColor
      },

      '&__forecast': {
        stroke: accumForecastPrecipColor
      },

      '&__gdps': {
        stroke: accumGDPSPrecipColor
      },

      '&__rdps': {
        stroke: accumRDPSPrecipColor
      },

      '&__hrdps': {
        stroke: accumHRDPSPrecipColor
      },

      '&--hidden': {
        visibility: 'hidden'
      }
    }
  }
})

interface PrecipValue {
  date: Date
  observedPrecip?: number
  accumObservedPrecip?: number
  forecastPrecip?: number
  accumForecastPrecip?: number
  gdpsPrecip?: number
  accumGDPSPrecip?: number
  rdpsPrecip?: number
  accumRDPSPrecip?: number
  hrdpsPrecip?: number
  accumHRDPSPrecip?: number
}

interface Props {
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
  forecastValues: NoonForecastValue[]
  gdpsModelValues: ModelValue[]
  rdpsModelValues: ModelValue[]
  hrdpsModelValues: ModelValue[]
}

/* Table layout constants */
const margin = { top: 10, right: 40, bottom: 50, left: 40 }
const svgWidth = 600
const svgHeight = 250
const chartWidth = svgWidth - margin.left - margin.right
const chartHeight = svgHeight - margin.top - margin.bottom

const PrecipGraph: React.FunctionComponent<Props> = ({
  toggleValues,
  observedValues,
  forecastValues,
  gdpsModelValues,
  rdpsModelValues,
  hrdpsModelValues
}: Props) => {
  const classes = useStyles()
  const svgRef = useRef<SVGSVGElement>(null)
  const utcOffset = PDT_UTC_OFFSET

  // useMemo will only recompute the memoized value when one of the dependencies has changed.
  // This optimization helps to avoid expensive calculations on every render.
  const graphCalculations = useMemo(() => {
    const datesFromAllSources: Date[] = []
    let maxDailyPrecip = 10
    let maxAccumPrecip = 10

    const aggreObservedPrecips: { [k: string]: number } = {}
    observedValues.forEach(({ datetime, precipitation }) => {
      const date = formatDateInPDT(datetime, 'YYYY-MM-DD')
      const precip = Number(precipitation)

      if (!aggreObservedPrecips[date]) {
        aggreObservedPrecips[date] = precip
      } else {
        aggreObservedPrecips[date] = aggreObservedPrecips[date] + precip
      }
    })

    const observedPrecips = Object.entries(aggreObservedPrecips).map(
      ([formattedDate, totalPrecip]) => {
        const date = moment(formattedDate)
          .utc()
          .set({ hour: Math.abs(utcOffset), minute: 0 })
          .toDate()
        datesFromAllSources.push(date)

        if (totalPrecip > maxDailyPrecip) {
          maxDailyPrecip = totalPrecip
        }

        return {
          date,
          value: Number(totalPrecip.toFixed(2))
        }
      }
    )

    const accumObservedPrecips: { date: Date, accumPrecip: number }[] = []
    observedPrecips.forEach(({ date, value }) => {
      const observed = { date, accumPrecip: NaN }
      if (value != null) {
        if (accumObservedPrecips.length == 0) {
          observed.accumPrecip = value
        }
        else {
          observed.accumPrecip = value + accumObservedPrecips[accumObservedPrecips.length - 1].accumPrecip
        }
        accumObservedPrecips.push(observed)
      }
    })
    if (maxAccumPrecip < accumObservedPrecips[accumObservedPrecips.length - 1].accumPrecip) {
      maxAccumPrecip = accumObservedPrecips[accumObservedPrecips.length - 1].accumPrecip
    }

    const forecastPrecips = forecastValues.map(
      ({ datetime, total_precipitation: totalPrecip }) => {
        const date = moment(datetime)
          .utc()
          .set({ hour: Math.abs(utcOffset) })
          .toDate()
        datesFromAllSources.push(date)

        if (totalPrecip > maxDailyPrecip) {
          maxDailyPrecip = totalPrecip
        }

        return {
          date,
          value: Number(totalPrecip.toFixed(2))
        }
      }
    )

    const accumForecastPrecips: { date: Date, accumPrecip: number }[] = []
    forecastPrecips.forEach(({ date, value }) => {
      const forecast = { date, accumPrecip: NaN }
      if (value != null) {
        if (accumForecastPrecips.length == 0) {
          forecast.accumPrecip = value
        }
        else {
          forecast.accumPrecip = value + accumForecastPrecips[accumForecastPrecips.length - 1].accumPrecip
        }
        accumForecastPrecips.push(forecast)
      }
    })
    if (maxAccumPrecip < accumForecastPrecips[accumForecastPrecips.length - 1].accumPrecip) {
      maxAccumPrecip = accumForecastPrecips[accumForecastPrecips.length - 1].accumPrecip
    }
    
    const aggreGDPSPrecips: { [k: string]: number } = {}
    gdpsModelValues.forEach(({ datetime, delta_precipitation }) => {
      const date = formatDateInPDT(datetime, 'YYYY-MM-DD')
      const precip = Number(delta_precipitation)

      if (!aggreGDPSPrecips[date]) {
        aggreGDPSPrecips[date] = precip
      } else {
        aggreGDPSPrecips[date] += precip
      }
    })

    const gdpsPrecips = Object.entries(aggreGDPSPrecips).map(
      ([formattedDate, totalPrecip]) => {
        const date = moment(formattedDate)
          .utc()
          .set({ hour: Math.abs(utcOffset), minute: 0 })
          .toDate()
        datesFromAllSources.push(date)
        if (totalPrecip > maxDailyPrecip) {
          maxDailyPrecip = totalPrecip
        }

        return {
          date,
          value: Number(totalPrecip?.toFixed(2))
        }
      }
    )

    const accumGDPSPrecips: { date: Date, accumPrecip: number }[] = []
    gdpsPrecips.forEach(({ date, value }) => {
      const gdps = { date, accumPrecip: NaN }
      if (value != null) {
        if (accumGDPSPrecips.length == 0) {
          gdps.accumPrecip = value
        }
        else {
          gdps.accumPrecip = value + accumGDPSPrecips[accumGDPSPrecips.length - 1].accumPrecip
        }
        accumGDPSPrecips.push(gdps)
      }
    })
    if (maxAccumPrecip < accumGDPSPrecips[accumGDPSPrecips.length - 1].accumPrecip) {
      maxAccumPrecip = accumGDPSPrecips[accumGDPSPrecips.length - 1].accumPrecip
    }

    const aggreRDPSPrecips: { [k: string]: number } = {}
    rdpsModelValues.forEach(({ datetime, delta_precipitation: precip }) => {
      const date = formatDateInPDT(datetime, 'YYYY-MM-DD')
      if (!aggreRDPSPrecips[date]) {
        aggreRDPSPrecips[date] = Number(precip)
      } else {
        aggreRDPSPrecips[date] += Number(precip)
      }
    })

    const rdpsPrecips = Object.entries(aggreRDPSPrecips).map(
      ([formattedDate, totalPrecip]) => {
        const date = moment(formattedDate)
          .utc()
          .set({ hour: Math.abs(utcOffset), minute: 0 })
          .toDate()
        datesFromAllSources.push(date)

        if (totalPrecip > maxDailyPrecip) {
          maxDailyPrecip = totalPrecip
        }

        return {
          date,
          value: Number(totalPrecip?.toFixed(2))
        }
      }
    )

    const accumRDPSPrecips: { date: Date, accumPrecip: number }[] = []
    rdpsPrecips.forEach(({ date, value }) => {
      const rdps = { date, accumPrecip: NaN }
      if (value != null) {
        if (accumRDPSPrecips.length == 0) {
          rdps.accumPrecip = value
        }
        else {
          rdps.accumPrecip = value + accumRDPSPrecips[accumRDPSPrecips.length - 1].accumPrecip
        }
        accumRDPSPrecips.push(rdps)
      }
    })
    if (maxAccumPrecip < accumRDPSPrecips[accumRDPSPrecips.length - 1].accumPrecip) {
      maxAccumPrecip = accumRDPSPrecips[accumRDPSPrecips.length - 1].accumPrecip
    }

    const aggreHRDPSPrecips: { [k: string]: number } = {}
    hrdpsModelValues.forEach(({ datetime, delta_precipitation: precip }) => {
      const date = formatDateInPDT(datetime, 'YYYY-MM-DD')
      if (!aggreHRDPSPrecips[date]) {
        aggreHRDPSPrecips[date] = Number(precip)
      } else {
        aggreHRDPSPrecips[date] += Number(precip)
      }
    })
    const hrdpsPrecips = Object.entries(aggreHRDPSPrecips).map(
      ([formattedDate, totalPrecip]) => {
        const date = moment(formattedDate)
          .utc()
          .set({ hour: Math.abs(utcOffset), minute: 0 })
          .toDate()
        datesFromAllSources.push(date)

        if (totalPrecip > maxDailyPrecip) {
          maxDailyPrecip = totalPrecip
        }

        return {
          date,
          value: Number(totalPrecip?.toFixed(2))
        }
      }
    )

    const accumHRDPSPrecips: { date: Date, accumPrecip: number }[] = []
    hrdpsPrecips.forEach(({ date, value }) => {
      const hrdps = { date, accumPrecip: NaN }
      if (value != null) {
        if (accumHRDPSPrecips.length == 0) {
          hrdps.accumPrecip = value
        }
        else {
          hrdps.accumPrecip = value + accumHRDPSPrecips[accumHRDPSPrecips.length - 1].accumPrecip
        }
        accumHRDPSPrecips.push(hrdps)
      }
    })
    if (maxAccumPrecip < accumHRDPSPrecips[accumHRDPSPrecips.length - 1].accumPrecip) {
      maxAccumPrecip = accumHRDPSPrecips[accumHRDPSPrecips.length - 1].accumPrecip
    }

    const currDate = new Date()
    const past5Date = moment(currDate)
      .subtract(5, 'days')
      .toDate()
    const [minDate, maxDate] = d3.extent(datesFromAllSources)
    let d1 = minDate || past5Date
    let d2 = maxDate || currDate
    d1 = moment(d1)
      .subtract(6, 'hours')
      .toDate()
    d2 = moment(d2)
      .add(6, 'hours')
      .toDate()
    const xDomain: [Date, Date] = [d1, d2]
    maxDailyPrecip = Math.ceil(maxDailyPrecip / 10) * 10 // round to the nearest 10
    maxAccumPrecip = Math.ceil(maxAccumPrecip / 10) * 10 // round to the nearest 10

    return {
      xDomain,
      xTickValues: d3Utils.getTickValues(xDomain, utcOffset, false),
      maxDailyPrecip,
      maxAccumPrecip,
      observedPrecips,
      accumObservedPrecips,
      forecastPrecips,
      accumForecastPrecips,
      gdpsPrecips,
      accumGDPSPrecips,
      rdpsPrecips,
      accumRDPSPrecips,
      hrdpsPrecips,
      accumHRDPSPrecips
    }
  }, [
    utcOffset,
    observedValues,
    forecastValues,
    gdpsModelValues,
    rdpsModelValues,
    hrdpsModelValues
  ])

  // Effect hook for displaying graphics
  useEffect(() => {
    const {
      xDomain,
      xTickValues,
      maxDailyPrecip,
      maxAccumPrecip,
      observedPrecips,
      accumObservedPrecips,
      forecastPrecips,
      accumForecastPrecips,
      gdpsPrecips,
      accumGDPSPrecips,
      rdpsPrecips,
      accumRDPSPrecips,
      hrdpsPrecips,
      accumHRDPSPrecips
    } = graphCalculations

    if (svgRef.current) {
      /* Clear previous graphics before rendering new ones */
      d3.select(svgRef.current)
        .selectAll('*')
        .remove()

      const svg = d3
        .select(svgRef.current)
        .attr('viewBox', `0 0 ${svgWidth} ${svgHeight}`)

      const chart = svg
        .append('g')
        .attr('class', 'chart')
        .attr('transform', `translate(${margin.left}, ${margin.top})`)

      const context = svg // svg group for Y axis and its labels
        .append('g')
        .attr('class', 'context')
        .attr('transform', `translate(${margin.left}, ${margin.top})`)

      const legendMarginTop = chartHeight + 40
      svg
        .append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${margin.left}, ${legendMarginTop})`)

      /* Create scales for x and y axes */
      const xScale = d3
        .scaleTime()
        .domain(xDomain)
        .range([0, chartWidth])
      const xScaleOriginal = xScale.copy()
      const yDailyScale = d3
        .scaleLinear()
        .domain([0, maxDailyPrecip])
        .range([chartHeight, 0])
      const yAccumScale = d3
        .scaleLinear()
        .domain([0, maxAccumPrecip])
        .range([chartHeight, 0])

      observedPrecips.forEach(precip =>
        d3Utils.drawVerticalLine({
          svg: chart,
          className: 'precipLine__observed',
          xScale: xScaleOriginal,
          x: xScale(precip.date) - 8,
          y1: yDailyScale(precip.value),
          y2: yDailyScale(0),
          testId: 'observed-precip-line'
        })
      )

      d3Utils.drawPath({
        svg: chart,
        className: 'accumPrecipLine__observed',
        data: accumObservedPrecips,
        x: d => xScale(d.date),
        y: d => yAccumScale(d.accumPrecip),
        testId: 'accum-observed-precip-path'
      })

      forecastPrecips.forEach(precip =>
        d3Utils.drawVerticalLine({
          svg: chart,
          className: 'precipLine__forecast',
          xScale: xScaleOriginal,
          x: xScale(precip.date) - 4,
          y1: yDailyScale(precip.value),
          y2: yDailyScale(0),
          testId: 'forecast-precip-line'
        })
      )

      d3Utils.drawPath({
        svg: chart,
        className: 'accumPrecipLine__forecast',
        data: accumForecastPrecips,
        x: d => xScale(d.date),
        y: d => yAccumScale(d.accumPrecip),
        testId: 'accum-forecast-precip-path'
      })

      gdpsPrecips.forEach(precip =>
        d3Utils.drawVerticalLine({
          svg: chart,
          className: 'precipLine__gdps',
          xScale: xScaleOriginal,
          x: xScale(precip.date),
          y1: yDailyScale(precip.value),
          y2: yDailyScale(0),
          testId: 'gdps-precip-line'
        })
      )

      d3Utils.drawPath({
        svg: chart,
        className: 'accumPrecipLine__gdps',
        data: accumGDPSPrecips,
        x: d => xScale(d.date),
        y: d => yAccumScale(d.accumPrecip),
        testId: 'accum-gdps-precip-path'
      })

      rdpsPrecips.forEach(precip =>
        d3Utils.drawVerticalLine({
          svg: chart,
          className: 'precipLine__rdps',
          xScale: xScaleOriginal,
          x: xScale(precip.date) + 4,
          y1: yDailyScale(precip.value),
          y2: yDailyScale(0),
          testId: 'rdps-precip-line'
        })
      )

      d3Utils.drawPath({
        svg: chart,
        className: 'accumPrecipLine__rdps',
        data: accumRDPSPrecips,
        x: d => xScale(d.date),
        y: d => yAccumScale(d.accumPrecip),
        testId: 'accum-rdps-precip-path'
      })

      hrdpsPrecips.forEach(precip =>
        d3Utils.drawVerticalLine({
          svg: chart,
          className: 'precipLine__hrdps',
          xScale: xScaleOriginal,
          x: xScale(precip.date) + 8,
          y1: yDailyScale(precip.value),
          y2: yDailyScale(0),
          testId: 'hrdps-precip-line'
        })
      )

      d3Utils.drawPath({
        svg: chart,
        className: 'accumPrecipLine__hrdps',
        data: accumHRDPSPrecips,
        x: d => xScale(d.date),
        y: d => yAccumScale(d.accumPrecip),
        testId: 'accum-hrdps-precip-path'
      })

      /* Render the X & Y axis and labels */
      chart
        .append('g')
        .attr('class', 'xAxis')
        .attr('transform', `translate(0, ${chartHeight})`)
        .call(
          d3
            .axisBottom(xScale)
            .tickFormat(d3Utils.formatDateInMonthAndDay)
            .tickValues(xTickValues)
        )
      context
        .append('g')
        .attr('class', 'yAxis')
        .call(d3.axisLeft(yDailyScale).ticks(5))
      context
        .append('g')
        .attr('class', 'yAccumAxis')
        .attr('transform', `translate(${chartWidth}, 0)`)
        .call(d3.axisRight(yAccumScale).ticks(5))
      context // Daily Precipitation label
        .append('text')
        .attr('y', 0 - margin.left)
        .attr('x', 0 - chartHeight / 2)
        .attr('dy', '1.3em')
        .attr('dx', '0')
        .attr('class', 'yAxisLabel')
        .text('Daily Precipitation (mm/cm)')
        .attr('transform', 'rotate(-90)')
      context // Accum Precipitation label
        .append('text')
        .attr('y', 0 - chartWidth - margin.left)
        .attr('x', chartHeight / 2)
        .attr('dy', '1.3em')
        .attr('dx', '0')
        .attr('class', 'yAxisLabel')
        .text('Accumulated Precipitation (mm/cm)')
        .attr('transform', 'rotate(90)')
    }
  }, [graphCalculations])

  const precipsOfInterest = useMemo(() => {
    const precipsByDatetime: { [date: string]: PrecipValue } = {}

    toggleValues.showObservations &&
      graphCalculations.observedPrecips.forEach(({ date, value }) => {
        precipsByDatetime[date.toISOString()] = { date, observedPrecip: value }
      })
    toggleValues.showObservations &&
      graphCalculations.accumObservedPrecips.forEach(({ date, accumPrecip }) => {
        precipsByDatetime[date.toISOString()] = {
          ...precipsByDatetime[date.toISOString()],
          date,
          accumObservedPrecip: accumPrecip
        }
      })

    toggleValues.showForecasts &&
      graphCalculations.forecastPrecips.forEach(({ date, value }) => {
        precipsByDatetime[date.toISOString()] = {
          ...precipsByDatetime[date.toISOString()],
          date,
          forecastPrecip: value
        }
      })
    toggleValues.showForecasts &&
      graphCalculations.accumForecastPrecips.forEach(({ date, accumPrecip }) => {
        precipsByDatetime[date.toISOString()] = { 
          ...precipsByDatetime[date.toISOString()],
          date,
          accumForecastPrecip: accumPrecip
        }
      })

    toggleValues.showModels &&
      graphCalculations.gdpsPrecips.forEach(({ date, value }) => {
        precipsByDatetime[date.toISOString()] = {
          ...precipsByDatetime[date.toISOString()],
          date,
          gdpsPrecip: value
        }
      })
    toggleValues.showModels &&
      graphCalculations.accumGDPSPrecips.forEach(({ date, accumPrecip }) => {
        precipsByDatetime[date.toISOString()] = {
          ...precipsByDatetime[date.toISOString()],
          date,
          accumGDPSPrecip: accumPrecip
        }
      })

    toggleValues.showRegionalModels &&
      graphCalculations.rdpsPrecips.forEach(({ date, value }) => {
        precipsByDatetime[date.toISOString()] = {
          ...precipsByDatetime[date.toISOString()],
          date,
          rdpsPrecip: value
        }
      })
    toggleValues.showRegionalModels &&
      graphCalculations.accumRDPSPrecips.forEach(({ date, accumPrecip }) => {
        precipsByDatetime[date.toISOString()] = {
          ...precipsByDatetime[date.toISOString()],
          date,
          accumRDPSPrecip: accumPrecip
        }
      })

    toggleValues.showHighResModels &&
      graphCalculations.hrdpsPrecips.forEach(({ date, value }) => {
        precipsByDatetime[date.toISOString()] = {
          ...precipsByDatetime[date.toISOString()],
          date,
          hrdpsPrecip: value
        }
      })
    toggleValues.showHighResModels &&
      graphCalculations.accumHRDPSPrecips.forEach(({ date, accumPrecip }) => {
        precipsByDatetime[date.toISOString()] = {
          ...precipsByDatetime[date.toISOString()],
          date,
          accumHRDPSPrecip: accumPrecip
        }
      })

    return Object.values(precipsByDatetime)
  }, [toggleValues, graphCalculations])

  // Effect hook for updating the legend
  useEffect(() => {
    const legendData: d3Utils.Legend[] = []
    if (toggleValues.showObservations) {
      legendData.push({
        text: 'Observed Precip',
        shape: 'rect',
        color: observedPrecipColor
      })
      legendData.push({
        text: 'Accumulated Observed Precip',
        shape: 'rect',
        color: accumObservedPrecipColor
      })
    }
    if (toggleValues.showForecasts) {
      legendData.push({
        text: 'Forecast Precip',
        shape: 'rect',
        color: forecastPrecipColor
      })
      legendData.push({
        text: 'Accumulated Forecast Precip',
        shape: 'rect',
        color: accumForecastPrecipColor
      })
    }
    if (toggleValues.showHighResModels) {
      legendData.push({
        text: 'HRDPS Precip',
        shape: 'rect',
        color: hrdpsPrecipColor
      })
      legendData.push({
        text: 'Accumulated HRDPS Precip',
        shape: 'rect',
        color: accumHRDPSPrecipColor
      })
    }
    if (toggleValues.showRegionalModels) {
      legendData.push({
        text: 'RDPS Precip',
        shape: 'rect',
        color: rdpsPrecipColor
      })
      legendData.push({
        text: 'Accumulated RDPS Precip',
        shape: 'rect', 
        color: accumRDPSPrecipColor
      })
    }
    if (toggleValues.showModels) {
      legendData.push({
        text: 'GDPS Precip',
        shape: 'rect',
        color: gdpsPrecipColor
      })
      legendData.push({
        text: 'Accumulated GDPS Precip',
        shape: 'rect',
        color: accumGDPSPrecipColor
      })
    }
    const svgElement = svgRef.current
    if (svgElement) {
      const svg = d3.select(svgElement)
      // Grab the legend.
      const legend = svg.select<SVGGElement>('.legend')
      // Clear out all the child nodes.
      legend.selectAll('*').remove()
      // Re-create the legend.
      d3Utils.addLegend(legend, chartWidth, legendData)
    }
  }, [toggleValues])

  // Effect hook for adding/updating tooltip
  useEffect(() => {
    const svgElement = svgRef.current
    if (svgElement) {
      const svg = d3.select(svgElement)
      svg.select('.tooltip').remove()
      svg.select('.tooltipCursor').remove()
      svg.select('.tooltipBackground').remove()

      const xScale = d3
        .scaleTime()
        .domain(graphCalculations.xDomain)
        .range([0, chartWidth])

      d3Utils.addTooltipListener({
        svg: svg.select('.chart'),
        xScale,
        width: chartWidth,
        height: chartHeight,
        data: precipsOfInterest,
        textTestId: 'precip-tooltip-text',
        bgdTestId: 'precip-graph-background',
        getTextData: v =>
          Object.entries(v).map(([k, value]) => {
            const key = k as keyof PrecipValue
            if (key === 'date' && value instanceof Date) {
              return {
                text: `${formatDateInPDT(value, 'dddd, MMM Do')} (PDT, UTC-7)`
              }
            } else if (typeof value === 'number') {
              switch (key) {
                case 'observedPrecip':
                  return {
                    text: `Observed Precip: ${value} (mm/cm)`,
                    color: observedPrecipColor
                  }
                case 'accumObservedPrecip':
                  return {
                    text: `Accumulated Observed Precip: ${Number(value).toFixed(2)} (mm/cm)`,
                    color: accumObservedPrecipColor
                  }
                case 'forecastPrecip':
                  return {
                    text: `Forecast Precip: ${value} (mm/cm)`,
                    color: forecastPrecipColor
                  }
                case 'accumForecastPrecip':
                  return {
                    text: `Accumulated Forecast Precip: ${Number(value).toFixed(2)} (mm/cm)`,
                    color: accumForecastPrecipColor
                  }
                case 'gdpsPrecip':
                  return {
                    text: `GDPS Precip: ${value} (mm/cm)`,
                    color: gdpsPrecipColor
                  }
                case 'accumGDPSPrecip':
                  return {
                    text: `Accumulated GDPS Precip: ${Number(value).toFixed(2)} (mm/cm)`,
                    color: accumGDPSPrecipColor
                  }
                case 'rdpsPrecip':
                  return {
                    text: `RDPS Precip: ${value} (mm/cm)`,
                    color: rdpsPrecipColor
                  }
                case 'accumRDPSPrecip':
                  return {
                    text: `Accumulated RDPS Precip: ${Number(value).toFixed(2)} (mm/cm)`,
                    color: accumRDPSPrecipColor
                  }
                case 'hrdpsPrecip':
                  return {
                    text: `HRDPS Precip: ${value} (mm/cm)`,
                    color: hrdpsPrecipColor
                  }
                case 'accumHRDPSPrecip':
                  return {
                    text: `Accumulated HRDPS Precip: ${Number(value).toFixed(2)} (mm/cm)`,
                    color: accumHRDPSPrecipColor
                  }
                default:
                  return undefined
              }
            }

            return undefined
          })
      })
    }

    return () => {
      if (svgElement) {
        // clean up the event listeners
        const svg = d3.select(svgElement)
        svg.on('touchmove mousemove', null)
        svg.on('touchend mouseleave', null)
      }
    }
  }, [graphCalculations, precipsOfInterest])

  // Effect hooks for showing/hiding graphics
  useEffect(() => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current)
      svg.selectAll('.precipLine__forecast').classed('precipLine--hidden', !toggleValues.showForecasts)
      svg.selectAll('.accumPrecipLine__forecast').classed('accumPrecipLine--hidden', !toggleValues.showForecasts)
      svg.selectAll('.precipLine__observ').classed('precipLine--hidden', !toggleValues.showObservations)
      svg.selectAll('.accumPrecipLine__observed').classed('accumPrecipLine--hidden', !toggleValues.showObservations)
      svg
        .selectAll('.precipLine__gdps')
        .classed('precipLine--hidden', !toggleValues.showModels)
      svg.selectAll('.accumPrecipLine__gdps').classed('accumPrecipLine--hidden', !toggleValues.showModels)
      svg
        .selectAll('.precipLine__rdps')
        .classed('precipLine--hidden', !toggleValues.showRegionalModels)
      svg.selectAll('.accumPrecipLine__rdps').classed('accumPrecipLine--hidden', !toggleValues.showRegionalModels)
      svg
        .selectAll('.precipLine__hrdps')
        .classed('precipLine--hidden', !toggleValues.showHighResModels)
      svg.selectAll('.accumPrecipLine__hrdps').classed('accumPrecipLine--hidden', !toggleValues.showHighResModels)
    }
  }, [toggleValues])

  return (
    <div className={classes.root}>
      <svg data-testid="precip-graph" ref={svgRef} />
    </div>
  )
}

export default React.memo(PrecipGraph)
