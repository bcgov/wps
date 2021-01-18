/* eslint-disable @typescript-eslint/ban-ts-comment */
import React from 'react'
import Plot from 'react-plotly.js'
import moment from 'moment'

import { ObservedValue } from 'api/observationAPI'
import { ModelValue } from 'api/modelAPI'
import { NoonForecastValue } from 'api/forecastAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'

interface PrecipValues {
  datetime: string
  precipitation?: number | null
  delta_precipitation?: number | null
  total_precipitation?: number | null
}

const populateGraphData = (values: PrecipValues[]) => {
  const dates: Date[] = []
  const dailyPrecips: number[] = []
  let maxDailyPrecip = 0

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

      if (totalPrecip > maxDailyPrecip) {
        maxDailyPrecip = totalPrecip
      }
    })
  } else {
    values.forEach(({ datetime, total_precipitation }) => {
      if (total_precipitation !== undefined) {
        const midNightOfTheDay = moment(datetime)
          .set({ hour: 0 })
          .toDate()
        dates.push(midNightOfTheDay)
        const totalPrecip = Number(total_precipitation)
        dailyPrecips.push(totalPrecip)

        if (totalPrecip > maxDailyPrecip) {
          maxDailyPrecip = totalPrecip
        }
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

  return { dates, maxDailyPrecip, dailyPrecips, accumPrecips }
}

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

export interface Props {
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
  const {
    showObservations,
    showForecasts,
    showModels,
    showRegionalModels,
    showHighResModels
  } = toggleValues

  const observed = populateGraphData(observedValues)
  const forecast = populateGraphData(forecastValues)
  const hrdps = populateGraphData(hrdpsModelValues)
  const gdps = populateGraphData(gdpsModelValues)
  const rdps = populateGraphData(rdpsModelValues)

  const maxY = Math.max(
    observed.maxDailyPrecip,
    forecast.maxDailyPrecip,
    hrdps.maxDailyPrecip,
    gdps.maxDailyPrecip,
    rdps.maxDailyPrecip
  )

  return (
    <Plot
      style={{ width: '100%', height: '100%' }}
      onUpdate={e => {
        const updatedRange = e.layout.xaxis?.range as [string, string] | undefined
        if (updatedRange) {
          setSliderRange(updatedRange)
        }
      }}
      config={{ responsive: true }}
      data={[
        {
          x: observed.dates,
          y: observed.dailyPrecips,
          name: 'Observed',
          type: 'bar',
          showlegend: showObservations,
          marker: {
            color: showObservations ? observedPrecipColor : 'transparent'
          },
          hoverinfo: showObservations ? 'y' : 'skip',
          hovertemplate: showObservations
            ? 'Observation: %{y:.2f} (mm/cm)<extra></extra>'
            : undefined
        },
        {
          x: observed.dates,
          y: observed.accumPrecips,
          name: 'Accumulated Observed',
          mode: 'lines',
          yaxis: 'y2',
          showlegend: showObservations,
          marker: {
            color: showObservations ? accumObservedPrecipColor : 'transparent'
          },
          hoverinfo: showObservations ? 'y' : 'skip',
          hovertemplate: showObservations
            ? 'Accumulated Observation: %{y:.2f} (mm/cm)<extra></extra>'
            : undefined
        },
        {
          x: forecast.dates,
          y: forecast.dailyPrecips,
          name: 'Forecast',
          type: 'bar',
          showlegend: showForecasts,
          marker: {
            color: showForecasts ? forecastPrecipColor : 'transparent'
          },
          hoverinfo: showForecasts ? 'y' : 'skip',
          hovertemplate: showForecasts
            ? 'Forecast: %{y:.2f} (mm/cm)<extra></extra>'
            : undefined
        },
        {
          x: forecast.dates,
          y: forecast.accumPrecips,
          name: 'Accumulated Forecast',
          mode: 'lines',
          yaxis: 'y2',
          showlegend: showForecasts,
          marker: {
            color: showForecasts ? accumForecastPrecipColor : 'transparent'
          },
          hoverinfo: showForecasts ? 'y' : 'skip',
          hovertemplate: showForecasts
            ? 'Accumulated Forecast: %{y:.2f} (mm/cm)<extra></extra>'
            : undefined
        },
        {
          x: hrdps.dates,
          y: hrdps.dailyPrecips,
          name: 'HRDPS',
          type: 'bar',
          showlegend: showHighResModels,
          marker: {
            color: showHighResModels ? hrdpsPrecipColor : 'transparent'
          },
          hoverinfo: showHighResModels ? 'y' : 'skip',
          hovertemplate: showHighResModels
            ? 'HRDPS: %{y:.2f} (mm/cm)<extra></extra>'
            : undefined
        },
        {
          x: hrdps.dates,
          y: hrdps.accumPrecips,
          name: 'Accumulated HRDPS',
          mode: 'lines',
          yaxis: 'y2',
          showlegend: showHighResModels,
          marker: {
            color: showHighResModels ? accumHRDPSPrecipColor : 'transparent'
          },
          hoverinfo: showHighResModels ? 'y' : 'skip',
          hovertemplate: showHighResModels
            ? 'Accumulated HRDPS: %{y:.2f} (mm/cm)<extra></extra>'
            : undefined
        },
        {
          x: rdps.dates,
          y: rdps.dailyPrecips,
          name: 'RDPS',
          type: 'bar',
          showlegend: showRegionalModels,
          marker: {
            color: showRegionalModels ? rdpsPrecipColor : 'transparent'
          },
          hoverinfo: showRegionalModels ? 'y' : 'skip',
          hovertemplate: showRegionalModels
            ? 'RDPS: %{y:.2f} (mm/cm)<extra></extra>'
            : undefined
        },
        {
          x: rdps.dates,
          y: rdps.accumPrecips,
          name: 'Accumulated RDPS',
          mode: 'lines',
          yaxis: 'y2',
          showlegend: showRegionalModels,
          marker: {
            color: showRegionalModels ? accumRDPSPrecipColor : 'transparent'
          },
          hoverinfo: showRegionalModels ? 'y' : 'skip',
          hovertemplate: showRegionalModels
            ? 'Accumulated RDPS: %{y:.2f} (mm/cm)<extra></extra>'
            : undefined
        },
        {
          x: gdps.dates,
          y: gdps.dailyPrecips,
          name: 'GDPS',
          type: 'bar',
          showlegend: showModels,
          marker: {
            color: showModels ? gdpsPrecipColor : 'transparent'
          },
          hoverinfo: showModels ? 'y' : 'skip',
          hovertemplate: showModels ? 'GDPS: %{y:.2f} (mm/cm)<extra></extra>' : undefined
        },
        {
          x: gdps.dates,
          y: gdps.accumPrecips,
          name: 'Accumulated GDPS',
          mode: 'lines',
          yaxis: 'y2',
          showlegend: showModels,
          marker: {
            color: showModels ? accumGDPSPrecipColor : 'transparent'
          },
          hoverinfo: showModels ? 'y' : 'skip',
          hovertemplate: showModels
            ? 'Accumulated GDPS: %{y:.2f} (mm/cm)<extra></extra>'
            : undefined
        },
        {
          x: [currDate],
          y: [maxY + 0.6],
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
          text: 'Daily Precipitation graph (with accumulated)',
          yanchor: 'middle'
        },
        height: 600,
        margin: { pad: 10 },
        xaxis: {
          range: sliderRange,
          // rangeslider: {
          //   visible: true,
          //   bgcolor: '#dbdbdb',
          //   thickness: 0.1
          // },
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
          y: -0.15 // -0.45
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
