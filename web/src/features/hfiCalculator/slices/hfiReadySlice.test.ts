import { ReadyPlanningAreaDetails } from 'api/hfiCalculatorAPI'
import hfiReadyReducer, {
  initialState,
  setHFIReadyStart,
  setHFIToggleReadyState,
  setHFIReadyFailed,
  setAllReadyStates
} from 'features/hfiCalculator/slices/hfiReadySlice'
import { DateTime } from 'luxon'

describe('hfiReadySlice', () => {
  describe('reducer', () => {
    const dummyError = 'an error'
    it('should be initialized with correct state', () => {
      expect(hfiReadyReducer(undefined, { type: undefined })).toEqual(initialState)
    })
    it('should set loading = true when fetchFuelTypesStart is called', () => {
      expect(hfiReadyReducer(initialState, setHFIReadyStart())).toEqual({
        ...initialState,
        loading: true
      })
    })
    it('should set a value for error state when fetchFuelTypesFailed is called', () => {
      expect(hfiReadyReducer(initialState, setHFIReadyFailed(dummyError)).error).not.toBeNull()
    })
    it('should set ready state details when first updated', () => {
      const newDetails: ReadyPlanningAreaDetails = {
        planning_area_id: 1,
        hfi_request_id: 1,
        ready: true,
        create_timestamp: DateTime.fromISO('2016-05-25T09:08:34.123'),
        create_user: 'test',
        update_timestamp: DateTime.fromISO('2017-05-25T09:08:34.123'),
        update_user: 'test'
      }
      const res = hfiReadyReducer(initialState, setHFIToggleReadyState(newDetails))
      expect(res.planningAreaReadyDetails['1'].planning_area_id).toBe(1)
      expect(res.planningAreaReadyDetails['1'].ready).toBe(true)
      expect(res.planningAreaReadyDetails['1'].create_timestamp).toEqual(DateTime.fromISO('2016-05-25T09:08:34.123'))
      expect(res.planningAreaReadyDetails['1'].update_timestamp).toEqual(DateTime.fromISO('2017-05-25T09:08:34.123'))
    })
    it('should update ready state details cumulatively', () => {
      const existingState = {
        loading: false,
        error: null,
        readyToggleSuccess: false,
        planningAreaReadyDetails: {
          '1': {
            planning_area_id: 1,
            hfi_request_id: 1,
            ready: true,
            create_timestamp: DateTime.fromISO('2016-05-25T09:08:34.123'),
            create_user: 'test',
            update_timestamp: DateTime.fromISO('2017-05-25T09:08:34.123'),
            update_user: 'test'
          }
        }
      }
      const newDetails: ReadyPlanningAreaDetails = {
        planning_area_id: 2,
        hfi_request_id: 2,
        ready: true,
        create_timestamp: DateTime.fromISO('2016-05-25T09:08:34.123'),
        create_user: 'test',
        update_timestamp: DateTime.fromISO('2017-05-25T09:08:34.123'),
        update_user: 'test'
      }
      const res = hfiReadyReducer(existingState, setHFIToggleReadyState(newDetails))
      expect(res.planningAreaReadyDetails['1'].planning_area_id).toBe(1)
      expect(res.planningAreaReadyDetails['1'].ready).toBe(true)
      expect(res.planningAreaReadyDetails['1'].create_timestamp).toEqual(DateTime.fromISO('2016-05-25T09:08:34.123'))
      expect(res.planningAreaReadyDetails['1'].update_timestamp).toEqual(DateTime.fromISO('2017-05-25T09:08:34.123'))

      expect(res.planningAreaReadyDetails['2'].planning_area_id).toBe(2)
      expect(res.planningAreaReadyDetails['2'].ready).toBe(true)
      expect(res.planningAreaReadyDetails['2'].create_timestamp).toEqual(DateTime.fromISO('2016-05-25T09:08:34.123'))
      expect(res.planningAreaReadyDetails['2'].update_timestamp).toEqual(DateTime.fromISO('2017-05-25T09:08:34.123'))
    })
    it('should set build ready state map for all ready states', () => {
      const newDetails: ReadyPlanningAreaDetails[] = [
        {
          planning_area_id: 1,
          hfi_request_id: 1,
          ready: true,
          create_timestamp: DateTime.fromISO('2016-05-25T09:08:34.123'),
          create_user: 'test',
          update_timestamp: DateTime.fromISO('2017-05-25T09:08:34.123'),
          update_user: 'test'
        },
        {
          planning_area_id: 2,
          hfi_request_id: 2,
          ready: true,
          create_timestamp: DateTime.fromISO('2019-05-25T09:08:34.123'),
          create_user: 'test',
          update_timestamp: DateTime.fromISO('2019-05-25T09:08:34.123'),
          update_user: 'test'
        }
      ]
      const res = hfiReadyReducer(initialState, setAllReadyStates(newDetails))
      expect(res.planningAreaReadyDetails['1'].planning_area_id).toBe(1)
      expect(res.planningAreaReadyDetails['1'].ready).toBe(true)
      expect(res.planningAreaReadyDetails['1'].create_timestamp).toEqual(DateTime.fromISO('2016-05-25T09:08:34.123'))
      expect(res.planningAreaReadyDetails['1'].update_timestamp).toEqual(DateTime.fromISO('2017-05-25T09:08:34.123'))

      expect(res.planningAreaReadyDetails['2'].planning_area_id).toBe(2)
      expect(res.planningAreaReadyDetails['2'].ready).toBe(true)
      expect(res.planningAreaReadyDetails['2'].create_timestamp).toEqual(DateTime.fromISO('2019-05-25T09:08:34.123'))
      expect(res.planningAreaReadyDetails['2'].update_timestamp).toEqual(DateTime.fromISO('2019-05-25T09:08:34.123'))
    })
  })
})
