import React, { useState } from 'react'
import { XAxis, YAxis, CartesianGrid, Line, LineChart, Legend, Tooltip, ResponsiveContainer } from 'recharts'
import { MultiDayRow } from 'features/fwiCalculator/components/dataModel'
import _ from 'lodash'
import ToggleLegend from 'features/fwiCalculator/components/ToggleLegend'

const chartColors = new Map([
  ['ffmc', '#264653'],
  ['dmc', '#2a9d8f'],
  ['dc', '#e9c46a'],
  ['isi', '#f4a261'],
  ['bui', '#e76f51'],
  ['fwi', '#82ca9d']
])

export interface FWIGraphRow {
  rowData: MultiDayRow
  color: string
}

export interface FireIndexGraphProps {
  rowData: MultiDayRow[]
}

const FireIndexGraph = ({ rowData }: FireIndexGraphProps) => {
  const [disabled, setDisabled] = useState<string[]>(['dc'])
  const linesToShow = _.without(Array.from(chartColors.keys()), ...disabled).map((line, idx) => (
    <Line key={idx} type="monotone" dataKey={line} stroke={chartColors.get(line)} />
  ))

  return (
    <ResponsiveContainer minWidth={100} minHeight={600}>
      <LineChart data={rowData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend
          wrapperStyle={{
            textAlign: 'center'
          }}
          content={<ToggleLegend disabled={disabled} setDisabled={setDisabled} />}
          payload={_.toPairs(chartColors).map(pair => ({
            value: pair[0],
            color: pair[1]
          }))}
        />
        {linesToShow}
      </LineChart>
    </ResponsiveContainer>
  )
}

export default React.memo(FireIndexGraph)
