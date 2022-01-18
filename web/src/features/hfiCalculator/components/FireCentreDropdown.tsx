import React from 'react'
import Autocomplete from '@material-ui/lab/Autocomplete'
import { TextField } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'
import { FireCentre } from 'api/hfiCalcAPI'

const useStyles = makeStyles({
  autocomplete: {
    width: '100%'
  },
  wrapper: {
    display: 'flex',
    alignItems: 'flex-start',
    minWidth: 300
  }
})

export interface Option {
  name: string
}

interface Props {
  className?: string
  fireCentres: Record<string, FireCentre>
}

const FireCentreDropdown = (props: Props) => {
  const classes = useStyles()

  const allFireCentreOptions: Option[] = Object.values(props.fireCentres).map(
    (centre: FireCentre) => ({ name: centre.name })
  )

  return (
    <div className={props.className}>
      <div className={classes.wrapper}>
        <Autocomplete
          id="fire-centre-dropdown"
          className={classes.autocomplete}
          data-testid="fire-centre-dropdown"
          options={allFireCentreOptions}
          getOptionLabel={option => `${option.name}`}
          getOptionSelected={(option, value) => option.name === value.name}
          size="small"
          renderInput={params => (
            <TextField
              {...params}
              label="Fire Centre"
              variant="outlined"
              fullWidth
              size="small"
            />
          )}
        />
      </div>
    </div>
  )
}

export default React.memo(FireCentreDropdown)
