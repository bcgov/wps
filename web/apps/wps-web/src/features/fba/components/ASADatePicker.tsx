import { PlayArrow } from '@mui/icons-material'
import { CircularProgress, IconButton, TextField } from '@mui/material'
import {
  CalendarIcon,
  DatePicker,
  DatePickerFieldProps,
  DatePickerProps,
  LocalizationProvider,
  usePickerContext,
  useSplitFieldProps
} from '@mui/x-date-pickers'
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'
import { isNil, isNull } from 'lodash'
import { DateTime } from 'luxon'
import React from 'react'

interface CustomDateTextFieldProps extends DatePickerFieldProps {
  date: DateTime | null
  updateDate: React.Dispatch<React.SetStateAction<DateTime>>
  minimumDate: DateTime
  maximumDate: DateTime
}

function CustomDateTextField(props: Readonly<CustomDateTextFieldProps>) {
  const { forwardedProps } = useSplitFieldProps(props, 'date')
  const { date, updateDate, minimumDate, maximumDate, ...other } = forwardedProps
  const pickerContext = usePickerContext<DateTime | null>()
  const disabled = pickerContext.disabled

  const handleTogglePicker = () => {
    pickerContext.setOpen(prev => !prev)
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
      label={pickerContext.label}
      value={
        isNil(pickerContext.value)
          ? 'No data available'
          : pickerContext.value.toLocaleString({ weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
      }
      slotProps={{
        input: {
          ref: pickerContext.triggerRef,
          readOnly: true,
          startAdornment: renderStartAdornments(),
          endAdornment: renderEndAdornments(),
          sx: { cursor: disabled ? 'default' : 'pointer', '& *': { cursor: 'inherit' } }
        }
      }}
    />
  )
}

interface ASADatePickerProps extends DatePickerProps {
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
        label={other.label ?? 'Date of Interest'}
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
        sx={{ ...other.sx }}
        value={date}
      />
    </LocalizationProvider>
  )
}
export default React.memo(ASADatePicker)
