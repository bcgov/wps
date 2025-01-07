import { IconButton, TableCell, TableRow, TextField, Typography } from '@mui/material'
import { DateTime } from 'luxon'
import { MORECAST_MODEL_COLORS } from 'app/theme'
import { Close } from '@mui/icons-material'
import { SelectedModelByDate } from '@/features/moreCast2/interfaces'

interface SelectedModelRowProps {
  selectedModel: SelectedModelByDate
  updateSelectedModel: (newModel: SelectedModelByDate) => void
  deleteSelectedModel: (date: DateTime) => void
}

const SelectedModelRow = ({ selectedModel, deleteSelectedModel, updateSelectedModel }: SelectedModelRowProps) => {
  const handleSelectedModelChanged = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newModel = {
      adjustment: parseFloat(event.target.value),
      date: selectedModel.date,
      model: selectedModel.model,
      weatherParameter: selectedModel.weatherParameter
    }
    updateSelectedModel(newModel)
  }

  return (
    <TableRow
      sx={{
        backgroundColor: MORECAST_MODEL_COLORS[selectedModel.model.toLocaleLowerCase()].bg
      }}
    >
      <TableCell>
        <Typography sx={{ flexGrow: 1 }}>{selectedModel.date.toLocaleString()}</Typography>
      </TableCell>
      <TableCell>
        <Typography>{selectedModel.model.toUpperCase()}</Typography>
      </TableCell>
      <TableCell>
        <TextField
          type="number"
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
            handleSelectedModelChanged(event)
          }}
          size="small"
          sx={{ width: '75px' }}
          value={selectedModel.adjustment ?? 0.0}
        ></TextField>
      </TableCell>
      <TableCell>
        <IconButton onClick={() => deleteSelectedModel(selectedModel.date)}>
          <Close fontSize="small" />
        </IconButton>
      </TableCell>
    </TableRow>
  )
}

export default SelectedModelRow
