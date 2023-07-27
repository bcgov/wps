import {
  startOfWeek,
  startOfMonth,
  endOfWeek,
  endOfMonth,
  isBefore,
  addDays,
  isSameDay,
  isWithinInterval,
  isSameMonth,
  addMonths,
  isValid,
  min,
  max
} from 'date-fns'
import { isUndefined } from 'lodash'

interface DateRange {
  startDate?: Date
  endDate?: Date
}

export const identity = <T>(x: T): T => x

export const chunks = <T>(array: ReadonlyArray<T>, size: number): T[][] =>
  Array.from({ length: Math.ceil(array.length / size) }, (_v, i) => array.slice(i * size, i * size + size))

export const combineCSSClassNames = (...args: Array<string | false | undefined>): string =>
  args.filter(identity).join(' ')

export const getDaysInMonth = (date: Date): Date[] => {
  const startWeek = startOfWeek(startOfMonth(date))
  const endWeek = endOfWeek(endOfMonth(date))
  const days = []
  for (let curr = startWeek; isBefore(curr, endWeek); ) {
    days.push(curr)
    curr = addDays(curr, 1)
  }
  return days
}

export const isStartOfRange = ({ startDate }: DateRange, day: Date): boolean =>
  (!isUndefined(startDate) && isSameDay(day, startDate)) as boolean

export const isEndOfRange = ({ endDate }: DateRange, day: Date): boolean =>
  (!isUndefined(endDate) && isSameDay(day, endDate)) as boolean

export const inDateRange = ({ startDate, endDate }: DateRange, day: Date): boolean =>
  (startDate &&
    endDate &&
    (isWithinInterval(day, { start: startDate, end: endDate }) ||
      isSameDay(day, startDate) ||
      isSameDay(day, endDate))) as boolean

export const isRangeSameDay = ({ startDate, endDate }: DateRange): boolean => {
  if (startDate && endDate) {
    return isSameDay(startDate, endDate)
  }
  return false
}

type Falsy = false | null | undefined | 0 | ''

export const parseOptionalDate = (date: Date | Falsy, defaultValue: Date): Date => {
  if (date && isValid(date)) {
    return new Date(date)
  }
  return defaultValue
}

export const getValidatedMonths = (range: DateRange, minDate: Date, maxDate: Date): Array<Date | undefined> => {
  const { startDate, endDate } = range
  if (startDate && endDate) {
    const newStart = max([startDate, minDate])
    const newEnd = min([endDate, maxDate])

    return [newStart, isSameMonth(newStart, newEnd) ? addMonths(newStart, 1) : newEnd]
  }
  return [startDate, endDate]
}

export const isSameRange = (first: DateRange, second: DateRange): boolean => {
  const { startDate: fStart, endDate: fEnd } = first
  const { startDate: sStart, endDate: sEnd } = second
  if (fStart && sStart && fEnd && sEnd) {
    return isSameDay(fStart, sStart) && isSameDay(fEnd, sEnd)
  }
  return false
}
