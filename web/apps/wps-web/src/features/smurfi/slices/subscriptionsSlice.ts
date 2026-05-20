import { RootState } from '@/app/rootReducer'
import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { getSubscriptions, subscribeToSpot, unsubscribeFromSpot } from '@wps/api/SMURFIAPI'
import { AppThunk } from 'app/store'

export interface SubscriptionsState {
  subscribedIds: number[]
  loading: boolean
  error: string | null
}

const initialState: SubscriptionsState = {
  subscribedIds: [],
  loading: false,
  error: null
}

const subscriptionsSlice = createSlice({
  name: 'subscriptions',
  initialState,
  reducers: {
    fetchSubscriptionsStart(state: SubscriptionsState) {
      state.loading = true
      state.error = null
    },
    fetchSubscriptionsSuccess(state: SubscriptionsState, action: PayloadAction<number[]>) {
      state.subscribedIds = action.payload
      state.loading = false
    },
    fetchSubscriptionsFailed(state: SubscriptionsState, action: PayloadAction<string>) {
      state.error = action.payload
      state.loading = false
    },
    toggleSubscribedId(state: SubscriptionsState, action: PayloadAction<{ spotRequestId: number; status: string }>) {
      const { spotRequestId, status } = action.payload
      if (status === 'active') {
        if (!state.subscribedIds.includes(spotRequestId)) {
          state.subscribedIds.push(spotRequestId)
        }
      } else {
        state.subscribedIds = state.subscribedIds.filter(id => id !== spotRequestId)
      }
    }
  }
})

export const {
  fetchSubscriptionsStart,
  fetchSubscriptionsSuccess,
  fetchSubscriptionsFailed,
  toggleSubscribedId
} = subscriptionsSlice.actions

export default subscriptionsSlice.reducer

export const fetchSubscriptions = (): AppThunk => async dispatch => {
  try {
    dispatch(fetchSubscriptionsStart())
    const { spot_request_ids } = await getSubscriptions()
    dispatch(fetchSubscriptionsSuccess(spot_request_ids))
  } catch (err) {
    dispatch(fetchSubscriptionsFailed((err as Error).toString()))
  }
}

export const toggleSpotSubscription =
  (spotRequestId: number): AppThunk =>
  async (dispatch, getState) => {
    const isSubscribed = getState().subscriptions.subscribedIds.includes(spotRequestId)
    try {
      if (isSubscribed) {
        await unsubscribeFromSpot(spotRequestId)
        dispatch(toggleSubscribedId({ spotRequestId, status: 'inactive' }))
      } else {
        await subscribeToSpot(spotRequestId)
        dispatch(toggleSubscribedId({ spotRequestId, status: 'active' }))
      }
    } catch (err) {
      console.error('Failed to toggle subscription:', err)
      dispatch(fetchSubscriptionsFailed((err as Error).toString()))
    }
  }

export const selectSubscribedIds = (state: RootState) => state.subscriptions.subscribedIds
export const selectSubscriptionsLoading = (state: RootState) => state.subscriptions.loading
