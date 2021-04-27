import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import { WxDataDisplays } from 'features/fireWeather/components/WxDataDisplays'
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
  regionalModelSummaries,
  station322
} from 'utils/storybook'
import { NoonForecastValue } from 'api/forecastAPI'
import { ModelValue } from 'api/modelAPI'
import { isNoonInPST } from 'utils/date'
import { getTimeOfInterestFromUrl } from 'utils/url'

export default {
  title: 'morecast/WxDataDisplays',
  component: WxDataDisplays
} as Meta

type PropTypes = React.ComponentProps<typeof WxDataDisplays>

const Template: Story<PropTypes> = args => {
  return <WxDataDisplays {...args} />
}

const defaultArgs: PropTypes = {
  showTableView: 'true',
  timeOfInterest: getTimeOfInterestFromUrl(''),
  wxDataLoading: false,
  stationCodes: [322],
  stationsByCode: { 322: station322 },
  observationsByStation: {},
  allModelsByStation: {},
  noonModelsByStation: {},
  modelSummariesByStation: {},
  allNoonForecastsByStation: {},
  forecastSummariesByStation: {},
  allHighResModelsByStation: {},
  highResModelSummariesByStation: {},
  allRegionalModelsByStation: {},
  regionalModelSummariesByStation: {}
}

export const NoData = Template.bind({})
NoData.args = {
  ...defaultArgs
}

export const ObservationsOnly = Template.bind({})
ObservationsOnly.args = {
  ...defaultArgs,
  observationsByStation: { 322: observedValues }
}

export const ForecastsOnly = Template.bind({})
ForecastsOnly.args = {
  ...defaultArgs,
  allNoonForecastsByStation: {
    322: pastForecastValues.concat(forecastValues) as NoonForecastValue[]
  },
  forecastSummariesByStation: {
    322: forecastSummaries
  }
}

export const GDPSOnly = Template.bind({})
GDPSOnly.args = {
  ...defaultArgs,
  allModelsByStation: { 322: pastModelValues.concat(modelValues) as ModelValue[] },
  noonModelsByStation: {
    322: pastModelValues.concat(modelValues).filter(v => isNoonInPST(v.datetime))
  },
  modelSummariesByStation: { 322: modelSummaries }
}

export const AllModels = Template.bind({})
AllModels.args = {
  ...defaultArgs,
  allModelsByStation: { 322: pastModelValues.concat(modelValues) as ModelValue[] },
  noonModelsByStation: {
    322: pastModelValues.concat(modelValues).filter(v => isNoonInPST(v.datetime))
  },
  modelSummariesByStation: { 322: modelSummaries },
  allHighResModelsByStation: {
    322: pastHighResModelValues.concat(highResModelValues) as ModelValue[]
  },
  highResModelSummariesByStation: { 322: highResModelSummaries },
  allRegionalModelsByStation: {
    322: pastRegionalModelValues.concat(regionalModelValues) as ModelValue[]
  },
  regionalModelSummariesByStation: { 322: regionalModelSummaries }
}
