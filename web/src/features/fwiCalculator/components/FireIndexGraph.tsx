import React from 'react'
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import { LineChart } from 'recharts'
import { Line } from 'recharts'
import { MultiDayRow } from 'features/fwiCalculator/components/dataModel'

export interface FireIndexGraphProps {
  rowData: MultiDayRow[]
}

const FireIndexGraph = ({ rowData }: FireIndexGraphProps) => {
  return (
    <ResponsiveContainer minWidth={100} minHeight={600}>
      <LineChart data={rowData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="ffmc" stroke="#264653" activeDot={{ r: 8 }} />
        <Line type="monotone" dataKey="dmc" stroke="#2a9d8f" />
        <Line type="monotone" dataKey="dc" stroke="#e9c46a" />
        <Line type="monotone" dataKey="isi" stroke="#f4a261" />
        <Line type="monotone" dataKey="bui" stroke="#e76f51" />
        <Line type="monotone" dataKey="fwi" stroke="#82ca9d" />
      </LineChart>
    </ResponsiveContainer>
  )
}

export default React.memo(FireIndexGraph)
