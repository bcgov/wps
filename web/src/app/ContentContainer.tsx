import React from 'react'
import Box from '@mui/material/Box'
import { LANDING_BACKGROUND_COLOUR } from 'app/theme'

interface ContentContainerProps {
  children: React.ReactNode
}

// A container that grows to fill available space that can be used to host arbitrary content. It will
// be used to host the tool cards or a complete application if we eventually display them within the
// landing page
const ContentContainer: React.FunctionComponent<ContentContainerProps> = (props: ContentContainerProps) => {
  return <Box sx={{ bgcolor: LANDING_BACKGROUND_COLOUR, flex: 1 }}>{props.children}</Box>
}

export default React.memo(ContentContainer)
