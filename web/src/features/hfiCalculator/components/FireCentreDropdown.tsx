import React from 'react'
import { styled } from '@mui/material/styles'
import Autocomplete from '@mui/material/Autocomplete'
import { TextField } from '@mui/material'
import { FireCentre } from 'api/hfiCalculatorAPI'
import { isNull } from 'lodash'

const PREFIX = 'FireCentreDropdown'

const classes = {
  autocomplete: `${PREFIX}-autocomplete`,
  wrapper: `${PREFIX}-wrapper`,
  fireCentreTextField: `${PREFIX}-fireCentreTextField`,
  fireCentreTextFieldInput: `${PREFIX}-fireCentreTextFieldInput`
}

const Root = styled('div')({
  [`& .${classes.autocomplete}`]: {
    width: '100%',
    color: 'white'
  },
  [`& .${classes.wrapper}`]: {
    minWidth: 300
  },
  [`& .${classes.fireCentreTextField}`]: {
    color: 'white',
    '& .MuiAutocomplete-clearIndicator': {
      color: 'white'
    },
    '& .MuiAutocomplete-popupIndicator': {
      color: 'white'
    },
    '& .MuiAutocomplete-endAdornment': {
      right: -3,
      top: -3
    },
    '& .MuiInputLabel-root': {
      color: 'white'
    },
    '& .MuiOutlinedInput-root': {
      '& fieldset': {
        borderColor: 'white'
      },
      '&:hover fieldset': {
        borderColor: 'white'
      },
      '&.Mui-focused fieldset': {
        borderColor: 'white'
      }
    }
  },
  [`& .${classes.fireCentreTextFieldInput}`]: {
    color: 'white'
  }
})

export interface Option {
  name: string
}

interface Props {
  className?: string
  fireCentres: FireCentre[]
  selectedValue: Option | null
  onChange: (value: FireCentre | undefined) => void
}

const FireCentreDropdown = (props: Props) => {
  const allFireCentreOptions: Option[] = props.fireCentres.map((centre: FireCentre) => ({
    name: centre.name
  }))

  return (
    <Root className={props.className}>
      <div className={classes.wrapper}>
        <Autocomplete
          id="fire-centre-dropdown"
          className={classes.autocomplete}
          classes={{ inputRoot: classes.fireCentreTextFieldInput }}
          data-testid="fire-centre-dropdown"
          options={allFireCentreOptions}
          value={props.selectedValue}
          getOptionLabel={option => `${option.name}`}
          isOptionEqualToValue={(option, value) => option.name === value.name}
          onChange={(_, option) => {
            if (isNull(option)) {
              props.onChange(undefined)
            } else {
              const fc = Object.values(props.fireCentres).filter(record => record.name === option.name)[0]
              props.onChange(fc)
            }
          }}
          size="small"
          renderInput={params => (
            <TextField
              {...params}
              label="Fire Centre"
              variant="outlined"
              fullWidth
              size="small"
              className={classes.fireCentreTextField}
            />
          )}
        />
      </div>
    </Root>
  )
}

export default React.memo(FireCentreDropdown)
