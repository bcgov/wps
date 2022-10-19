/* eslint-disable radix */

import { Grid, IconButton, Select, MenuItem } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import React from 'react'
import ChevronLeft from '@mui/icons-material/ChevronLeft'
import ChevronRight from '@mui/icons-material/ChevronRight'
import { setMonth, getMonth, setYear, getYear } from 'date-fns'

const useStyles = makeStyles(() => ({
  iconContainer: {
    padding: 5
  },
  icon: {
    padding: 10,
    '&:hover': {
      background: 'none'
    }
  }
}))

interface HeaderProps {
  date: Date
  setDate: (date: Date) => void
  nextDisabled: boolean
  prevDisabled: boolean
  onClickNext: () => void
  onClickPrevious: () => void
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']

const generateYears = (relativeTo: Date, count: number) => {
  const half = Math.floor(count / 2)
  return Array(count)
    .fill(0)
    .map((_y, i) => relativeTo.getFullYear() - half + i) // TODO: make part of the state
}

const Header: React.FunctionComponent<HeaderProps> = ({
  date,
  setDate,
  nextDisabled,
  prevDisabled,
  onClickNext,
  onClickPrevious
}: HeaderProps) => {
  const classes = useStyles()

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleMonthChange = (event: any) => {
    setDate(setMonth(date, parseInt(event.target.value)))
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleYearChange = (event: any) => {
    setDate(setYear(date, parseInt(event.target.value)))
  }

  return (
    <Grid container justifyContent="space-between" alignItems="center">
      <Grid item className={classes.iconContainer}>
        <IconButton className={classes.icon} disabled={prevDisabled} onClick={onClickPrevious} size="large">
          <ChevronLeft color={prevDisabled ? 'disabled' : 'action'} />
        </IconButton>
      </Grid>
      <Grid item>
        <Select
          variant="standard"
          value={getMonth(date)}
          onChange={handleMonthChange}
          MenuProps={{ disablePortal: true }}
        >
          {MONTHS.map((month, idx) => (
            <MenuItem key={month} value={idx}>
              {month}
            </MenuItem>
          ))}
        </Select>
      </Grid>

      <Grid item>
        <Select
          variant="standard"
          value={getYear(date)}
          onChange={handleYearChange}
          MenuProps={{ disablePortal: true }}
        >
          {generateYears(date, 30).map(year => (
            <MenuItem key={year} value={year}>
              {year}
            </MenuItem>
          ))}
        </Select>
      </Grid>
      <Grid item className={classes.iconContainer}>
        <IconButton className={classes.icon} disabled={nextDisabled} onClick={onClickNext} size="large">
          <ChevronRight color={nextDisabled ? 'disabled' : 'action'} />
        </IconButton>
      </Grid>
    </Grid>
  )
}

export default Header
