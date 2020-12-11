import React from 'react'
import { storiesOf } from '@storybook/react'

import NoonWeatherValueTable from 'features/fireWeather/components/NoonWeatherValueTable'
import HourlyObservationsTable from 'features/fireWeather/components/HourlyObservationsTable'
import { forecastValues, modelValues, observedValues } from 'utils/storybook'
import { isNoonInPST } from 'utils/date'
import { ModelValue } from 'api/modelAPI'
import { NoonForecastValue } from 'api/forecastAPI'

storiesOf('Weather data tables', module)
  .add('NoonWeatherValueTable', () => {
    const modelTableTitle = 'Interpolated global model noon values (PST, UTC−08:00): '
    const forecastTableTitle = 'Weather forecast noon values (PST, UTC−08:00): '

    return (
      <>
        <NoonWeatherValueTable
          rows={modelValues.filter(v => isNoonInPST(v.datetime)) as ModelValue[]}
          title={modelTableTitle}
          testId=""
        />
        <NoonWeatherValueTable
          rows={forecastValues as NoonForecastValue[]}
          title={forecastTableTitle}
          testId=""
        />
      </>
    )
  })
  .add('HourlyObservationsTable', () => {
    return (
      <HourlyObservationsTable
        testId="hmm"
        title="This is title!"
        rows={observedValues}
      />
    )
  })
