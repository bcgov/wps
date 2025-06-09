import React, { useState } from 'react'
import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'
import {
  BaseSingleInputFieldProps,
  DatePicker,
  DateFieldProps,
  DateValidationError,
  FieldSection,
  LocalizationProvider,
  UseDateFieldProps,
  useSplitFieldProps,
  usePickersContext,
  useValidation,
  validateDate,
  CalendarIcon,
  DatePickerFieldProps
} from '@mui/x-date-pickers'
import { useParsedFormat } from '@mui/x-date-pickers/hooks/useParsedFormat'
import { DateTime } from 'luxon'
import { isNil, isNull } from 'lodash'
import { IconButton, Stack, TextField } from '@mui/material'
import { KeyboardArrowLeft, KeyboardArrowRight } from '@mui/icons-material'

// interface CustomDatePickerTextFieldProps
//   extends UseDateFieldProps<DateTime, false>,
//     BaseSingleInputFieldProps<DateTime | null, DateTime, FieldSection, false, DateValidationError> {}

// const CustomDatePickerTextField = (props: CustomDatePickerTextFieldProps) => {
//   const {
//     label,
//     disabled,
//     readOnly,
//     id,
//     value,
//     onChange,
//     InputProps: { ref, startAdornment, endAdornment } = {},
//     inputProps
//   } = props

//   const mergeAdornments = (...adornments: React.ReactNode[]) => {
//     const nonNullAdornments = adornments.filter(el => el != null)
//     if (nonNullAdornments.length === 0) {
//       return null
//     }

//     if (nonNullAdornments.length === 1) {
//       return nonNullAdornments[0]
//     }

//     return (
//       <Stack direction="row">
//         {nonNullAdornments.map((adornment, index) => (
//           <React.Fragment key={index}>{adornment}</React.Fragment>
//         ))}
//       </Stack>
//     )
//   }

// const CustomDatePickerTextField = () => {
//   return (
//     <TextField
//       id={id}
//       disabled={disabled}
//       label={label}
//       inputProps={inputProps}
//       InputProps={{
//         startAdornment: mergeAdornments(startAdornment),
//         endAdornment: mergeAdornments(endAdornment)
//       }}
//     />
//   )
// }

interface CustomDateTextFieldProps extends DatePickerFieldProps<DateTime, false> {}

function CustomDateTextField(props: DatePickerFieldProps<DateTime, false>) {
  const { internalProps, forwardedProps } = useSplitFieldProps(props, 'date')
  const { value, timezone, format } = internalProps
  const { InputProps, slotProps, slots, ...other } = forwardedProps

  const pickersContext = usePickersContext()

  const parsedFormat = 'yyyy/MM/dd' //useParsedFormat(internalProps)

  const handleTogglePicker = (event: React.UIEvent) => {
    if (pickersContext.open) {
      pickersContext.onClose(event)
    } else {
      pickersContext.onOpen(event)
    }
  }

  const endAdornmments = () => {
    return (
      <>
        <IconButton onClick={handleTogglePicker}>
          <CalendarIcon color="action" />
        </IconButton>
        {/* <IconButton>
          <KeyboardArrowLeft />
        </IconButton> */}
        {/* <IconButton>
          <KeyboardArrowRight />
        </IconButton> */}
      </>
    )
  }

  return (
    <TextField
      {...other}
      value={isNil(value) ? '' : value}
      placeholder={parsedFormat}
      InputProps={{
        ...InputProps,
        // readOnly: true,
        // startAdornment: (
        //   <IconButton>
        //     <KeyboardArrowLeft />
        //   </IconButton>
        // ),
        endAdornment: endAdornmments(),
        sx: { cursor: 'pointer', '& *': { cursor: 'inherit' } }
      }}
    />
  )
}

interface WPSDatePickerProps {
  testId?: string
  label?: string
  size?: 'small' | 'medium'
  date: DateTime
  updateDate: (d: DateTime) => void
  minDate?: DateTime
  maxDate?: DateTime
}

const WPSDatePicker = (props: WPSDatePickerProps) => {
  const [selectedDate, setSelectedDate] = useState<DateTime | null>(props.date)

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      event.stopPropagation()
      if (selectedDate?.isValid) {
        props.updateDate(selectedDate)
      }
    }
  }

  let label = isNil(props.label) ? 'Date of Interest' : props.label

  return (
    <LocalizationProvider dateAdapter={AdapterLuxon}>
      <DatePicker
        label={label}
        format="yyyy/MM/dd"
        value={selectedDate}
        onAccept={(newValue: DateTime | null) => {
          if (!isNull(newValue) && newValue.isValid) {
            props.updateDate(newValue)
          }
        }}
        onChange={newValue => setSelectedDate(newValue)}
        slots={{
          textField: CustomDateTextField
        }}
      />
    </LocalizationProvider>
  )
}
export default React.memo(WPSDatePicker)
