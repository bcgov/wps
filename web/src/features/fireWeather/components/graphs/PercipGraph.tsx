/* eslint-disable @typescript-eslint/ban-ts-comment */
import React from 'react'
import Plot from 'react-plotly.js'
import { Data } from 'plotly.js'
import moment from 'moment'

import { ObservedValue } from 'api/observationAPI'
import { ModelValue } from 'api/modelAPI'
import { NoonForecastValue } from 'api/forecastAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'

interface PrecipValue {
  datetime: string
  precipitation?: number | null
  delta_precipitation?: number | null
  total_precipitation?: number | null
}

const getDailyAndAccumPrecips = (values: PrecipValue[]) => {
  const dates: Date[] = []
  const dailyPrecips: number[] = []
  const shouldAggregate =
    values.length > 0 &&
    (values[0].precipitation !== undefined || values[0].delta_precipitation !== undefined)

  // if the type of the value is observation or one of weather models, then aggregate hourly data to daily
  if (shouldAggregate) {
    const aggregatedPrecips: { [k: string]: number } = {}
    values.forEach(({ datetime, precipitation, delta_precipitation }) => {
      const date = moment(datetime).format('YYYY-MM-DD')
      const precip = Number(precipitation) || Number(delta_precipitation)

      if (!aggregatedPrecips[date]) {
        aggregatedPrecips[date] = precip
      } else {
        aggregatedPrecips[date] = aggregatedPrecips[date] + precip
      }
    })

    Object.entries(aggregatedPrecips).forEach(([formattedDate, totalPrecip]) => {
      const midNightOfTheDay = moment(formattedDate)
        .set({ hour: 0 })
        .toDate()
      dates.push(midNightOfTheDay)
      dailyPrecips.push(totalPrecip)
    })
  } else {
    values.forEach(({ datetime, total_precipitation }) => {
      if (total_precipitation !== undefined) {
        const midNightOfTheDay = moment(datetime)
          .set({ hour: 0 })
          .toDate()
        dates.push(midNightOfTheDay)
        dailyPrecips.push(Number(total_precipitation))
      }
    })
  }

  // Create a list of accumulated precips for each day in time
  const accumPrecips: number[] = []
  dailyPrecips.forEach((daily, idx) => {
    if (idx === 0) {
      return accumPrecips.push(daily)
    }

    const prevAccum = accumPrecips[accumPrecips.length - 1]
    accumPrecips.push(prevAccum + daily)
  })

  return { dates, dailyPrecips, accumPrecips }
}

const populateGraphData = (
  values: PrecipValue[],
  name: string,
  color: string,
  show: boolean
) => {
  const { dates, dailyPrecips, accumPrecips } = getDailyAndAccumPrecips(values)

  const dailyPrecipsBar: Data = {
    x: dates,
    y: dailyPrecips,
    name,
    type: 'bar',
    showlegend: show,
    marker: {
      color: show ? color : 'transparent'
    },
    hoverinfo: show ? 'y' : 'skip',
    hovertemplate: show ? `${name}: %{y:.2f} (mm/cm)<extra></extra>` : undefined
  }

  const accumPrecipsline: Data = {
    x: dates,
    y: accumPrecips,
    name: `Accumulated ${name}`,
    mode: 'lines',
    yaxis: 'y2',
    showlegend: show,
    marker: {
      color: show ? color : 'transparent'
    },
    hoverinfo: show ? 'y' : 'skip',
    hovertemplate: show
      ? `Accumulated ${name}: %{y:.2f} (mm/cm)<extra></extra>`
      : undefined
  }

  return {
    dailyPrecipsBar,
    accumPrecipsline,
    maxDailyPrecip: Math.max(...dailyPrecips)
  }
}

const observedPrecipColor = '#a50b41'
const forecastPrecipColor = '#fb0058'
const gdpsPrecipColor = '#32e7e7'
const hrdpsPrecipColor = '#a017c2'
const rdpsPrecipColor = '#026200'

interface Props {
  currDate: Date
  sliderRange: [string, string]
  setSliderRange: (range: [string, string]) => void
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
  forecastValues: NoonForecastValue[]
  hrdpsModelValues: ModelValue[]
  rdpsModelValues: ModelValue[]
  gdpsModelValues: ModelValue[]
}

