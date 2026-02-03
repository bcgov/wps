import { PlayArrow } from '@mui/icons-material'
import { CircularProgress, IconButton, TextField } from '@mui/material'
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
  date: DateTime | null
  updateDate: React.Dispatch<React.SetStateAction<DateTime>>
  minimumDate: DateTime
  maximumDate: DateTime
  disabled?: boolean
}

function CustomDateTextField(props: Readonly<CustomDateTextFieldProps>) {
  const { internalProps, forwardedProps } = useSplitFieldProps(props, 'date')
  const { value } = internalProps
  const { date, updateDate, minimumDate, maximumDate, slotProps, InputProps, ...other } = forwardedProps
  const disabled = props.disabled
  const pickersContext = usePickersContext()
  const handleTogglePicker = (event: React.UIEvent) => {
    if (pickersContext.open) {
      pickersContext.onClose(event)
    } else {
      pickersContext.onOpen(event)
    }
  }

  const handleArrowButton = (value: number) => {
    if (!isNil(date)) {
      const newDate = date.plus({ days: value })
      updateDate(newDate)
    }
  }

  const renderStartAdornments = () => {
    return (
      <>
        <IconButton
          disabled={disabled || isNil(date) || minimumDate >= date.minus({ days: 1 })}
          onClick={() => handleArrowButton(-1)}
          sx={{ paddingLeft: 0, transform: 'rotate(180deg)' }}
        >
          <PlayArrow />
        </IconButton>
        <IconButton
          disabled={disabled || isNil(date) || date >= maximumDate}
          onClick={() => handleArrowButton(1)}
          sx={{ paddingLeft: 0 }}
        >
          <PlayArrow />
        </IconButton>
      </>
    )
  }

  const renderEndAdornments = () => {
    return (
      <IconButton aria-label="calendar" onClick={handleTogglePicker} disabled={disabled}>
        <CalendarIcon color="action" />
      </IconButton>
    )
  }

  return (
    <TextField
      {...other}
      disabled={disabled}
      value={
        isNil(value)
          ? 'No data available'
          : value.toLocaleString({ weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
      }
      InputProps={{
        ...InputProps,
        readOnly: true,
        startAdornment: renderStartAdornments(),
        endAdornment: renderEndAdornments(),
        sx: { cursor: disabled ? 'default' : 'pointer', '& *': { cursor: 'inherit' } }
      }}
    />
  )
}

interface ASADatePickerProps extends DatePickerProps<DateTime> {
  date: DateTime | null
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
  disabled,
  ...other
}: ASADatePickerProps) => {
  return (
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <DatePicker
        loading={isNil(date)}
        renderLoading={() => <CircularProgress />}
        label="Date of Interest"
        format="yyyy/MM/dd"
        maxDate={historicalMaxDate}
        minDate={historicalMinDate}
        disabled={disabled}
        onAccept={(newValue: DateTime | null) => {
          if (!isNull(newValue) && newValue.isValid) {
            updateDate(newValue)
          }
        }}
        slots={{ ...other.slots, field: CustomDateTextField }}
        slotProps={{
          ...other.slotProps,
          actionBar: { actions: ['today'] },
          field: {
            date,
            updateDate,
            minimumDate: currentYearMinDate,
            maximumDate: currentYearMaxDate
          } as any
        }}
        value={date}
      />
    </LocalizationProvider>
  )
}
export default React.memo(ASADatePicker)
