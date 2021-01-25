import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import PeakValuesTable, {columns as peakValuesTableColumns} from 'features/peakBurniness/components/tables/PeakValuesTable'
import { peakValues } from 'utils/storybook'

export default {
  title: 'component/PeakBurniness',
  component: PeakValuesTable
} as Meta

type PropTypes = React.ComponentProps<typeof PeakValuesTable>

const Template: Story<PropTypes> = (args) => <PeakValuesTable {...args} />

export const PeakWeatherValuesTable = Template.bind({})
PeakWeatherValuesTable.args = {
  title: 'Median of max hourly weather values for 2011 - 2020 at station:',
  testId: 'test_id_1',
  rows: peakValues,
  columns: peakValuesTableColumns
}
