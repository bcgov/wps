import makeStyles from '@mui/styles/makeStyles'
import { ToggleButtonGroup, ToggleButton } from '@mui/material'
import { theme } from 'app/theme'
import { isNull } from 'lodash'
import React from 'react'

export interface ViewSwitcherTogglesProps {
  testId?: string
  isBasic: boolean
  toggleView: React.Dispatch<React.SetStateAction<boolean>>
}

const useStyles = makeStyles({
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
})

const FWIToggle = (props: ViewSwitcherTogglesProps) => {
  const classes = useStyles()

  const handleToggle = (_: React.MouseEvent<HTMLElement, MouseEvent>, changeToMulti: boolean) => {
    if (!isNull(changeToMulti)) {
      props.toggleView(changeToMulti)
    }
  }
  return (
    <React.Fragment>
      <ToggleButtonGroup
        exclusive
        onChange={handleToggle}
        aria-label="view toggles"
        value={props.isBasic}
        className={classes.toggleGroup}
      >
        <ToggleButton data-testid="fwi-multi-toggle" value={true} aria-label="fwi multi toggle">
          Basic
        </ToggleButton>
        <ToggleButton data-testid="fwi-multi-toggle" value={false} aria-label="fwi daily toggle">
          Multi
        </ToggleButton>
      </ToggleButtonGroup>
    </React.Fragment>
  )
}

export default React.memo(FWIToggle)
