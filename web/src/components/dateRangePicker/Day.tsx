import * as React from 'react'
import { styled } from '@mui/material/styles'
import { IconButton, Typography } from '@mui/material'
import { theme } from 'app/theme'
import { combineCSSClassNames } from 'components/dateRangePicker/utils'

const PREFIX = 'Day'

const classes = {
  leftBorderRadius: `${PREFIX}-leftBorderRadius`,
  rightBorderRadius: `${PREFIX}-rightBorderRadius`,
  buttonContainer: `${PREFIX}-buttonContainer`,
  button: `${PREFIX}-button`,
  buttonText: `${PREFIX}-buttonText`,
  outlined: `${PREFIX}-outlined`,
  filled: `${PREFIX}-filled`,
  highlighted: `${PREFIX}-highlighted`,
  contrast: `${PREFIX}-contrast`
}

const Root = styled('div')(() => ({
  [`& .${classes.leftBorderRadius}`]: {
    borderRadius: '50% 0 0 50%'
  },

  [`& .${classes.rightBorderRadius}`]: {
    borderRadius: '0 50% 50% 0'
  },

  [`&.${classes.buttonContainer}`]: {
    display: 'flex'
  },

  [`& .${classes.button}`]: {
    height: 36,
    width: 36,
    padding: 0
  },

  [`& .${classes.buttonText}`]: {
    lineHeight: 1.6
  },

  [`& .${classes.outlined}`]: {
    border: `1px solid ${theme.palette.primary.dark}`
  },

  [`& .${classes.filled}`]: {
    '&:hover': {
      backgroundColor: theme.palette.primary.dark
    },
    backgroundColor: theme.palette.primary.dark
  },

  [`& .${classes.highlighted}`]: {
    backgroundColor: theme.palette.action.hover
  },

  [`& .${classes.contrast}`]: {
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
  return (
    <Root
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
    </Root>
  )
}

export default Day
