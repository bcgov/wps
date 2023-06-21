import { styled } from '@mui/material/styles'
import { ToggleButtonGroup, ToggleButton } from '@mui/material'
import { isNull, isUndefined, range } from 'lodash'
import { theme } from 'app/theme'
import React from 'react'
import { pstFormatter } from 'utils/date'
import { useDispatch } from 'react-redux'
import { PrepDateRange, setSelectedPrepDate } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { DateTime } from 'luxon'

const PREFIX = 'ViewSwitcherToggles'

const classes = {
  toggleGroup: `${PREFIX}-toggleGroup`
}

// TODO jss-to-styled codemod: The Fragment root was replaced by div. Change the tag if needed.
const Root = styled('div')(() => ({
  [`& .${classes.toggleGroup}`]: {
    '& .MuiToggleButton-root': {
      height: 56,
      lineHeight: '16px',
      color: theme.palette.primary.main
    },
    '& .MuiToggleButton-root.Mui-selected': {
      backgroundColor: theme.palette.primary.main,
      color: 'white',
      fontWeight: 'bold'
    }
  }
}))

export interface ViewSwitcherTogglesProps {
  dateRange?: PrepDateRange
  selectedPrepDate: string
  testId?: string
}

const ViewSwitcherToggles = (props: ViewSwitcherTogglesProps) => {
  const dispatch = useDispatch()

  const handleToggle = (_: React.MouseEvent<HTMLElement, MouseEvent>, prepDate: string) => {
    if (!isNull(prepDate)) {
      dispatch(setSelectedPrepDate(prepDate))
    }
  }

  let daysInDateRange = 0
  let start: DateTime = DateTime.now()

  if (
    !isUndefined(props.dateRange) &&
    !isUndefined(props.dateRange.start_date) &&
    !isUndefined(props.dateRange.end_date)
  ) {
    start = DateTime.fromISO(props.dateRange.start_date)
    const end = DateTime.fromISO(props.dateRange.end_date)
    daysInDateRange = end.diff(start, 'days').days + 1
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
    <Root>
      <div data-testid={props.testId}>
        <ToggleButtonGroup
          exclusive
          onChange={handleToggle}
          aria-label="view toggles"
          value={formatDateString(props.selectedPrepDate)}
          className={classes.toggleGroup}
        >
          <ToggleButton data-testid="prep-period-toggle" value={''} aria-label="prep toggle">
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
    </Root>
  )
}

export default React.memo(ViewSwitcherToggles)