const PrecipGraph = (props: Props) => {
  const {
    currDate,
    sliderRange,
    setSliderRange,
    toggleValues,
    observedValues,
    forecastValues,
    gdpsModelValues,
    rdpsModelValues,
    hrdpsModelValues
  } = props

  const observation = populateGraphData(
    observedValues,
    'Observation',
    observedPrecipColor,
    toggleValues.showObservations
  )
  const forecast = populateGraphData(
    forecastValues,
    'Forecast',
    forecastPrecipColor,
    toggleValues.showForecasts
  )
  const hrdps = populateGraphData(
    hrdpsModelValues,
    'HRDPS',
    hrdpsPrecipColor,
    toggleValues.showHighResModels
  )
  const gdps = populateGraphData(
    gdpsModelValues,
    'GDPS',
    gdpsPrecipColor,
    toggleValues.showModels
  )
  const rdps = populateGraphData(
    rdpsModelValues,
    'RDPS',
    rdpsPrecipColor,
    toggleValues.showRegionalModels
  )

  const maxY = Math.max(
    observation.maxDailyPrecip,
    forecast.maxDailyPrecip,
    hrdps.maxDailyPrecip,
    gdps.maxDailyPrecip,
    rdps.maxDailyPrecip
  )

  return (
    <Plot
      style={{ width: '100%', height: '100%' }}
      config={{ responsive: true }}
      onUpdate={e => {
        const updatedRange = e.layout.xaxis?.range as [string, string] | undefined
        if (updatedRange) {
          setSliderRange(updatedRange)
        }
      }}
      data={[
        observation.dailyPrecipsBar,
        observation.accumPrecipsline,
        forecast.dailyPrecipsBar,
        forecast.accumPrecipsline,
        hrdps.dailyPrecipsBar,
        hrdps.accumPrecipsline,
        gdps.dailyPrecipsBar,
        gdps.accumPrecipsline,
        rdps.dailyPrecipsBar,
        rdps.accumPrecipsline,
        {
          x: [currDate],
          y: [maxY * 1.02],
          mode: 'text',
          text: ['Now'],
          showlegend: false,
          hoverinfo: 'skip',
          textfont: { color: 'green', size: 15 },
          // a workaround to remove this from the slider: https://github.com/plotly/plotly.js/issues/2010#issuecomment-637697204
          xaxis: 'x2' // This moves trace to alternative xaxis(x2) which does not have a slider
        }
      ]}
      layout={{
        dragmode: 'pan',
        autosize: true,
        title: {
          text: 'Daily Precipitation (with accumulated)',
          yanchor: 'middle'
        },
        height: 600,
        margin: { pad: 10 },
        xaxis: {
          range: sliderRange,
          rangeslider: {
            visible: true,
            bgcolor: '#dbdbdb',
            thickness: 0.1
          },
          hoverformat: '%a, %b %e', // https://github.com/d3/d3-3.x-api-reference/blob/master/Time-Formatting.md#format
          tickfont: { size: 14 },
          type: 'date',
          dtick: 86400000.0 // Set the interval between ticks to one day: https://plotly.com/javascript/reference/#scatter-marker-colorbar-dtick
        },
        xaxis2: {
          type: 'date',
          showticklabels: false,
          // @ts-expect-error
          matches: 'x', // Important for slider to work properly for all traces
          overlaying: 'x' // Important for hover to work properly for all traces
        },
        yaxis: {
          title: 'Daily Precipitation (mm/cm)',
          tickfont: { size: 14 },
          fixedrange: true
        },
        yaxis2: {
          title: 'Accumulated Precipitation (mm/cm)',
          tickfont: { size: 14 },
          overlaying: 'y',
          side: 'right',
          gridcolor: 'transparent'
        },
        legend: {
          orientation: 'h',
          y: -0.45
        },
        barmode: 'group',
        bargap: 0.75,
        bargroupgap: 0.3,
        shapes: [
          {
            type: 'line',
            x0: currDate,
            y0: 0,
            x1: currDate,
            y1: maxY,
            line: {
              color: 'green',
              width: 1.5,
              dash: 'dot'
            },
            xref: 'x2',
            layer: 'below'
          }
        ]
      }}
    />
  )
}

export default React.memo(PrecipGraph)
