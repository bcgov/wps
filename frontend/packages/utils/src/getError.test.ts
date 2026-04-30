import { getErrorMessage } from './getError'

describe('hfiReadySlice', () => {
  describe('reducer', () => {
    it('should return correct error message', () => {
      const error = {
        response: {
          data: {
            detail: 'key details'
          }
        }
      }
      expect(getErrorMessage(error)).toBe('key details')
      const error2 = new Error('other type')
      expect(getErrorMessage(error2)).toBe('Error: other type')

      const error3 = 'some garbage'
      expect(getErrorMessage(error3)).toBe('some garbage')
    })
  })
})
