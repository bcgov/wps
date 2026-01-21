import { SpotAdminRow, SpotForecastStatus, SpotForecastStatusColorMap } from '@/features/smurfi/interfaces'
import EditIcon from '@mui/icons-material/Edit'
import { Box } from '@mui/material'
import { DataGridPro, GridActionsCellItem, GridColDef, GridRowId } from '@mui/x-data-grid-pro'
import { isNull } from 'lodash'
import { DateTime } from 'luxon'
import { useState } from 'react'

interface SpotManagementTableProps {
  spotAdminRows: SpotAdminRow[]
  selectedRowId: number | undefined
  setSelectedRowId: React.Dispatch<React.SetStateAction<number | undefined>>
}

const SpotManagementTable = ({ spotAdminRows, selectedRowId, setSelectedRowId }: SpotManagementTableProps) => {
  const [selectionModel, setSelectionModel] = useState<GridRowId[]>([])
  const selectRow = (id: number) => {
    setSelectionModel([id])
  }
  const columns: GridColDef<SpotAdminRow>[] = [
    {
      field: 'spot_id',
      headerName: 'Spot ID',
      width: 80
    },
    {
      field: 'fire_id',
      headerName: 'Fire ID',
      width: 100
    },
    {
      field: 'forecaster',
      headerName: 'Forecaster',
      width: 145
    },
    {
      field: 'fire_centre',
      headerName: 'Fire Centre',
      width: 120
    },
    {
      field: 'last_updated',
      headerName: 'Last Updated',
      width: 120,
      renderCell: params => {
        if (isNull(params.value)) {
          return 'n/a'
        }
        return <Box>{DateTime.fromMillis(params.value).toLocaleString()}</Box>
      }
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 100,
      renderCell: params => (
        <Box
          sx={{
            backgroundColor: SpotForecastStatusColorMap[params.value as SpotForecastStatus],
            borderRadius: '4px',
            alignItems: 'center',
            justifyContent: 'center',
            display: 'flex',
            flexGrow: 1,
            height: '100%',
            width: '100%'
          }}
        >
          {params.value}
        </Box>
      )
    },
    {
      field: 'details',
      headerName: 'Details',
      type: 'actions',
      width: 80,
      getActions: (params: { row: SpotAdminRow }) => [
        <GridActionsCellItem
          key={params.row.id}
          icon={<EditIcon />}
          label="View details"
          onClick={() => handleEditButtonClick(params.row)}
          showInMenu={false}
        />
      ]
    }
  ]

  const handleEditButtonClick = (row: SpotAdminRow) => {
    console.log(row)
  }

  const handleRowSelection = (row: SpotAdminRow) => {
    console.log(row)
    setSelectedRowId(row.id)
    setSelectionModel([row.id])
  }

  return (
    <Box sx={{ display: 'flex', flexGrow: 1, pr: 3 }}>
      <DataGridPro
        disableMultipleRowSelection={true}
        columns={columns}
        rows={spotAdminRows}
        rowSelectionModel={selectedRowId}
        onRowSelectionModelChange={newModel => setSelectionModel(newModel)}
        onRowClick={params => handleRowSelection(params.row)}
        sx={{ display: 'flex', flexGrow: 1 }}
      />
    </Box>
  )
}

export default SpotManagementTable
