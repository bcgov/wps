import { Button, FormControl, Grid, Menu, MenuItem } from '@mui/material'
import { ExpandMore } from '@mui/icons-material'
import SaveIcon from '@mui/icons-material/Save'
import React, { MouseEvent, useState } from 'react'
import { DEFAULT_MODEL_TYPE, ModelOptions, ModelType } from 'api/moreCast2API'
import WeatherModelDropdown from 'features/moreCast2/components/WeatherModelDropdown'
import { isNull } from 'lodash'
import { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'
import { GridColDef } from '@mui/x-data-grid-pro'

interface ForecastHeaderProps {
  colDef: Pick<GridColDef, 'field' | 'headerName'>
  columnClickHandlerProps: ColumnClickHandlerProps
}

const ForecastHeader = ({ colDef, columnClickHandlerProps }: ForecastHeaderProps) => {
  const title = colDef.headerName ? colDef.headerName : ''

  const [selectedColumnModel, setSelectedColumnModel] = React.useState<ModelType>(DEFAULT_MODEL_TYPE)
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null)

  const open = Boolean(anchorEl)
  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const isAForecastColumn = (): boolean => {
    return colDef.field.includes('Forecast')
  }

  return (
    <>
      <Button
        data-testid={`${colDef.field}-column-header`}
        endIcon={<ExpandMore />}
        onClick={handleClick}
        sx={{ color: 'black' }}
      >
        {'Forecast'}
      </Button>
      <Menu
        data-testid="apply-to-column-menu"
        open={isAForecastColumn() && open}
        onClose={handleClose}
        anchorReference="anchorEl"
        anchorEl={anchorEl}
        slotProps={{
          root: {
            onContextMenu: e => {
              e.preventDefault()
              columnClickHandlerProps.handleClose()
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
              backgroundColor: 'transparent' // remove the background color when focused
            }
          }}
        >
          <FormControl>
            <Grid container direction={'column'} alignContent="center" alignItems={'center'} spacing={1} rowSpacing={1}>
              <Grid item>
                <WeatherModelDropdown
                  label="Select model to apply to column"
                  weatherModelOptions={ModelOptions}
                  selectedModelType={selectedColumnModel}
                  setSelectedModelType={setSelectedColumnModel}
                />
              </Grid>
              <Grid item>
                <Button
                  data-testid="apply-model-to-column-button"
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={() => {
                    if (!isNull(columnClickHandlerProps.colDef)) {
                      columnClickHandlerProps.updateColumnWithModel(selectedColumnModel, columnClickHandlerProps.colDef)
                      columnClickHandlerProps.handleClose()
                    }
                  }}
                >
                  Apply {selectedColumnModel} to {title}
                </Button>
              </Grid>
            </Grid>
          </FormControl>
        </MenuItem>
      </Menu>
    </>
  )
}

export default React.memo(ForecastHeader)
