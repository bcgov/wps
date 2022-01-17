import { makeStyles } from '@material-ui/core'
import { DateTime } from 'luxon'
import { ToggleButtonGroup, ToggleButton } from '@material-ui/lab'
import { NUM_WEEK_DAYS } from 'features/hfiCalculator/constants'
import { range } from 'lodash'
import { theme } from 'app/theme'
import React from 'react'
import { getPrepWeeklyDateRange } from 'utils/date'
import { toISO } from 'utils/date'

export interface ViewSwitcherTogglesProps {
  testId?: string
  setSelectedPrepDay: React.Dispatch<React.SetStateAction<DateTime | null>>
  selectedPrepDay: DateTime | null
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
    }
  }
}))

const ViewSwitcherToggles = (props: ViewSwitcherTogglesProps) => {
  const classes = useStyles()

  const handleToggle = (
    _: React.MouseEvent<HTMLElement, MouseEvent>,
    dayOfInterest: string | null
  ) => {
    props.setSelectedPrepDay(
      dayOfInterest == null ? null : DateTime.fromISO(dayOfInterest)
    )
  }

  const { start } = getPrepWeeklyDateRange(props.dateOfInterest)

  const selectedPrepDayString =
    props.selectedPrepDay == null ? null : toISO(props.selectedPrepDay)

  return (
    <React.Fragment>
      <ToggleButtonGroup
        exclusive
        onChange={handleToggle}
        aria-label="view toggles"
        value={selectedPrepDayString}
        className={classes.toggleGroup}
      >
        <ToggleButton
          data-testid="prep-period-toggle"
          value={null}
          aria-label="prep toggle"
        >
          Prep Period
        </ToggleButton>
        {/* Create a button for each day of the prep period. */}
        {range(NUM_WEEK_DAYS).map(i => {
          const day = start.plus({ days: i })
          const rowA = `Day ${i + 1}`
          const rowB = day.toLocaleString({
            weekday: 'short',
            month: 'short',
            day: '2-digit'
          })
          return (
            <ToggleButton key={i} value={toISO(day)} aria-label={`${rowA}. ${rowB}.`}>
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
