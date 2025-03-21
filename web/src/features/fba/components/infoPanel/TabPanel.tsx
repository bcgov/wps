import { Box } from '@mui/material'
import React from 'react'
import { theme } from 'app/theme'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

const TabPanel = ({ children, index, value }: TabPanelProps) => {
  return (
    <div
      hidden={value !== index}
      id={`tabpanel-${index}`}
      data-testid={`tabpanel-${index}`}
      style={{ backgroundColor: theme.palette.common.white }}
    >
      {value === index && <Box border={'1px solid #ccc'}>{children}</Box>}
    </div>
  )
}

export default TabPanel
