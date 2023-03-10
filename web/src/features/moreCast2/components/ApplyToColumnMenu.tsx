import React from 'react'
import SaveIcon from '@mui/icons-material/Save'
import { Button, FormControl, Grid } from '@mui/material'
import { GridColDef } from '@mui/x-data-grid'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'
import { ModelChoices, DEFAULT_MODEL_TYPE, ModelType } from 'api/moreCast2API'

export interface ApplyFunctionMenuItemProps {
  testId?: string
  colDef: GridColDef | null
}

const ApplyToColumnMenu = ({ colDef }: ApplyFunctionMenuItemProps) => {
  const [selectedColumnModel, setSelectedColumnModel] = React.useState<ModelType>(DEFAULT_MODEL_TYPE)
  return (
    <FormControl size="medium">
      <Grid container direction={'column'} alignContent="center" alignItems={'center'} spacing={1} rowSpacing={1}>
        <Grid item>
          <WeatherModelDropdown
            label="Select model to apply to column"
            weatherModelOptions={ModelChoices}
            selectedModelType={selectedColumnModel}
            setSelectedModelType={setSelectedColumnModel}
          />
        </Grid>
        <Grid item>
          <Button
            variant="contained"
            data-testid={'apply-model-to-column-button'}
            startIcon={<SaveIcon />}
            onClick={() => {
              console.log('Applied')
            }}
          >
            Apply {selectedColumnModel} to {colDef ? colDef.headerName : 'column'}
          </Button>
        </Grid>
      </Grid>
    </FormControl>
  )
}

export default React.memo(ApplyToColumnMenu)
