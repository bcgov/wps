import { Box } from "@mui/material"
import { DateTime } from "luxon"

interface SkillSelectionRowProps {
    date: DateTime
    deleteSelectedModel: (date:DateTime) => void
    model: string
}

const SkillSelectionRow = ({date, deleteSelectedModel, model}: SkillSelectionRowProps) => {
    return (
        <Box>
            chicken
        </Box>
    )
}