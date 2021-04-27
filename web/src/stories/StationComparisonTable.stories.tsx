import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'
import { NoonForecastValue } from 'api/forecastAPI'
import {
  forecastValues,
  pastForecastValues,
  modelValues,
  pastModelValues,
  regionalModelValues,
  pastRegionalModelValues,
  highResModelValues,
  pastHighResModelValues,
  observedValues,
  station322
} from 'utils/storybook'
import StationComparisonTable from 'features/fireWeather/components/tables/StationComparisonTable'
import { GeoJsonStation } from 'api/stationAPI'

export default {
  title: 'morecast/StationComparisonTable'
} as Meta

type PropTypes = React.ComponentProps<typeof StationComparisonTable>

const Template: Story<PropTypes> = args => <StationComparisonTable {...args} />

const station838: GeoJsonStation = {
  type: 'Feature',
  properties: {
    code: 838,
    name: 'AKOKLI CREEK',
    ecodivision_name: 'HUMID CONTINENTAL HIGHLANDS',
    core_season: {
      start_month: 5,
      start_day: 15,
      end_month: 8,
      end_day: 31
    }
  },
  geometry: {
    type: 'Point',
    coordinates: [-116.7464, 49.4358]
  }
}

export const ComparisonTable = Template.bind({})
ComparisonTable.args = {
  timeOfInterest: '2021-04-26T13:51:00-08:00',
  stationCodes: [322, 828],
  stationsByCode: { 322: station322, 828: station838 },
  allNoonForecastsByStation: {
    322: pastForecastValues.concat(forecastValues) as NoonForecastValue[],
    828: pastForecastValues.concat(forecastValues) as NoonForecastValue[]
  },
  observationsByStation: { 322: observedValues, 828: observedValues },
  allHighResModelsByStation: {
    322: highResModelValues.concat(pastHighResModelValues),
    828: highResModelValues.concat(pastHighResModelValues)
  },
  allRegionalModelsByStation: {
    322: pastRegionalModelValues.concat(regionalModelValues),
    828: pastRegionalModelValues.concat(regionalModelValues)
  },
  noonModelsByStation: {
    322: pastModelValues.concat(modelValues),
    828: pastModelValues.concat(modelValues)
  }
}
