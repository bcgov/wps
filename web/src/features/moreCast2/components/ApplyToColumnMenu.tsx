import React from 'react'
import SaveIcon from '@mui/icons-material/Save'
import { Button, FormControl, Grid, Menu, MenuItem } from '@mui/material'
import { GridColDef } from '@mui/x-data-grid'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'
import { ModelChoices, DEFAULT_MODEL_TYPE, ModelType, ModelChoice } from 'api/moreCast2API'
import { isNull } from 'lodash'

export interface ApplyFunctionMenuItemProps {
  testId?: string
  colDef: GridColDef | null
  contextMenu: {
    mouseX: number
    mouseY: number
  } | null
  updateColumnWithModel: (modelType: ModelType, colDef: GridColDef) => void
  handleClose: () => void
}

const ApplyToColumnMenu = ({ colDef, contextMenu, handleClose, updateColumnWithModel }: ApplyFunctionMenuItemProps) => {
  const [selectedColumnModel, setSelectedColumnModel] = React.useState<ModelType>(DEFAULT_MODEL_TYPE)
  return (
    <Menu
      open={contextMenu !== null}
      onClose={handleClose}
      anchorReference="anchorPosition"
      anchorPosition={contextMenu !== null ? { top: contextMenu.mouseY, left: contextMenu.mouseX } : undefined}
      slotProps={{
        root: {
          onContextMenu: e => {
            e.preventDefault()
            handleClose()
          }
        }
      }}
    >
      <MenuItem
        disableRipple
        sx={{
          '&:hover': {
            backgroundColor: 'transparent' // remove the background color on hover
          },
          '&.Mui-selected': {
            backgroundColor: 'transparent' // remove the background color when selected
          },
          '&.Mui-focusVisible': {
            backgroundColor: 'transparent' // remove the background color when fovused
          }
        }}
      >
        <FormControl>
          <Grid container direction={'column'} alignContent="center" alignItems={'center'} spacing={1} rowSpacing={1}>
            <Grid item>
              <WeatherModelDropdown
                label="Select model to apply to column"
                weatherModelOptions={ModelChoices.filter(model => model !== ModelChoice.MANUAL)}
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
                  if (!isNull(colDef)) {
                    updateColumnWithModel(selectedColumnModel, colDef)
                    handleClose()
                  }
                }}
              >
                Apply {selectedColumnModel} to {colDef ? colDef.headerName : 'column'}
              </Button>
            </Grid>
          </Grid>
        </FormControl>
      </MenuItem>
    </Menu>
  )
}

export default React.memo(ApplyToColumnMenu)
