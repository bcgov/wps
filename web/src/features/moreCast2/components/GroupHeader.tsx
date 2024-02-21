import { Checkbox, FormControlLabel, FormGroup, IconButton, Popover, Stack, Typography, styled } from '@mui/material'
import { ExpandMore } from '@mui/icons-material'
import React, { ChangeEvent, MouseEvent, useState } from 'react'
import { LIGHT_GREY, MEDIUM_GREY, DARK_GREY, MorecastColors } from 'app/theme'
import { ColumnVis } from 'features/moreCast2/components/DataGridColumns'

interface GroupHeaderProps {
  id: string
  columns: ColumnVis[]
  weatherParam: keyof MorecastColors
  handleShowHideChange: (weatherParam: keyof MorecastColors, columnName: string, value: boolean) => void
}

const PopoverHeader = styled(Typography)(({ theme }) => ({
  backgroundColor: DARK_GREY,
  fontSize: '14px',
  fontWeight: 'bold',
  padding: theme.spacing(1)
}))

const PopoverFormControlLabel = styled(FormControlLabel)(({ theme }) => ({
  height: theme.spacing(4),
  marginRight: 0,
  paddingLeft: theme.spacing(1),
  [':hover']: {
    backgroundColor: LIGHT_GREY
  }
}))

const ShowHideCheckbox = styled(Checkbox)({
  ['&.Mui-checked']: {
    color: MEDIUM_GREY
  }
})

const GroupHeader = ({ id, columns, weatherParam, handleShowHideChange }: GroupHeaderProps) => {
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null)
  const open = Boolean(anchorEl)
  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleOnChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleShowHideChange(weatherParam, event.target.name, event.target.checked)
  }

  return (
    <>
      <Typography style={{ fontWeight: 'bold' }}>{id}</Typography>
      <IconButton onClick={handleClick}>
        <ExpandMore />
      </IconButton>
      <Popover
        id={id}
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Stack sx={{ overflow: 'hidden' }}>
          <PopoverHeader>Choose Models to Display</PopoverHeader>
          <FormGroup>
            {columns.map(column => {
              return (
                <PopoverFormControlLabel
                  control={
                    <ShowHideCheckbox
                      checked={column.visible}
                      name={column.columnName}
                      onChange={handleOnChange}
                      size="small"
                    />
                  }
                  key={column.columnName}
                  label={<Typography sx={{ fontSize: '12px' }}>{column.displayName}</Typography>}
                />
              )
            })}
          </FormGroup>
        </Stack>
      </Popover>
    </>
  )
}

export default React.memo(GroupHeader)
