import { Box } from '@mui/material'
import SkillChart from '@/features/moreCast2/components/skill/SkillChart'
import SkillStats from '@/features/moreCast2/components/skill/SkillStats'

const SkillPanel = () => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
      <SkillStats />
      <SkillChart />
    </Box>
  )
}

export default SkillPanel
