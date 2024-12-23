import WhatshotIcon from '@mui/icons-material/Whatshot'
import { Button } from '@mui/material'

interface ValuesImportButtonProps {
  computeRisk: () => Promise<void>
}

export const ComputeRiskButton = ({ computeRisk }: ValuesImportButtonProps) => {
  return (
    <Button variant="contained" component="label" startIcon={<WhatshotIcon />} onClick={() => computeRisk()}>
      Compute Risk
    </Button>
  )
}
