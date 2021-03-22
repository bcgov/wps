import React from 'react'
import { Story, Meta } from '@storybook/react/types-6-0'

import { PercentileResults } from 'features/percentileCalculator/components/PercentileResults'

const stationSummaryResponse = {
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

const stationSummaryResponse2 = {
  ffmc: null,
  isi: null,
  bui: null,
  years: [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018],
  station: {
    code: 838,
    name: 'AKOKLI CREEK',
    lat: 49.4358,
    long: -116.7464,
    ecodivision_name: 'HUMID CONTINENTAL HIGHLANDS',
    core_season: {
      start_month: 5,
      start_day: 15,
      end_month: 8,
      end_day: 31
    }
  }
}

export default {
  title: 'percentile/PercentileResults',
  component: PercentileResults
} as Meta

type PropTypes = React.ComponentProps<typeof PercentileResults>

const Template: Story<PropTypes> = args => <PercentileResults {...args} />

export const OneStation = Template.bind({})
OneStation.args = {
  result: {
    stations: {
      [stationSummaryResponse.station.code]: stationSummaryResponse
    },
    mean_values: { ffmc: null, isi: null, bui: null },
    year_range: { start: 2010, end: 2019 },
    percentile: 90
  }
}

export const TwoStations = Template.bind({})
TwoStations.args = {
  result: {
    stations: {
      [stationSummaryResponse.station.code]: stationSummaryResponse,
      [stationSummaryResponse2.station.code]: stationSummaryResponse2
    },
    mean_values: { ffmc: 94, isi: 181, bui: 15 },
    year_range: { start: 2010, end: 2019 },
    percentile: 90
  }
}
