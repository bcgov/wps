import { Meta, Story } from '@storybook/react'
import React from 'react'
import DailyViewTable, {
  StationData
} from '../features/hfiCalculator/components/DailyViewTable'

export default {
  title: 'hfiCalculator/DailyViewTable'
} as Meta

type PropTypes = React.ComponentProps<typeof DailyViewTable>

const Template: Story<PropTypes> = args => <DailyViewTable {...args} />

const testRowData = [
  [159, 6.0, 24, 4.0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
  [237, 9.0, 37, 4.3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
]

const stationData: StationData[] = [
  { name: 'Test Station 1', metrics: testRowData[0], ros: { type01a: 1, type01b: 1 } },
  { name: 'Test Station 2', metrics: testRowData[1], ros: { type01a: 2, type01b: 2 } }
]

export const DailyTable = Template.bind({})
DailyTable.args = {
  title: 'Daily Table View',
  stationData
}
