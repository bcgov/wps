import { makeStyles } from '@material-ui/core'
import { ToggleButtonGroup, ToggleButton } from '@material-ui/lab'
import React from 'react'

export interface ViewSwitcherTogglesProps {
  testId?: string
  isWeeklyView: boolean
  toggleTableView: React.Dispatch<React.SetStateAction<boolean>>
}

const useStyles = makeStyles(() => ({
  toggleGroup: {
    paddingLeft: 25
  }
}))

const ViewSwitcherToggles = (props: ViewSwitcherTogglesProps) => {
  const classes = useStyles()

  const handleToggle = (
    _: React.MouseEvent<HTMLElement, MouseEvent>,
    changeToWeekly: boolean
  ) => {
    props.toggleTableView(changeToWeekly)
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
        <ToggleButton value={false} aria-label="daily">
          Daily Table
        </ToggleButton>
        <ToggleButton value={true} aria-label="weekly toggle">
          Weekly Table
        </ToggleButton>
      </ToggleButtonGroup>
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcherToggles)
