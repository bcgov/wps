import { theme } from '@/app/theme'
import { Box, Typography } from '@mui/material'

interface SummaryLineTextProps {
  indentLevel: number
  left: string
  right: string
  rightColor?: string
}

const SummaryTextLine = ({ indentLevel, left, right, rightColor }: SummaryLineTextProps) => {
  return (
    <Box sx={{ display: 'flex', pl: theme.spacing(2 * indentLevel) }}>
      <Typography component={'div'} variant="body1" fontStyle="italic">
        • {left}: &nbsp;
      </Typography>
      <Typography component={'div'} variant="body1" color={rightColor}>
        {right}
      </Typography>
    </Box>
  )
}

export default SummaryTextLine
