import { makeStyles } from '@material-ui/core'
import { ToggleButtonGroup, ToggleButton } from '@material-ui/lab'
import { isUndefined, range } from 'lodash'
import { theme } from 'app/theme'
import React from 'react'
import { pstFormatter } from 'utils/date'
import { useDispatch, useSelector } from 'react-redux'
import { selectHFICalculatorState } from 'app/rootReducer'
import { setSelectedPrepDate } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { DateTime } from 'luxon'

export interface ViewSwitcherTogglesProps {
  testId?: string
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
  const { dateRange, selectedPrepDate } = useSelector(selectHFICalculatorState)
  const classes = useStyles()
  const dispatch = useDispatch()

  const handleToggle = (
    _: React.MouseEvent<HTMLElement, MouseEvent>,
    prepDate: string
  ) => {
    dispatch(setSelectedPrepDate(prepDate))
  }

  let daysInDateRange = 0
  let start: DateTime = DateTime.now()

  if (
    !isUndefined(dateRange) &&
    !isUndefined(dateRange.start_date) &&
    !isUndefined(dateRange.end_date)
  ) {
    start = DateTime.fromISO(dateRange.start_date)
    const end = DateTime.fromISO(dateRange.end_date)
    daysInDateRange = end.diff(start, 'days').valueOf()
  }

  const formatDateString = (dateString: string): string => {
    // Dates get really gross. We don't know what kind of format the date string is coming in as,
    // since our codebase is all over the place. Until we re-factor everything date related, I'm
    // putting this in here to make sure we're dealing with ISO string in the PST timezone.
    if (dateString == '') {
      return ''
    }
    const dtObject: DateTime = DateTime.fromISO(dateString)
    return pstFormatter(dtObject)
  }

  return (
    <React.Fragment>
      <div data-testid={props.testId}>
        <ToggleButtonGroup
          exclusive
          onChange={handleToggle}
          aria-label="view toggles"
          value={formatDateString(selectedPrepDate)}
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

          {range(daysInDateRange).map(i => {
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
                value={pstFormatter(day)}
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
      </div>
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcherToggles)
