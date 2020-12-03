import { useMemo } from 'react'
import * as d3 from 'd3'
import moment from 'moment'

import { Props } from 'features/fireWeather/components/graphs/TempRHGraph'

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
 * A custom hook to process the weather data and memoize the output,
 * the output being used to draw graphics in the temp & rh graph.
 */
export const useGraphCalculation = ({
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
}: Props) => {
  return useMemo(() => {
    const datesFromAllSources: Date[] = []
    const weatherValuesByDatetime: { [k: string]: WeatherValue } = {}
    let maxTemp = 40, minTemp = -10 // prettier-ignore

    const observedTempValues: { date: Date; value: number }[] = []
    const observedRHValues: { date: Date; value: number }[] = []
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
        observedTempValues.push({ date, value: temp })
        if (temp > maxTemp) {
          maxTemp = temp
        } else if (temp < minTemp) {
          minTemp = temp
        }
      }
      if (v.relative_humidity != null) {
        const rh = Math.round(v.relative_humidity)
        weatherValue.observedRH = rh
        observedRHValues.push({ date, value: rh })
      }

      weatherValuesByDatetime[v.datetime] = weatherValue
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

      if (rest.tmp_max > maxTemp) {
        maxTemp = rest.tmp_max
      }
      if (rest.tmp_min < minTemp) {
        minTemp = rest.tmp_min
      }

      return { date, ...rest }
    })

    const gdpsTempValues: { date: Date; value: number }[] = []
    const gdpsRHValues: { date: Date; value: number }[] = []
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
        gdpsTempValues.push({ date, value: temp })
        if (temp > maxTemp) {
          maxTemp = temp
        } else if (temp < minTemp) {
          minTemp = temp
        }
      }
      if (v.relative_humidity != null) {
        const rh = Math.round(v.relative_humidity)
        weatherValue.gdpsRH = rh
        gdpsRHValues.push({ date, value: rh })
      }

      weatherValuesByDatetime[v.datetime] = {
        ...weatherValuesByDatetime[v.datetime],
        ...weatherValue
      }
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

    return {
      xDomain,
      maxTemp: Math.ceil(maxTemp / 5) * 5, // nearest 5
      minTemp: Math.floor(minTemp / 5) * 5, // nearest -5
      currDate,
      past2Date,
      future2Date,
      weatherValues,
      observedTempValues,
      observedRHValues,
      forecastTempRHValues,
      forecastTempRHSummaries,
      gdpsTempValues,
      gdpsRHValues
    }
  }, [
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
  ])
}
