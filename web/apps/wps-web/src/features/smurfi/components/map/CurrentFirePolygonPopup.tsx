import { CurrentFireAttributes } from '@/features/currentFires/map/currentFireLayers'
import CloseIcon from '@mui/icons-material/Close'
import { Box, IconButton, Typography } from '@mui/material'

interface CurrentFirePolygonPopupProps {
  attributes: CurrentFireAttributes
  onClose: () => void
}

const formatValue = (value: string | number | null | undefined) => {
  if (value === null || value === undefined || value === '') {
    return '-'
  }
  return String(value)
}

const Field = ({ label, value }: { label: string; value: string | number | null | undefined }) => (
  <Box sx={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 1 }}>
    <Typography variant="body2" color="text.secondary">
      {label}
    </Typography>
    <Typography variant="body2">{formatValue(value)}</Typography>
  </Box>
)

const CurrentFirePolygonPopup = ({ attributes, onClose }: CurrentFirePolygonPopupProps) => (
  <Box
    sx={{
      p: 2,
      background: 'white',
      border: '1px solid #ddd',
      borderRadius: 2,
      boxShadow: 3,
      minWidth: 300
    }}
  >
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
        Current Fire
      </Typography>
      <IconButton aria-label="Close fire information" onClick={onClose} size="small">
        <CloseIcon fontSize="small" />
      </IconButton>
    </Box>
    <Field label="Fire Number" value={attributes.fireNumber} />
    <Field label="Size (ha)" value={attributes.fireSizeHectares} />
    <Field label="Status" value={attributes.fireStatus} />
    <Field label="Year" value={attributes.fireYear} />
  </Box>
)

export default CurrentFirePolygonPopup
