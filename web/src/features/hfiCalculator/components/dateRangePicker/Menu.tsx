import React from 'react'
import { Paper, Grid, Typography, Divider, makeStyles, Theme } from '@material-ui/core'
import { format, differenceInCalendarMonths } from 'date-fns'
import ArrowRightAlt from '@material-ui/icons/ArrowRightAlt'
import DefinedRanges from 'features/hfiCalculator/components/dateRangePicker/DefinedRanges'
import { MARKERS } from 'features/hfiCalculator/components/dateRangePicker/DateRangePickerMod'
import {
  DateRange,
  NavigationAction,
  Setter
} from 'features/hfiCalculator/components/dateRangePicker/types'
import Month from 'features/hfiCalculator/components/dateRangePicker/Month'

const useStyles = makeStyles((theme: Theme) => ({
  header: {
    padding: '20px 70px'
  },
  headerItem: {
    flex: 1,
    textAlign: 'center'
  },
  divider: {
    borderLeft: `1px solid ${theme.palette.action.hover}`,
    marginBottom: 20
  }
}))

interface MenuProps {
  dateRange: DateRange
  minDate: Date
  maxDate: Date
  firstMonth: Date
  secondMonth: Date
  setFirstMonth: Setter<Date>
  setSecondMonth: Setter<Date>
  setDateRange: Setter<DateRange>
  helpers: {
    inHoverRange: (day: Date) => boolean
  }
  handlers: {
    onDayClick: (day: Date) => void
    onDayHover: (day: Date) => void
    onMonthNavigate: (marker: symbol, action: NavigationAction) => void
  }
}

const Menu: React.FunctionComponent<MenuProps> = (props: MenuProps) => {
  const classes = useStyles()

  const {
    dateRange,
    minDate,
    maxDate,
    firstMonth,
    setFirstMonth,
    secondMonth,
    setSecondMonth,
    setDateRange,
    helpers,
    handlers
  } = props

  const { startDate, endDate } = dateRange
  const canNavigateCloser = differenceInCalendarMonths(secondMonth, firstMonth) >= 2
  const commonProps = {
    dateRange,
    minDate,
    maxDate,
    helpers,
    handlers
  }
  return (
    <Paper elevation={5} square>
      <Grid container direction="row" wrap="nowrap">
        <Grid>
          <Grid container className={classes.header} alignItems="center">
            <Grid item className={classes.headerItem}>
              <Typography variant="subtitle1">
                {startDate ? format(startDate, 'MMMM DD, YYYY') : 'Start Date'}
              </Typography>
            </Grid>
            <Grid item className={classes.headerItem}>
              <ArrowRightAlt color="action" />
            </Grid>
            <Grid item className={classes.headerItem}>
              <Typography variant="subtitle1">
                {endDate ? format(endDate, 'MMMM DD, YYYY') : 'End Date'}
              </Typography>
            </Grid>
          </Grid>
          <Divider />
          <Grid container direction="row" justifyContent="center" wrap="nowrap">
            <Month
              {...commonProps}
              value={firstMonth}
              setValue={setFirstMonth}
              navState={[true, canNavigateCloser]}
              marker={MARKERS.FIRST_MONTH}
            />
            <div className={classes.divider} />
            <Month
              {...commonProps}
              value={secondMonth}
              setValue={setSecondMonth}
              navState={[canNavigateCloser, true]}
              marker={MARKERS.SECOND_MONTH}
            />
          </Grid>
        </Grid>
        <div className={classes.divider} />
        <Grid>
          <DefinedRanges selectedRange={dateRange} ranges={[]} setRange={setDateRange} />
        </Grid>
      </Grid>
    </Paper>
  )
}

export default Menu
