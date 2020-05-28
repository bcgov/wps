import React from 'react'
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import Typography from '@material-ui/core/Typography'
import { makeStyles } from '@material-ui/core/styles'

import { datetimeInPDT } from 'utils/date'
import { ModelValue } from 'api/modelAPI'
import { MODEL_VALUE_DECIMAL } from 'utils/constants'

const useStyles = makeStyles({
  graph: {
    paddingBottom: 16
  },
  title: {
    paddingBottom: 4
  }
})

const formatXAxis = (dt: string) => {
  return datetimeInPDT(dt, 'Do MMM')
}

const formatTooltipLabel = (dt: string | number) => {
  return datetimeInPDT(dt, 'h:mm a, dddd, MMM Do')
}

const formatTooltipValue = (
  value: string | number | (string | number)[],
  name: string
) => {
  if (typeof value === 'number') {
    if (name === 'RH') return Math.round(value)

    return value.toFixed(MODEL_VALUE_DECIMAL)
  }

  return value
}

const getDateRange = (values: ModelValue[]) => {
  const days: string[] = []
  const map: { [k: string]: boolean } = {}
  values.forEach(v => {
    const dt = datetimeInPDT(v.datetime, 'Do MMM')
    if (!map[dt]) {
      map[dt] = true
      days.push(v.datetime)
    }
  })

  return days
}

interface Props {
  values: ModelValue[] | undefined
}

const WxGraphByStation = ({ values }: Props) => {
  const classes = useStyles()

  if (!values || values.length === 0) {
    return null
  }

  const dateRange = getDateRange(values)

  return (
    <div className={classes.graph} data-testid="weather-graph-by-station">
      <Typography className={classes.title} component="div" variant="subtitle2">
        GDPS 3 hourly data with interpolated noon values (PDT, UTC-7):
      </Typography>

      <ResponsiveContainer width="100%" minHeight={300}>
        <LineChart data={values} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
          <XAxis
            dataKey="datetime"
            allowDataOverflow
            ticks={dateRange}
            tickFormatter={formatXAxis}
          />
          <YAxis
            yAxisId="left"
            orientation="left"
            type="number"
            unit="°"
            domain={['auto', 'auto']}
            allowDataOverflow
            label={{ value: 'Temp (°C)', angle: -90, position: 'insideLeft' }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            type="number"
            unit="%"
            domain={[0, 100]}
            allowDataOverflow
            label={{
              value: 'RH',
              angle: -270,
              position: 'insideRight'
            }}
          />
          <Line
            yAxisId="left"
            type="natural"
            name="Temp"
            dataKey="temperature"
            stroke="#8884d8"
          />
          <Line
            yAxisId="right"
            type="natural"
            name="RH"
            dataKey="relative_humidity"
            stroke="#82ca9d"
          />
          <CartesianGrid stroke="#ccc" strokeDasharray="1 1" />
          <Tooltip labelFormatter={formatTooltipLabel} formatter={formatTooltipValue} />
          <Legend />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default React.memo(WxGraphByStation)
