import React from 'react'
import { storiesOf } from '@storybook/react'

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

storiesOf('WxDataGraph', module).add('default', () => {
  return (
    <WxDataGraph
      observedValues={observedValues}
      allModelValues={pastModelValues.concat(modelValues) as ModelValue[]}
      modelSummaries={modelSummaries}
      allForecasts={pastForecastValues.concat(forecastValues) as NoonForecastValue[]}
      forecastSummaries={forecastSummaries}
      allHighResModelValues={
        pastHighResModelValues.concat(highResModelValues) as ModelValue[]
      }
      highResModelSummaries={highResModelSummaries}
      allRegionalModelValues={pastRegionalModelValues.concat(regionalModelValues) as ModelValue[]}
      regionalModelSummaries={regionalModelSummaries}
    />
  )
})
