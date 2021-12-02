import { makeStyles } from '@material-ui/core'
import { ToggleButtonGroup, ToggleButton } from '@material-ui/lab'
import { theme } from 'app/theme'
import { isNull } from 'lodash'
import React from 'react'

export interface ViewSwitcherTogglesProps {
  testId?: string
  isWeeklyView: boolean
  toggleTableView: React.Dispatch<React.SetStateAction<boolean>>
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
    changeToWeekly: boolean
  ) => {
    if (!isNull(changeToWeekly)) {
      props.toggleTableView(changeToWeekly)
    }
  }
  return (
    <React.Fragment>
      <ToggleButtonGroup
        exclusive
        onChange={handleToggle}
        aria-label="view toggles"
        value={props.isWeeklyView}
        className={classes.toggleGroup}
      >
        <ToggleButton value={true} aria-label="prep toggle">
          Prep Period
        </ToggleButton>
        <ToggleButton value={false} aria-label="daily toggle">
          Daily Table
        </ToggleButton>
      </ToggleButtonGroup>
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcherToggles)
