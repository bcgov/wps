// @ts-nocheck
import React from 'react'
import { storiesOf } from '@storybook/react'
import moment from 'moment'

import WxDataGraph from 'features/fireWeather/components/WxDataGraph'

const getModelValues = () => {
  const modelValues = []
  const days = 3
  const first = moment()
    .utc()
    .set({ hour: 0, minute: 0, second: 0 })
  const last = moment(first).add(days, 'days')
  const hourInterval = 3

  while (last.diff(first, 'days') >= 0) {
    for (let length = 0; length < 24 / hourInterval; length++) {
      modelValues.push({
        datetime: moment(first)
          .add(hourInterval * length, 'hours')
          .utc()
          .format(),
        temperature: Math.random() * 25,
        dew_point: Math.random() * 10,
        relative_humidity: Math.random() * 101,
        wind_speed: Math.random() * 10,
        wind_direction: Math.random() * 100,
        total_precipitation: Math.random()
      })
    }

    first.add(1, 'days')
  }

  return modelValues
}

const getReadingValues = () => {
  const readingValues = []
  const days = 2
  const first = moment()
    .utc()
    .set({ hour: 0, minute: 0, second: 0 })
    .subtract(days, 'days')
  const last = moment(first).add(days, 'days')

  while (last.diff(first, 'days') >= 0) {
    for (let length = 0; length < 24; length++) {
      readingValues.push({
        datetime: moment(first)
          .add(length, 'hours')
          .utc()
          .format(),
        temperature: Math.random() * 30,
        dew_point: Math.random() * 10,
        relative_humidity: Math.random() * 101,
        wind_speed: Math.random() * 10,
        wind_direction: Math.random() * 100,
        total_precipitation: Math.random(),
        ffmc: null,
        isi: null,
        fwi: null
      })
    }

    first.add(1, 'days')
  }

  return readingValues
}

storiesOf('WxDataGraph', module)
  .add('default', () => (
    <WxDataGraph modelValues={getModelValues()} readingValues={getReadingValues()} />
  ))
  .add('only model', () => (
    <WxDataGraph modelValues={getModelValues()} readingValues={[]} />
  ))
