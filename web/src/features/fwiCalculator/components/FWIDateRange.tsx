import React from 'react'
import { DateRange, DateRangePicker } from 'materialui-daterange-picker'
import { Dialog } from '@material-ui/core'
import { isUndefined } from 'lodash'

export interface FWIDateRangeProps {
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
  startDate: Date
  endDate: Date
  updateStartDate: (newDate: Date) => void
  updateEndDate: (newDate: Date) => void
}

const FWIDateRange = ({
  open,
  setOpen,
  startDate,
  updateStartDate,
  endDate,
  updateEndDate
}: FWIDateRangeProps) => {
  const toggle = () => setOpen(!open)
  const changeHandler = (newDateRange: DateRange) => {
    if (!isUndefined(newDateRange.startDate) && !isUndefined(newDateRange.endDate)) {
      updateStartDate(newDateRange.startDate)
      updateEndDate(newDateRange.endDate)
      toggle()
    }
  }

  return (
    <Dialog open={open} onClose={toggle}>
      <DateRangePicker
        initialDateRange={{ startDate, endDate }}
        open={open}
        toggle={toggle}
        onChange={changeHandler}
      />
    </Dialog>
  )
}
export default React.memo(FWIDateRange)
