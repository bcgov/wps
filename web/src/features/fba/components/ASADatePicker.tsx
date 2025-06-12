import { PlayArrow } from '@mui/icons-material'
import { IconButton, TextField } from '@mui/material'
import {
  BaseSingleInputFieldProps,
  CalendarIcon,
  DatePicker,
  DatePickerProps,
  DateValidationError,
  FieldSection,
  LocalizationProvider,
  UseDateFieldProps,
  usePickersContext,
  useSplitFieldProps
} from '@mui/x-date-pickers'
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'
import { isNil, isNull } from 'lodash'
import { DateTime } from 'luxon'
import React from 'react'

interface CustomDateTextFieldProps
  extends UseDateFieldProps<DateTime, false>,
    BaseSingleInputFieldProps<DateTime | null, DateTime, FieldSection, false, DateValidationError> {
  date: DateTime
  updateDate: React.Dispatch<React.SetStateAction<DateTime>>
  minimumDate: DateTime
  maximumDate: DateTime
}

function CustomDateTextField(props: Readonly<CustomDateTextFieldProps>) {
  const { internalProps, forwardedProps } = useSplitFieldProps(props, 'date')
  const { value } = internalProps
  const { date, updateDate, minimumDate, maximumDate, slotProps, InputProps, ...other } = forwardedProps
  const pickersContext = usePickersContext()
  const handleTogglePicker = (event: React.UIEvent) => {
    if (pickersContext.open) {
      pickersContext.onClose(event)
    } else {
      pickersContext.onOpen(event)
    }
  }

  const handleArrowButton = (value: number) => {
    const newDate = date.plus({ days: value })
    updateDate(newDate)
  }

  const renderStartAdornments = () => {
    return (
      <>
        <IconButton
          disabled={minimumDate >= date.minus({ days: 1 })}
          onClick={() => handleArrowButton(-1)}
          sx={{ paddingLeft: 0, transform: 'rotate(180deg)' }}
        >
          <PlayArrow />
        </IconButton>
        <IconButton disabled={date >= maximumDate} onClick={() => handleArrowButton(1)} sx={{ paddingLeft: 0 }}>
          <PlayArrow />
        </IconButton>
      </>
    )
  }

  const renderEndAdornments = () => {
    return (
      <IconButton aria-label="calendar" onClick={handleTogglePicker}>
        <CalendarIcon color="action" />
      </IconButton>
    )
  }

  return (
    <TextField
      {...other}
      value={
        isNil(value) ? '' : value.toLocaleString({ weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
      }
      InputProps={{
        ...InputProps,
        readOnly: true,
        startAdornment: renderStartAdornments(),
        endAdornment: renderEndAdornments(),
        sx: { cursor: 'pointer', '& *': { cursor: 'inherit' } }
      }}
    />
  )
}

interface ASADatePickerProps extends DatePickerProps<DateTime> {
  date: DateTime
  updateDate: (d: DateTime) => void
  currentYearMinDate?: DateTime
  currentYearMaxDate?: DateTime
  historicalMinDate?: DateTime
  historicalMaxDate?: DateTime
}

const ASADatePicker = ({
  date,
  currentYearMinDate,
  currentYearMaxDate,
  historicalMinDate,
  historicalMaxDate,
  updateDate,
  ...other
}: ASADatePickerProps) => {
  return (
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <DatePicker
        label="Date of Interest"
        format="yyyy/MM/dd"
        maxDate={historicalMaxDate}
        minDate={historicalMinDate}
        onAccept={(newValue: DateTime | null) => {
          if (!isNull(newValue) && newValue.isValid) {
            updateDate(newValue)
          }
        }}
        slots={{ ...other.slots, field: CustomDateTextField }}
        slotProps={{
          ...other.slotProps,
          actionBar: { actions: ['today'] },
          field: { date, updateDate, minimumDate: currentYearMinDate, maximumDate: currentYearMaxDate } as any
        }}
        value={date}
      />
    </LocalizationProvider>
  )
}
export default React.memo(ASADatePicker)

actionBar: {
  actions: ['today']
}