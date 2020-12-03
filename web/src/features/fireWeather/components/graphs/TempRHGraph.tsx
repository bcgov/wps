import React, { useRef, useEffect, useMemo } from 'react'
import * as d3 from 'd3'
import moment from 'moment'

import { ObservedValue } from 'api/observationAPI'
import { ModelSummary as _ModelSummary, ModelValue } from 'api/modelAPI'
import { ForecastSummary as _ForecastSummary, NoonForecastValue } from 'api/forecastAPI'
import { formatDateInPDT } from 'utils/date'
import { PDT_UTC_OFFSET } from 'utils/constants'
import * as d3Utils from 'utils/d3'
import * as styles from 'features/fireWeather/components/graphs/TempRHGraph.styles'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'

interface WeatherValue {
  date: Date
  temp?: number
  rh?: number
  modelTemp?: number
  modelRH?: number
  forecastTemp?: number
  forecastRH?: number
  biasAdjModelTemp?: number
  biasAdjModelRH?: number
  hrModelTemp?: number
  hrModelRH?: number
  regModelTemp?: number
  regModelRH?: number
}
type ModelSummary = Omit<_ModelSummary, 'datetime'> & { date: Date }
type ForecastSummary = Omit<_ForecastSummary, 'datetime'> & { date: Date }

export interface Props {
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
  modelValues: ModelValue[]
  modelSummaries: _ModelSummary[]
  forecastValues: NoonForecastValue[]
  forecastSummaries: _ForecastSummary[]
  biasAdjModelValues: ModelValue[]
  highResModelValues: ModelValue[]
  highResModelSummaries: _ModelSummary[]
  regionalModelValues: ModelValue[]
  regionalModelSummaries: _ModelSummary[]
}

/* Table layout constants */
const chartMargin = { top: 10, right: 40, bottom: 50, left: 40 }
const svgWidth = 600
const svgHeight = 300
const chartWidth = svgWidth - chartMargin.left - chartMargin.right
const chartHeight = svgHeight - chartMargin.top - chartMargin.bottom - 50

