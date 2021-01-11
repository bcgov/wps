import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import { PercentileStationResultTable } from 'features/percentileCalculator/components/PercentileStationResultTable'
import { StationSummaryResponse } from 'api/percentileAPI'

const stationResponse: StationSummaryResponse = {
  ffmc: 94.0249,
  isi: 15.57171,
  bui: 181.013,
  years: [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019],
  station: {
    code: 322,
    name: 'AFTON',
    lat: 50.6733333,
    long: -120.4816667,
    ecodivision_name: 'SEMI-ARID STEPPE HIGHLANDS',
    core_season: {
      start_month: 5,
      start_day: 1,
      end_month: 9,
      end_day: 15
    }
  }
}

export default {
  title: 'component/PercentileStationResultTable',
  component: PercentileStationResultTable,
  argTypes: {
    width: {
      control: {
        type: 'inline-radio',
        options: ['33%', '50%', '100%'] // https://storybook.js.org/docs/react/essentials/controls
      }
    }
  }
} as Meta

type PropTypes = React.ComponentProps<typeof PercentileStationResultTable> & {
  width: string
}

const Template: Story<PropTypes> = args => {
  const { stationResponse, width } = args

  return (
    <div style={{ width }}>
      <PercentileStationResultTable stationResponse={stationResponse} />
    </div>
  )
}

export const DifferentWidths = Template.bind({})
DifferentWidths.args = {
  stationResponse,
  width: '33%'
}
