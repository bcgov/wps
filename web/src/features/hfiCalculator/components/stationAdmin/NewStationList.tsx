import React from 'react'
import { Grid } from '@mui/material'
import { AddStationOptions, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { AdminStationDropdown } from 'features/hfiCalculator/components/stationAdmin/AdminStationDropdown'
import { AdminFuelTypesDropdown } from 'features/hfiCalculator/components/stationAdmin/AdminFuelTypesDropdown'
import AdminRemoveButton from 'features/hfiCalculator/components/stationAdmin/AdminRemoveButton'

export interface NewStationListProps {
  testId?: string
  newStation: StationAdminRow
  planningAreaId: number
  addStationOptions?: AddStationOptions
  handleRemoveStation: (planningAreaId: number, rowId: number) => void
  handleEditStation: (planningAreaId: number, rowId: number, station: StationAdminRow) => void
}

export const NewStationList = ({
  newStation,
  addStationOptions,
  planningAreaId,
  handleRemoveStation,
  handleEditStation
}: NewStationListProps): JSX.Element => {
  return (
    <Grid
      container
      spacing={1}
      sx={{ pt: 1 }}
      data-testid={`new-pa-admin-station-${planningAreaId}-${newStation.rowId}`}
    >
      <Grid item>
        <Grid container direction="row" spacing={1}>
          <Grid item>
            <AdminStationDropdown
              testId={`added-station-dropdown-${planningAreaId}-${newStation.rowId}`}
              adminRow={newStation}
              planningAreaId={planningAreaId}
              stationOptions={addStationOptions ? addStationOptions.stationOptions : []}
              disabled={false}
              handleEditStation={handleEditStation}
            />
          </Grid>
          <Grid item>
            <AdminFuelTypesDropdown
              testId={`added-ft-dropdown-${planningAreaId}-${newStation.rowId}`}
              adminRow={newStation}
              planningAreaId={planningAreaId}
              fuelTypes={addStationOptions ? addStationOptions.fuelTypeOptions : []}
              disabled={false}
              handleEditStation={handleEditStation}
            />
          </Grid>
          <Grid item>
            <AdminRemoveButton
              adminRow={newStation}
              planningAreaId={planningAreaId}
              handleRemoveStation={handleRemoveStation}
            />
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  )
}

export default React.memo(NewStationList)
