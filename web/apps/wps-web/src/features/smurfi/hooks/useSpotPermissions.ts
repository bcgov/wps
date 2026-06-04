import { RootState } from '@/app/rootReducer'
import { ROLES } from '@/features/auth/roles'
import { SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { useSelector } from 'react-redux'

const useSpotPermissions = (spotRequest: SpotRequestOutput | undefined) => {
  const idir = useSelector((state: RootState) => state.authentication.idir)
  const roles = useSelector((state: RootState) => state.authentication.roles)

  const isOwner = !!idir && !!spotRequest && idir.toLowerCase() === spotRequest.requestor_idir?.toLowerCase()
  const isForecaster = roles.includes(ROLES.MORECAST_2.WRITE_FORECAST)
  const canChangeStatus = isOwner || isForecaster

  return { isOwner, isForecaster, canChangeStatus }
}

export default useSpotPermissions
