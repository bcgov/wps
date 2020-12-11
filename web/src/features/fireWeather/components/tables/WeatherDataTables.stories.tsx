import React from 'react'
import { storiesOf } from '@storybook/react'

import NoonForecastTable from 'features/fireWeather/components/tables/NoonForecastTable'
import ObservationTable from 'features/fireWeather/components/tables/ObservationTable'
import NoonModelTable from 'features/fireWeather/components/tables/NoonModelTable'
import { forecastValues, modelValues, observedValues } from 'utils/storybook'
import { isNoonInPST } from 'utils/date'
import { ModelValue } from 'api/modelAPI'
import { NoonForecastValue } from 'api/forecastAPI'

storiesOf('Weather data tables', module).add('Sortable weather data tables', () => {
  const ObservationTableTitle = 'Past 5 days of hourly observations from station: '
  const modelTableTitle = 'Interpolated global model noon values (20:00 UTC): '
  const forecastTableTitle = 'Weather forecast noon values (20:00 UTC): '

  return (
    <>
      <ObservationTable
        testId="hmm"
        title={ObservationTableTitle}
        rows={observedValues}
      />

      <NoonModelTable
        rows={modelValues.filter(v => isNoonInPST(v.datetime)) as ModelValue[]}
        title={modelTableTitle}
        testId=""
      />

      <NoonForecastTable
        rows={forecastValues as NoonForecastValue[]}
        title={forecastTableTitle}
        testId=""
      />
    </>
  )
})
