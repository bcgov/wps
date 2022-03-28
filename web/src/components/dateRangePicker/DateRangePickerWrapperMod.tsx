import * as React from 'react'

import DateRangePickerMod from './DateRangePickerMod'

// eslint-disable-next-line no-unused-vars
import { DateRange } from './types'
import { DateTime } from 'luxon'

export interface DateRangePickerWrapperModProps {
  open: boolean
  toggle: () => void
  initialDateRange: DateRange
  minDate?: Date | string
  maxDate?: Date | string
  onChange: (dateRange: DateRange) => void
  closeOnClickOutside?: boolean
}

const DateRangePickerWrapper: React.FunctionComponent<DateRangePickerWrapperModProps> = (
  props: DateRangePickerWrapperModProps
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
    <div>
      {open && <div onKeyPress={handleKeyPress} onClick={handleToggle} />}

      <div>
        <DateRangePickerMod {...props} minDate={minDate} maxDate={maxDate} />
      </div>
    </div>
  )
}

export default DateRangePickerWrapper
