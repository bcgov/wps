import React from 'react'
import { storiesOf } from '@storybook/react'
import { withKnobs, select } from '@storybook/addon-knobs'

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

storiesOf('PercentileStationResultTable', module)
  .addDecorator(withKnobs)
  .add('default', () => {
    const width = select('width', { Third: '33%', Half: '50%', Full: '100%' }, '33%')

    return (
      <div style={{ width: width }}>
        <PercentileStationResultTable stationResponse={stationResponse} />
      </div>
    )
  })
