import moment from 'moment'
import { isNoonInPST } from 'utils/date'

const getPastValues = () => {
  const _observedValues = []
  const _pastForecastValues = []
  const _forecastSummaries = []
  const _pastModelValues = []
  const _modelSummaries = []
  const _pastHighResModelValues = []
  const _highResModelSummaries = []

  const days = 3
  const first = moment()
    .utc()
    .set({ minute: 0, second: 0 })
    .subtract(days, 'days')
  const last = moment(first).add(days - 1, 'days')

  while (last.diff(first, 'days') >= 0) {
    for (let length = 0; length < 24; length++) {
      const sineWeight = 7
      const temp = 20 + Math.sin(length) * sineWeight
      const rh = 20 - Math.sin(length) * sineWeight
      const wind_speed = 20 + Math.sin(length) * sineWeight
      const wind_direction = 20 + Math.sin(length) * sineWeight
      const barometric_pressure = 10 + Math.sin(length) * sineWeight
      const precipitation = 10 + Math.sin(length) * sineWeight
      const datetime = moment(first)
        .add(length, 'hours')
        .utc()
        .format()

      // every hour
      _observedValues.push({
        datetime,
        temperature: Math.random() <= 0.8 ? temp : null,
        relative_humidity: rh,
        wind_speed,
        wind_direction,
        barometric_pressure,
        precipitation,
        ffmc: null,
        isi: null,
        fwi: null
      })
      _pastHighResModelValues.push({
        datetime,
        temperature: temp + (Math.random() - 0.5) * 6,
        bias_adjusted_temperature: temp + (Math.random() - 0.5) * 6 - 2,
        relative_humidity: rh + (Math.random() - 0.5) * 6,
        bias_adjusted_relative_humidity: rh + (Math.random() - 0.5) * 6 - 2
      })
      _highResModelSummaries.push({
        datetime,
        tmp_tgl_2_5th: temp + 3,
        tmp_tgl_2_median: temp,
        tmp_tgl_2_90th: temp - 3,
        rh_tgl_2_5th: rh + 3,
        rh_tgl_2_median: rh,
        rh_tgl_2_90th: rh - 3
      })

      if (isNoonInPST(datetime)) {
        _pastForecastValues.push({
          datetime,
          temperature: temp + (Math.random() - 0.5) * 8,
          relative_humidity: rh + (Math.random() - 0.5) * 8
        })
        _forecastSummaries.push({
          datetime,
          tmp_min: temp - 4,
          tmp_max: temp + 4,
          rh_min: rh - 4,
          rh_max: rh + 4
        })
      }

      // every 3 hour
      if (length % 3 === 0) {
        _pastModelValues.push({
          datetime,
          temperature: temp + (Math.random() - 0.5) * 8,
          bias_adjusted_temperature: temp + (Math.random() - 0.5) * 8 - 2,
          relative_humidity: rh + (Math.random() - 0.5) * 8,
          bias_adjusted_relative_humidity: rh + (Math.random() - 0.5) * 8 - 2
        })
        _modelSummaries.push({
          datetime,
          tmp_tgl_2_5th: temp + 4,
          tmp_tgl_2_median: temp,
          tmp_tgl_2_90th: temp - 4,
          rh_tgl_2_5th: rh + 4,
          rh_tgl_2_median: rh,
          rh_tgl_2_90th: rh - 4
        })
      }
    }

    first.add(1, 'days')
  }

  return {
    observedValues: _observedValues,
    pastForecastValues: _pastForecastValues,
    forecastSummaries: _forecastSummaries,
    pastModelValues: _pastModelValues,
    modelSummaries: _modelSummaries,
    pastHighResModelValues: _pastHighResModelValues,
    highResModelSummaries: _highResModelSummaries
  }
}

const getFutureValues = () => {
  const _modelValues = []
  const _highResModelValues = []
  const _forecastValues = []

  const days = 2
  const first = moment()
    .utc()
    .set({ minute: 0, second: 0 })
  const last = moment(first).add(days, 'days')

  while (last.diff(first, 'days') >= 0) {
    for (let length = 0; length < 24; length++) {
      const sineWeight = 7
      const temp = 20 + Math.sin(length) * sineWeight
      const rh = 20 - Math.sin(length) * sineWeight
      const dew_point = 20 + Math.sin(length) * sineWeight
      const wind_speed = 20 + Math.sin(length) * sineWeight
      const wind_direction = 20 + Math.sin(length) * sineWeight
      const total_precipitation = 10 + Math.sin(length) * sineWeight
      const datetime = moment(first)
        .add(length, 'hours')
        .utc()
        .format()

      // every hour
      _highResModelValues.push({
        datetime,
        temperature: temp + (Math.random() - 0.5) * 6,
        bias_adjusted_temperature: temp + (Math.random() - 0.5) * 6 - 2,
        relative_humidity: rh + (Math.random() - 0.5) * 6,
        bias_adjusted_relative_humidity: rh + (Math.random() - 0.5) * 6 - 2
      })

      // every 3 hour and PST noon
      if (length % 3 === 0 || isNoonInPST(datetime)) {
        _modelValues.push({
          datetime,
          temperature: temp + (Math.random() - 0.5) * 8,
          bias_adjusted_temperature: temp + (Math.random() - 0.5) * 8 - 2,
          dew_point,
          relative_humidity: rh + (Math.random() - 0.5) * 8,
          bias_adjusted_relative_humidity: rh + (Math.random() - 0.5) * 8 - 5,
          wind_speed,
          wind_direction,
          total_precipitation
        })
      }

      // every PST noon
      if (isNoonInPST(datetime)) {
        _forecastValues.push({
          datetime,
          temperature: temp + (Math.random() - 0.5) * 8,
          relative_humidity: rh + (Math.random() - 0.5) * 8
        })
      }
    }

    first.add(1, 'days')
  }

  return {
    modelValues: _modelValues,
    highResModelValues: _highResModelValues,
    forecastValues: _forecastValues
  }
}

export const { forecastValues, modelValues, highResModelValues } = getFutureValues()

export const {
  observedValues,
  pastForecastValues,
  forecastSummaries,
  pastModelValues,
  modelSummaries,
  pastHighResModelValues,
  highResModelSummaries
} = getPastValues()
