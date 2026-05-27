import { Box, Button, Divider, Stack, Typography } from '@mui/material'

interface NewRequestPopupProps {
  onConfirm: () => void
  onCancel: () => void
}

const NewRequestPopup = ({ onConfirm, onCancel }: NewRequestPopupProps) => (
  <Box
    sx={{
      p: 2,
      background: 'white',
      border: '1px solid #ddd',
      borderRadius: 2,
      boxShadow: 3,
      minWidth: 280
    }}
  >
    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
      New Spot Request
    </Typography>
    <Divider sx={{ mb: 2 }} />
    <Typography variant="body2" sx={{ mb: 2, color: 'primary.main' }}>
      Create new spot request at this location?
    </Typography>
    <Stack direction="row" spacing={1} sx={{ justifyContent: 'flex-end' }}>
      <Button size="small" onClick={onCancel}>
        Cancel
      </Button>
      <Button variant="contained" size="small" onClick={onConfirm}>
        Confirm
      </Button>
    </Stack>
  </Box>
)

export default NewRequestPopup
