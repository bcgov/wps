import React, { useEffect, useState } from 'react'
import Box from '@mui/material/Box'
import { LANDING_BACKGROUND_COLOUR } from 'app/theme'

interface ContentContainerProps {
  children: any
}

const ContentContainer: React.FunctionComponent<ContentContainerProps> = (props: ContentContainerProps) => {
  return <Box sx={{ bgcolor: LANDING_BACKGROUND_COLOUR, flex: 1 }}>{props.children}</Box>
}

export default ContentContainer
