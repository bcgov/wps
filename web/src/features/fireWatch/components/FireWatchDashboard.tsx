import { RootState } from '@/app/rootReducer'
import { AppDispatch } from '@/app/store'
import DetailPanelContent from '@/features/fireWatch/components/DetailPanelContent'
import FireWatchDetailsModal from '@/features/fireWatch/components/FireWatchDetailsModal'
import {
  BurnStatusEnum,
  burnStatusFromString,
  BurnWatchRow,
  FireWatchBurnForecast
} from '@/features/fireWatch/interfaces'
import { fetchBurnForecasts, selectBurnForecasts, updateFireWatch } from '@/features/fireWatch/slices/burnForecastSlice'
import InfoIcon from '@mui/icons-material/Info'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'
import { Backdrop, Box, CircularProgress, Typography, useTheme } from '@mui/material'
import { DataGridPro, DataGridProProps, GridActionsCellItem, GridColDef } from '@mui/x-data-grid-pro'
import { FireWatchPrescriptionColors } from 'app/theme'
import { upperFirst } from 'lodash'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

const FireWatchDashboard = () => {
  const dispatch: AppDispatch = useDispatch()
  const burnForecasts = useSelector(selectBurnForecasts)
  const { loading: updateLoading } = useSelector((state: RootState) => state.burnForecasts)

  const theme = useTheme()
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedFireWatch, setSelectedFireWatch] = useState<FireWatchBurnForecast | null>(null)

  const getFireWatchDetails = (row: BurnWatchRow) => {
    const fireWatchID = row.id
    const fireWatch = burnForecasts.find(fireWatch => fireWatch.fireWatch.id === fireWatchID)
    if (fireWatch) {
      return fireWatch
    }
  }

  const handleOpenModal = (row: BurnWatchRow) => {
    const fireWatch = getFireWatchDetails(row)
    if (fireWatch) {
      setSelectedFireWatch(fireWatch)
    }
    setModalOpen(true)
  }

  const handleCloseModal = () => {
    setSelectedFireWatch(null)
    setModalOpen(false)
  }

  const columns: GridColDef<BurnWatchRow>[] = [
    {
      field: 'id',
      headerName: 'ID',
      width: 80
    },
    {
      field: 'title',
      headerName: 'Burn Name',
      width: 200
    },
    {
      field: 'fireCentre',
      headerName: 'Fire Centre',
      width: 140
    },
    {
      field: 'station',
      headerName: 'Weather Station',
      width: 180
    },
    {
      field: 'fuelType',
      headerName: 'Fuel Type',
      width: 100
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      type: 'singleSelect',
      valueOptions: Object.values(BurnStatusEnum),
      getOptionLabel: value => (typeof value === 'string' ? upperFirst(value) : String(value)),
      editable: true,
      cellClassName: 'editable-status-cell',
      renderCell: params => (
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <Typography sx={{ mr: 0.5 }}>{upperFirst(params.value)}</Typography>
          <KeyboardArrowDownIcon fontSize="small" color="action" sx={{ opacity: 0.7 }} />
        </Box>
      ),
      sortComparator: (a, b) => {
        const order = [BurnStatusEnum.ACTIVE, BurnStatusEnum.HOLD, BurnStatusEnum.COMPLETE, BurnStatusEnum.CANCELLED]
        return order.indexOf(a) - order.indexOf(b)
      }
    },
    {
      field: 'inPrescription',
      headerName: 'In Prescription',
      width: 120
    },
    {
      field: 'details',
      headerName: 'Details',
      type: 'actions',
      width: 80,
      getActions: (params: { row: BurnWatchRow }) => [
        <GridActionsCellItem
          key={params.row.id}
          icon={<InfoIcon />}
          label="View details"
          onClick={() => handleOpenModal(params.row)}
          showInMenu={false}
        />
      ]
    }
  ]

  useEffect(() => {
    dispatch(fetchBurnForecasts())
  }, [])

  const getDetailPanelContent = React.useCallback<NonNullable<DataGridProProps['getDetailPanelContent']>>(
    ({ row }) => <DetailPanelContent row={row} />,
    []
  )

  const processRowUpdate = (newRow: BurnWatchRow, oldRow: BurnWatchRow) => {
    const newStatus = burnStatusFromString(newRow.status)
    const oldStatus = oldRow.fireWatch.status

    const updatedRow: BurnWatchRow = {
      ...oldRow,
      ...newRow,
      fireWatch: {
        ...oldRow.fireWatch,
        ...newRow.fireWatch,
        status: newStatus
      }
    }

    // only dispatch if status changed
    if (newStatus !== oldStatus) {
      dispatch(updateFireWatch(updatedRow.fireWatch))
    }

    return updatedRow
  }

  return (
    <Box data-testid="fire-watch-dashboard" id="fire-watch-dashboard" sx={{ flexGrow: 1 }}>
      <Typography sx={{ padding: theme.spacing(2) }} variant="h4">
        Dashboard
      </Typography>
      <Backdrop open={updateLoading} sx={{ color: '#fff', zIndex: theme => theme.zIndex.drawer + 1 }}>
        <CircularProgress color="inherit" />
      </Backdrop>
      <Box sx={{ padding: theme.spacing(2) }}>
        <DataGridPro
          density="compact"
          getRowId={row => row.id}
          processRowUpdate={processRowUpdate}
          disableRowSelectionOnClick
          disableVirtualization
          hideFooter
          columns={columns}
          rows={burnForecasts}
          getDetailPanelContent={getDetailPanelContent}
          getDetailPanelHeight={() => 'auto'}
          getRowClassName={params => `in-prescription-${params.row.inPrescription}`}
          initialState={{
            sorting: {
              sortModel: [
                { field: 'status', sort: 'asc' }, // or 'desc'
                { field: 'id', sort: 'asc' }
              ]
            }
          }}
          sx={{
            '.in-prescription-all': {
              bgcolor: `${FireWatchPrescriptionColors.all.bgcolor} !important`,
              '&:hover': { bgcolor: `${FireWatchPrescriptionColors.all.hover} !important` }
            },
            '.in-prescription-hfi, .in-prescription-hfi.MuiDataGrid-cell--editing': {
              bgcolor: `${FireWatchPrescriptionColors.hfi.bgcolor} !important`,
              '&:hover': { bgcolor: `${FireWatchPrescriptionColors.hfi.hover} !important` }
            },
            '&.MuiDataGrid-root .in-prescription-no, &.MuiDataGrid-root .in-prescription-no.MuiDataGrid-cell--editing':
              {
                bgcolor: `${FireWatchPrescriptionColors.no.bgcolor} !important`
              }
          }}
        />
      </Box>
      <FireWatchDetailsModal open={modalOpen} onClose={handleCloseModal} selectedFireWatch={selectedFireWatch} />
    </Box>
  )
}

export default FireWatchDashboard
