import { PlaylistAdd } from '@mui/icons-material'
import { Button, Checkbox, FormControlLabel, FormGroup, Popover, Stack, styled, Typography } from '@mui/material'
import { DARK_GREY, LIGHT_GREY, MEDIUM_GREY, type MoreCastParams } from '@wps/ui/theme'
import type { ColumnVis } from 'features/moreCast2/components/DataGridColumns'
import React, { type ChangeEvent, type MouseEvent, useState } from 'react'

interface GroupHeaderProps {
  id: string
  columns: ColumnVis[]
  weatherParam: keyof MoreCastParams
  handleShowHideChange: (weatherParam: keyof MoreCastParams, columnName: string, value: boolean) => void
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
  ':hover': {
    backgroundColor: LIGHT_GREY
  }
}))

const ShowHideCheckbox = styled(Checkbox)({
  '&.Mui-checked': {
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
      <Button sx={{ color: 'black' }} endIcon={<PlaylistAdd />} onClick={handleClick}>
        <Typography style={{ fontWeight: 'bold' }}>{id}</Typography>
      </Button>
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
            {columns?.map(column => {
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
