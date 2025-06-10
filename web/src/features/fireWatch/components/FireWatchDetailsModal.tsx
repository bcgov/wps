import CreateFireWatch from '@/features/fireWatch/components/CreateFireWatch'
import { FireWatchBurnForecast } from '@/features/fireWatch/interfaces'
import { Modal, Paper, Typography } from '@mui/material'
import { useTheme } from '@mui/system'

export interface FireWatchDetailsModalProps {
  open: boolean
  onClose: () => void
  selectedFireWatch: FireWatchBurnForecast | null
}

const FireWatchDetailsModal = ({ open, onClose, selectedFireWatch }: FireWatchDetailsModalProps) => {
  const theme = useTheme()

  return (
    <Modal open={open} onClose={onClose}>
      <Paper
        sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          padding: theme.spacing(4),
          width: 'auto',
          height: `calc(100vh - ${theme.spacing(8)})`,
          overflowY: 'auto'
        }}
      >
        <Typography variant="h6" gutterBottom>
          {selectedFireWatch ? selectedFireWatch.fireWatch.title : 'Fire Watch Details'}
        </Typography>
        {selectedFireWatch && (
          <CreateFireWatch fireWatch={selectedFireWatch.fireWatch} activeStep={5} onCloseModal={onClose} />
        )}
      </Paper>
    </Modal>
  )
}

export default FireWatchDetailsModal
