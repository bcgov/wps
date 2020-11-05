// @ts-nocheck
import React from 'react'
import { storiesOf } from '@storybook/react'

import HourlyObservationsTable from 'features/fireWeather/components/HourlyObservationsTable'
import { ErrorBoundary } from 'components'

storiesOf('ErrorBoundary', module).add('default', () => {
  return (
    <ErrorBoundary>
      <HourlyObservationsTable title="this is title" values={{}} />
    </ErrorBoundary>
  )
})
