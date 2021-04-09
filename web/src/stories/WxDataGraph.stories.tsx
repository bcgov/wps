import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import WxDataGraph from 'features/fireWeather/components/graphs/WxDataGraph'
import {
  observedValues,
  pastModelValues,
  modelValues,
  modelSummaries,
  pastForecastValues,
  forecastValues,
  forecastSummaries,
  pastHighResModelValues,
  highResModelValues,
  highResModelSummaries,
  pastRegionalModelValues,
  regionalModelValues,
  regionalModelSummaries
} from 'utils/storybook'
import { ModelValue } from 'api/modelAPI'
import { NoonForecastValue } from 'api/forecastAPI'
import { getTimeOfInterestFromUrl } from 'utils/url'
import { GeoJsonStation } from 'api/stationAPI'

export default {
  title: 'morecast/WxDataGraph',
  component: WxDataGraph
} as Meta

type PropTypes = React.ComponentProps<typeof WxDataGraph>

const Template: Story<PropTypes> = args => <WxDataGraph {...args} />

const station: GeoJsonStation = {
  type: 'Feature',
  properties: {
    code: 322,
    name: 'AFTON',
    ecodivision_name: 'SEMI-ARID STEPPE HIGHLANDS',
    core_season: {
      start_month: 5,
      start_day: 1,
      end_month: 9,
      end_day: 15
    }
  },
  geometry: {
    type: 'Point',
    coordinates: [-120.4816667, 50.6733333]
  }
}

export const Default = Template.bind({})
Default.args = {
  timeOfInterest: getTimeOfInterestFromUrl(''),
  station,
  observations: observedValues,
  gdpsModels: pastModelValues.concat(modelValues) as ModelValue[],
  gdpsSummaries: modelSummaries,
  noonForecasts: pastForecastValues.concat(forecastValues) as NoonForecastValue[],
  noonForecastSummaries: forecastSummaries,
  hrdpsModels: pastHighResModelValues.concat(highResModelValues) as ModelValue[], // prettier-ignore
  hrdpsSummaries: highResModelSummaries,
  rdpsModels: pastRegionalModelValues.concat(regionalModelValues) as ModelValue[], // prettier-ignore
  rdpsSummaries: regionalModelSummaries
}
