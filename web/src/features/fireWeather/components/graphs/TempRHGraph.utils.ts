import { useMemo } from 'react'
import * as d3 from 'd3'
import moment from 'moment'

import { Props } from 'features/fireWeather/components/graphs/TempRHGraph'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import { Legend } from 'utils/d3'
import * as styles from 'features/fireWeather/components/graphs/TempRHGraph.styles'

export interface WeatherValue {
  date: Date
  observedTemp?: number
  observedRH?: number
  gdpsTemp?: number
  gdpsRH?: number
  forecastTemp?: number
  forecastRH?: number
  biasAdjGdpsTemp?: number
  biasAdjGdpsRH?: number
  hrdpsTemp?: number
  hrdpsRH?: number
  rdpsTemp?: number
  rdpsRH?: number
}

/**
 * A custom hook to process the weather data and memoize the output
 * which will be used to draw graphics on the graph.
 */
export const useMemoGraphCalculation = (props: Props, chartWidth: number) => {
  const {
    observedValues,
    gdpsValues,
    gdpsSummaries,
    forecastValues,
    forecastSummaries,
    biasAdjGdpsValues,
    hrdpsValues,
    hrdpsSummaries,
    rdpsValues,
    rdpsSummaries
  } = props

  return useMemo(
    () => {
      const datesFromAllSources: Date[] = []
      const weatherValuesByDatetime: { [k: string]: WeatherValue } = {}
      const allTemps: number[] = [40, -10]

      const observedTemps: { date: Date; value: number }[] = []
      const observedRHs: { date: Date; value: number }[] = []
      observedValues.forEach(v => {
        if (v.temperature == null && v.relative_humidity == null) {
          return
        }

        const date = new Date(v.datetime)
        datesFromAllSources.push(date)

        const weatherValue: WeatherValue = { date, observedTemp: NaN, observedRH: NaN }
        if (v.temperature != null) {
          const temp = Number(v.temperature.toFixed(2))
          weatherValue.observedTemp = temp
          observedTemps.push({ date, value: temp })
          allTemps.push(temp)
        }
        if (v.relative_humidity != null) {
          const rh = Math.round(v.relative_humidity)
          weatherValue.observedRH = rh
          observedRHs.push({ date, value: rh })
        }

        weatherValuesByDatetime[v.datetime] = weatherValue
      })

      const forecastTempRHs = forecastValues.map(v => {
        const date = new Date(v.datetime)
        datesFromAllSources.push(date)

        const temp = Number(v.temperature.toFixed(2))
        const rh = Math.round(v.relative_humidity)

        allTemps.push(temp)

        const weatherValue: WeatherValue = { date, forecastTemp: temp, forecastRH: rh }
        weatherValuesByDatetime[v.datetime] = {
          ...weatherValuesByDatetime[v.datetime],
          ...weatherValue
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

        allTemps.push(rest.tmp_min, rest.tmp_max)

        return { date, ...rest }
      })

      const gdpsTemps: { date: Date; value: number }[] = []
      const gdpsRHs: { date: Date; value: number }[] = []
      gdpsValues.forEach(v => {
        if (v.temperature == null && v.relative_humidity == null) {
          return
        }

        const date = new Date(v.datetime)
        datesFromAllSources.push(date)

        const weatherValue: WeatherValue = { date, gdpsTemp: NaN, gdpsRH: NaN }
        if (v.temperature != null) {
          const temp = Number(v.temperature.toFixed(2))
          weatherValue.gdpsTemp = temp
          gdpsTemps.push({ date, value: temp })
          allTemps.push(temp)
        }
        if (v.relative_humidity != null) {
          const rh = Math.round(v.relative_humidity)
          weatherValue.gdpsRH = rh
          gdpsRHs.push({ date, value: rh })
        }

        weatherValuesByDatetime[v.datetime] = {
          ...weatherValuesByDatetime[v.datetime],
          ...weatherValue
        }
      })

      const gdpsTempRHSummaries = gdpsSummaries.map(summary => {
        const { datetime, ...rest } = summary

        const date = new Date(datetime)
        datesFromAllSources.push(date)

        allTemps.push(rest.tmp_tgl_2_5th, rest.tmp_tgl_2_90th)

        return { date, ...rest }
      })

      const biasAdjGdpsTemps: { date: Date; value: number }[] = []
      const biasAdjGdpsRHs: { date: Date; value: number }[] = []
      biasAdjGdpsValues.forEach(v => {
        if (
          v.bias_adjusted_temperature == null &&
          v.bias_adjusted_relative_humidity == null
        ) {
          return
        }

        const date = new Date(v.datetime)
        datesFromAllSources.push(date)

        const weatherValue: WeatherValue = { date, biasAdjGdpsTemp: NaN, biasAdjGdpsRH: NaN } // prettier-ignore
        if (v.bias_adjusted_temperature != null) {
          const temp = Number(v.bias_adjusted_temperature.toFixed(2))
          weatherValue.biasAdjGdpsTemp = temp
          biasAdjGdpsTemps.push({ date, value: temp })
          allTemps.push(temp)
        }
        if (v.bias_adjusted_relative_humidity != null) {
          const rh = Math.round(v.bias_adjusted_relative_humidity)
          weatherValue.biasAdjGdpsRH = rh
          biasAdjGdpsRHs.push({ date, value: rh })
        }

        weatherValuesByDatetime[v.datetime] = {
          ...weatherValuesByDatetime[v.datetime],
          ...weatherValue
        }
      })

      const hrdpsTemps: { date: Date; value: number }[] = []
      const hrdpsRHs: { date: Date; value: number }[] = []
      hrdpsValues.forEach(v => {
        if (v.temperature == null && v.relative_humidity == null) {
          return
        }

        const date = new Date(v.datetime)
        datesFromAllSources.push(date)

        const weatherValue: WeatherValue = { date, hrdpsTemp: NaN, hrdpsRH: NaN }
        if (v.temperature != null) {
          const temp = Number(v.temperature.toFixed(2))
          weatherValue.hrdpsTemp = temp
          hrdpsTemps.push({ date, value: temp })
          allTemps.push(temp)
        }
        if (v.relative_humidity != null) {
          const rh = Math.round(v.relative_humidity)
          weatherValue.hrdpsRH = rh
          hrdpsRHs.push({ date, value: rh })
        }

        weatherValuesByDatetime[v.datetime] = {
          ...weatherValuesByDatetime[v.datetime],
          ...weatherValue
        }
      })

      const hrdpsTempRHSummaries = hrdpsSummaries.map(summary => {
        const { datetime, ...rest } = summary

        const date = new Date(datetime)
        datesFromAllSources.push(date)

        allTemps.push(rest.tmp_tgl_2_5th, rest.tmp_tgl_2_90th)

        return { date, ...rest }
      })

      const rdpsTemps: { date: Date; value: number }[] = []
      const rdpsRHs: { date: Date; value: number }[] = []
      rdpsValues.forEach(v => {
        if (v.temperature == null && v.relative_humidity == null) {
          return
        }

        const date = new Date(v.datetime)
        datesFromAllSources.push(date)

        const weatherValue: WeatherValue = { date, rdpsTemp: NaN, rdpsRH: NaN }
        if (v.temperature != null) {
          const temp = Number(v.temperature.toFixed(2))
          weatherValue.rdpsTemp = temp
          rdpsTemps.push({ date, value: temp })
          allTemps.push(temp)
        }
        if (v.relative_humidity != null) {
          const rh = Math.round(v.relative_humidity)
          weatherValue.rdpsRH = rh
          rdpsRHs.push({ date, value: rh })
        }

        weatherValuesByDatetime[v.datetime] = {
          ...weatherValuesByDatetime[v.datetime],
          ...weatherValue
        }
      })

      const rdpsTempRHSummaries = rdpsSummaries.map(summary => {
        const { datetime, ...rest } = summary

        const date = new Date(datetime)
        datesFromAllSources.push(date)

        allTemps.push(rest.tmp_tgl_2_5th, rest.tmp_tgl_2_90th)

        return { date, ...rest }
      })

      const weatherValues = Object.values(weatherValuesByDatetime).sort(
        (a, b) => a.date.valueOf() - b.date.valueOf()
      )

      const currDate = new Date()
      const past2Date = moment(currDate).subtract(2, 'days').toDate() // prettier-ignore
      const future2Date = moment(currDate).add(2, 'days').toDate() // prettier-ignore
      const [minDate, maxDate] = d3.extent(datesFromAllSources)
      let d1 = past2Date
      if (minDate && minDate < past2Date) {
        d1 = minDate
      }
      let d2 = future2Date
      if (maxDate && maxDate > future2Date) {
        d2 = maxDate
      }
      d1 = moment(d1).subtract(1, 'hours').toDate() // prettier-ignore
      d2 = moment(d2).add(1, 'hours').toDate() // prettier-ignore
      const xDomain: [Date, Date] = [d1, d2]
      const xScale = d3
        .scaleTime()
        .domain(xDomain)
        .range([0, chartWidth])

      const maxTemp = Math.ceil((d3.max(allTemps) as number) / 5) * 5 // nearest 5
      const minTemp = Math.floor((d3.min(allTemps) as number) / 5) * 5 // nearest -5
      const tempDomain = [minTemp, maxTemp]

      return {
        tempDomain,
        xDomain,
        xScale,
        currDate,
        past2Date,
        future2Date,
        weatherValues,
        observedTemps,
        observedRHs,
        forecastTempRHs,
        forecastTempRHSummaries,
        gdpsTemps,
        gdpsRHs,
        gdpsTempRHSummaries,
        biasAdjGdpsTemps,
        biasAdjGdpsRHs,
        hrdpsTemps,
        hrdpsRHs,
        hrdpsTempRHSummaries,
        rdpsTemps,
        rdpsRHs,
        rdpsTempRHSummaries
      }
    },
    [] // eslint-disable-line react-hooks/exhaustive-deps
  )
}

export const getLegendData = (toggleValues: ToggleValues) => {
  const legendData: Legend[] = []

  if (toggleValues.showObservations) {
    legendData.push(
      {
        text: 'Observed Temp',
        color: styles.observedTempColor,
        shape: 'rect'
      },
      {
        text: 'Observed RH',
        color: styles.observedRHColor,
        shape: 'rect'
      }
    )
  }

  if (toggleValues.showForecasts) {
    legendData.push(
      {
        text: 'Forecast Temp',
        color: styles.forecastTempDotColor,
        shape: 'circle',
        fill: 'none'
      },
      {
        text: 'Forecast RH',
        color: styles.forecastRHDotColor,
        shape: 'circle',
        fill: 'none'
      }
    )
  }

  if (toggleValues.showHighResModels) {
    legendData.push(
      {
        text: 'HRDPS Temp',
        color: styles.highResModelTempColor,
        shape: 'circle'
      },
      {
        text: 'HRDPS RH',
        color: styles.highResModelRHColor,
        shape: 'circle'
      },
      {
        text: 'HRDPS Temp 5th - 90th percentiles',
        color: styles.highResModelSummaryTempAreaColor,
        shape: 'rect'
      },
      {
        text: 'HRDPS RH 5th - 90th percentiles',
        color: styles.highResModelSummaryRHAreaColor,
        shape: 'rect'
      }
    )
  }

  if (toggleValues.showRegionalModels) {
    legendData.push(
      {
        text: 'RDPS Temp',
        color: styles.regionalModelTempColor,
        shape: 'cross'
      },
      {
        text: 'RDPS RH',
        color: styles.regionalModelRHColor,
        shape: 'cross'
      },
      {
        text: 'RDPS Temp 5th - 90th percentiles',
        color: styles.regionalModelSummaryTempAreaColor,
        shape: 'rect'
      },
      {
        text: 'RDPS RH 5th - 90th percentiles',
        color: styles.regionalModelSummaryRHAreaColor,
        shape: 'rect'
      }
    )
  }

  if (toggleValues.showModels) {
    legendData.push(
      {
        text: 'GDPS Temp',
        color: styles.modelTempColor,
        shape: 'triangle'
      },
      {
        text: 'GDPS RH',
        color: styles.modelRHColor,
        shape: 'triangle'
      },
      {
        text: 'GDPS Temp 5th - 90th percentiles',
        color: styles.modelSummaryTempAreaColor,
        shape: 'rect'
      },
      {
        text: 'GDPS RH 5th - 90th percentiles',
        color: styles.modelSummaryRHAreaColor,
        shape: 'rect'
      }
    )
  }

  if (toggleValues.showBiasAdjModels) {
    legendData.push(
      {
        text: 'Bias Adjusted GDPS Temp',
        color: styles.biasModelTempColor,
        shape: 'diamond'
      },
      {
        text: 'Bias Adjusted GDPS RH',
        color: styles.biasModelRHColor,
        shape: 'diamond'
      }
    )
  }

  return legendData
}
