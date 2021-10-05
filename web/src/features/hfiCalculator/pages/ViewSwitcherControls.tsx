import { FormControl, makeStyles } from '@material-ui/core'
import { Button } from 'components'
import DatePicker from 'components/DatePicker'
import { fetchHFIDailies } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { fetchHFIStations } from 'features/hfiCalculator/slices/stationsSlice'
import { DateTime } from 'luxon'
import React, { useState } from 'react'
import { useDispatch } from 'react-redux'
import { getDateRange } from 'utils/date'

export interface ViewSwitcherControlsProps {
  testId?: string
  dateOfInterest: string
  isWeeklyView: boolean
  toggleTableView: React.Dispatch<React.SetStateAction<boolean>>
  setDateOfInterest: React.Dispatch<React.SetStateAction<string>>
}

const useStyles = makeStyles(theme => ({
  container: {
    display: 'flex',
    justifyContent: 'center'
  },
  formControl: {
    margin: theme.spacing(1),
    minWidth: 210
  },
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

const ViewSwitcherControls = (props: ViewSwitcherControlsProps) => {
  const classes = useStyles()
  const dispatch = useDispatch()

  const [previouslySelectedDateOfInterest, setPreviouslySelectedDateOfInterest] =
    useState(DateTime.now().toISODate())

  const toggleView = () => {
    props.toggleTableView(!props.isWeeklyView)
  }

  const updateDate = () => {
    if (previouslySelectedDateOfInterest !== props.dateOfInterest) {
      const { start, end } = getDateRange(props.isWeeklyView, props.dateOfInterest)
      dispatch(fetchHFIStations())
      dispatch(fetchHFIDailies(start.toUTC().valueOf(), end.toUTC().valueOf()))

      setPreviouslySelectedDateOfInterest(props.dateOfInterest)
    }
  }

  return (
    <React.Fragment>
      <FormControl className={classes.formControl}>
        <DatePicker
          date={props.dateOfInterest}
          onChange={props.setDateOfInterest}
          updateDate={updateDate}
        />
      </FormControl>
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

export default React.memo(ViewSwitcherControls)
