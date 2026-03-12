import * as React from 'react'
import { styled } from '@mui/material/styles'
import { Paper, Grid, Typography } from '@mui/material'
import { getDate, isSameMonth, isToday, format, isWithinInterval } from 'date-fns'
import {
  chunks,
  getDaysInMonth,
  isStartOfRange,
  isEndOfRange,
  inDateRange,
  isRangeSameDay
} from 'components/dateRangePicker/utils'
import { NavigationAction, DateRange } from 'components/dateRangePicker/types'
import Header from 'components/dateRangePicker/Header'
import Day from 'components/dateRangePicker/Day'

const PREFIX = 'Month'

const classes = {
  root: `${PREFIX}-root`,
  weekDaysContainer: `${PREFIX}-weekDaysContainer`,
  daysContainer: `${PREFIX}-daysContainer`
}

const Root = styled('div')(() => ({
  [`& .${classes.root}`]: {
    width: 290
  },

  [`& .${classes.weekDaysContainer}`]: {
    marginTop: 10,
    paddingLeft: 30,
    paddingRight: 30
  },

  [`& .${classes.daysContainer}`]: {
    paddingLeft: 15,
    paddingRight: 15,
    marginTop: 15,
    marginBottom: 20
  }
}))

const WEEK_DAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

interface MonthProps {
  testId?: string
  value: Date
  marker: symbol
  dateRange: DateRange
  minDate: Date
  maxDate: Date
  navState: [boolean, boolean]
  setValue: (date: Date) => void
  helpers: {
    inHoverRange: (day: Date) => boolean
  }
  handlers: {
    onDayClick: (day: Date) => void
    onDayHover: (day: Date) => void
    onMonthNavigate: (marker: symbol, action: NavigationAction) => void
  }
}

const Month: React.FunctionComponent<MonthProps> = (props: MonthProps) => {
  const { testId, helpers, handlers, value: date, dateRange, marker, setValue: setDate, minDate, maxDate } = props

  const [back, forward] = props.navState

  return (
    <Root data-testid={testId}>
      <Paper square elevation={0} className={classes.root}>
        <Grid container>
          <Header
            date={date}
            setDate={setDate}
            nextDisabled={!forward}
            prevDisabled={!back}
            onClickPrevious={() => handlers.onMonthNavigate(marker, NavigationAction.Previous)}
            onClickNext={() => handlers.onMonthNavigate(marker, NavigationAction.Next)}
          />

          <Grid item container direction="row" justifyContent="space-between" className={classes.weekDaysContainer}>
            {WEEK_DAYS.map(day => (
              <Typography color="textSecondary" key={day} variant="caption">
                {day}
              </Typography>
            ))}
          </Grid>

          <Grid item container direction="column" justifyContent="space-between" className={classes.daysContainer}>
            {chunks(getDaysInMonth(date), 7).map((week, idx) => (
              <Grid key={idx} container direction="row" justifyContent="center">
                {week.map(day => {
                  const isStart = isStartOfRange(dateRange, day)
                  const isEnd = isEndOfRange(dateRange, day)
                  const isRangeOneDay = isRangeSameDay(dateRange)
                  const highlighted = inDateRange(dateRange, day) || helpers.inHoverRange(day)

                  return (
                    <Day
                      testId={`day-${day.toISOString().split('T')[0]}`}
                      key={format(day, 'MM-dd-yyyy')}
                      filled={isStart || isEnd}
                      outlined={isToday(day)}
                      highlighted={highlighted && !isRangeOneDay}
                      disabled={!isSameMonth(date, day) || !isWithinInterval(day, { start: minDate, end: maxDate })}
                      startOfRange={isStart && !isRangeOneDay}
                      endOfRange={isEnd && !isRangeOneDay}
                      onClick={() => handlers.onDayClick(day)}
                      onHover={() => handlers.onDayHover(day)}
                      value={getDate(day)}
                    />
                  )
                })}
              </Grid>
            ))}
          </Grid>
        </Grid>
      </Paper>
    </Root>
  )
}

export default Month
