/* eslint-disable no-multi-assign */
/* eslint-disable no-param-reassign */

import * as React from 'react'
import {
  addMonths,
  isSameDay,
  isWithinInterval,
  isAfter,
  isBefore,
  isSameMonth,
  addYears,
  max,
  min
} from 'date-fns'

// eslint-disable-next-line no-unused-vars
import { DateRange, NavigationAction, DefinedRange } from './types'
import { getValidatedMonths, parseOptionalDate } from './utils'

import Menu from './Menu'
import { DateTime } from 'luxon'

type Marker = symbol

export const MARKERS: { [key: string]: Marker } = {
  FIRST_MONTH: Symbol('firstMonth'),
  SECOND_MONTH: Symbol('secondMonth')
}

export interface DateRangePickerModProps {
  open: boolean
  initialDateRange?: DateRange
  definedRanges?: DefinedRange[]
  minDate: Date
  maxDate: Date
  onChange: (dateRange: DateRange) => void
}

const DateRangePickerMod: React.FunctionComponent<DateRangePickerModProps> = (
  props: DateRangePickerModProps
) => {
  const today = new Date()

  const { open, onChange, initialDateRange, maxDate } = props

  const minDateValid = addYears(today, -10)
  const maxDateValid = parseOptionalDate(maxDate, addYears(today, 10))
  const [intialFirstMonth, initialSecondMonth] = getValidatedMonths(
    initialDateRange || {},
    minDateValid,
    maxDateValid
  )
  const [currentMaxDate, setCurrentMaxDate] = React.useState<Date>(maxDate)
  const [dateRange, setDateRange] = React.useState<DateRange>({ ...initialDateRange })
  const [hoverDay, setHoverDay] = React.useState<Date>()
  const [firstMonth, setFirstMonth] = React.useState<Date>(intialFirstMonth || today)
  const [secondMonth, setSecondMonth] = React.useState<Date>(
    initialSecondMonth || addMonths(firstMonth, 1)
  )

  const { startDate, endDate } = dateRange

  // handlers
  const setFirstMonthValidated = (date: Date) => {
    if (isBefore(date, secondMonth)) {
      setFirstMonth(date)
    }
  }

  const setSecondMonthValidated = (date: Date) => {
    if (isAfter(date, firstMonth)) {
      setSecondMonth(date)
    }
  }

  const setDateRangeValidated = (range: DateRange) => {
    let { startDate: newStart, endDate: newEnd } = range

    if (newStart && newEnd) {
      range.startDate = newStart = max([newStart, minDateValid])
      range.endDate = newEnd = min([newEnd, maxDateValid])

      setDateRange(range)
      onChange(range)

      setFirstMonth(newStart)
      setSecondMonth(isSameMonth(newStart, newEnd) ? addMonths(newStart, 1) : newEnd)
    } else {
      const emptyRange = {}

      setDateRange(emptyRange)
      onChange(emptyRange)

      setFirstMonth(today)
      setSecondMonth(addMonths(firstMonth, 1))
    }
  }

  const onDayClick = (day: Date) => {
    if (startDate && !endDate && !isBefore(day, startDate)) {
      const newRange = { startDate, endDate: day }
      onChange(newRange)
      setDateRange(newRange)
    } else {
      setDateRange({ startDate: day, endDate: undefined })
      const newMaxDate = DateTime.fromJSDate(day).plus({ days: 6 })
      setCurrentMaxDate(newMaxDate.toJSDate())
    }
    setHoverDay(day)
  }

  const onMonthNavigate = (marker: Marker, action: NavigationAction) => {
    if (marker === MARKERS.FIRST_MONTH) {
      const firstNew = addMonths(firstMonth, action)
      if (isBefore(firstNew, secondMonth)) setFirstMonth(firstNew)
    } else {
      const secondNew = addMonths(secondMonth, action)
      if (isBefore(firstMonth, secondNew)) setSecondMonth(secondNew)
    }
  }

  const onDayHover = (date: Date) => {
    if (startDate && !endDate) {
      if (!hoverDay || !isSameDay(date, hoverDay)) {
        setHoverDay(date)
      }
    }
  }

  // helpers
  const inHoverRange = (day: Date) =>
    (startDate &&
      !endDate &&
      hoverDay &&
      isAfter(hoverDay, startDate) &&
      isWithinInterval(day, { start: startDate, end: hoverDay })) as boolean

  const helpers = {
    inHoverRange
  }

  const handlers = {
    onDayClick,
    onDayHover,
    onMonthNavigate
  }

  return open ? (
    <Menu
      dateRange={dateRange}
      minDate={minDateValid}
      maxDate={currentMaxDate}
      firstMonth={firstMonth}
      secondMonth={secondMonth}
      setFirstMonth={setFirstMonthValidated}
      setSecondMonth={setSecondMonthValidated}
      setDateRange={setDateRangeValidated}
      helpers={helpers}
      handlers={handlers}
    />
  ) : null
}

export default DateRangePickerMod
