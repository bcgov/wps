import { Chip, Tooltip } from '@mui/material'

interface ForecasterInitialsChipProps {
  forecasterName?: string | null
}

const getForecasterInitials = (forecasterName: string) => {
  const nameParts = forecasterName.trim().split(/\s+/).filter(Boolean)

  if (nameParts.length === 0) {
    return ''
  }

  if (nameParts.length === 1) {
    return nameParts[0].slice(0, 2).toUpperCase()
  }

  return `${nameParts[0][0]}${nameParts.at(-1)?.[0] ?? ''}`.toUpperCase()
}

const ForecasterInitialsChip = ({ forecasterName }: ForecasterInitialsChipProps) => {
  if (!forecasterName) {
    return null
  }

  const initials = getForecasterInitials(forecasterName)
  if (!initials) {
    return null
  }

  return (
    <Tooltip title={forecasterName}>
      <Chip label={initials} size="small" />
    </Tooltip>
  )
}

export default ForecasterInitialsChip
