import React from 'react'
import { Grid } from '@mui/material'
import { AddStationOptions, StationAdminRow } from 'features/hfiCalculator/components/stationAdmin/AddStationModal'
import { AdminHandlers } from 'features/hfiCalculator/components/stationAdmin/StationListAdmin'
import { AdminStationDropdown } from 'features/hfiCalculator/components/stationAdmin/AdminStationDropdown'
import { AdminFuelTypesDropdown } from 'features/hfiCalculator/components/stationAdmin/AdminFuelTypesDropdown'
import AdminRemoveButton from 'features/hfiCalculator/components/stationAdmin/AdminRemoveButton'

export interface StationFormProps {
  testId?: string
  adminRow: StationAdminRow
  planningAreaId: number
  addStationOptions?: AddStationOptions
  adminHandlers: AdminHandlers
}

export const StationForm = ({
  adminRow,
  addStationOptions,
  planningAreaId,
  adminHandlers
}: StationFormProps): JSX.Element => {
  return (
    <Grid container spacing={1} sx={{ pt: 1 }} data-testid={`pa-admin-station-${planningAreaId}-${adminRow.rowId}`}>
      <Grid item>
        <Grid container direction="row" spacing={1}>
          <Grid item>
            <AdminStationDropdown
              adminRow={adminRow}
              planningAreaId={planningAreaId}
              stationOptions={addStationOptions ? addStationOptions.stationOptions : []}
              handleEditStation={adminHandlers.handleEditStation}
            />
          </Grid>
          <Grid item>
            <AdminFuelTypesDropdown
              adminRow={adminRow}
              planningAreaId={planningAreaId}
              fuelTypes={addStationOptions ? addStationOptions.fuelTypeOptions : []}
              handleEditStation={adminHandlers.handleEditStation}
            />
          </Grid>
          <Grid item>
            <AdminRemoveButton
              adminRow={adminRow}
              planningAreaId={planningAreaId}
              handleRemoveStation={adminHandlers.handleRemoveStation}
            />
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  )
}

export default React.memo(StationForm)
