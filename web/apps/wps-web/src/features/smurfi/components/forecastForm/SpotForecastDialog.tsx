import CloseIcon from '@mui/icons-material/Close'
import { Dialog, DialogContent, DialogTitle, IconButton, Typography } from '@mui/material'
import { SpotRequestOutput } from '@wps/api/SMURFIAPI'
import SpotForecastForm from '@/features/smurfi/components/forecastForm/SpotForecastForm'

interface SpotForecastDialogProps {
  open: boolean
  spotRequest: SpotRequestOutput | null
  onClose: () => void
}

const SpotForecastDialog = ({ open, spotRequest, onClose }: SpotForecastDialogProps) => (
  <Dialog
    open={open}
    onClose={onClose}
    maxWidth="lg"
    fullWidth
    slotProps={{
      paper: {
        sx: {
          maxHeight: '90vh'
        }
      }
    }}
  >
    <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <Typography variant="h6">
        New Spot Forecast
        {spotRequest && ` - Spot ID: ${spotRequest.id}`}
      </Typography>
      <IconButton aria-label="close" onClick={onClose} size="small">
        <CloseIcon />
      </IconButton>
    </DialogTitle>
    <DialogContent dividers>
      {spotRequest && <SpotForecastForm spotRequest={spotRequest} onSubmitSuccess={onClose} />}
    </DialogContent>
  </Dialog>
)

export default SpotForecastDialog
