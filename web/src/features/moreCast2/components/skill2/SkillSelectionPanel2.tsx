import {
  Alert,
  Box,
  Button,
  Paper,
  Snackbar,
  SnackbarCloseReason,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography
} from '@mui/material'
import { DateTime } from 'luxon'
import { useDispatch, useSelector } from 'react-redux'
import {
  selectedModelByDateChanged,
  selectSelectedModelByDate
} from '@/features/moreCast2/slices/selectedModelByDateSlice'
import SelectedModelRow from '@/features/moreCast2/components/skill2/SelectedModelRow'
import { SelectedModelByDate } from '@/features/moreCast2/interfaces'
import { AppDispatch } from '@/app/store'
import { useState } from 'react'

interface SkillSelectionPanel2Props {
  deleteSelectedModel: (date: DateTime) => void
}

const SkillSelectionPanel2 = ({ deleteSelectedModel }: SkillSelectionPanel2Props) => {
  const [open, setOpen] = useState<boolean>(false)
  const dispatch: AppDispatch = useDispatch()
  const selectedModels = useSelector(selectSelectedModelByDate)
  const handleSelectedModelChanged = (newModel: SelectedModelByDate) => {
    const newSelectedModels = [...selectedModels]
    const index = newSelectedModels.findIndex(selectedModel => selectedModel.date === newModel.date)
    if (index > -1) {
      newSelectedModels[index] = newModel
      dispatch(selectedModelByDateChanged(newSelectedModels))
    }
  }
  const handleClick = () => {
    setOpen(true)
  }
  const handleClose = (event?: React.SyntheticEvent | Event, reason?: SnackbarCloseReason) => {
    if (reason === 'clickaway') {
      return
    }

    setOpen(false)
  }
  return (
    <Box sx={{ display: 'flex', padding: '16px' }}>
      <Box>
        <TableContainer component={Paper} sx={{ width: '600px' }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>
                  <Typography fontWeight="bold">Date</Typography>
                </TableCell>
                <TableCell>
                  <Typography fontWeight="bold">Model</Typography>
                </TableCell>
                <TableCell>
                  <Typography fontWeight="bold">Adjustment</Typography>
                </TableCell>
                <TableCell>
                  <Typography fontWeight="bold">Action</Typography>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {selectedModels.map(selectedModel => {
                return (
                  <SelectedModelRow
                    deleteSelectedModel={deleteSelectedModel}
                    selectedModel={selectedModel}
                    updateSelectedModel={handleSelectedModelChanged}
                  />
                )
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
      <Button
        disabled={selectedModels.length === 0}
        size="small"
        onClick={handleClick}
        sx={{ height: '40px', marginLeft: '16px' }}
        variant="contained"
      >
        Apply to Morecast DataGrid
      </Button>
      <Snackbar
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        autoHideDuration={5000}
        onClose={handleClose}
        open={open}
      >
        <Alert onClose={handleClose} severity="success" sx={{ width: '100%' }} variant="filled">
          Morecast DataGrid successfully updated.
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default SkillSelectionPanel2
