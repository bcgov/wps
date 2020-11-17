import React, { useRef, useEffect } from 'react'
import * as d3 from 'd3'

import { ObservedValue } from 'api/observationAPI'
import { ModelSummary as _ModelSummary, ModelValue } from 'api/modelAPI'
import { ForecastSummary as _ForecastSummary, NoonForecastValue } from 'api/forecastAPI'
import { formatDateInPDT } from 'utils/date'
import * as styles from 'features/fireWeather/components/graphs/TempRHGraph.styles'
import * as d3Utils from 'utils/d3'

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

interface Props {
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

const TempRHGraph: React.FunctionComponent<Props> = ({
  observedValues: _observedValues,
  modelValues: _modelValues,
  modelSummaries: _modelSummaries,
  forecastValues: _forecastValues,
  forecastSummaries: _forecastSummaries,
  biasAdjModelValues: _biasAdjModelValues,
  highResModelValues: _highResModelValues,
  highResModelSummaries: _highResModelSummaries,
  regionalModelValues: _regionalModelValues,
  regionalModelSummaries: _regionalModelSummaries
}: Props) => {
  const classes = styles.useStyles()
  const svgRef = useRef(null)

  // Keep track of the sidebar position & size so that the sidebar can stay
  // exactly as it is when toggling weather sources
  // Use mutable ref object that doesn't cause re-render
  const brushSelection = useRef<[number, number] | null>(null)

  useEffect(() => {
    if (svgRef.current) {
      /* Clear previous graphics before rendering new ones */
      d3.select(svgRef.current)
        .selectAll('*')
        .remove()

      /* Prepare for data */
      const daysLookup: { [k: string]: Date } = {} // will help to create the date label on x axis
      const datesFromAllSources: Date[] = [] // will be used to determine x axis range
      const weatherValuesByDatetime: { [k: string]: WeatherValue } = {}

      const observedTempValues: { date: Date; temp: number }[] = []
      const observedRHValues: { date: Date; rh: number }[] = []
      _observedValues.forEach(v => {
        if (v.temperature == null && v.relative_humidity == null) {
          return
        }

        const date = d3Utils.storeDaysLookup(daysLookup, v.datetime)
        datesFromAllSources.push(date)

        const observation = { date, temp: NaN, rh: NaN }
        if (v.temperature != null) {
          observation.temp = Number(v.temperature.toFixed(2))
          observedTempValues.push(observation)
        }
        if (v.relative_humidity != null) {
          observation.rh = Math.round(v.relative_humidity)
          observedRHValues.push(observation)
        }
        weatherValuesByDatetime[v.datetime] = observation
      })

      const forecastValues = _forecastValues.map(d => {
        const date = d3Utils.storeDaysLookup(daysLookup, d.datetime)
        datesFromAllSources.push(date)

        const forecast = {
          date,
          forecastTemp: Number(d.temperature.toFixed(2)),
          forecastRH: Math.round(d.relative_humidity)
        }
        // combine with existing observed and models values
        weatherValuesByDatetime[d.datetime] = {
          ...weatherValuesByDatetime[d.datetime],
          ...forecast
        }

        return forecast
      })

      const forecastSummaries: ForecastSummary[] = _forecastSummaries.map(d => {
        const date = d3Utils.storeDaysLookup(daysLookup, d.datetime)
        datesFromAllSources.push(date)

        return { ...d, date }
      })

      // GDPS
      const modelTempValues: { date: Date; modelTemp: number }[] = []
      const modelRHValues: { date: Date; modelRH: number }[] = []
      _modelValues.forEach(v => {
        const { temperature: temp, relative_humidity: rh } = v

        if (temp == null && rh == null) {
          return
        }

        const date = d3Utils.storeDaysLookup(daysLookup, v.datetime)
        datesFromAllSources.push(date)

        const model = {
          date,
          modelTemp: NaN,
          modelRH: NaN
        }
        if (temp != null) {
          model.modelTemp = Number(temp.toFixed(2))
          modelTempValues.push(model)
        }
        if (rh != null) {
          model.modelRH = Math.round(rh)
          modelRHValues.push(model)
        }
        // combine with the existing weather values
        weatherValuesByDatetime[v.datetime] = {
          ...weatherValuesByDatetime[v.datetime],
          ...model
        }
      })

      const modelSummaries: ModelSummary[] = _modelSummaries.map(d => {
        const date = d3Utils.storeDaysLookup(daysLookup, d.datetime)
        datesFromAllSources.push(date)

        return { ...d, date }
      })

      // Bias Adjusted GDPS
      const biasAdjModelTempValues: { date: Date; biasAdjModelTemp: number }[] = []
      const biasAdjModelRHValues: { date: Date; biasAdjModelRH: number }[] = []
      _biasAdjModelValues.forEach(v => {
        const {
          bias_adjusted_temperature: biasAdjTemp,
          bias_adjusted_relative_humidity: biasAdjRH
        } = v
        if (biasAdjTemp == null && biasAdjRH == null) {
          return
        }

        const date = d3Utils.storeDaysLookup(daysLookup, v.datetime)
        datesFromAllSources.push(date)

        const biasAdjModel = {
          date,
          biasAdjModelTemp: NaN,
          biasAdjModelRH: NaN
        }
        if (biasAdjTemp != null) {
          biasAdjModel.biasAdjModelTemp = Number(biasAdjTemp.toFixed(2))
          biasAdjModelTempValues.push(biasAdjModel)
        }
        if (biasAdjRH != null) {
          biasAdjModel.biasAdjModelRH = Math.round(biasAdjRH)
          biasAdjModelRHValues.push(biasAdjModel)
        }
        weatherValuesByDatetime[v.datetime] = {
          ...weatherValuesByDatetime[v.datetime],
          ...biasAdjModel
        }
      })

      // HRDPS
      const hrModelTempValues: { date: Date; hrModelTemp: number }[] = []
      const hrModelRHValues: { date: Date; hrModelRH: number }[] = []
      _highResModelValues.forEach(v => {
        if (v.temperature == null && v.relative_humidity == null) {
          return
        }

        const date = d3Utils.storeDaysLookup(daysLookup, v.datetime)
        datesFromAllSources.push(date)

        const hrModel = { date, hrModelTemp: NaN, hrModelRH: NaN }
        if (v.temperature != null) {
          hrModel.hrModelTemp = Number(v.temperature.toFixed(2))
          hrModelTempValues.push(hrModel)
        }
        if (v.relative_humidity != null) {
          hrModel.hrModelRH = Math.round(v.relative_humidity)
          hrModelRHValues.push(hrModel)
        }
        weatherValuesByDatetime[v.datetime] = {
          ...weatherValuesByDatetime[v.datetime],
          ...hrModel
        }
      })
      const highResModelSummaries: ModelSummary[] = _highResModelSummaries.map(d => {
        const date = d3Utils.storeDaysLookup(daysLookup, d.datetime)
        datesFromAllSources.push(date)

        return { ...d, date }
      })

      // RDPS
      const regModelTempValues: { date: Date; regModelTemp: number }[] = []
      const regModelRHValues: { date: Date; regModelRH: number }[] = []
      _regionalModelValues.forEach(v => {
        if (v.temperature == null && v.relative_humidity == null) {
          return
        }

        const date = d3Utils.storeDaysLookup(daysLookup, v.datetime)
        datesFromAllSources.push(date)

        const regModel = { date, regModelTemp: NaN, regModelRH: NaN }
        if (v.temperature != null) {
          regModel.regModelTemp = Number(v.temperature.toFixed(2))
          regModelTempValues.push(regModel)
        }
        if (v.relative_humidity != null) {
          regModel.regModelRH = Math.round(v.relative_humidity)
          regModelRHValues.push(regModel)
        }
        weatherValuesByDatetime[v.datetime] = {
          ...weatherValuesByDatetime[v.datetime],
          ...regModel
        }
      })
      const regionalModelSummaries: ModelSummary[] = _regionalModelSummaries.map(d => {
        const date = d3Utils.storeDaysLookup(daysLookup, d.datetime)
        datesFromAllSources.push(date)

        return { ...d, date }
      })

      // weather values without percentile summaries
      const weatherValues = Object.values(weatherValuesByDatetime).sort(
        (a, b) => a.date.valueOf() - b.date.valueOf()
      )
      const xDomain = d3.extent(datesFromAllSources) as [Date, Date]
      const xTickValues = Object.values(daysLookup)
        .sort((a, b) => a.valueOf() - b.valueOf()) // Sort in ascending order
        .map((day, idx) => {
          if (idx === 0) {
            // Return the first day as it is
            return day
          }
          // Return the rest with 0h 0m 0s set
          return new Date(day.setHours(0, 0, 0))
        })

      /* Set dimensions and svg groups */
      const margin = { top: 10, right: 40, bottom: 200, left: 40 }
      const svgWidth = 600
      const svgHeight = 400
      const chartWidth = svgWidth - margin.left - margin.right
      const chartHeight = svgHeight - margin.top - margin.bottom
      const svg = d3
        .select(svgRef.current)
        // Make it responsive: https://medium.com/@louisemoxy/a-simple-way-to-make-d3-js-charts-svgs-responsive-7afb04bc2e4b
        .attr('viewBox', `0 0 ${svgWidth} ${svgHeight}`)

      // Set up a clipper that removes graphics that don't fall within the boundary
      svg
        .append('defs')
        .append('clipPath')
        .attr('id', 'clip')
        .append('rect')
        .attr('x', -1) // -1 to give some tiny window to show stuff that's hidden on the left
        .attr('y', -10) // - 10 to show the text(Now) from the reference line
        .attr('width', chartWidth + 2) // + 2 to show the last tick of the x axis
        .attr('height', svgHeight) // Use svgHeight to show the x axis and its labels
      const chart = svg
        .append('g')
        .attr('class', 'chart')
        .attr('transform', `translate(${margin.left}, ${margin.top})`)
        .attr('clip-path', 'url(#clip)')

      const context = svg // svg group for Y axis and its labels
        .append('g')
        .attr('class', 'context')
        .attr('transform', `translate(${margin.left}, ${margin.top})`)

      const sidebarHeight = 20
      const sidebarMarginTop = chartHeight + sidebarHeight + 30
      const sidebar = svg
        .append('g')
        .attr('class', 'sidebar')
        .attr('transform', `translate(${margin.left}, ${sidebarMarginTop})`)

      const legendMarginTop = sidebarMarginTop + 70
      const legend = svg
        .append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${margin.left}, ${legendMarginTop})`)

      /* Create scales for x and y axes */
      const xScale = d3
        .scaleTime()
        .domain(xDomain)
        .range([0, chartWidth])
      const xSidebarScale = xScale.copy()
      const yTempScale = d3
        .scaleLinear()
        .domain([-10, 40])
        .range([chartHeight, 0])
      const yRHScale = d3
        .scaleLinear()
        .domain([0, 100])
        .range([chartHeight, 0])

      /* Render temp and rh model summary clouds */
      const updateModelSummaryTempArea = d3Utils.drawArea({
        svg: chart,
        className: 'modelSummaryTempArea',
        datum: modelSummaries,
        x: d => xScale(d.date),
        y0: d => yTempScale(d.tmp_tgl_2_90th),
        y1: d => yTempScale(d.tmp_tgl_2_5th),
        testId: 'model-summary-temp-area'
      })
      const updateModelSummaryRHArea = d3Utils.drawArea({
        svg: chart,
        className: 'modelSummaryRHArea',
        datum: modelSummaries,
        x: d => xScale(d.date),
        y0: d => yRHScale(d.rh_tgl_2_90th),
        y1: d => yRHScale(d.rh_tgl_2_5th)
      })

      /* Render high resolution model temp and rh summary clouds */
      const updateHighResModelSummaryTempArea = d3Utils.drawArea({
        svg: chart,
        className: 'highResModelSummaryTempArea',
        datum: highResModelSummaries,
        x: d => xScale(d.date),
        y0: d => yTempScale(d.tmp_tgl_2_90th),
        y1: d => yTempScale(d.tmp_tgl_2_5th),
        testId: 'high-res-model-summary-temp-area'
      })
      const updateHighResModelSummaryRHArea = d3Utils.drawArea({
        svg: chart,
        className: 'highResModelSummaryRHArea',
        datum: highResModelSummaries,
        x: d => xScale(d.date),
        y0: d => yRHScale(d.rh_tgl_2_90th),
        y1: d => yRHScale(d.rh_tgl_2_5th)
      })

      /* Render regional model temp and rh summary clouds */
      const updateRegionalModelSummaryTempArea = d3Utils.drawArea({
        svg: chart,
        className: 'regionalModelSummaryTempArea',
        datum: regionalModelSummaries,
        x: d => xScale(d.date),
        y0: d => yTempScale(d.tmp_tgl_2_90th),
        y1: d => yTempScale(d.tmp_tgl_2_5th),
        testId: 'regional-model-summary-temp-area'
      })
      const updateRegionalModelSummaryRHArea = d3Utils.drawArea({
        svg: chart,
        className: 'regionalModelSummaryRHArea',
        datum: regionalModelSummaries,
        x: d => xScale(d.date),
        y0: d => yRHScale(d.rh_tgl_2_90th),
        y1: d => yRHScale(d.rh_tgl_2_5th)
      })

      // Past forecasts temp min & max vertical lines
      const updateForecastSummaryTempLines = forecastSummaries.map(forecast =>
        d3Utils.drawVerticalLine({
          svg: chart,
          className: 'forecastSummaryTempLine',
          xScale: xScale.copy(),
          x: xScale(forecast.date),
          y1: yTempScale(forecast.tmp_min),
          y2: yTempScale(forecast.tmp_max),
          testId: 'forecast-summary-temp-line'
        })
      )
      // Past forecasts rh min & max vertical lines
      const updateForecastSummaryRHLines = forecastSummaries.map(forecast =>
        d3Utils.drawVerticalLine({
          svg: chart,
          className: 'forecastSummaryRHLine',
          xScale: xScale.copy(),
          x: xScale(forecast.date),
          y1: yRHScale(forecast.rh_min),
          y2: yRHScale(forecast.rh_max)
        })
      )

      /* Render temp and rh models */
      const updateModelTempSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'modelTempSymbol',
        data: modelTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.modelTemp),
        size: 10,
        symbol: d3.symbolTriangle,
        testId: 'model-temp-symbol'
      })
      const updateModelTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'modelTempPath',
        data: modelTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.modelTemp),
        testId: 'model-temp-path'
      })
      const updateModelRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'modelRHSymbol',
        data: modelRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.modelRH),
        size: 10,
        symbol: d3.symbolTriangle,
        testId: 'model-rh-symbol'
      })
      const updateModelRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'modelRHPath',
        data: modelRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.modelRH),
        testId: 'model-rh-path'
      })

      /* Render bias adjusted model temp and rh values */
      const updateBiasAdjModelTempSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'biasAdjModelTempSymbol',
        data: biasAdjModelTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.biasAdjModelTemp),
        size: 5,
        symbol: d3.symbolDiamond,
        testId: 'bias-adjusted-model-temp-symbol'
      })
      const updateBiasAdjModelTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'biasAdjModelTempPath',
        data: biasAdjModelTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.biasAdjModelTemp),
        testId: 'bias-adjusted-model-temp-path'
      })
      const updateBiasAdjModelRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'biasAdjModelRHSymbol',
        data: biasAdjModelRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.biasAdjModelRH),
        size: 5,
        symbol: d3.symbolDiamond,
        testId: 'bias-adjusted-model-rh-symbol'
      })
      const updateBiasAdjModelRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'biasAdjModelRHPath',
        data: biasAdjModelRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.biasAdjModelRH),
        testId: 'bias-adjusted-model-rh-path'
      })

      /* Render high resolution model temp and rh values */
      const updateHighResModelTempSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'highResModelTempSymbol',
        data: hrModelTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.hrModelTemp),
        size: 7,
        symbol: d3.symbolCircle,
        testId: 'high-res-model-temp-symbol'
      })
      const updateHighResModelTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'highResModelTempPath',
        data: hrModelTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.hrModelTemp),
        testId: 'high-res-model-temp-path'
      })
      const updateHighResModelRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'highResModelRHSymbol',
        data: hrModelRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.hrModelRH),
        size: 7,
        symbol: d3.symbolCircle,
        testId: 'high-res-model-rh-symbol'
      })
      const updateHighResModelRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'highResModelRHPath',
        data: hrModelRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.hrModelRH),
        testId: 'high-res-model-rh-path'
      })

      /* Render regional model temp and rh values */
      const updateRegionalModelTempSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'regionalModelTempSymbol',
        data: regModelTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.regModelTemp),
        size: 5,
        symbol: d3.symbolCross,
        testId: 'regional-model-temp-symbol'
      })
      const updateRegionalModelTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'regionalModelTempPath',
        data: regModelTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.regModelTemp),
        testId: 'regional-model-temp-path'
      })
      const updateRegionalModelRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'regionalModelRHSymbol',
        data: regModelRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.regModelRH),
        size: 5,
        symbol: d3.symbolCross,
        testId: 'regional-model-rh-symbol'
      })
      const updateRegionalModelRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'regionalModelRHPath',
        data: regModelRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.regModelRH),
        testId: 'regional-model-rh-path'
      })

      /* Render temp and rh noon forecasts */
      const updateForecastTempDots = d3Utils.drawDots({
        svg: chart,
        className: 'forecastTempDot',
        data: forecastValues,
        cx: d => xScale(d.date),
        cy: d => yTempScale(d.forecastTemp),
        testId: 'forecast-temp-dot'
      })
      const updateForecastRHDots = d3Utils.drawDots({
        svg: chart,
        className: 'forecastRHDot',
        data: forecastValues,
        cx: d => xScale(d.date),
        cy: d => yRHScale(d.forecastRH)
      })

      /* Render temp and rh hourly observations */
      const updateObservedTempSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'observedTempSymbol',
        data: observedTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.temp),
        symbol: d3.symbolSquare,
        size: 10,
        testId: 'hourly-observed-temp-symbol'
      })
      const updateObservedTempPath = d3Utils.drawPath({
        svg: chart,
        className: 'observedTempPath',
        data: observedTempValues,
        x: d => xScale(d.date),
        y: d => yTempScale(d.temp),
        strokeWidth: 1.5,
        testId: 'hourly-observed-temp-path'
      })
      const updateObservedRHSymbols = d3Utils.drawSymbols({
        svg: chart,
        className: 'observedRHSymbol',
        data: observedRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.rh),
        symbol: d3.symbolSquare,
        size: 10,
        testId: 'hourly-observed-rh-symbol'
      })
      const updateObservedRHPath = d3Utils.drawPath({
        svg: chart,
        className: 'observedRHPath',
        data: observedRHValues,
        x: d => xScale(d.date),
        y: d => yRHScale(d.rh),
        strokeWidth: 1.5,
        testId: 'hourly-observed-rh-path'
      })

      /* Render the current time reference line */
      const scaledCurrDate = xScale(new Date())
      const updateCurrLine = d3Utils.drawVerticalLine({
        svg: chart,
        className: 'currLine',
        xScale: xScale.copy(),
        x: scaledCurrDate,
        y1: 0,
        y2: chartHeight
      })
      const updateCurrLineText = d3Utils.drawText({
        svg: chart,
        className: 'currLabel',
        xScale: xScale.copy(),
        x: scaledCurrDate,
        y: -12,
        dx: '-1em',
        dy: '1em',
        text: 'Now'
      })

      /* Render the X & Y axis and labels */
      const xAxisFunc = d3
        .axisBottom(xScale)
        .tickFormat(d3Utils.formatDateInMonthAndDay)
        .tickValues(xTickValues)
      chart // Include only x axis to the chart group
        .append('g')
        .attr('class', 'xAxis')
        .attr('transform', `translate(0, ${chartHeight})`)
        .call(xAxisFunc)
        .selectAll('text')
        .attr('class', 'xAxisLabel')
        .attr('y', 0)
        .attr('x', 0)
        .attr('dy', '-0.1em')
        .attr('dx', '0.8em')
        .attr('transform', 'rotate(45)')
      context // Y temp axis
        .append('g')
        .call(d3.axisLeft(yTempScale).tickValues([-10, 0, 10, 20, 30, 40]))
      context // Y rh axis
        .append('g')
        .attr('transform', `translate(${chartWidth}, 0)`)
        .call(d3.axisRight(yRHScale).tickValues([0, 25, 50, 75, 100]))

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
      // When the sidebar is moved or resized
      const brushed = () => {
        const selection = d3.event.selection as [number, number]
        if (selection) {
          brushSelection.current = selection
          // Update x scale with a new domain modified by the sidebar
          xScale.domain(selection.map(xSidebarScale.invert, xSidebarScale))

          // Update chart's x axis with the new scale
          chart.select<SVGGElement>('.xAxis').call(xAxisFunc)

          // Redraw all the displayed graphics
          updateObservedTempSymbols?.(d => xScale(d.date))
          updateObservedRHSymbols?.(d => xScale(d.date))
          updateObservedTempPath(d => xScale(d.date))
          updateObservedRHPath(d => xScale(d.date))
          updateForecastTempDots?.(d => xScale(d.date))
          updateForecastRHDots?.(d => xScale(d.date))
          updateForecastSummaryTempLines.forEach(update => update(xScale))
          updateForecastSummaryRHLines.forEach(update => update(xScale))
          updateModelTempSymbols?.(d => xScale(d.date))
          updateModelRHSymbols?.(d => xScale(d.date))
          updateModelTempPath(d => xScale(d.date))
          updateModelRHPath(d => xScale(d.date))
          updateModelSummaryTempArea?.(d => xScale(d.date))
          updateModelSummaryRHArea?.(d => xScale(d.date))
          updateHighResModelTempSymbols?.(d => xScale(d.date))
          updateHighResModelRHSymbols?.(d => xScale(d.date))
          updateHighResModelTempPath(d => xScale(d.date))
          updateHighResModelRHPath(d => xScale(d.date))
          updateHighResModelSummaryTempArea?.(d => xScale(d.date))
          updateHighResModelSummaryRHArea?.(d => xScale(d.date))
          updateBiasAdjModelTempSymbols?.(d => xScale(d.date))
          updateBiasAdjModelRHSymbols?.(d => xScale(d.date))
          updateBiasAdjModelTempPath(d => xScale(d.date))
          updateBiasAdjModelRHPath(d => xScale(d.date))
          updateRegionalModelTempSymbols?.(d => xScale(d.date))
          updateRegionalModelRHSymbols?.(d => xScale(d.date))
          updateRegionalModelTempPath(d => xScale(d.date))
          updateRegionalModelRHPath(d => xScale(d.date))
          updateRegionalModelSummaryTempArea?.(d => xScale(d.date))
          updateRegionalModelSummaryRHArea?.(d => xScale(d.date))
          updateCurrLine(xScale)
          updateCurrLineText(xScale)
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
            .axisBottom(xSidebarScale)
            .tickFormat(d3Utils.formatDateInMonthAndDay)
            .tickValues(xTickValues)
        )
        .selectAll('text')
        .attr('class', 'xAxisLabel')
        .attr('y', 0)
        .attr('x', 0)
        .attr('dy', '1em')
        .attr('dx', '0.8em')
        .attr('transform', 'rotate(45)')
      sidebar
        .append('g')
        .call(brush)
        .call(brush.move, brushSelection.current || xSidebarScale.range().map(x => x / 4))

      /* Render legends */
      // TODO: We're going to have to look at using layouts moving forward to achieve the placement of objects. https://www.d3indepth.com/layouts/
      let legendY = 0
      let legendX = 0
      d3Utils.addLegend({
        svg: legend,
        text: 'Observed Temp',
        color: styles.observedTempColor,
        shape: 'rect',
        shapeX: legendX - 2,
        shapeY: legendY - 4,
        textX: legendX += 10,
        textY: legendY + 4
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'Observed RH',
        color: styles.observedRHColor,
        shape: 'rect',
        shapeX: legendX += 80,
        shapeY: legendY - 4,
        textX: legendX += 12,
        textY: legendY + 4
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'Forecast Temp',
        color: styles.forecastTempDotColor,
        fill: 'none',
        shapeX: legendX += 73,
        shapeY: legendY,
        textX: legendX += 7,
        textY: legendY + 3
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'Forecast RH',
        color: styles.forecastRHDotColor,
        fill: 'none',
        shapeX: legendX += 80,
        shapeY: legendY,
        textX: legendX += 7,
        textY: legendY + 3
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'GDPS Temp',
        shape: 'triangle',
        color: styles.modelTempColor,
        fill: styles.modelTempColor,
        shapeX: legendX += 70,
        shapeY: legendY,
        textX: legendX += 7,
        textY: legendY + 3
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'GDPS RH',
        shape: 'triangle',
        color: styles.modelRHColor,
        fill: styles.modelRHColor,
        shapeX: legendX += 70,
        shapeY: legendY,
        textX: legendX + 7,
        textY: legendY + 3
      })
      // New line
      legendX = 0
      legendY += 16
      d3Utils.addLegend({
        svg: legend,
        shape: 'rect',
        text: 'GDPS Temp 5th - 90th percentiles',
        color: styles.modelSummaryTempAreaColor,
        shapeX: legendX - 2,
        shapeY: legendY - 4,
        textX: legendX += 11,
        textY: legendY + 3
      })
      d3Utils.addLegend({
        svg: legend,
        shape: 'rect',
        text: 'GDPS RH 5th - 90th percentiles',
        color: styles.modelSummaryRHAreaColor,
        shapeX: legendX += 165,
        shapeY: legendY - 4,
        textX: legendX + 13,
        textY: legendY + 3
      })
      // New line
      legendX = 0
      legendY += 16
      d3Utils.addLegend({
        svg: legend,
        text: 'Bias Adjusted GDPS Temp',
        shape: 'diamond',
        color: styles.biasModelTempColor,
        fill: styles.biasModelTempColor,
        shapeX: legendX,
        shapeY: legendY,
        textX: legendX += 7,
        textY: legendY + 3,
        radius: 0.5
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'Bias Adjusted GDPS RH',
        shape: 'diamond',
        color: styles.biasModelRHColor,
        fill: styles.biasModelRHColor,
        shapeX: legendX += 130,
        shapeY: legendY,
        textX: legendX + 7,
        textY: legendY + 3,
        radius: 0.5
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'HRDPS Temp',
        color: styles.highResModelTempColor,
        fill: styles.highResModelTempColor,
        shapeX: legendX += 127,
        shapeY: legendY,
        textX: legendX += 7,
        textY: legendY + 3
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'HRDPS RH',
        color: styles.highResModelRHColor,
        fill: styles.highResModelRHColor,
        shapeX: legendX += 81,
        shapeY: legendY,
        textX: legendX + 7,
        textY: legendY + 3
      })
      // new line
      legendX = 0
      legendY += 16
      d3Utils.addLegend({
        svg: legend,
        text: 'HRDPS Temp 5th - 90th percentiles',
        shape: 'rect',
        color: styles.highResModelSummaryTempAreaColor,
        fill: styles.highResModelSummaryTempAreaColor,
        shapeX: legendX - 2,
        shapeY: legendY - 4,
        textX: legendX += 10,
        textY: legendY + 4
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'HRDPS RH 5th - 90th percentiles',
        shape: 'rect',
        color: styles.highResModelSummaryRHAreaColor,
        fill: styles.highResModelSummaryRHAreaColor,
        shapeX: legendX += 165,
        shapeY: legendY - 4,
        textX: legendX + 13,
        textY: legendY + 3
      })
      // New line
      legendX = 0
      legendY += 16
      d3Utils.addLegend({
        svg: legend,
        text: 'RDPS Temp',
        color: styles.regionalModelTempColor,
        fill: styles.regionalModelTempColor,
        shape: 'cross',
        shapeX: legendX,
        shapeY: legendY,
        textX: legendX += 6,
        textY: legendY + 4
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'RDPS RH',
        color: styles.regionalModelRHColor,
        fill: styles.regionalModelRHColor,
        shape: 'cross',
        shapeX: legendX += 81,
        shapeY: legendY,
        textX: legendX += 6,
        textY: legendY + 4
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'RDPS Temp 5th - 90th percentiles',
        shape: 'rect',
        color: styles.regionalModelSummaryTempAreaColor,
        fill: styles.regionalModelSummaryTempAreaColor,
        shapeX: legendX += 82,
        shapeY: legendY - 4,
        textX: legendX += 13,
        textY: legendY + 4
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'RDPS RH 5th - 90th percentiles',
        shape: 'rect',
        color: styles.regionalModelSummaryRHAreaColor,
        fill: styles.regionalModelSummaryRHAreaColor,
        shapeX: legendX += 160,
        shapeY: legendY - 4,
        textX: legendX + 13,
        textY: legendY + 4
      })
      /* Attach tooltip listener */
      d3Utils.addTooltipListener({
        svg: chart,
        xScale,
        width: chartWidth,
        height: chartHeight,
        data: weatherValues,
        textTestId: 'temp-rh-tooltip-text',
        bgdTestId: 'temp-rh-graph-background',
        getInnerText: ([k, value]) => {
          const key = k as keyof WeatherValue
          if (key === 'date' && value instanceof Date) {
            return `${formatDateInPDT(value, 'h:mm a, ddd, MMM Do')} (PDT, UTC-7)`
          } else if (typeof value === 'number') {
            let weatherValue: number | string = value
            if (isNaN(weatherValue)) {
              weatherValue = '-'
            }

            switch (key) {
              case 'temp':
                return `Observed Temp: ${weatherValue} (°C)`
              case 'forecastTemp':
                return `Forecast Temp: ${weatherValue} (°C)`
              case 'modelTemp':
                return `GDPS Temp: ${weatherValue} (°C)`
              case 'biasAdjModelTemp':
                return `Bias adjusted GDPS Temp: ${weatherValue} (°C)`
              case 'hrModelTemp':
                return `HRDPS Temp ${weatherValue} (°C)`
              case 'regModelTemp':
                return `RDPS Temp ${weatherValue} (°C)`

              case 'rh':
                return `Observed RH: ${weatherValue} (%)`
              case 'forecastRH':
                return `Forecast RH: ${weatherValue} (%)`
              case 'modelRH':
                return `GDPS RH: ${weatherValue} (%)`
              case 'biasAdjModelRH':
                return `Bias adjusted GDPS RH: ${weatherValue} (%)`
              case 'hrModelRH':
                return `HRDPS RH ${weatherValue} (%)`
              case 'regModelRH':
                return `RDPS RH ${weatherValue} (%)`

              default:
                return ''
            }
          }
          return ''
        }
      })
    }
  }, [
    classes.root,
    _observedValues,
    _modelValues,
    _modelSummaries,
    _forecastValues,
    _forecastSummaries,
    _highResModelValues,
    _biasAdjModelValues,
    _highResModelSummaries,
    _regionalModelValues,
    _regionalModelSummaries
  ])

  return (
    <div className={classes.root}>
      <svg data-testid="temp-rh-graph" ref={svgRef} />
    </div>
  )
}

export default React.memo(TempRHGraph)
