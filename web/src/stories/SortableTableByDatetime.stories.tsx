import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import { columns as observationTableColumns } from 'features/fireWeather/components/tables/ObservationTable'
import {
  noonModelTableColumns,
  noonForecastTableColumns
} from 'features/fireWeather/components/tables/NoonWxValueTables'
import { forecastValues, modelValues, observedValues } from 'utils/storybook'
import { isNoonInPST } from 'utils/date'
import SortableTableByDatetime from 'features/fireWeather/components/tables/SortableTableByDatetime'

export default {
  title: 'component/WeatherDataTables'
} as Meta

type PropTypes = React.ComponentProps<typeof SortableTableByDatetime>

const Template: Story<PropTypes> = args => <SortableTableByDatetime {...args} />

export const ObservationTable = Template.bind({})
ObservationTable.args = {
  title: 'Hourly observations in past 5 days: ',
  testId: 'test_id_1',
  rows: observedValues,
  columns: observationTableColumns
}

export const NoonModelTable = Template.bind({})
NoonModelTable.args = {
  title: 'Interpolated GDPS noon values: ',
  testId: 'test_id_2',
  rows: modelValues.filter(v => isNoonInPST(v.datetime)),
  columns: noonModelTableColumns
}

export const NoonForecastTable = Template.bind({})
NoonForecastTable.args = {
  title: 'Weather forecast noon values: ',
  testId: 'test_id_3',
  rows: forecastValues,
  columns: noonForecastTableColumns
}
