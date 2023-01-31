import React from 'react'
import { TextField } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isNull } from 'lodash'

const useStyles = makeStyles({
  autocomplete: {
    width: '100%',
    color: 'white'
  },
  wrapper: {
    minWidth: 300
  },
  fireCentreTextField: {
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
  }
})

export interface Option {
  name: string
}

interface Props {
  className?: string
  selectedZoneID: number | null
}

const ZoneSummaryPanel = (props: Props) => {
  const classes = useStyles()

  if (isNull(props.selectedZoneID)) {
    return <div></div>
  } else {
    return (
      <div className={props.className}>
        <div className={classes.wrapper}>
          <TextField value={props.selectedZoneID} />
        </div>
      </div>
    )
  }
}

export default React.memo(ZoneSummaryPanel)
