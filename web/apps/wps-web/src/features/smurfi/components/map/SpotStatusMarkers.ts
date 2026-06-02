import { SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { Icon } from 'ol/style'
import activeSpot from './styles/activeSpot.svg'
import archivedSpot from './styles/archivedSpot.svg'
import completeSpot from './styles/completeSpot.svg'
import pendingSpot from './styles/newSpotRequest.svg'
import pausedSpot from './styles/onHoldSpot.svg'

const SPOT_MARKER_SCALE = 0.65

export const statusToPath: Record<SpotRequestStatus, string> = {
  [SpotRequestStatus.REQUESTED]: pendingSpot,
  [SpotRequestStatus.STARTED]: activeSpot,
  [SpotRequestStatus.SUSPENDED]: pausedSpot,
  [SpotRequestStatus.COMPLETE]: completeSpot,
  [SpotRequestStatus.ARCHIVED]: archivedSpot
}

export const createSpotStatusIcon = (status: SpotRequestStatus, scale = SPOT_MARKER_SCALE, opacity = 1) =>
  new Icon({
    anchor: [0.5, 1],
    src: statusToPath[status],
    scale,
    opacity
  })
