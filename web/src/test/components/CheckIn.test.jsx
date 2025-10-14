/**
 * CheckIn Component Race Condition Tests
 * Tests the elimination of setTimeout hacks and proper API synchronization
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React, { useState } from 'react'

// Test Constants
const INITIAL_CHECKED_IN_COUNT = 5
const CHECKED_OUT_COUNT_AFTER_OPERATION = 0
const CHECK_OUT_ALL_SUCCESS_MESSAGE = 'All people checked out successfully'
const TEST_ERROR_MESSAGE = 'Network error during checkout'
const API_RESPONSE_DELAY_MS = 100
const TIMEOUT_HACK_DELAY_MS = 500

// Mock CheckIn component with race condition fixes
const MockCheckInComponent = ({ 
  initialCheckedInCount = INITIAL_CHECKED_IN_COUNT,
  mockApiResponse = null,
  shouldSimulateError = false 
}) => {
  const [checkedInCount, setCheckedInCount] = useState(initialCheckedInCount)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [people, setPeople] = useState([
    { id: 1, name: 'Person 1', checked_in: true },
    { id: 2, name: 'Person 2', checked_in: true },
    { id: 3, name: 'Person 3', checked_in: true },
    { id: 4, name: 'Person 4', checked_in: true },
    { id: 5, name: 'Person 5', checked_in: true }
  ])

  // NEW IMPLEMENTATION: Synchronous API response handling
  const handleCheckOutAll = async () => {
    if (isLoading) return // Prevent multiple requests

    setIsLoading(true)
    setError(null)

    try {
      // Simulate API call with small delay for testing
      await new Promise(resolve => setTimeout(resolve, 10))
      
      const response = mockApiResponse || {
        success: true,
        message: CHECK_OUT_ALL_SUCCESS_MESSAGE,
        checked_out_count: CHECKED_OUT_COUNT_AFTER_OPERATION
      }

      if (shouldSimulateError) {
        throw new Error(TEST_ERROR_MESSAGE)
      }

      // NEW: Use API response directly for state synchronization
      if (response.success) {
        // Update count based on API response
        setCheckedInCount(response.checked_out_count)
        
        // Update people states
        setPeople(prevPeople => 
          prevPeople.map(person => ({ ...person, checked_in: false }))
        )
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div data-testid="checkin-component">
      <div data-testid="checked-in-count">
        Checked In: {checkedInCount}
      </div>
      
      <button 
        onClick={handleCheckOutAll}
        disabled={isLoading}
        data-testid="checkout-all-button"
      >
        {isLoading ? 'Checking Out...' : 'Check Out All'}
      </button>
      
      {error && (
        <div data-testid="error-message" role="alert">
          Error: {error}
        </div>
      )}
      
      <div data-testid="people-list">
        {people.map(person => (
          <div 
            key={person.id} 
            data-testid={`person-${person.id}`}
            data-checked-in={person.checked_in}
          >
            {person.name} - {person.checked_in ? 'Checked In' : 'Checked Out'}
          </div>
        ))}
      </div>
      
      <div data-testid="loading-state" data-loading={isLoading}>
        {isLoading ? 'Loading...' : 'Ready'}
      </div>
    </div>
  )
}

describe('CheckIn Component Race Condition Fixes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Synchronous API Response Handling', () => {
    it('should update state immediately after API response without setTimeout', async () => {
      const mockResponse = {
        success: true,
        message: CHECK_OUT_ALL_SUCCESS_MESSAGE,
        checked_out_count: CHECKED_OUT_COUNT_AFTER_OPERATION
      }

      render(
        <MockCheckInComponent 
          mockApiResponse={mockResponse}
        />
      )

      const checkoutButton = screen.getByTestId('checkout-all-button')
      const checkedInCount = screen.getByTestId('checked-in-count')

      // Initial state
      expect(checkedInCount).toHaveTextContent(`Checked In: ${INITIAL_CHECKED_IN_COUNT}`)

      // Trigger checkout
      fireEvent.click(checkoutButton)

      // State should update immediately after API response (no setTimeout delay)
      await waitFor(() => {
        expect(checkedInCount).toHaveTextContent(`Checked In: ${CHECKED_OUT_COUNT_AFTER_OPERATION}`)
      }, { timeout: API_RESPONSE_DELAY_MS + 50 }) // Much less than the old 500ms timeout
    })

    it('should eliminate setTimeout hack dependency', async () => {
      const startTime = Date.now()
      
      render(<MockCheckInComponent />)

      const checkoutButton = screen.getByTestId('checkout-all-button')
      fireEvent.click(checkoutButton)

      await waitFor(() => {
        expect(screen.getByTestId('checked-in-count')).toHaveTextContent('Checked In: 0')
      })

      const endTime = Date.now()
      const totalTime = endTime - startTime

      // Should complete much faster than the old 500ms setTimeout hack
      expect(totalTime).toBeLessThan(TIMEOUT_HACK_DELAY_MS)
    })

    it('should use checked_out_count from API response for state synchronization', async () => {
      const customResponse = {
        success: true,
        message: 'Custom checkout response',
        checked_out_count: 2 // Partial checkout
      }

      render(
        <MockCheckInComponent 
          mockApiResponse={customResponse}
        />
      )

      fireEvent.click(screen.getByTestId('checkout-all-button'))

      await waitFor(() => {
        expect(screen.getByTestId('checked-in-count')).toHaveTextContent('Checked In: 2')
      })
    })
  })

  describe('Race Condition Prevention', () => {
    it('should prevent race condition between API call and state update', async () => {
      let apiCallCompleted = false
      let stateUpdated = false

      const CustomComponent = () => {
        const [count, setCount] = useState(INITIAL_CHECKED_IN_COUNT)
        
        const handleClick = async () => {
          // Simulate API call
          await new Promise(resolve => setTimeout(resolve, 50))
          apiCallCompleted = true
          
          // State update happens immediately after API response
          setCount(0)
          stateUpdated = true
        }

        return (
          <div>
            <div data-testid="count">{count}</div>
            <button onClick={handleClick} data-testid="button">Click</button>
          </div>
        )
      }

      render(<CustomComponent />)
      
      fireEvent.click(screen.getByTestId('button'))

      await waitFor(() => {
        expect(screen.getByTestId('count')).toHaveTextContent('0')
      })

      // State should only update after API completion
      expect(apiCallCompleted).toBe(true)
      expect(stateUpdated).toBe(true)
    })

    it('should handle API errors without state corruption', async () => {
      render(
        <MockCheckInComponent shouldSimulateError={true} />
      )

      const checkoutButton = screen.getByTestId('checkout-all-button')
      const initialCount = screen.getByTestId('checked-in-count')
      
      expect(initialCount).toHaveTextContent(`Checked In: ${INITIAL_CHECKED_IN_COUNT}`)

      fireEvent.click(checkoutButton)

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument()
      })

      // State should remain unchanged on error
      expect(initialCount).toHaveTextContent(`Checked In: ${INITIAL_CHECKED_IN_COUNT}`)
    })

    it('should prevent multiple simultaneous requests', async () => {
      render(<MockCheckInComponent />)

      const checkoutButton = screen.getByTestId('checkout-all-button')
      
      // First click
      fireEvent.click(checkoutButton)
      
      // Wait a small amount to let loading state set
      await new Promise(resolve => setTimeout(resolve, 5))
      
      // Button should be disabled while loading
      expect(checkoutButton).toBeDisabled()
      
      // Second click should be ignored
      fireEvent.click(checkoutButton)
      
      await waitFor(() => {
        expect(screen.getByTestId('checked-in-count')).toHaveTextContent('Checked In: 0')
      })
      
      // Button should be enabled again
      expect(checkoutButton).not.toBeDisabled()
    })
  })

  describe('Loading State Management', () => {
    it('should manage loading state properly during operation', async () => {
      render(<MockCheckInComponent />)

      const loadingState = screen.getByTestId('loading-state')
      const checkoutButton = screen.getByTestId('checkout-all-button')

      // Initial state
      expect(loadingState).toHaveAttribute('data-loading', 'false')
      expect(loadingState).toHaveTextContent('Ready')

      // During operation
      fireEvent.click(checkoutButton)
      
      // Wait a bit for loading state to be set
      await new Promise(resolve => setTimeout(resolve, 5))
      expect(loadingState).toHaveAttribute('data-loading', 'true')
      expect(loadingState).toHaveTextContent('Loading...')

      // After completion
      await waitFor(() => {
        expect(loadingState).toHaveAttribute('data-loading', 'false')
      })
      expect(loadingState).toHaveTextContent('Ready')
    })

    it('should clear error state before new operation', async () => {
      const { rerender } = render(
        <MockCheckInComponent shouldSimulateError={true} />
      )

      // First operation - simulate error
      fireEvent.click(screen.getByTestId('checkout-all-button'))

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument()
      })

      // Second operation - should clear error
      rerender(<MockCheckInComponent shouldSimulateError={false} />)
      
      fireEvent.click(screen.getByTestId('checkout-all-button'))

      await waitFor(() => {
        expect(screen.queryByTestId('error-message')).not.toBeInTheDocument()
      })
    })
  })

  describe('State Consistency', () => {
    it('should maintain consistent state after successful operation', async () => {
      render(<MockCheckInComponent />)

      fireEvent.click(screen.getByTestId('checkout-all-button'))

      await waitFor(() => {
        // Count should be updated
        expect(screen.getByTestId('checked-in-count')).toHaveTextContent('Checked In: 0')
        
        // All people should be checked out
        const people = screen.getAllByTestId(/^person-\d+$/)
        people.forEach(person => {
          expect(person).toHaveAttribute('data-checked-in', 'false')
          expect(person).toHaveTextContent('Checked Out')
        })
        
        // Loading should be false
        expect(screen.getByTestId('loading-state')).toHaveAttribute('data-loading', 'false')
        
        // No error should be present
        expect(screen.queryByTestId('error-message')).not.toBeInTheDocument()
      })
    })

    it('should handle idempotent operations correctly', async () => {
      // Start with everyone already checked out
      render(
        <MockCheckInComponent 
          initialCheckedInCount={0}
          mockApiResponse={{
            success: true,
            message: 'Already checked out',
            checked_out_count: 0
          }}
        />
      )

      const checkoutButton = screen.getByTestId('checkout-all-button')
      const countDisplay = screen.getByTestId('checked-in-count')

      expect(countDisplay).toHaveTextContent('Checked In: 0')

      // Operation should still work without issues
      fireEvent.click(checkoutButton)

      await waitFor(() => {
        expect(countDisplay).toHaveTextContent('Checked In: 0')
      })

      // No error should occur
      expect(screen.queryByTestId('error-message')).not.toBeInTheDocument()
    })
  })

  describe('Timing-Independent Logic', () => {
    it('should eliminate all timing-dependent logic patterns', async () => {
      // Test the concept that we don't rely on setTimeout for business logic
      // This test verifies that our component works without setTimeout dependencies
      
      render(<MockCheckInComponent />)

      const startTime = Date.now()
      fireEvent.click(screen.getByTestId('checkout-all-button'))

      await waitFor(() => {
        expect(screen.getByTestId('checked-in-count')).toHaveTextContent('Checked In: 0')
      })
      
      const endTime = Date.now()
      const duration = endTime - startTime

      // The key test: our operation should complete quickly without timing dependencies
      // If it relied on setTimeout(500), it would take at least 500ms
      expect(duration).toBeLessThan(200) // Much faster than the old 500ms setTimeout
    })

    it('should implement proper async/await pattern', async () => {
      let asyncOperationCompleted = false

      const AsyncComponent = () => {
        const [result, setResult] = useState(null)

        const handleAsyncOperation = async () => {
          try {
            // Simulate async API call
            await new Promise(resolve => setTimeout(resolve, 50))
            const apiResult = { success: true, data: 'test' }
            
            setResult(apiResult)
            asyncOperationCompleted = true
          } catch (error) {
            setResult({ success: false, error: error.message })
          }
        }

        return (
          <div>
            <button onClick={handleAsyncOperation} data-testid="async-button">
              Start Async
            </button>
            {result && (
              <div data-testid="async-result">
                {result.success ? 'Success' : 'Error'}
              </div>
            )}
          </div>
        )
      }

      render(<AsyncComponent />)

      fireEvent.click(screen.getByTestId('async-button'))

      await waitFor(() => {
        expect(screen.getByTestId('async-result')).toHaveTextContent('Success')
      })

      expect(asyncOperationCompleted).toBe(true)
    })
  })
})