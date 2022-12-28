import React from 'react'
import SearchIcon from '@mui/icons-material/Search'
import Box from '@mui/material/Box'
import FormControl from '@mui/material/FormControl'
import IconButton from '@mui/material/IconButton'
import InputAdornment from '@mui/material/InputAdornment'
import OutlinedInput from '@mui/material/OutlinedInput'
import TextField from '@mui/material/TextField'
import makeStyles from '@mui/styles/makeStyles'
import { LANDING_BACKGROUND_COLOUR } from 'app/theme'

const searchHeight = 78

const useStyles = makeStyles(() => ({
  input: {
    position: 'absolute',
    top: '22px',
    width: '599px'
  },
  root: {
    backgroundColor: LANDING_BACKGROUND_COLOUR,
    display: 'flex',
    height: `${searchHeight}px`,
    justifyContent: 'center'
  }
}))

const Search: React.FunctionComponent = () => {
  const classes = useStyles()

  return (
    <Box className={classes.root}>
      <FormControl className={classes.input} variant="outlined">
        <OutlinedInput
          endAdornment={
            <InputAdornment position="end">
              <IconButton>
                <SearchIcon />
              </IconButton>
            </InputAdornment>
          }
          placeholder="Enter a keyword or phrase to search"
        />
      </FormControl>
    </Box>
  )
}

export default React.memo(Search)
