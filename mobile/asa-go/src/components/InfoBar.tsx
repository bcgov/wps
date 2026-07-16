import { Box, Typography, useTheme } from '@mui/material'
import { DateTime } from 'luxon'
import { StatusEnum } from '@/utils/constants'

interface StatusStyle {
  backgroundColor: string
  fontColor: string
  border: string
}

interface InfoBarProps {
  validUntil?: string | null
  viewingDate: DateTime
  status: StatusEnum
  Icon: string
  statusText?: string
}

const getValidUntilString = (validUntil?: string | null) => {
  if (!validUntil) {
    return 'n/a'
  }

  const validUntilDateTime = DateTime.fromISO(validUntil)
  if (!validUntilDateTime.isValid) {
    return 'n/a'
  }

  const today = DateTime.now().startOf('day')
  const validUntilDay = validUntilDateTime.startOf('day')

  if (validUntilDay.equals(today)) {
    return `${validUntilDateTime.toFormat('HH:mm')} Today`
  }

  if (validUntilDay.equals(today.plus({ days: 1 }))) {
    return `${validUntilDateTime.toFormat('HH:mm')} Tomorrow`
  }

  return validUntilDateTime.toFormat('MMM d, HH:mm')
}

const InfoBar = ({ validUntil, viewingDate, status, statusText, Icon }: InfoBarProps) => {
  const theme = useTheme()
  const message = `Viewing: ${viewingDate.toFormat('EEE, MMM d')}. Valid until: ${getValidUntilString(validUntil)}.`

  const statusMap: Record<StatusEnum, StatusStyle> = {
    [StatusEnum.INFO]: {
      backgroundColor: theme.palette.info.main,
      fontColor: 'black',
      border: theme.palette.info.dark
    },
    [StatusEnum.WARNING]: {
      backgroundColor: theme.palette.warning.main,
      fontColor: 'black',
      border: theme.palette.warning.dark
    }
  }

  return (
    <Box
      component="span"
      sx={{
        backgroundColor: statusMap[status].backgroundColor,
        color: statusMap[status].fontColor,
        padding: theme.spacing(0.5),
        display: 'inline-flex',
        alignItems: 'center',
        borderLeftColor: statusMap[status].border,
        borderLeftStyle: 'solid',
        borderLeftWidth: '4px'
      }}
    >
      <Box component="img" src={Icon} sx={{ color: statusMap[status].fontColor, px: theme.spacing(1) }} />
      {statusText && (
        <Typography component="span" variant="body2" sx={{ color: statusMap[status].fontColor }}>
          {`${statusText}\u00A0`}
        </Typography>
      )}
      <Typography component="span" variant="body2">
        {message}
      </Typography>
    </Box>
  )
}

export default InfoBar
