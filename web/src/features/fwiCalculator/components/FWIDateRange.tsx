import React from 'react'
import { Dialog } from '@mui/material'
import { isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import { PST_UTC_OFFSET } from 'utils/constants'
import DateRangePickerWrapper from 'components/dateRangePicker/DateRangePickerWrapper'
import { DateRange } from 'components/dateRangePicker/types'

export interface FWIDateRangeProps {
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
  startDate: Date
  endDate: Date
  updateStartDate: (newDate: Date) => void
  updateEndDate: (newDate: Date) => void
}

const FWIDateRange = ({ open, setOpen, startDate, updateStartDate, endDate, updateEndDate }: FWIDateRangeProps) => {
  const toggle = () => setOpen(!open)
  const changeHandler = (newDateRange: DateRange) => {
    if (!isUndefined(newDateRange.startDate) && !isUndefined(newDateRange.endDate)) {
      const isoStart = DateTime.fromISO(newDateRange.startDate.toISOString())
      const isoEnd = DateTime.fromISO(newDateRange.endDate.toISOString())

      const pstStartDate = DateTime.fromObject(
        {
          year: isoStart.year,
          month: isoStart.month,
          day: isoStart.day
        },
        { zone: `UTC${PST_UTC_OFFSET}` }
      )

      const pstEndDate = DateTime.fromObject(
        {
          year: isoEnd.year,
          month: isoEnd.month,
          day: isoEnd.day
        },
        { zone: `UTC${PST_UTC_OFFSET}` }
      )

      updateStartDate(pstStartDate.toJSDate())
      updateEndDate(pstEndDate.toJSDate())
      toggle()
    }
  }

  return (
    <Dialog open={open} onClose={toggle}>
      <DateRangePickerWrapper
        initialDateRange={{ startDate, endDate }}
        open={open}
        toggle={toggle}
        onChange={changeHandler}
      />
    </Dialog>
  )
}
export default React.memo(FWIDateRange)
