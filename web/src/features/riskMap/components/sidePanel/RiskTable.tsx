import { DataGridPro, GridColDef, GridRowParams } from '@mui/x-data-grid-pro'

interface RiskTableProps {
  valueDetails: any[]
  open: boolean
}

const columns: GridColDef[] = [
  { field: 'id', headerName: 'ID', width: 100 },
  { field: 'name', headerName: 'Value', width: 130 },
  { field: 'closestDistance', headerName: 'Distance (km)', width: 130 },
  { field: 'closestBearing', headerName: 'Hotspot Direction', width: 10 },
  {
    field: 'risk',
    headerName: 'Risk',
    width: 130,
    valueFormatter: params => (params.value === 3 ? 'High Risk' : params.value === 2 ? 'Med Risk' : 'Low Risk')
  }
]

const getCompassDirection = (bearing: number) => {
  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  const index = Math.round((((bearing % 360) + 360) % 360) / 45)
  return directions[index]
}

const handleRowClick = (params: GridRowParams) => {
  const rowId = params.row.id
  console.log(rowId)
}

export const RiskTable = ({ open, valueDetails }: RiskTableProps) => {
  const res = valueDetails.map(item => {
    return {
      id: item.id,
      name: item.name,
      closestDistance: (item.distance / 1000).toPrecision(3),
      closestBearing: getCompassDirection(item.bearing),
      risk: item.distance / 1000 < 5 ? 3 : item.distance <= 10 ? 2 : 1
    }
  })

  return (
    <DataGridPro
      density="compact"
      rows={res}
      columns={columns}
      onRowClick={handleRowClick}
      initialState={{
        pagination: { paginationModel: { page: 0, pageSize: 5 } },
        sorting: {
          sortModel: [{ field: 'closestDistance', sort: 'asc' }]
        }
      }}
      pageSizeOptions={[5, 10]}
      sx={{ border: 0, overflow: 'auto' }}
    />
  )
}

export default RiskTable
