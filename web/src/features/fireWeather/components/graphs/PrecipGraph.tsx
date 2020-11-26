import React, { useRef, useEffect, useMemo } from 'react'
import * as d3 from 'd3'
import { makeStyles } from '@material-ui/core/styles'
import moment from 'moment'

import { ObservedValue } from 'api/observationAPI'
import * as d3Utils from 'utils/d3'
import { formatDateInPDT } from 'utils/date'
import { NoonForecastValue } from 'api/forecastAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import { PDT_UTC_OFFSET } from 'utils/constants'

const observedPrecipColor = '#a50b41'
const forecastPrecipColor = '#fb0058'

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

      '&__cursor': {
        strokeWidth: 1,
        stroke: 'gray',
        strokeDasharray: '1,1',
        opacity: 0
      },

      '&--hidden': {
        display: 'none'
      }
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

      '&--hidden': {
        visibility: 'hidden'
      }
    }
  }
})

interface PrecipValue {
  date: Date
  observedPrecip?: number
  forecastPrecip?: number
}

interface Props {
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
  forecastValues: NoonForecastValue[]
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
  forecastValues
}: Props) => {
  const classes = useStyles()
  const svgRef = useRef<SVGSVGElement>(null)
  const utcOffset = PDT_UTC_OFFSET

  // useMemo will only recompute the memoized value when one of the dependencies has changed.
  // This optimization helps to avoid expensive calculations on every render.
  const { xDomain, xTickValues, observedPrecips, forecastPrecips } = useMemo(() => {
    const datesFromAllSources: Date[] = []

    const aggreObservedPrecips: { [k: string]: number } = {}
    observedValues.forEach(({ datetime, precipitation: precip }) => {
      const date = formatDateInPDT(datetime, 'YYYY-MM-DD')
      if (!aggreObservedPrecips[date]) {
        aggreObservedPrecips[date] = Number(precip)
      } else {
        aggreObservedPrecips[date] = aggreObservedPrecips[date] + Number(precip)
      }
    })

    const _observedPrecips = Object.entries(aggreObservedPrecips).map(
      ([formattedDate, totalPrecip]) => {
        const date = moment(formattedDate)
          .utc()
          .set({ hour: Math.abs(utcOffset), minute: 0 })
          .toDate()
        datesFromAllSources.push(date)

        return {
          date,
          value: Number(totalPrecip.toFixed(2))
        }
      }
    )

    const _forecastPrecips = forecastValues.map(({ datetime, total_precipitation }) => {
      const date = moment(datetime)
        .utc()
        .set({ hour: Math.abs(utcOffset) })
        .toDate()
      datesFromAllSources.push(date)

      return {
        date,
        value: Number(total_precipitation.toFixed(2))
      }
    })

    const currDate = new Date()
    const pastDate = moment(currDate)
      .subtract(5, 'days')
      .toDate()
    const [minDate, maxDate] = d3.extent(datesFromAllSources)
    let d1 = minDate || pastDate
    let d2 = maxDate || currDate
    d1 = moment(d1)
      .subtract(6, 'hours')
      .toDate()
    d2 = moment(d2)
      .add(6, 'hours')
      .toDate()
    const _xDomain: [Date, Date] = [d1, d2]

    return {
      xDomain: _xDomain,
      xTickValues: d3Utils.getTickValues(_xDomain, utcOffset, false),
      observedPrecips: _observedPrecips,
      forecastPrecips: _forecastPrecips
    }
  }, [utcOffset, observedValues, forecastValues])

  // Effect hook for displaying graphics
  useEffect(() => {
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
      const legend = svg
        .append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(${margin.left}, ${legendMarginTop})`)

      /* Create scales for x and y axes */
      const xScale = d3
        .scaleTime()
        .domain(xDomain)
        .range([0, chartWidth])
      const xScaleOriginal = xScale.copy()
      const yScale = d3
        .scaleLinear()
        .domain([0, 100])
        .range([chartHeight, 0])

      observedPrecips.forEach(precip =>
        d3Utils.drawVerticalLine({
          svg: chart,
          className: 'precipLine__observed',
          xScale: xScaleOriginal,
          x: xScale(precip.date) - 2,
          y1: yScale(precip.value),
          y2: yScale(0),
          testId: 'observed-precip-line'
        })
      )

      forecastPrecips.forEach(precip =>
        d3Utils.drawVerticalLine({
          svg: chart,
          className: 'precipLine__forecast',
          xScale: xScaleOriginal,
          x: xScale(precip.date) + 2,
          y1: yScale(precip.value),
          y2: yScale(0),
          testId: 'forecast-precip-line'
        })
      )

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
        .call(d3.axisLeft(yScale).ticks(5))
      context // Temperature label
        .append('text')
        .attr('y', 0 - margin.left)
        .attr('x', 0 - chartHeight / 2)
        .attr('dy', '1.3em')
        .attr('dx', '0')
        .attr('class', 'yAxisLabel')
        .text('Precipitation (mm/cm)')
        .attr('transform', 'rotate(-90)')

      /* Render legends */
      // TODO: We're going to have to look at using layouts moving forward to achieve the placement of objects. https://www.d3indepth.com/layouts/
      const legendY = 0
      let legendX = 0
      d3Utils.addLegend({
        svg: legend,
        text: 'Observed Precip',
        color: observedPrecipColor,
        shape: 'rect',
        shapeX: legendX - 2,
        shapeY: legendY - 4,
        textX: legendX += 10,
        textY: legendY + 3.5
      })
      d3Utils.addLegend({
        svg: legend,
        text: 'Forecast Precip',
        color: forecastPrecipColor,
        shape: 'rect',
        shapeX: legendX += 85,
        shapeY: legendY - 4,
        textX: legendX += 12,
        textY: legendY + 3.5
      })
    }
  }, [xDomain, xTickValues, observedPrecips, forecastPrecips])

  const precipsOfInterest = useMemo(() => {
    const precipsByDatetime: { [date: string]: PrecipValue } = {}

    toggleValues.showObservations &&
      observedPrecips.forEach(({ date, value }) => {
        precipsByDatetime[date.toISOString()] = { date, observedPrecip: value }
      })

    toggleValues.showForecasts &&
      forecastPrecips.forEach(({ date, value }) => {
        precipsByDatetime[date.toISOString()] = {
          ...precipsByDatetime[date.toISOString()],
          date,
          forecastPrecip: value
        }
      })

    return Object.values(precipsByDatetime)
  }, [toggleValues, observedPrecips, forecastPrecips])

  // Effect hook for adding/updating tooltip
  useEffect(() => {
    const svgElement = svgRef.current
    if (svgElement) {
      const svg = d3.select(svgElement)
      svg.select('.tooltip').remove()
      svg.select('.tooltip__cursor').remove()
      svg.select('.tooltip__background').remove()

      const xScale = d3
        .scaleTime()
        .domain(xDomain)
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
                case 'forecastPrecip':
                  return {
                    text: `Forecast Precip: ${value} (mm/cm)`,
                    color: forecastPrecipColor
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
  }, [xDomain, precipsOfInterest])

  // Effect hooks for showing/hiding graphics
  const { showObservations, showForecasts } = toggleValues
  useEffect(() => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current)
      svg
        .selectAll('.precipLine__observed')
        .classed('precipLine--hidden', !showObservations)
    }
  }, [showObservations])
  useEffect(() => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current)
      svg.selectAll('.precipLine__forecast').classed('precipLine--hidden', !showForecasts)
    }
  }, [showForecasts])

  return (
    <div className={classes.root}>
      <svg data-testid="precip-graph" ref={svgRef} />
    </div>
  )
}

export default React.memo(PrecipGraph)
