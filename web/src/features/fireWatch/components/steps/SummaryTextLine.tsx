import { theme } from "@/app/theme"
import { Box, Typography } from "@mui/material"

interface SummaryLineTextProps {
    indentLevel: number
    left: string
    right: string
}

const SummaryTextLine = ({indentLevel, left, right}: SummaryLineTextProps) => {

  return (
    <Box sx={{display: 'flex', pl: theme.spacing(2 * indentLevel)}}>
      <Typography component={"div"} variant="body1" fontStyle="italic">
        • {left}: &nbsp;
      </Typography>
      <Typography component={"div"} variant="body1">
        { right }
      </Typography>
    </Box>
  )
}

export default SummaryTextLine