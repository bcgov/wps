import { Grid, Paper, Stack, Typography } from '@mui/material'
import { styled } from '@mui/material/styles'
import { format, getDate, isSameMonth, isToday, isWithinInterval } from 'date-fns'
import type * as React from 'react'
import Day from './Day'
import Header from './Header'
import { type DateRange, NavigationAction } from './types'
import { chunks, getDaysInMonth, inDateRange, isEndOfRange, isRangeSameDay, isStartOfRange } from './utils'

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

          <Grid
            container
            direction="row"
            className={classes.weekDaysContainer}
            sx={{
              justifyContent: 'space-between'
            }}
          >
            {WEEK_DAYS.map(day => (
              <Typography color="textSecondary" key={day} variant="caption">
                {day}
              </Typography>
            ))}
          </Grid>

          <Stack
            className={classes.daysContainer}
            sx={{
              justifyContent: 'space-between'
            }}
          >
            {chunks(getDaysInMonth(date), 7).map(week => (
              <Grid
                key={week[0].toISOString()}
                container
                direction="row"
                sx={{
                  justifyContent: 'center'
                }}
              >
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
          </Stack>
        </Grid>
      </Paper>
    </Root>
  )
}

export default Month
