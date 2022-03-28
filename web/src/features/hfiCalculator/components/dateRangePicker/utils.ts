import {
  startOfWeek,
  startOfMonth,
  endOfWeek,
  endOfMonth,
  isBefore,
  addDays,
  isSameDay,
  isWithinRange,
  isSameMonth,
  addMonths,
  parse,
  isValid,
  min,
  max
} from 'date-fns'

// eslint-disable-next-line no-unused-vars
import { DateRange } from './types'

export const identity = <T>(x: T): T => x

export const chunks = <T>(array: ReadonlyArray<T>, size: number): T[][] =>
  Array.from({ length: Math.ceil(array.length / size) }, (_v, i) =>
    array.slice(i * size, i * size + size)
  )

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const combine = (...args: any[]): string => args.filter(identity).join(' ')

// Date
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
  (startDate && isSameDay(day, startDate)) as boolean

export const isEndOfRange = ({ endDate }: DateRange, day: Date): boolean =>
  (endDate && isSameDay(day, endDate)) as boolean

export const inDateRange = ({ startDate, endDate }: DateRange, day: Date): boolean =>
  (startDate &&
    endDate &&
    (isWithinRange(day, startDate, endDate) ||
      isSameDay(day, startDate) ||
      isSameDay(day, endDate))) as boolean

export const isRangeSameDay = ({ startDate, endDate }: DateRange): boolean => {
  if (startDate && endDate) {
    return isSameDay(startDate, endDate)
  }
  return false
}

type Falsy = false | null | undefined | 0 | ''

export const parseOptionalDate = (
  date: Date | string | Falsy,
  defaultValue: Date
): Date => {
  if (date) {
    const parsed = parse(date)
    if (isValid(parsed)) return parsed
  }
  return defaultValue
}

export const getValidatedMonths = (
  range: DateRange,
  minDate: Date,
  maxDate: Date
): Array<Date | undefined> => {
  const { startDate, endDate } = range
  if (startDate && endDate) {
    const newStart = max(startDate, minDate)
    const newEnd = min(endDate, maxDate)

    return [newStart, isSameMonth(newStart, newEnd) ? addMonths(newStart, 1) : newEnd]
  }
  return [startDate, endDate]
}
