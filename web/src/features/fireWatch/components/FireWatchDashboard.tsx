import { RootState } from '@/app/rootReducer'
import { AppDispatch } from '@/app/store'
import DetailPanelContent from '@/features/fireWatch/components/DetailPanelContent'
import FireWatchDetailsModal from '@/features/fireWatch/components/FireWatchDetailsModal'
import { BurnStatusEnum, BurnWatchRow, FireWatchBurnForecast } from '@/features/fireWatch/interfaces'
import { fetchBurnForecasts, selectBurnForecasts, updateFireWatch } from '@/features/fireWatch/slices/burnForecastSlice'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import InfoIcon from '@mui/icons-material/Info'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'
import PauseCircleIcon from '@mui/icons-material/PauseCircle'
import CancelIcon from '@mui/icons-material/Cancel'
import PlayCircleIcon from '@mui/icons-material/PlayCircle'
import { Alert, Backdrop, Box, CircularProgress, Snackbar, Typography, useTheme } from '@mui/material'
import { DataGridPro, DataGridProProps, GridActionsCellItem, GridColDef } from '@mui/x-data-grid-pro'
import { FireWatchPrescriptionColors } from 'app/theme'
import { upperFirst } from 'lodash'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

const FireWatchDashboard = () => {
  const dispatch: AppDispatch = useDispatch()
  const burnForecasts = useSelector(selectBurnForecasts)
  const { loading: updateLoading, error: updateError } = useSelector((state: RootState) => state.burnForecasts)

  const theme = useTheme()
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedFireWatch, setSelectedFireWatch] = useState<FireWatchBurnForecast | null>(null)
  const [snackbarOpen, setSnackbarOpen] = useState(false)
  const [snackbarMsg, setSnackbarMsg] = useState('')

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

  const statusIconMap = {
    [BurnStatusEnum.ACTIVE]: <PlayCircleIcon sx={{ color: '#1976D280' }} titleAccess="Active" />,
    [BurnStatusEnum.HOLD]: <PauseCircleIcon sx={{ color: '#FE690080' }} titleAccess="Hold" />,
    [BurnStatusEnum.COMPLETE]: <CheckCircleIcon sx={{ color: '#8E24AC80' }} titleAccess="Complete" />,
    [BurnStatusEnum.CANCELLED]: <CancelIcon sx={{ color: '#75757580' }} titleAccess="Cancelled" />
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
      width: 140,
      type: 'singleSelect',
      valueOptions: Object.values(BurnStatusEnum),
      getOptionLabel: value => (typeof value === 'string' ? upperFirst(value) : String(value)),
      editable: true,
      cellClassName: 'editable-status-cell',
      renderCell: params => (
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          {statusIconMap[params.row.status] ?? null}
          <Typography sx={{ mx: 0.5, fontSize: 'inherit' }}>{upperFirst(params.value)}</Typography>
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

  const processRowUpdate = async (newRow: BurnWatchRow, oldRow: BurnWatchRow): Promise<BurnWatchRow> => {
    const newStatus = newRow.status
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

    if (newStatus !== oldStatus) {
      try {
        await dispatch(updateFireWatch(updatedRow.fireWatch))
        return updatedRow
      } catch (error) {
        setSnackbarOpen(true)
        setSnackbarMsg('Failed to update row status')
        // on error revert to oldRow
        return oldRow
      }
    }

    return oldRow
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
                { field: 'status', sort: 'asc' },
                { field: 'id', sort: 'asc' }
              ]
            }
          }}
          sx={{
            '.MuiDataGrid-row.in-prescription-all': {
              bgcolor: `${FireWatchPrescriptionColors.all.bgcolor}`,
              '&:hover': { bgcolor: `${FireWatchPrescriptionColors.all.hover}` }
            },
            '.MuiDataGrid-row.in-prescription-hfi': {
              bgcolor: `${FireWatchPrescriptionColors.hfi.bgcolor}`,
              '&:hover': { bgcolor: `${FireWatchPrescriptionColors.hfi.hover}` }
            },
            '&.MuiDataGrid-root .MuiDataGrid-row.in-prescription-no': {
              bgcolor: `${FireWatchPrescriptionColors.no.bgcolor}`
            }
          }}
        />
      </Box>
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={8000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity="error"
          sx={{ width: '100%' }}
          data-testid="snackbar-alert"
        >
          {snackbarMsg}
        </Alert>
      </Snackbar>
      <FireWatchDetailsModal open={modalOpen} onClose={handleCloseModal} selectedFireWatch={selectedFireWatch} />
    </Box>
  )
}

export default FireWatchDashboard
