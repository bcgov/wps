import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import {PeakValuesResults} from 'features/peakBurniness/components/tables/PeakValuesResults'
import {columns as peakValuesTableColumns} from 'features/peakBurniness/components/tables/PeakValuesStationResultTable'
import { peakValues } from 'utils/storybook'

export default {
  title: 'component/PeakBurniness',
  component: PeakValuesResults
} as Meta

type PropTypes = React.ComponentProps<typeof PeakValuesResults>

const Template: Story<PropTypes> = (args) => <PeakValuesResults {...args} />

export const PeakWeatherValuesTable = Template.bind({})
PeakWeatherValuesTable.args = {
}
