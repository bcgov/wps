import { Box, IconButton, Typography } from '@mui/material'
import { DateTime, DateTimeOptions } from 'luxon'
import { MORECAST_MODEL_COLORS } from 'app/theme'
import { toUpper } from 'lodash'
import { Close } from '@mui/icons-material'

interface SelectedModelProps {
  date: DateTime
  model: string
  deleteSelectedModel: (date: DateTime) => void
}

const SelectedModel = ({ date, deleteSelectedModel, model }: SelectedModelProps) => {
  return (
    <Box
      sx={{
        alignItems: 'center',
        backgroundColor: MORECAST_MODEL_COLORS[model.toLocaleLowerCase()].bg,
        border: `1px solid ${MORECAST_MODEL_COLORS[model.toLowerCase()].border}`,
        borderRadius: '5px',
        display: 'flex',
        margin: '8px',
        padding: '8px'
      }}
    >
      <Typography sx={{ flexGrow: 1 }}>
        {date.toLocaleString()}: {toUpper(model)}
      </Typography>
      <IconButton onClick={() => deleteSelectedModel(date)}>
        <Close fontSize="small" />
      </IconButton>
    </Box>
  )
}

export default SelectedModel
