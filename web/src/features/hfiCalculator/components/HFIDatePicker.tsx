import React from 'react'
import { createTheme, ThemeProvider } from '@material-ui/core/styles'

import { theme } from 'app/theme'
import DatePicker from 'components/DatePicker'

const hfiDateTheme = createTheme({
  overrides: {
    MuiOutlinedInput: {
      input: {
        padding: 10
      }
    },
    MuiFormLabel: {
      root: {
        color: theme.palette.primary.contrastText
      }
    },
    MuiInputBase: {
      input: {
        color: theme.palette.primary.contrastText
      }
    },
    MuiSvgIcon: {
      root: {
        color: theme.palette.primary.contrastText
      }
    }
  }
})
interface Props {
  dateOfInterest: string
  updateDate: (newDate: string) => void
}

export const HFIDatePicker: React.FunctionComponent<Props> = (props: Props) => {
  return (
    <ThemeProvider theme={hfiDateTheme}>
      <DatePicker date={props.dateOfInterest} updateDate={props.updateDate} />
    </ThemeProvider>
  )
}
