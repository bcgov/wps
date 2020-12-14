// @ts-nocheck
import React from 'react'
import { storiesOf } from '@storybook/react'

import ObservationTable from 'features/fireWeather/components/tables/ObservationTable'
import { ErrorBoundary } from 'components'

storiesOf('ErrorBoundary', module).add('default', () => {
  return (
    <ErrorBoundary>
      <ObservationTable title="this is title" rows={{}} />
    </ErrorBoundary>
  )
})
