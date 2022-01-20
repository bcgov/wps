import { makeStyles } from '@material-ui/core'
import { DateTime } from 'luxon'
import { ToggleButtonGroup, ToggleButton } from '@material-ui/lab'
import { range } from 'lodash'
import { theme } from 'app/theme'
import React from 'react'
import { getPrepWeeklyDateRange, toISO } from 'utils/date'
import { useSelector } from 'react-redux'
import { selectHFICalculatorState } from 'app/rootReducer'

export interface ViewSwitcherTogglesProps {
  testId?: string
  setSelectedPrepDay: (prepDayIso: string | null) => void
  dateOfInterest: string
}

const useStyles = makeStyles(() => ({
  toggleGroup: {
    '& .MuiToggleButton-root': {
      color: theme.palette.primary.main
    },
    '& .MuiToggleButton-root.Mui-selected': {
      backgroundColor: theme.palette.primary.main,
      color: 'white',
      fontWeight: 'bold'
    },
    '& .MuiToggleButton-label': {
      lineHeight: '16px'
    }
  }
}))

const ViewSwitcherToggles = (props: ViewSwitcherTogglesProps) => {
  const { numPrepDays, selectedPrepDay } = useSelector(selectHFICalculatorState)
  const classes = useStyles()

  const handleToggle = (
    _: React.MouseEvent<HTMLElement, MouseEvent>,
    dayOfInterest: string
  ) => {
    props.setSelectedPrepDay(
      dayOfInterest == '' ? null : DateTime.fromISO(dayOfInterest).toISO()
    )
  }

  const { start } = getPrepWeeklyDateRange(props.dateOfInterest)

  return (
    <React.Fragment>
      <ToggleButtonGroup
        exclusive
        onChange={handleToggle}
        aria-label="view toggles"
        value={selectedPrepDay}
        className={classes.toggleGroup}
      >
        <ToggleButton
          data-testid="prep-period-toggle"
          value={''}
          aria-label="prep toggle"
        >
          Prep Period
        </ToggleButton>
        {/* Create a button for each day of the prep period. */}
        {range(numPrepDays).map(i => {
          const day = start.plus({ days: i })
          const rowA = `Day ${i + 1}`
          const rowB = day.toLocaleString({
            weekday: 'short',
            month: 'short',
            day: '2-digit'
          })
          return (
            <ToggleButton
              key={i}
              value={toISO(day)}
              aria-label={`${rowA}. ${rowB}.`}
              data-testid={`daily-toggle-${i}`}
            >
              {rowA}
              <br />
              {rowB}
            </ToggleButton>
          )
        })}
      </ToggleButtonGroup>
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcherToggles)
