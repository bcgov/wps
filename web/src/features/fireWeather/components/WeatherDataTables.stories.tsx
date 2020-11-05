import React from 'react'
import { storiesOf } from '@storybook/react'

import NoonForecastTable from 'features/fireWeather/components/NoonForecastTable'
import { forecastValues, modelValues, observedValues } from 'utils/storybook'
import HourlyObservationsTable from 'features/fireWeather/components/HourlyObservationsTable'
import { isNoonInPST } from 'utils/date'
import { ModelValue } from 'api/modelAPI'
import { NoonForecastValue } from 'api/forecastAPI'

storiesOf('Weather data tables', module)
  .add('NoonForecastTable', () => {
    const modelTableTitle = 'Interpolated global model noon values (PST, UTC−08:00): '
    const forecastTableTitle = 'Weather forecast noon values (PST, UTC−08:00): '

    return (
      <>
        <NoonForecastTable
          values={modelValues.filter(v => isNoonInPST(v.datetime)) as ModelValue[]}
          title={modelTableTitle}
          testId=""
        />
        <NoonForecastTable
          values={forecastValues as NoonForecastValue[]}
          title={forecastTableTitle}
          testId=""
        />
      </>
    )
  })
  .add('HourlyObservationsTable', () => {
    return <HourlyObservationsTable title="This is title!" values={observedValues} />
  })
