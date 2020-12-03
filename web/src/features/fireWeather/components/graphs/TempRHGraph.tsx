import React, { useRef, useEffect, useMemo } from 'react'
import * as d3 from 'd3'

import { ObservedValue } from 'api/observationAPI'
import { ModelSummary as _ModelSummary, ModelValue } from 'api/modelAPI'
import { ForecastSummary as _ForecastSummary, NoonForecastValue } from 'api/forecastAPI'
import { formatDateInPDT } from 'utils/date'
import { PDT_UTC_OFFSET } from 'utils/constants'
import * as d3Utils from 'utils/d3'
import * as styles from 'features/fireWeather/components/graphs/TempRHGraph.styles'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import {
  useGraphCalculation,
  WeatherValue
} from 'features/fireWeather/components/graphs/TempRHGraph.utils'

export interface Props {
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
  forecastValues: NoonForecastValue[]
  forecastSummaries: _ForecastSummary[]
  gdpsValues: ModelValue[]
  gdpsSummaries: _ModelSummary[]
  biasAdjGdpsValues: ModelValue[]
  hrdpsValues: ModelValue[]
  hrdpsSummaries: _ModelSummary[]
  rdpsValues: ModelValue[]
  rdpsSummaries: _ModelSummary[]
}

/* Table layout constants */
const chartMargin = { top: 10, right: 40, bottom: 50, left: 40 }
const svgWidth = 600
const svgHeight = 300
const chartWidth = svgWidth - chartMargin.left - chartMargin.right
const chartHeight = svgHeight - chartMargin.top - chartMargin.bottom - 50

const TempRHGraph: React.FunctionComponent<Props> = (props: Props) => {
  const { toggleValues } = props
  const classes = styles.useStyles()
  const utcOffset = PDT_UTC_OFFSET

  const svgRef = useRef(null)
  const graphCalculations = useGraphCalculation(props)
  const xScale = d3
    .scaleTime()
    .domain(graphCalculations.xDomain)
    .range([0, chartWidth])
  // Use mutable ref object that doesn't cause re-render
  const xScaleRef = useRef(xScale)

  // Effect hook for displaying graphics
  useEffect(() => {
    console.log('hmm')

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
        y: d => yTempScale(d.value),
        symbol: d3.symbolSquare,
        size: 10,
        testId: 'hourly-observed-temp-symbol'
      })
      const redrawObservedTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'observed observedTempPath',
        data: gc.observedTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.value),
        strokeWidth: 1.5,
        testId: 'hourly-observed-temp-path'
      })
      const redrawObservedRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'observed observedRHSymbol',
        data: gc.observedRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value),
        symbol: d3.symbolSquare,
        size: 10,
        testId: 'hourly-observed-rh-symbol'
      })
      const redrawObservedRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'observed observedRHPath',
        data: gc.observedRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value),
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
        .call(brush.move, [xScale(gc.past2Date), xScale(gc.future2Date)])
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
                delete value.observedTemp
                delete value.observedRH
              }
              if (!toggleValues.showForecasts) {
                delete value.forecastTemp
                delete value.forecastRH
              }
              if (!toggleValues.showModels) {
                delete value.gdpsTemp
                delete value.gdpsRH
              }
              if (!toggleValues.showBiasAdjModels) {
                delete value.biasAdjGdpsTemp
                delete value.biasAdjGdpsRH
              }
              if (!toggleValues.showHighResModels) {
                delete value.hrdpsTemp
                delete value.hrdpsRH
              }
              if (!toggleValues.showRegionalModels) {
                delete value.rdpsTemp
                delete value.rdpsRH
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
                case 'observedTemp':
                  return {
                    text: `Observed Temp: ${weatherPrint} (°C)`,
                    color: styles.observedTempColor
                  }
                case 'observedRH':
                  return {
                    text: `Observed RH: ${weatherPrint} (%)`,
                    color: styles.observedRHColor
                  }
                case 'forecastTemp':
                  return {
                    text: `Forecast Temp: ${weatherPrint} (°C)`,
                    color: styles.forecastTempDotColor
                  }
                case 'forecastRH':
                  return {
                    text: `Forecast RH: ${weatherPrint} (%)`,
                    color: styles.forecastRHDotColor
                  }
                case 'gdpsTemp':
                  return {
                    text: `GDPS Temp: ${weatherPrint} (°C)`,
                    color: styles.modelTempColor
                  }
                case 'gdpsRH':
                  return {
                    text: `GDPS RH: ${weatherPrint} (%)`,
                    color: styles.modelRHColor
                  }
                case 'biasAdjGdpsTemp':
                  return {
                    text: `Bias adjusted GDPS Temp: ${weatherPrint} (°C)`,
                    color: styles.biasModelTempColor
                  }
                case 'biasAdjGdpsRH':
                  return {
                    text: `Bias adjusted GDPS RH: ${weatherPrint} (%)`,
                    color: styles.biasModelRHColor
                  }
                case 'hrdpsTemp':
                  return {
                    text: `HRDPS Temp ${weatherPrint} (°C)`,
                    color: styles.highResModelTempColor
                  }
                case 'hrdpsRH':
                  return {
                    text: `HRDPS RH ${weatherPrint} (%)`,
                    color: styles.highResModelRHColor
                  }
                case 'rdpsTemp':
                  return {
                    text: `RDPS Temp ${weatherPrint} (°C)`,
                    color: styles.regionalModelTempColor
                  }
                case 'rdpsRH':
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
