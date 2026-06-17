import { DateTime } from 'luxon'
import * as React from 'react'
import DateRangePicker from './DateRangePicker'
import type { DateRange } from './types'

export interface DateRangePickerWrapperProps {
  open: boolean
  toggle: () => void
  initialDateRange: DateRange
  minDate?: Date | string
  maxDate?: Date | string
  maxDayOffset?: number
  onChange: (dateRange: DateRange) => void
  closeOnClickOutside?: boolean
}

const DateRangePickerWrapper: React.FunctionComponent<DateRangePickerWrapperProps> = (
  props: DateRangePickerWrapperProps
) => {
  const { closeOnClickOutside, initialDateRange, toggle, open, maxDayOffset } = props

  const handleToggle = () => {
    if (closeOnClickOutside === false) {
      return
    }
    toggle()
  }

  React.useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (open && event.key === 'Escape') {
        handleToggle()
      }
    }
    document.addEventListener('keydown', handleKeyPress)
    return () => {
      document.removeEventListener('keydown', handleKeyPress)
    }
  })

  const minDate = initialDateRange.startDate || new Date()
  const maxDate = DateTime.fromJSDate(minDate).plus({ days: 10 }).toJSDate()

  return (
    <div data-testid="date-range-picker-wrapper">
      <div>
        <DateRangePicker {...props} minDate={minDate} maxDate={maxDate} maxDayOffset={maxDayOffset} />
      </div>
    </div>
  )
}

export default React.memo(DateRangePickerWrapper)
