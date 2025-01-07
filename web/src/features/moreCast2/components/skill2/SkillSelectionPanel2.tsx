import { Box, Typography } from '@mui/material'
import { DateTime } from 'luxon'
import { useSelector } from 'react-redux'
import { selectSelectedModelByDate } from '@/features/moreCast2/slices/selectedModelByDateSlice'
import SelectedModel2 from '@/features/moreCast2/components/skill2/SelectedModel2'

interface SkillSelectionPanel2Props {
  deleteSelectedModel: (date: DateTime) => void
}

const SkillSelectionPanel2 = ({ deleteSelectedModel }: SkillSelectionPanel2Props) => {
  const selectedModels = useSelector(selectSelectedModelByDate)
  return (
    <Box sx={{ borderTop: '1px solid #0e3366', flexDirection: 'column', padding: '32px' }}>
      <Typography fontWeight="bold">Selected Model</Typography>
      {selectedModels.map((selectedModel, index) => {
        return (
          <SelectedModel2
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

export default SkillSelectionPanel2
