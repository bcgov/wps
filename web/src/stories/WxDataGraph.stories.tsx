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

export default {
  title: 'component/WxDataGraph',
  component: WxDataGraph
} as Meta

type PropTypes = React.ComponentProps<typeof WxDataGraph>

const Template: Story<PropTypes> = args => <WxDataGraph {...args} />

const station = {
  code: 322,
  name: 'AFTON',
  lat: 50.6733333,
  long: -120.4816667,
  ecodivision_name: 'SEMI-ARID STEPPE HIGHLANDS',
  core_season: {
    start_month: 5,
    start_day: 1,
    end_month: 9,
    end_day: 15
  }
}

export const Default = Template.bind({})
Default.args = {
  station,
  observedValues: observedValues,
  allModelValues: pastModelValues.concat(modelValues) as ModelValue[],
  modelSummaries: modelSummaries,
  allForecasts: pastForecastValues.concat(forecastValues) as NoonForecastValue[],
  forecastSummaries: forecastSummaries,
  allHighResModelValues: pastHighResModelValues.concat(highResModelValues) as ModelValue[], // prettier-ignore
  highResModelSummaries: highResModelSummaries,
  allRegionalModelValues: pastRegionalModelValues.concat(regionalModelValues) as ModelValue[], // prettier-ignore
  regionalModelSummaries: regionalModelSummaries
}