const TempRHGraph: React.FunctionComponent<Props> = ({
  toggleValues,
  observedValues,
  modelValues,
  modelSummaries,
  forecastValues,
  forecastSummaries,
  biasAdjModelValues,
  highResModelValues,
  highResModelSummaries,
  regionalModelValues,
  regionalModelSummaries
}: Props) => {
  const classes = styles.useStyles()
  const svgRef = useRef(null)
  const utcOffset = PDT_UTC_OFFSET

  const graphCalculations = useMemo(() => {
    const datesFromAllSources: Date[] = []
    const weatherValuesByDatetime: { [k: string]: WeatherValue } = {}
    let maxTemp = 40, minTemp = -10 // prettier-ignore

    const observedTempValues: { date: Date; temp: number }[] = []
    const observedRHValues: { date: Date; rh: number }[] = []
    observedValues.forEach(v => {
      if (v.temperature == null && v.relative_humidity == null) {
        return
      }

      const date = new Date(v.datetime)
      datesFromAllSources.push(date)

      const observation = { date, temp: NaN, rh: NaN }
      if (v.temperature != null) {
        const temp = Number(v.temperature.toFixed(2))
        observation.temp = temp
        observedTempValues.push(observation)
        if (temp > maxTemp) {
          maxTemp = temp
        } else if (temp < minTemp) {
          minTemp = temp
        }
      }
      if (v.relative_humidity != null) {
        observation.rh = Math.round(v.relative_humidity)
        observedRHValues.push(observation)
      }
      weatherValuesByDatetime[v.datetime] = observation
    })

    const forecastTempRHValues = forecastValues.map(v => {
      const date = new Date(v.datetime)
      datesFromAllSources.push(date)

      const temp = Number(v.temperature.toFixed(2))
      const rh = Math.round(v.relative_humidity)

      if (temp > maxTemp) {
        maxTemp = temp
      } else if (temp < minTemp) {
        minTemp = temp
      }

      // combine with existing observed and models values
      weatherValuesByDatetime[v.datetime] = {
        ...weatherValuesByDatetime[v.datetime],
        date,
        forecastTemp: temp,
        forecastRH: rh
      }

      return {
        date,
        temp,
        rh
      }
    })

    const forecastTempRHSummaries = forecastSummaries.map(summary => {
      const { datetime, ...rest } = summary

      const date = new Date(datetime)
      datesFromAllSources.push(date)

      if (rest.tmp_max > maxTemp) {
        maxTemp = rest.tmp_max
      }
      if (rest.tmp_min < minTemp) {
        minTemp = rest.tmp_min
      }

      return { date, ...rest }
    })

    const weatherValues = Object.values(weatherValuesByDatetime).sort(
      (a, b) => a.date.valueOf() - b.date.valueOf()
    )

    const currDate = new Date()
    const past5Date = moment(currDate).subtract(5, 'days').toDate() // prettier-ignore
    const past2Date = moment(currDate).subtract(2, 'days').toDate() // prettier-ignore
    const future2Date = moment(currDate).add(2, 'days').toDate() // prettier-ignore
    const [minDate, maxDate] = d3.extent(datesFromAllSources)
    let d1 = minDate || past5Date
    let d2 = maxDate || future2Date
    d1 = moment(d1)
      .subtract(1, 'hours')
      .toDate()
    d2 = moment(d2)
      .add(1, 'hours')
      .toDate()
    const xDomain: [Date, Date] = [d1, d2]
    const xScale = d3
      .scaleTime()
      .domain(xDomain)
      .range([0, chartWidth])
    const defaultBrushSelection = [xScale(past2Date), xScale(future2Date)]

    return {
      xDomain,
      xScale,
      defaultBrushSelection,
      maxTemp: Math.ceil(maxTemp / 5) * 5, // nearest 5
      minTemp: Math.floor(minTemp / 5) * 5, // nearest -5
      currDate,
      weatherValues,
      observedTempValues,
      observedRHValues,
      forecastTempRHValues,
      forecastTempRHSummaries
    }
  }, [
    observedValues,
    modelValues,
    modelSummaries,
    forecastValues,
    forecastSummaries,
    biasAdjModelValues,
    highResModelValues,
    highResModelSummaries,
    regionalModelValues,
    regionalModelSummaries
  ])

  // Use mutable ref object that doesn't cause re-render
  const xScaleRef = useRef(graphCalculations.xScale)

  // Effect hook for displaying graphics
  useEffect(() => {
    const gc = graphCalculations
    if (svgRef.current) {
      /* Clear previous graphics before rendering new ones */
      d3.select(svgRef.current)
        .selectAll('*')
        .remove()

      const svg = d3
        .select(svgRef.current)
        .attr('viewBox', `0 0 ${svgWidth} ${svgHeight}`)

      // Set up a clipper that removes graphics that don't fall within the boundary
      svg
        .append('defs')
        .append('clipPath')
        .attr('id', 'clip')
        .append('rect')
        .attr('x', 0)
        .attr('y', -10) // - 10 to show the text(Now) from the reference line
        .attr('width', chartWidth + 2) // + 2 to show the last tick of the x axis
        .attr('height', chartHeight + 50) // +50 to show the x axis and its labels

      const chart = svg
        .append('g')
        .attr('class', 'chart')
        .attr('transform', `translate(${chartMargin.left}, ${chartMargin.top})`)
        .attr('clip-path', 'url(#clip)')

      const context = svg // svg group for Y axis and its labels
        .append('g')
        .attr('class', 'context')
        .attr('transform', `translate(${chartMargin.left}, ${chartMargin.top})`)

      const sidebarHeight = 15
      const sidebarMarginTop = chartHeight + sidebarHeight + 25
      const sidebar = svg
        .append('g')
        .attr('class', 'sidebar')
        .attr('transform', `translate(${chartMargin.left}, ${sidebarMarginTop})`)

      /* Create scales for x and y axes */
      const xScale = xScaleRef.current
      const xScaleOriginal = xScaleRef.current.copy()
      const yTempScale = d3
        .scaleLinear()
        .domain([gc.minTemp, gc.maxTemp])
        .range([chartHeight, 0])
      const yRHScale = d3
        .scaleLinear()
        .domain([0, 100])
        .range([chartHeight, 0])

      /* Render temp and rh noon forecasts and forecast summaries */
      const redrawForecastSummaryTempLines = gc.forecastTempRHSummaries.map(summary =>
        d3Utils.drawVerticalLine({
          svg: chart,
          className: 'forecast forecastSummaryTempLine',
          xScale: xScaleOriginal,
          x: xScale(summary.date),
          y1: yTempScale(summary.tmp_min),
          y2: yTempScale(summary.tmp_max),
          testId: 'forecast-summary-temp-line'
        })
      )
      const redrawForecastSummaryRHLines = gc.forecastTempRHSummaries.map(summary =>
        d3Utils.drawVerticalLine({
          svg: chart,
          className: 'forecast forecastSummaryRHLine',
          xScale: xScaleOriginal,
          x: xScale(summary.date),
          y1: yRHScale(summary.rh_min),
          y2: yRHScale(summary.rh_max)
        })
      )
      const redrawForecastTempDots = d3Utils.drawDots({
        svg: chart,
        className: 'forecast forecastTempDot',
        data: gc.forecastTempRHValues,
        cx: d => xScale(d.date),
        cy: d => yTempScale(d.temp),
        testId: 'forecast-temp-dot'
      })
      const redrawForecastRHDots = d3Utils.drawDots({
        svg: chart,
        className: 'forecast forecastRHDot',
        data: gc.forecastTempRHValues,
        cx: d => xScale(d.date),
        cy: d => yRHScale(d.rh)
      })

      /* Render temp and rh hourly observations */
      const redrawObservedTempSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'observed observedTempSymbol',
        data: gc.observedTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.temp),
        symbol: d3.symbolSquare,
        size: 10,
        testId: 'hourly-observed-temp-symbol'
      })
      const redrawObservedTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'observed observedTempPath',
        data: gc.observedTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.temp),
        strokeWidth: 1.5,
        testId: 'hourly-observed-temp-path'
      })
      const redrawObservedRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'observed observedRHSymbol',
        data: gc.observedRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.rh),
        symbol: d3.symbolSquare,
        size: 10,
        testId: 'hourly-observed-rh-symbol'
      })
      const redrawObservedRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'observed observedRHPath',
        data: gc.observedRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.rh),
        strokeWidth: 1.5,
        testId: 'hourly-observed-rh-path'
      })

      /* Render the current time reference line */
      const scaledCurrDate = xScale(gc.currDate)
      const redrawCurrLine = d3Utils.drawVerticalLine({
        svg: chart,
        className: 'currLine',
        xScale: xScaleOriginal,
        x: scaledCurrDate,
        y1: 0,
        y2: yRHScale(0)
      })
      const redrawCurrLineText = d3Utils.drawText({
        svg: chart,
        className: 'currLabel',
        xScale: xScaleOriginal,
        x: scaledCurrDate,
        y: -12,
        dx: '-1em',
        dy: '1em',
        text: 'Now'
      })

      /* Render the X & Y axis and labels */
      const xTickValues = d3Utils.getTickValues(gc.xDomain, utcOffset, false)
      const xAxisFunc = d3
        .axisBottom(xScale)
        .tickFormat(d3Utils.formatDateInMonthAndDay)
        .tickValues(xTickValues)
      chart // Include only x axis to the chart group
        .append('g')
        .attr('class', 'xAxis')
        .attr('transform', `translate(0, ${chartHeight})`)
        .call(xAxisFunc)
      context // Y temp axis
        .append('g')
        .call(d3.axisLeft(yTempScale).ticks(6))
      context // Y rh axis
        .append('g')
        .attr('transform', `translate(${chartWidth}, 0)`)
        .call(d3.axisRight(yRHScale).ticks(4))
      context // Temperature label
        .append('text')
        .attr('y', 0 - chartMargin.left)
        .attr('x', 0 - chartHeight / 2)
        .attr('dy', '1.3em')
        .attr('dx', '0')
        .attr('class', 'yAxisLabel')
        .text('Temp (°C)')
        .attr('transform', 'rotate(-90)')
      context // RH label
        .append('text')
        .attr('transform', 'rotate(-270)')
        .attr('y', 0 - chartWidth - chartMargin.left)
        .attr('x', chartHeight / 2)
        .attr('dy', '1.3em')
        .attr('class', 'yAxisLabel')
        .text('RH (%)')

      /* Render sidebar and attach its listener */
      const brushed = () => {
        // When the sidebar is moved or resized
        const selection = d3.event.selection as [number, number]
        if (selection) {
          // Update x scale with a new domain modified by the sidebar
          xScale.domain(selection.map(xScaleOriginal.invert, xScaleOriginal))

          // Update chart's x axis with the new scale
          chart.select<SVGGElement>('.xAxis').call(xAxisFunc)

          // Redraw all the displayed graphics
          redrawObservedTempSymbols?.(d => xScale(d.date))
          redrawObservedRHSymbols?.(d => xScale(d.date))
          redrawObservedTempPath(d => xScale(d.date))
          redrawObservedRHPath(d => xScale(d.date))
          redrawForecastTempDots?.(d => xScale(d.date))
          redrawForecastRHDots?.(d => xScale(d.date))
          redrawForecastSummaryTempLines.forEach(redraw => redraw(xScale))
          redrawForecastSummaryRHLines.forEach(redraw => redraw(xScale))
          // redrawModelTempSymbols?.(d => xScale(d.date))
          // redrawModelRHSymbols?.(d => xScale(d.date))
          // redrawModelTempPath(d => xScale(d.date))
          // redrawModelRHPath(d => xScale(d.date))
          // redrawModelSummaryTempArea?.(d => xScale(d.date))
          // redrawModelSummaryRHArea?.(d => xScale(d.date))
          // redrawHighResModelTempSymbols?.(d => xScale(d.date))
          // redrawHighResModelRHSymbols?.(d => xScale(d.date))
          // redrawHighResModelTempPath(d => xScale(d.date))
          // redrawHighResModelRHPath(d => xScale(d.date))
          // redrawHighResModelSummaryTempArea?.(d => xScale(d.date))
          // redrawHighResModelSummaryRHArea?.(d => xScale(d.date))
          // redrawBiasAdjModelTempSymbols?.(d => xScale(d.date))
          // redrawBiasAdjModelRHSymbols?.(d => xScale(d.date))
          // redrawBiasAdjModelTempPath(d => xScale(d.date))
          // redrawBiasAdjModelRHPath(d => xScale(d.date))
          // redrawRegionalModelTempSymbols?.(d => xScale(d.date))
          // redrawRegionalModelRHSymbols?.(d => xScale(d.date))
          // redrawRegionalModelTempPath(d => xScale(d.date))
          // redrawRegionalModelRHPath(d => xScale(d.date))
          // redrawRegionalModelSummaryTempArea?.(d => xScale(d.date))
          // redrawRegionalModelSummaryRHArea?.(d => xScale(d.date))
          redrawCurrLine(xScale)
          redrawCurrLineText(xScale)
        }
      }
      const brush = d3
        .brushX()
        .extent([
          [0, 0],
          [chartWidth, sidebarHeight]
        ])
        .on('brush', brushed)
      sidebar // Render x axis for the sidebar
        .append('g')
        .attr('transform', `translate(0, ${sidebarHeight})`)
        .call(
          d3
            .axisBottom(xScaleOriginal)
            .tickFormat(d3Utils.formatDateInMonthAndDay)
            .tickValues(xTickValues)
        )
      sidebar
        .append('g')
        .call(brush)
        .call(brush.move, graphCalculations.defaultBrushSelection)
    }
  }, [utcOffset, graphCalculations])

  // Effect hook for adding/updating tooltip
  useEffect(() => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current)
      svg.select('.tooltip').remove()
      svg.select('.tooltipCursor').remove()
      svg.select('.tooltipBackground').remove()

      const gc = graphCalculations
      const shouldShowTooltip = Object.values(toggleValues).includes(true)
      const weatherValues = shouldShowTooltip
        ? gc.weatherValues
            .map(v => {
              const value = { ...v } // create a fresh copy
              if (!toggleValues.showObservations) {
                delete value.temp
                delete value.rh
              }

              if (!toggleValues.showForecasts) {
                delete value.forecastTemp
                delete value.forecastRH
              }

              const noDataToPresent = Object.keys(value).length === 1 // only date present
              if (noDataToPresent) {
                return undefined
              }

              return value
            })
            .filter((v): v is WeatherValue => Boolean(v))
        : []

      d3Utils.addTooltipListener({
        svg: svg.select('.chart'),
        xScale: xScaleRef.current,
        width: chartWidth,
        height: chartHeight,
        data: weatherValues,
        textTestId: 'temp-rh-tooltip-text',
        bgdTestId: 'temp-rh-graph-background',
        getTextData: v =>
          Object.entries(v).map(([k, value]) => {
            const key = k as keyof WeatherValue
            if (key === 'date' && value instanceof Date) {
              return {
                text: `${formatDateInPDT(value, 'h:mm a, ddd, MMM Do')} (PDT, UTC-7)`
              }
            } else if (typeof value === 'number') {
              let weatherPrint: number | string = value
              if (isNaN(weatherPrint)) {
                weatherPrint = '-'
              }

              switch (key) {
                case 'temp':
                  return {
                    text: `Observed Temp: ${weatherPrint} (°C)`,
                    color: styles.observedTempColor
                  }
                case 'forecastTemp':
                  return {
                    text: `Forecast Temp: ${weatherPrint} (°C)`,
                    color: styles.forecastTempDotColor
                  }
                case 'modelTemp':
                  return {
                    text: `GDPS Temp: ${weatherPrint} (°C)`,
                    color: styles.modelTempColor
                  }
                case 'biasAdjModelTemp':
                  return {
                    text: `Bias adjusted GDPS Temp: ${weatherPrint} (°C)`,
                    color: styles.biasModelTempColor
                  }
                case 'hrModelTemp':
                  return {
                    text: `HRDPS Temp ${weatherPrint} (°C)`,
                    color: styles.highResModelTempColor
                  }
                case 'regModelTemp':
                  return {
                    text: `RDPS Temp ${weatherPrint} (°C)`,
                    color: styles.regionalModelTempColor
                  }

                case 'rh':
                  return {
                    text: `Observed RH: ${weatherPrint} (%)`,
                    color: styles.observedRHColor
                  }
                case 'forecastRH':
                  return {
                    text: `Forecast RH: ${weatherPrint} (%)`,
                    color: styles.forecastRHDotColor
                  }
                case 'modelRH':
                  return {
                    text: `GDPS RH: ${weatherPrint} (%)`,
                    color: styles.modelRHColor
                  }
                case 'biasAdjModelRH':
                  return {
                    text: `Bias adjusted GDPS RH: ${weatherPrint} (%)`,
                    color: styles.biasModelRHColor
                  }
                case 'hrModelRH':
                  return {
                    text: `HRDPS RH ${weatherPrint} (%)`,
                    color: styles.highResModelRHColor
                  }
                case 'regModelRH':
                  return {
                    text: `RDPS RH ${weatherPrint} (%)`,
                    color: styles.regionalModelRHColor
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
      if (svgRef.current) {
        // clean up the event listeners
        const svg = d3.select(svgRef.current)
        svg.on('touchmove mousemove', null)
        svg.on('touchend mouseleave', null)
      }
    }
  }, [graphCalculations, toggleValues])

  // Effect hooks for showing/hiding graphics
  useEffect(() => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current)
      svg.selectAll('.observed').classed('hidden', !toggleValues.showObservations)
      svg.selectAll('.forecast').classed('hidden', !toggleValues.showForecasts)
    }
  }, [toggleValues])

  return (
    <div className={classes.root}>
      <svg data-testid="temp-rh-graph" ref={svgRef} />
    </div>
  )
}

export default React.memo(TempRHGraph)
