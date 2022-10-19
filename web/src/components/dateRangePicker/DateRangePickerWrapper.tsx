import * as React from 'react'

import { DateRange } from './types'
import { DateTime } from 'luxon'
import DateRangePicker from 'components/dateRangePicker/DateRangePicker'

export interface DateRangePickerWrapperProps {
  open: boolean
  toggle: () => void
  initialDateRange: DateRange
  minDate?: Date | string
  maxDate?: Date | string
  onChange: (dateRange: DateRange) => void
  closeOnClickOutside?: boolean
}

const DateRangePickerWrapper: React.FunctionComponent<DateRangePickerWrapperProps> = (
  props: DateRangePickerWrapperProps
) => {
  const { closeOnClickOutside, initialDateRange, toggle, open } = props

  const handleToggle = () => {
    if (closeOnClickOutside === false) {
      return
    }
    toggle()
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleKeyPress = (event: any) => event?.key === 'Escape' && handleToggle()

  const minDate = initialDateRange.startDate || new Date()
  const maxDate = DateTime.fromJSDate(minDate).plus({ days: 6 }).toJSDate()

  return (
    <div data-testid="date-range-picker-wrapper">
      {open && <div onKeyPress={handleKeyPress} onClick={handleToggle} />}

      <div>
        <DateRangePicker {...props} minDate={minDate} maxDate={maxDate} />
      </div>
    </div>
  )
}

export default React.memo(DateRangePickerWrapper)
