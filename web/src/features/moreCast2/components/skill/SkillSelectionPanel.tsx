import { Box, Typography } from '@mui/material'
import SelectedModel from '@/features/moreCast2/components/skill/SelectedModel'
import { DateTime } from 'luxon'
import { SelectedModelByDate } from '@/features/moreCast2/interfaces'

interface SkillSelectionPanelProps {
  deleteSelectedModel: (date: DateTime) => void
  selectedModels: SelectedModelByDate[]
}

const SkillSelectionPanel = ({ deleteSelectedModel, selectedModels }: SkillSelectionPanelProps) => {
  return (
    <Box sx={{ borderTop: '1px solid #0e3366', flex: 1, flexDirection: 'column', padding: '32px' }}>
      <Typography fontWeight="bold">Selected Model</Typography>
      {selectedModels.map((selectedModel, index) => {
        return (
          <SelectedModel
            date={selectedModel.date}
            deleteSelectedModel={deleteSelectedModel}
            model={selectedModel.model}
            key={index}
          />
        )
      })}
    </Box>
  )
}

export default SkillSelectionPanel
