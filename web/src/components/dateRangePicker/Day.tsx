import * as React from 'react'
import { IconButton, Typography } from '@mui/material'
import { theme } from 'app/theme'
import makeStyles from '@mui/styles/makeStyles'
import { combineCSSClassNames } from 'components/dateRangePicker/utils'

const useStyles = makeStyles(() => ({
  leftBorderRadius: {
    borderRadius: '50% 0 0 50%'
  },
  rightBorderRadius: {
    borderRadius: '0 50% 50% 0'
  },
  buttonContainer: {
    display: 'flex'
  },
  button: {
    height: 36,
    width: 36,
    padding: 0
  },
  buttonText: {
    lineHeight: 1.6
  },
  outlined: {
    border: `1px solid ${theme.palette.primary.dark}`
  },
  filled: {
    '&:hover': {
      backgroundColor: theme.palette.primary.dark
    },
    backgroundColor: theme.palette.primary.dark
  },
  highlighted: {
    backgroundColor: theme.palette.action.hover
  },
  contrast: {
    color: theme.palette.primary.contrastText
  }
}))

interface DayProps {
  testId?: string
  filled?: boolean
  outlined?: boolean
  highlighted?: boolean
  disabled?: boolean
  startOfRange?: boolean
  endOfRange?: boolean
  onClick?: () => void
  onHover?: () => void
  value: number | string
}

const Day: React.FunctionComponent<DayProps> = ({
  testId,
  startOfRange,
  endOfRange,
  disabled,
  highlighted,
  outlined,
  filled,
  onClick,
  onHover,
  value
}: DayProps) => {
  const classes = useStyles()

  return (
    <div
      data-testid={testId}
      className={combineCSSClassNames(
        classes.buttonContainer,
        startOfRange && classes.leftBorderRadius,
        endOfRange && classes.rightBorderRadius,
        !disabled && highlighted && classes.highlighted
      )}
    >
      <IconButton
        className={combineCSSClassNames(
          classes.button,
          !disabled && outlined && classes.outlined,
          !disabled && filled && classes.filled
        )}
        disabled={disabled}
        onClick={onClick}
        onMouseOver={onHover}
        size="large"
      >
        <Typography
          color={!disabled ? 'textPrimary' : 'textSecondary'}
          className={combineCSSClassNames(classes.buttonText, !disabled && filled && classes.contrast)}
          variant="body2"
        >
          {value}
        </Typography>
      </IconButton>
    </div>
  )
}

export default Day
