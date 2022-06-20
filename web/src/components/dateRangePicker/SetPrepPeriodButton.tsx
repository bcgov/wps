import React from 'react'
import { Button } from '@mui/material'
import { AppDispatch } from 'app/store'
import { useDispatch } from 'react-redux'
import { DateRange } from 'components/dateRangePicker/types'
import { setPrepPeriod } from 'features/hfiCalculator/slices/hfiCalculatorSlice'

export interface SetPrepPeriodProps {
  dateRange: DateRange
  toggle: () => void
}

const SetPrepPeriodButton = ({ dateRange, toggle }: SetPrepPeriodProps) => {
  const dispatch: AppDispatch = useDispatch()

  const onClickHandler = () => {
    dispatch(setPrepPeriod({ ...dateRange }))
    toggle()
  }

  return (
    <Button data-testid="set-prep-period-button" variant="contained" color="primary" onClick={onClickHandler}>
      Set prep period
    </Button>
  )
}

export default React.memo(SetPrepPeriodButton)
