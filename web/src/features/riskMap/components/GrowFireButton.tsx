import WhatshotIcon from '@mui/icons-material/Whatshot'
import { Button } from '@mui/material'

interface ValuesImportButtonProps {
  growFire: () => Promise<void>
}

export const GrowFireButton = ({ growFire }: ValuesImportButtonProps) => {
  return (
    <Button variant="contained" component="label" startIcon={<WhatshotIcon />} onClick={() => growFire()}>
      Grow Fire
    </Button>
  )
}
