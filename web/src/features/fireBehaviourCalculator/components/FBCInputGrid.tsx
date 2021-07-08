import { DataGrid, GridToolbar } from '@material-ui/data-grid'
import { GeoJsonStation } from 'api/stationAPI'
import React from 'react'
import { useState } from 'react'
import { FBCFuelType } from '../fuelTypes'

interface FBCInputGridProps {
  testId?: string
  stations: GeoJsonStation[]
  fuelTypes: Record<string, FBCFuelType>
}

interface GridMenuOption {
  label: string
  value: string | number
}

const FBCInputGrid = (props: FBCInputGridProps) => {
  // eslint-disable-next-line
  const [rowId, setRowId] = useState(1)
  const stationMenuOptions: GridMenuOption[] = props.stations.map(station => ({
    value: station.properties.code,
    label: `${station.properties.name} - ${station.properties.code}`
  }))

  const fuelTypeMenuOptions: GridMenuOption[] = Object.entries(props.fuelTypes).map(
    ([key, value]) => ({
      value: key,
      label: value.friendlyName
    })
  )
  // eslint-disable-next-line
  const [rows, setRows] = useState([
    {
      id: rowId,
      weatherStation: stationMenuOptions[0],
      fuelType: fuelTypeMenuOptions[0],
      grassCure: 0
    }
  ])
  return (
    <div style={{ display: 'flex', height: 350, width: '100%' }}>
      <div style={{ flexGrow: 1 }}>
        <DataGrid
          components={{
            Toolbar: GridToolbar
          }}
          rowHeight={30}
          columns={[
            {
              field: 'weatherStation',
              headerName: 'Weather Station',
              flex: 1,
              type: 'singleSelect',
              editable: true,
              valueOptions: stationMenuOptions
            },
            {
              field: 'fuelType',
              flex: 1,
              headerName: 'Fuel Type',
              type: 'singleSelect',
              editable: true,
              valueOptions: fuelTypeMenuOptions
            },
            {
              field: 'grassCure',
              headerName: 'Grass Cure %',
              flex: 1,
              type: 'number',
              editable: true
            }
          ]}
          rows={rows}
        />
      </div>
    </div>
  )
}

export default React.memo(FBCInputGrid)
