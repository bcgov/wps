import { makeStyles } from '@material-ui/core'
import { Button } from 'components'
import React from 'react'

export interface ViewSwitcherTogglesProps {
  testId?: string
  isWeeklyView: boolean
  toggleTableView: React.Dispatch<React.SetStateAction<boolean>>
}

const useStyles = makeStyles(theme => ({
  buttonUnselected: {
    height: '56px',
    width: '210px',
    margin: '8px',
    border: '3px solid ' + theme.palette.primary.main
  },
  buttonSelected: {
    height: '56px',
    width: '210px',
    margin: '8px',
    border: '3px solid ' + theme.palette.primary.main,
    backgroundColor: theme.palette.primary.main,
    color: '#FFFFFF'
  }
}))

const ViewSwitcherToggles = (props: ViewSwitcherTogglesProps) => {
  const classes = useStyles()

  const toggleView = () => {
    props.toggleTableView(!props.isWeeklyView)
  }

  return (
    <React.Fragment>
      <Button
        className={props.isWeeklyView ? classes.buttonUnselected : classes.buttonSelected}
        onClick={toggleView}
      >
        Daily Table
      </Button>
      <Button
        className={props.isWeeklyView ? classes.buttonSelected : classes.buttonUnselected}
        onClick={toggleView}
      >
        Weekly Table
      </Button>
    </React.Fragment>
  )
}

export default React.memo(ViewSwitcherToggles)
