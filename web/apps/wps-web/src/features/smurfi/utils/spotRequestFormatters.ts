import { DateTime } from 'luxon'

const frequencyDays = [
  { value: 'Sunday', label: 'Su' },
  { value: 'Monday', label: 'M' },
  { value: 'Tuesday', label: 'Tu' },
  { value: 'Wednesday', label: 'W' },
  { value: 'Thursday', label: 'Th' },
  { value: 'Friday', label: 'F' },
  { value: 'Saturday', label: 'Sa' }
]

const weekdayValues = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
const weekendValues = ['Sunday', 'Saturday']

const hasSameDays = (selectedDays: Set<string>, expectedDays: string[]) =>
  selectedDays.size === expectedDays.length && expectedDays.every(day => selectedDays.has(day))

export const formatSpotRequestDate = (value: string | null | undefined) => {
  if (!value) {
    return null
  }

  const dateTime = DateTime.fromISO(value)
  return dateTime.isValid ? dateTime.toFormat('yyyy-MM-dd') : null
}

export const formatSpotRequestDateWithDay = (value: string | null | undefined) => {
  if (!value) {
    return null
  }

  const dateTime = DateTime.fromISO(value)
  return dateTime.isValid ? dateTime.toFormat('EEE yyyy-MM-dd') : null
}

export const formatSpotRequestDateTimeWithDay = (value: string | null | undefined) => {
  if (!value) {
    return null
  }

  const dateTime = DateTime.fromISO(value)
  return dateTime.isValid ? dateTime.toFormat('EEE yyyy-MM-dd HH:mm') : null
}

export const formatRequestFrequency = (days: string[] | null | undefined) => {
  if (!days?.length) {
    return '-'
  }

  const selectedDays = new Set(days)
  if (
    hasSameDays(
      selectedDays,
      frequencyDays.map(day => day.value)
    )
  ) {
    return 'Daily'
  }

  if (hasSameDays(selectedDays, weekdayValues)) {
    return 'Weekdays'
  }

  if (hasSameDays(selectedDays, weekendValues)) {
    return 'Weekends'
  }

  return frequencyDays
    .filter(day => selectedDays.has(day.value))
    .map(day => day.label)
    .join(' ')
}
