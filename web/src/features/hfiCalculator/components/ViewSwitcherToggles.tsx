import { makeStyles } from '@material-ui/core'
import { ToggleButtonGroup, ToggleButton } from '@material-ui/lab'
import { range } from 'lodash'
import { theme } from 'app/theme'
import React from 'react'
import { getPrepWeeklyDateRange, toISO } from 'utils/date'
import { useDispatch, useSelector } from 'react-redux'
import { selectHFICalculatorState } from 'app/rootReducer'
import { setSelectedPrepDate } from 'features/hfiCalculator/slices/hfiCalculatorSlice'

export interface ViewSwitcherTogglesProps {
  testId?: string
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
  const { numPrepDays, selectedPrepDate } = useSelector(selectHFICalculatorState)
  const classes = useStyles()
  const dispatch = useDispatch()

  const handleToggle = (
    _: React.MouseEvent<HTMLElement, MouseEvent>,
    prepDate: string
  ) => {
    dispatch(setSelectedPrepDate(prepDate))
  }

  const { start } = getPrepWeeklyDateRange(props.dateOfInterest)

  return (
    <React.Fragment>
      <ToggleButtonGroup
        exclusive
        onChange={handleToggle}
        aria-label="view toggles"
        value={selectedPrepDate}
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
