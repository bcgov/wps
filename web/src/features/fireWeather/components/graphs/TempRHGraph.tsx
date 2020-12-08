import React, { useRef, useEffect } from 'react'
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
  getLegendData,
  useMemoGraphCalculation,
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
const margin = { top: 10, right: 40, bottom: 20, left: 40 }
const graphWidth = 600
const graphHeight = 300
const legendHeight = 15
const chartWidth = graphWidth - margin.left - margin.right
const chartHeight = graphHeight - margin.top - margin.bottom - 50

const TempRHGraph: React.FunctionComponent<Props> = (props: Props) => {
  const { toggleValues } = props
  const classes = styles.useStyles()
  const utcOffset = PDT_UTC_OFFSET

  const graphRef = useRef<SVGSVGElement>(null)
  const legendRef = useRef<SVGSVGElement>(null)
  const graphCalc = useMemoGraphCalculation(props, chartWidth)

  // Effect hook for displaying graphics
  useEffect(() => {
    const svgGraphElement = graphRef.current
    if (svgGraphElement) {
      /* Clear previous graphics before rendering new ones */
      d3.select(svgGraphElement)
        .selectAll('*')
        .remove()

      const svg = d3
        .select(svgGraphElement)
        .attr('viewBox', `0 0 ${graphWidth} ${graphHeight}`)

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
        .attr('transform', `translate(${margin.left}, ${margin.top})`)
        .attr('clip-path', 'url(#clip)')

      const context = svg // svg group for Y axis and its labels
        .append('g')
        .attr('class', 'context')
        .attr('transform', `translate(${margin.left}, ${margin.top})`)

      const sidebarHeight = 15
      const sidebarMarginTop = chartHeight + sidebarHeight + 25
      const sidebar = svg
        .append('g')
        .attr('class', 'sidebar')
        .attr('transform', `translate(${margin.left}, ${sidebarMarginTop})`)

      /* Create scales for x and y axes */
      const xScale = graphCalc.xScale
      const xScaleOriginal = graphCalc.xScale.copy()
      const yTempScale = d3
        .scaleLinear()
        .domain(graphCalc.tempDomain)
        .range([chartHeight, 0])
      const yRHScale = d3
        .scaleLinear()
        .domain([0, 100])
        .range([chartHeight, 0])

      /* Render GDPS temp and rh summary clouds */
      const redrawModelSummaryTempArea = d3Utils.drawArea({
        svg: chart,
        className: 'gdps modelSummaryTempArea',
        datum: graphCalc.gdpsTempRHSummaries,
        x: d => xScale(d.date),
        y0: d => yTempScale(d.tmp_tgl_2_90th),
        y1: d => yTempScale(d.tmp_tgl_2_5th),
        testId: 'model-summary-temp-area'
      })
      const redrawModelSummaryRHArea = d3Utils.drawArea({
        svg: chart,
        className: 'gdps modelSummaryRHArea',
        datum: graphCalc.gdpsTempRHSummaries,
        x: d => xScale(d.date),
        y0: d => yRHScale(d.rh_tgl_2_90th),
        y1: d => yRHScale(d.rh_tgl_2_5th)
      })

      /* Draw RDPS temp and rh clouds */
      const redrawRegionalModelSummaryTempArea = d3Utils.drawArea({
        svg: chart,
        className: 'rdps regionalModelSummaryTempArea',
        datum: graphCalc.rdpsTempRHSummaries,
        x: d => xScale(d.date),
        y0: d => yTempScale(d.tmp_tgl_2_90th),
        y1: d => yTempScale(d.tmp_tgl_2_5th),
        testId: 'regional-model-summary-temp-area'
      })
      const redrawRegionalModelSummaryRHArea = d3Utils.drawArea({
        svg: chart,
        className: 'rdps regionalModelSummaryRHArea',
        datum: graphCalc.rdpsTempRHSummaries,
        x: d => xScale(d.date),
        y0: d => yRHScale(d.rh_tgl_2_90th),
        y1: d => yRHScale(d.rh_tgl_2_5th)
      })

      /* Draw HRDPS temp and rh clouds */
      const redrawHighResModelSummaryTempArea = d3Utils.drawArea({
        svg: chart,
        className: 'hrdps highResModelSummaryTempArea',
        datum: graphCalc.hrdpsTempRHSummaries,
        x: d => xScale(d.date),
        y0: d => yTempScale(d.tmp_tgl_2_90th),
        y1: d => yTempScale(d.tmp_tgl_2_5th),
        testId: 'high-res-model-summary-temp-area'
      })
      const redrawHighResModelSummaryRHArea = d3Utils.drawArea({
        svg: chart,
        className: 'hrdps highResModelSummaryRHArea',
        datum: graphCalc.hrdpsTempRHSummaries,
        x: d => xScale(d.date),
        y0: d => yRHScale(d.rh_tgl_2_90th),
        y1: d => yRHScale(d.rh_tgl_2_5th)
      })

      /* Draw noon forecasts temp and rh lines and clouds */
      const redrawForecastSummaryTempLines = graphCalc.forecastTempRHSummaries.map(
        summary =>
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
      const redrawForecastSummaryRHLines = graphCalc.forecastTempRHSummaries.map(
        summary =>
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
        data: graphCalc.forecastTempRHs,
        cx: d => xScale(d.date),
        cy: d => yTempScale(d.temp),
        testId: 'forecast-temp-dot'
      })
      const redrawForecastRHDots = d3Utils.drawDots({
        svg: chart,
        className: 'forecast forecastRHDot',
        data: graphCalc.forecastTempRHs,
        cx: d => xScale(d.date),
        cy: d => yRHScale(d.rh)
      })

      /* Draw GDPS temp and rh lines and dots */
      const redrawModelTempSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'gdps modelTempSymbol',
        data: graphCalc.gdpsTemps,
        x: d => xScale(d.date),
        y: d => yTempScale(d.value),
        size: 10,
        symbol: d3.symbolTriangle,
        testId: 'model-temp-symbol'
      })
      const redrawModelTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'gdps modelTempPath',
        data: graphCalc.gdpsTemps,
        x: d => xScale(d.date),
        y: d => yTempScale(d.value),
        testId: 'model-temp-path'
      })
      const redrawModelRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'gdps modelRHSymbol',
        data: graphCalc.gdpsRHs,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value),
        size: 10,
        symbol: d3.symbolTriangle,
        testId: 'model-rh-symbol'
      })
      const redrawModelRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'gdps modelRHPath',
        data: graphCalc.gdpsRHs,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value),
        testId: 'model-rh-path'
      })

      /* Draw bias adjusted GDPS temp and rh lines and dots */
      const redrawBiasAdjModelTempSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'biasAdjGdps biasAdjModelTempSymbol',
        data: graphCalc.biasAdjGdpsTemps,
        x: d => xScale(d.date),
        y: d => yTempScale(d.value),
        size: 5,
        symbol: d3.symbolDiamond,
        testId: 'bias-adjusted-model-temp-symbol'
      })
      const redrawBiasAdjModelTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'biasAdjGdps biasAdjModelTempPath',
        data: graphCalc.biasAdjGdpsTemps,
        x: d => xScale(d.date),
        y: d => yTempScale(d.value),
        testId: 'bias-adjusted-model-temp-path'
      })
      const redrawBiasAdjModelRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'biasAdjGdps biasAdjModelRHSymbol',
        data: graphCalc.biasAdjGdpsRHs,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value),
        size: 5,
        symbol: d3.symbolDiamond,
        testId: 'bias-adjusted-model-rh-symbol'
      })
      const redrawBiasAdjModelRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'biasAdjGdps biasAdjModelRHPath',
        data: graphCalc.biasAdjGdpsRHs,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value),
        testId: 'bias-adjusted-model-rh-path'
      })

      /* Draw RDPS temp and rh lines and dots */
      const redrawRegionalModelTempSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'rdps regionalModelTempSymbol',
        data: graphCalc.rdpsTemps,
        x: d => xScale(d.date),
        y: d => yTempScale(d.value),
        size: 5,
        symbol: d3.symbolCross,
        testId: 'regional-model-temp-symbol'
      })
      const redrawRegionalModelTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'rdps regionalModelTempPath',
        data: graphCalc.rdpsTemps,
        x: d => xScale(d.date),
        y: d => yTempScale(d.value),
        testId: 'regional-model-temp-path'
      })
      const redrawRegionalModelRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'rdps regionalModelRHSymbol',
        data: graphCalc.rdpsRHs,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value),
        size: 5,
        symbol: d3.symbolCross
      })
      const redrawRegionalModelRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'rdps regionalModelRHPath',
        data: graphCalc.rdpsRHs,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value)
      })

      /* Draw HRDPS temp and rh lines and dots */
      const redrawHighResModelTempSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'hrdps highResModelTempSymbol',
        data: graphCalc.hrdpsTemps,
        x: d => xScale(d.date),
        y: d => yTempScale(d.value),
        size: 7,
        symbol: d3.symbolCircle,
        testId: 'high-res-model-temp-symbol'
      })
      const redrawHighResModelTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'hrdps highResModelTempPath',
        data: graphCalc.hrdpsTemps,
        x: d => xScale(d.date),
        y: d => yTempScale(d.value),
        testId: 'high-res-model-temp-path'
      })
      const redrawHighResModelRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'hrdps highResModelRHSymbol',
        data: graphCalc.hrdpsRHs,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value),
        size: 7,
        symbol: d3.symbolCircle,
        testId: 'high-res-model-rh-symbol'
      })
      const redrawHighResModelRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'hrdps highResModelRHPath',
        data: graphCalc.hrdpsRHs,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value),
        testId: 'high-res-model-rh-path'
      })

      /* Draw temp and rh hourly observation lines and dots */
      const redrawObservedTempSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'observed observedTempSymbol',
        data: graphCalc.observedTemps,
        x: d => xScale(d.date),
        y: d => yTempScale(d.value),
        symbol: d3.symbolSquare,
        size: 10,
        testId: 'hourly-observed-temp-symbol'
      })
      const redrawObservedTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'observed observedTempPath',
        data: graphCalc.observedTemps,
        x: d => xScale(d.date),
        y: d => yTempScale(d.value),
        strokeWidth: 1.5,
        testId: 'hourly-observed-temp-path'
      })
      const redrawObservedRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'observed observedRHSymbol',
        data: graphCalc.observedRHs,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value),
        symbol: d3.symbolSquare,
        size: 10,
        testId: 'hourly-observed-rh-symbol'
      })
      const redrawObservedRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'observed observedRHPath',
        data: graphCalc.observedRHs,
        x: d => xScale(d.date),
        y: d => yRHScale(d.value),
        strokeWidth: 1.5,
        testId: 'hourly-observed-rh-path'
      })

      /* Render the current time reference line */
      const scaledCurrDate = xScale(graphCalc.currDate)
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
      const xTickValues = d3Utils.getTickValues(graphCalc.xDomain, utcOffset, false)
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
        .attr('y', 0 - margin.left)
        .attr('x', 0 - chartHeight / 2)
        .attr('dy', '1.3em')
        .attr('dx', '0')
        .attr('class', 'yAxisLabel')
        .text('Temp (°C)')
        .attr('transform', 'rotate(-90)')
      context // RH label
        .append('text')
        .attr('transform', 'rotate(-270)')
        .attr('y', 0 - chartWidth - margin.left)
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
          redrawModelTempSymbols?.(d => xScale(d.date))
          redrawModelRHSymbols?.(d => xScale(d.date))
          redrawModelTempPath(d => xScale(d.date))
          redrawModelRHPath(d => xScale(d.date))
          redrawModelSummaryTempArea?.(d => xScale(d.date))
          redrawModelSummaryRHArea?.(d => xScale(d.date))
          redrawHighResModelTempSymbols?.(d => xScale(d.date))
          redrawHighResModelRHSymbols?.(d => xScale(d.date))
          redrawHighResModelTempPath(d => xScale(d.date))
          redrawHighResModelRHPath(d => xScale(d.date))
          redrawHighResModelSummaryTempArea?.(d => xScale(d.date))
          redrawHighResModelSummaryRHArea?.(d => xScale(d.date))
          redrawBiasAdjModelTempSymbols?.(d => xScale(d.date))
          redrawBiasAdjModelRHSymbols?.(d => xScale(d.date))
          redrawBiasAdjModelTempPath(d => xScale(d.date))
          redrawBiasAdjModelRHPath(d => xScale(d.date))
          redrawRegionalModelTempSymbols?.(d => xScale(d.date))
          redrawRegionalModelRHSymbols?.(d => xScale(d.date))
          redrawRegionalModelTempPath(d => xScale(d.date))
          redrawRegionalModelRHPath(d => xScale(d.date))
          redrawRegionalModelSummaryTempArea?.(d => xScale(d.date))
          redrawRegionalModelSummaryRHArea?.(d => xScale(d.date))
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
        .call(brush.move, [xScale(graphCalc.past2Date), xScale(graphCalc.future2Date)])
    }
  }, [utcOffset, graphCalc])

  // Effect hook for adding/updating tooltip
  useEffect(() => {
    const svgGraphElement = graphRef.current
    if (svgGraphElement) {
      const svg = d3.select(svgGraphElement)
      svg.select('.tooltip').remove()
      svg.select('.tooltipCursor').remove()
      svg.select('.tooltipBackground').remove()

      const weatherValues = graphCalc.weatherValues
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

      d3Utils.addTooltipListener({
        svg: svg.select('.chart'),
        xScale: graphCalc.xScale,
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
      if (svgGraphElement) {
        // clean up the event listeners
        const svg = d3.select(svgGraphElement)
        svg.on('touchmove mousemove', null)
        svg.on('touchend mouseleave', null)
      }
    }
  }, [toggleValues, graphCalc])

  // Effect hooks for showing/hiding graphics & legend
  useEffect(() => {
    if (graphRef.current) {
      const graphSvg = d3.select(graphRef.current)
      graphSvg.selectAll('.observed').classed('hidden', !toggleValues.showObservations)
      graphSvg.selectAll('.forecast').classed('hidden', !toggleValues.showForecasts)
      graphSvg.selectAll('.gdps').classed('hidden', !toggleValues.showModels)
      graphSvg.selectAll('.biasAdjGdps').classed('hidden', !toggleValues.showBiasAdjModels) // prettier-ignore
      graphSvg.selectAll('.hrdps').classed('hidden', !toggleValues.showHighResModels)
      graphSvg.selectAll('.rdps').classed('hidden', !toggleValues.showRegionalModels)
    }

    if (legendRef.current) {
      d3.select(legendRef.current)
        .selectAll('*')
        .remove()

      const legendSvg = d3
        .select(legendRef.current)
        .attr('viewBox', `0 0 ${graphWidth} ${legendHeight}`)

      const legend = legendSvg
        .append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${margin.left}, ${margin.top})`)

      const legendData = getLegendData(toggleValues)
      const newLegendHeight = d3Utils.addLegend(legend, chartWidth, legendData)
      legendSvg.attr('viewBox', `0 0 ${graphWidth} ${newLegendHeight}`)
    }
  }, [toggleValues])

  return (
    <div className={classes.root}>
      <svg data-testid="temp-rh-graph" ref={graphRef} />
      <svg data-testid="temp-rh-legend" ref={legendRef} />
    </div>
  )
}

export default React.memo(TempRHGraph)
