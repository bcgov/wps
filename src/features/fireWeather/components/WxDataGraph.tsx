import React from 'react'
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts'
import Typography from '@material-ui/core/Typography'
import { makeStyles } from '@material-ui/core/styles'

import { datetimeInPDT } from 'utils/date'
import { MODEL_VALUE_DECIMAL } from 'utils/constants'
import { ModelValue } from 'api/modelAPI'
import { ReadingValue } from 'api/readingAPI'

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

const sortByDatetime = (a: string, b: string) => {
  const a1 = new Date(a)
  const b1 = new Date(b)

  return a1 > b1 ? 1 : a1 < b1 ? -1 : 0
}

const getEarlierDt = (a: string, b: string) => {
  const aDate = new Date(a)
  const bDate = new Date(b)

  return aDate > bDate ? b : a
}

const getDateRangeAndToday = (wxData: WxValue[]) => {
  const lookup: { [k: string]: string } = {}
  const today = datetimeInPDT(new Date().toISOString(), 'Do MMM')
  let todayDt: string | undefined = undefined

  wxData.forEach(v => {
    const day = datetimeInPDT(v.datetime, 'Do MMM')

    if (!lookup[day]) {
      lookup[day] = v.datetime
    } else {
      lookup[day] = getEarlierDt(lookup[day], v.datetime)
    }

    if (today === day) {
      todayDt = lookup[day]
    }
  })

  const dateRange = Object.values(lookup).sort(sortByDatetime)

  return { dateRange, todayDt }
}

const useStyles = makeStyles({
  graph: {
    paddingBottom: 16
  },
  title: {
    paddingBottom: 4
  }
})

type WxValue = ReadingValue | ModelValue

interface Props {
  modelValues: ModelValue[] | undefined
  readingValues: ReadingValue[] | undefined
}

const WxDataGraph = ({ modelValues = [], readingValues = [] }: Props) => {
  const classes = useStyles()
  const wxData: WxValue[] = [...readingValues, ...modelValues]
  const { dateRange, todayDt } = getDateRangeAndToday(wxData)

  return (
    <div className={classes.graph} data-testid="weather-graph-by-station">
      <Typography className={classes.title} component="div" variant="subtitle2">
        Past 5 days of hourly readings and GDPS 3 hourly model with interpolated noon
        values (PDT, UTC-7):
      </Typography>

      <ResponsiveContainer width="100%" minHeight={300}>
        <LineChart margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid stroke="#ccc" strokeDasharray="1 1" />
          <XAxis
            dataKey="datetime"
            type="category"
            allowDuplicatedCategory={false}
            ticks={dateRange}
            tickFormatter={formatXAxis}
          />
          <YAxis
            yAxisId="left"
            dataKey="temperature"
            orientation="left"
            unit="°"
            domain={[-10, 45]}
            label={{ value: 'Temp (°C)', angle: -90, position: 'insideLeft' }}
          />
          <YAxis
            yAxisId="right"
            dataKey="relative_humidity"
            orientation="right"
            unit="%"
            domain={[0, 100]}
            label={{
              value: 'RH',
              angle: -270,
              position: 'insideRight'
            }}
          />
          <Tooltip labelFormatter={formatTooltipLabel} formatter={formatTooltipValue} />
          <Legend />
          <ReferenceLine
            x={todayDt}
            yAxisId="left"
            stroke="green"
            label="Today"
            strokeDasharray="4 4"
            strokeWidth={1.5}
          />
          <Line
            yAxisId="left"
            name="Temp"
            dataKey="temperature"
            data={readingValues}
            strokeWidth={1.5}
            type="monotone"
            stroke="crimson"
          />
          <Line
            yAxisId="left"
            name="Model Temp"
            dataKey="temperature"
            data={modelValues}
            type="monotone"
            stroke="indianred"
          />
          <Line
            yAxisId="right"
            name="RH"
            dataKey="relative_humidity"
            data={readingValues}
            strokeWidth={1.5}
            type="monotone"
            stroke="royalblue"
          />
          <Line
            yAxisId="right"
            name="Model RH"
            dataKey="relative_humidity"
            data={modelValues}
            type="monotone"
            stroke="dodgerblue"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default React.memo(WxDataGraph)
