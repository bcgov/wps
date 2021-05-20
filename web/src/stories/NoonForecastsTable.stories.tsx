import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'
import { NoonForecastValue } from 'api/forecastAPI'
import {
  forecastValues,
  pastForecastValues,
  observedValues
} from 'utils/storybook'
import NoonForecastTable from 'features/fireWeather/components/tables/NoonForecastTable'
import { GeoJsonStation } from 'api/stationAPI'

export default {
  title: 'morecast/StationComparisonTable'
} as Meta

type PropTypes = React.ComponentProps<typeof NoonForecastTable>

const Template: Story<PropTypes> = args => <NoonForecastTable {...args} />

export const ForecastTable = Template.bind({})
ForecastTable.args = {
  noonForecasts: pastForecastValues.concat(forecastValues) as NoonForecastValue[],
  noonObservations: observedValues
  }

