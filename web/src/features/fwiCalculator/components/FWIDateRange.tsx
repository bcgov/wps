import React, { useState } from 'react'
import { DateRange, DateRangePicker } from 'materialui-daterange-picker'

const FWIDateRange = () => {
  const [open, setOpen] = useState(true)
  const [dateRange, setDateRange] = useState<DateRange>({})

  const toggle = () => setOpen(!open)

  return (
    <DateRangePicker
      open={open}
      toggle={toggle}
      onChange={range => setDateRange(range)}
    />
  )
}
export default React.memo(FWIDateRange)
