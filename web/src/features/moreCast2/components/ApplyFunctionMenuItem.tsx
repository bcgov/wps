import React from 'react'
import SaveIcon from '@mui/icons-material/Save'
import { Button, FormControl, Grid, MenuItem, Select, TextField } from '@mui/material'

export interface ApplyFunctionMenuItemProps {
  testId?: string
}

const ApplyFunctionMenuItem = (props: ApplyFunctionMenuItemProps) => {
  return (
    <FormControl size="small">
      <Grid container direction={'column'} alignContent="center" alignItems={'center'} spacing={1} rowSpacing={1}>
        <Grid item>
          <TextField
            size="small"
            type="number"
            id="number-input"
            label="Value"
            inputProps={{ min: 0, style: { textAlign: 'center', maxWidth: 100, minWidth: 100 } }}
          />
        </Grid>
        <Grid item>
          <Select id="select-operation" label="Operation" sx={{ maxWidth: 130, minWidth: 130, textAlign: 'center' }}>
            <MenuItem value={'+'}>+</MenuItem>
            <MenuItem value={'-'}>-</MenuItem>
            <MenuItem value={'*'}>*</MenuItem>
            <MenuItem value={'/'}>/</MenuItem>
          </Select>
        </Grid>
        <Grid item>
          <Button variant="contained" data-testid={'submit-forecast-button'} startIcon={<SaveIcon />}>
            Apply to column
          </Button>
        </Grid>
      </Grid>
    </FormControl>
  )
}

export default React.memo(ApplyFunctionMenuItem)
