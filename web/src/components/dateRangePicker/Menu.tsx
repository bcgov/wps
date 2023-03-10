import React from 'react'
import { Paper, Grid, Typography, Divider, Button } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { format, differenceInCalendarMonths } from 'date-fns'
import ArrowRightAlt from '@mui/icons-material/ArrowRightAlt'
import { MARKERS } from 'components/dateRangePicker/DateRangePicker'
import { DateRange, NavigationAction, Setter } from 'components/dateRangePicker/types'
import Month from 'components/dateRangePicker/Month'
import { theme } from 'app/theme'

const useStyles = makeStyles(() => ({
  header: {
    padding: '20px 70px'
  },
  footer: {
    padding: '10px 10px'
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
  helpers: {
    inHoverRange: (day: Date) => boolean
  }
  handlers: {
    onDayClick: (day: Date) => void
    onDayHover: (day: Date) => void
    onMonthNavigate: (marker: symbol, action: NavigationAction) => void
    toggle: () => void
    resetDateRange: () => void
  }
}

const Menu: React.FunctionComponent<MenuProps> = (props: MenuProps) => {
  const classes = useStyles()

  const { dateRange, minDate, maxDate, firstMonth, setFirstMonth, secondMonth, setSecondMonth, helpers, handlers } =
    props

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
    <Paper elevation={5} square data-testid="date-range-picker-menu">
      <Grid container direction="row" wrap="nowrap">
        <Grid>
          <Grid container className={classes.header} alignItems="center">
            <Grid item className={classes.headerItem}>
              <Typography variant="subtitle1" data-testid="menu-start-date">
                {startDate ? format(startDate, 'MMMM dd, yyyy') : 'Start Date'}
              </Typography>
            </Grid>
            <Grid item className={classes.headerItem}>
              <ArrowRightAlt color="action" />
            </Grid>
            <Grid item className={classes.headerItem}>
              <Typography variant="subtitle1" data-testid="menu-end-date">
                {endDate ? format(endDate, 'MMMM dd, yyyy') : 'End Date'}
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
      </Grid>
      <Grid justifyContent="right" container spacing={1} className={classes.footer}>
        <Grid item>
          <Button data-testid="date-range-reset-button" variant="outlined" onClick={handlers.resetDateRange}>
            Reset
          </Button>
        </Grid>
        <Grid item>
          <Button data-testid="date-range-close-button" variant="outlined" onClick={handlers.toggle}>
            Close
          </Button>
        </Grid>
      </Grid>
    </Paper>
  )
}

export default Menu
