import ChevronLeft from '@mui/icons-material/ChevronLeft'
import ChevronRight from '@mui/icons-material/ChevronRight'
import { Grid, IconButton, MenuItem, Select } from '@mui/material'
import { styled } from '@mui/material/styles'
import { getMonth, getYear, setMonth, setYear } from 'date-fns'
import type React from 'react'

const PREFIX = 'Header'

const classes = {
  iconContainer: `${PREFIX}-iconContainer`,
  icon: `${PREFIX}-icon`
}

const StyledGrid = styled(Grid)(() => ({
  [`& .${classes.iconContainer}`]: {
    padding: 5
  },

  [`& .${classes.icon}`]: {
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
  const handleMonthChange = (event: any) => {
    setDate(setMonth(date, parseInt(event.target.value, 10)))
  }
  const handleYearChange = (event: any) => {
    setDate(setYear(date, parseInt(event.target.value, 10)))
  }

  return (
    <StyledGrid container sx={{ justifyContent: 'space-between', alignItems: 'center' }}>
      <Grid className={classes.iconContainer}>
        <IconButton className={classes.icon} disabled={prevDisabled} onClick={onClickPrevious} size="large">
          <ChevronLeft color={prevDisabled ? 'disabled' : 'action'} />
        </IconButton>
      </Grid>
      <Grid>
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

      <Grid>
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
      <Grid className={classes.iconContainer}>
        <IconButton className={classes.icon} disabled={nextDisabled} onClick={onClickNext} size="large">
          <ChevronRight color={nextDisabled ? 'disabled' : 'action'} />
        </IconButton>
      </Grid>
    </StyledGrid>
  )
}

export default Header
