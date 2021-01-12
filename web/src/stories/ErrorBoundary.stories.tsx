import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import { ErrorBoundary } from 'components'
import ObservationTable from 'features/fireWeather/components/tables/ObservationTable'

export default {
  title: 'component/ErrorBoundary',
  component: ErrorBoundary
} as Meta

type ObservationTablePropTypes = React.ComponentProps<typeof ObservationTable>

// TODO: Hide the error overlay if possible... (the overlay doesn't show up in the app)
const Template: Story<ObservationTablePropTypes> = args => {
  return (
    <ErrorBoundary>
      <ObservationTable {...args} />
    </ErrorBoundary>
  )
}

export const ErrorOccured = Template.bind({})
ErrorOccured.args = {
  testId: 'test-id',
  // @ts-expect-error
  rows: {},
  title: 'this is a title'
}
