import { WeatherValue } from 'features/fireWeather/components/tables/SortableTableByDatetime'
import { MinMaxValues, RowIdsOfMinMaxValues } from 'utils/table'

export const dummyWeatherData: WeatherValue[] = [
  {
    datetime: '2020-12-09T20:00:00+00:00',
    temperature: 8.1,
    relative_humidity: 70,
    wind_direction: 300,
    wind_speed: 17.3,
    precipitation: 0.4,
  },
  {
    datetime: '2020-12-09T19:00:00+00:00',
    temperature: 10.5,
    relative_humidity: 53,
    wind_direction: 260,
    wind_speed: 3.7,
    precipitation: 0.8,
  },
  {
    datetime: '2020-12-09T18:00:00+00:00',
    temperature: -1.5,
    relative_humidity: 28,
    wind_direction: 330,
    wind_speed: 63.2,
    precipitation: 0.0,
  },
  {
    datetime: '2020-12-09T17:00:00+00:00',
    temperature: 2.4,
    relative_humidity: 35,
    wind_direction: 150,
    wind_speed: 4.7,
    precipitation: 16.3,
  },
  {
    datetime: '2020-12-09T16:00:00+00:00',
    temperature: -1.5,
    relative_humidity: 25,
    wind_direction: 280,
    wind_speed: 2.5,
    precipitation: 0.0,
  },
]
export const correctMinMaxValues: MinMaxValues = {
  relative_humidity: 25,
  precipitation: 16.3,
  wind_speed: 63.2,
  temperature: {
    min: -1.5,
    max: 10.5,
  },
}
export const correctMinMaxRowIds: RowIdsOfMinMaxValues = {
  relative_humidity: [4],
  precipitation: [3],
  wind: [2],
  max_temp: [1],
  min_temp: [2, 4],
}

export const dummyWeatherDataNoPrecip: WeatherValue[] = [
  {
    datetime: '2020-12-09T20:00:00+00:00',
    temperature: 8.1,
    relative_humidity: 70,
    wind_direction: 300,
    wind_speed: 17.3,
    precipitation: 0.0,
  },
  {
    datetime: '2020-12-09T19:00:00+00:00',
    temperature: 10.5,
    relative_humidity: 53,
    wind_direction: 260,
    wind_speed: 3.7,
    precipitation: 0.0,
  },
  {
    datetime: '2020-12-09T18:00:00+00:00',
    temperature: -1.5,
    relative_humidity: 28,
    wind_direction: 330,
    wind_speed: 63.2,
    precipitation: 0.0,
  },
]
export const correctMinMaxValuesNoPrecip: MinMaxValues = {
  relative_humidity: 28,
  precipitation: null,
  wind_speed: 63.2,
  temperature: {
    min: -1.5,
    max: 10.5,
  },
}
export const correctMinMaxRowIdsNoPrecip: RowIdsOfMinMaxValues = {
  relative_humidity: [2],
  precipitation: [],
  wind: [2],
  max_temp: [1],
  min_temp: [2],
}

export const dummyWeatherDataNoWind: WeatherValue[] = [
  {
    datetime: '2020-12-09T18:00:00+00:00',
    temperature: -1.5,
    relative_humidity: 28,
    wind_direction: 330,
    wind_speed: 0.0,
    precipitation: 0.0,
  },
  {
    datetime: '2020-12-09T17:00:00+00:00',
    temperature: 2.4,
    relative_humidity: 35,
    wind_direction: 150,
    wind_speed: 0.0,
    precipitation: 16.3,
  },
  {
    datetime: '2020-12-09T16:00:00+00:00',
    temperature: -1.5,
    relative_humidity: 25,
    wind_direction: 280,
    wind_speed: 0.0,
    precipitation: 0.0,
  },
]
export const correctMinMaxValuesNoWind: MinMaxValues = {
  relative_humidity: 25,
  precipitation: 16.3,
  wind_speed: null,
  temperature: {
    min: -1.5,
    max: 2.4,
  },
}
export const correctMinMaxRowIdsNoWind: RowIdsOfMinMaxValues = {
  relative_humidity: [2],
  precipitation: [1],
  wind: [],
  max_temp: [1],
  min_temp: [0, 2],
}

export const dummyWeatherDataMultiplePrecipLabels: WeatherValue[] = [
  {
    datetime: '2020-12-09T20:00:00+00:00',
    temperature: 8.1,
    relative_humidity: 70,
    wind_direction: 300,
    wind_speed: 17.3,
    precipitation: 0.4,
  },
  {
    datetime: '2020-12-09T19:00:00+00:00',
    temperature: 10.5,
    relative_humidity: 53,
    wind_direction: 260,
    wind_speed: 3.7,
    delta_precipitation: 0.8,
  },
  {
    datetime: '2020-12-09T18:00:00+00:00',
    temperature: -1.5,
    relative_humidity: 28,
    wind_direction: 330,
    wind_speed: 63.2,
    delta_precipitation: 0.0,
  },
  {
    datetime: '2020-12-09T17:00:00+00:00',
    temperature: 2.4,
    relative_humidity: 35,
    wind_direction: 150,
    wind_speed: 4.7,
    precipitation: 16.3,
  },
  {
    datetime: '2020-12-09T16:00:00+00:00',
    temperature: -1.5,
    relative_humidity: 25,
    wind_direction: 280,
    wind_speed: 2.5,
    total_precipitation: 0.0,
  },
]
export const correctMinMaxValuesMultiplePrecipLabels: MinMaxValues = {
  relative_humidity: 25,
  precipitation: 16.3,
  wind_speed: 63.2,
  temperature: {
    min: -1.5,
    max: 10.5,
  },
}

export const dummyWeatherDataNullValues: WeatherValue[] = [
  {
    datetime: '2020-12-09T20:00:00+00:00',
    temperature: 8.1,
    relative_humidity: 70,
    wind_direction: 300,
    wind_speed: null,
    precipitation: 0.4,
  },
  {
    datetime: '2020-12-09T19:00:00+00:00',
    temperature: 10.5,
    relative_humidity: 53,
    wind_direction: 260,
    wind_speed: null,
    delta_precipitation: null,
  },
  {
    datetime: '2020-12-09T18:00:00+00:00',
    temperature: -1.5,
    relative_humidity: 28,
    wind_direction: 330,
    wind_speed: null,
    delta_precipitation: 0.0,
  },
  {
    datetime: '2020-12-09T17:00:00+00:00',
    temperature: null,
    relative_humidity: 35,
    wind_direction: 150,
    wind_speed: null,
    precipitation: 16.3,
  },
  {
    datetime: '2020-12-09T16:00:00+00:00',
    temperature: -1.5,
    relative_humidity: 25,
    wind_direction: 280,
    wind_speed: null,
    total_precipitation: 0.0,
  },
]
export const correctMinMaxValuesNullValues: MinMaxValues = {
  relative_humidity: 25,
  precipitation: 16.3,
  wind_speed: null,
  temperature: {
    min: -1.5,
    max: 10.5,
  },
}
