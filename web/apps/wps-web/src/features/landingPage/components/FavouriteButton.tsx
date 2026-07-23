import PushPinIcon from '@mui/icons-material/PushPin'
import PushPinOutlinedIcon from '@mui/icons-material/PushPinOutlined'
import IconButton from '@mui/material/IconButton'
import Tooltip from '@mui/material/Tooltip'

interface FavouriteButtonProps {
  isFavourite: boolean
  onToggle: () => void
  toolName: string
}

const FavouriteButton = ({ isFavourite, onToggle, toolName }: FavouriteButtonProps) => {
  const action = isFavourite ? 'Remove' : 'Add'
  const label = `${action} ${toolName} ${isFavourite ? 'from' : 'to'} favourites`

  return (
    <Tooltip title={label} placement="right-end">
      <IconButton aria-label={label} color={isFavourite ? 'primary' : 'default'} onClick={onToggle} size="small">
        {isFavourite ? <PushPinIcon fontSize="small" /> : <PushPinOutlinedIcon fontSize="small" />}
      </IconButton>
    </Tooltip>
  )
}

export default FavouriteButton
