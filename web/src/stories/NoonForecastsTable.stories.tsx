import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'
import { NoonForecastValue } from 'api/forecastAPI'
import {
  forecastValues,
  pastForecastValues,
  observedValues,
  station322
} from 'utils/storybook'
import NoonForecastTable from 'features/fireWeather/components/tables/NoonForecastTable'
import { GeoJsonStation } from 'api/stationAPI'

export default {
  title: 'morecast/StationComparisonTable'
} as Meta

type PropTypes = React.ComponentProps<typeof NoonForecastTable>

const Template: Story<PropTypes> = args => <NoonForecastTable {...args} />

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

export const ForecastTable = Template.bind({})
ForecastTable.args = {
  noonForecasts: pastForecastValues.concat(forecastValues) as NoonForecastValue[],
  noonObservations: observedValues
  }

