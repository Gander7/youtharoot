import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import React from 'react'
import MessageHistory from '../../components/MessageHistory'

// Mock child components
vi.mock('../../components/SimplePhoneInput', () => ({
  default: vi.fn(({ value, onChange, ...props }) => (
    <input 
      data-testid="simple-phone-input"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      {...props}
    />
  ))
}))

// Mock API
vi.mock('../../stores/auth', () => ({
  apiRequest: vi.fn()
}))

// Import the mocked function
import { apiRequest } from '../../stores/auth'

describe('MessageHistory Component', () => {
  const mockProps = {
    refreshTrigger: 0
  }

  const mockMessages = [
    {
      id: 1,
      content: 'Test message 1',
      group_id: 1,
      group_name: 'Test Group',
      created_at: '2024-01-01T12:00:00Z',
      status: 'delivered',
      twilio_sid: 'SM123456',
      delivered_at: '2024-01-01T12:01:00Z',
      delivery_info: {
        delivered_at: '2024-01-01T12:01:00Z',
        error: null
      }
    },
    {
      id: 2,
      content: 'Test message 2',
      recipient_phone: '+1234567890',
      created_at: '2024-01-01T13:00:00Z',
      status: 'sent',
      twilio_sid: 'SM789012'
    }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    // Mock both groups and messages API calls
    apiRequest.mockImplementation((url) => {
      if (url === '/groups') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { id: 1, name: 'Test Group' },
            { id: 2, name: 'Another Group' }
          ])
        });
      }
      if (url.startsWith('/api/sms/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            messages: mockMessages,
            total: 2,
            page: 1,
            pages: 1
          })
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      });
    });
  })

  it('should render without crashing', () => {
    render(<MessageHistory {...mockProps} />)
    expect(screen.getByText('Message History')).toBeInTheDocument()
  })

  it('should display loading state initially', () => {
    render(<MessageHistory {...mockProps} />)
    expect(screen.getByTestId('circularprogress')).toBeInTheDocument()
  })

  it('should load and display messages', async () => {
    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Test message 1')).toBeInTheDocument()
      expect(screen.getByText('Test message 2')).toBeInTheDocument()
    })
  })

  it('should display group indicator for group messages', async () => {
    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      // Look for the group icon which indicates a group message
      expect(screen.getByTestId('group')).toBeInTheDocument()
      // Verify the group name appears in a message context (not just the filter)
      const groupMessages = screen.getAllByText('Test Group')
      expect(groupMessages.length).toBeGreaterThan(1) // Should appear both in filter and message
    })
  })

  it('should display individual indicator for non-group messages', async () => {
    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('+1234567890')).toBeInTheDocument()
    })
  })

  it('should display formatted timestamps', async () => {
    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText(/Sent: 1\/1\/2024, 8:00:00 AM/)).toBeInTheDocument()
    })
  })

  it('should display status chips', async () => {
    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('delivered')).toBeInTheDocument()
      expect(screen.getByText('sent')).toBeInTheDocument()
    })
  })

  it('should filter messages by group', async () => {
    render(<MessageHistory {...mockProps} />)
    
    // Wait for messages to load
    await waitFor(() => {
      expect(screen.getByText('Test message 1')).toBeInTheDocument()
    })

    // Open group filter
    const selects = screen.getAllByTestId('select')
    const groupSelect = selects[0] // First select is the group filter
    fireEvent.change(groupSelect, { target: { value: '1' } })

    // Check if API was called with filter
    expect(apiRequest).toHaveBeenCalledWith('/api/sms/history?page=1&limit=10&group_id=1')
  })

  it('should filter messages by status', async () => {
    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Test message 1')).toBeInTheDocument()
    })

    const selects = screen.getAllByTestId('select')
    const statusSelect = selects[1] // Second select is the status filter
    fireEvent.change(statusSelect, { target: { value: 'delivered' } })

    expect(apiRequest).toHaveBeenCalledWith('/api/sms/history?page=1&limit=10&status=delivered')
  })

  it('should search messages by content', async () => {
    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Test message 1')).toBeInTheDocument()
    })

    const searchInput = screen.getByPlaceholderText('Search in message content...')
    fireEvent.change(searchInput, { target: { value: 'test search' } })

    await waitFor(() => {
      // Verify search parameter is in the URL
      expect(apiRequest).toHaveBeenCalledWith(
        expect.stringMatching(/\/api\/sms\/history.*search=test\+search/)
      )
    })
  })

  it.skip('should clear all filters when reset button is clicked', async () => {
    // TODO: This test is for a feature that doesn't exist yet - Clear Filters button
    // The resetFilters function exists but is not connected to any UI element
    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Test message 1')).toBeInTheDocument()
    })

    // Set some filters first
    const selects = screen.getAllByTestId('select')
    const groupSelect = selects[0] // First select is group filter
    fireEvent.change(groupSelect, { target: { value: '1' } })

    const statusSelect = selects[1] // Second select is status filter
    fireEvent.change(statusSelect, { target: { value: 'delivered' } })

    // Click clear filters button - THIS BUTTON DOESN'T EXIST YET
    // const clearButton = screen.getByText('Clear Filters')
    // fireEvent.click(clearButton)

    // Check if filters are reset
    // expect(groupSelect.value).toBe('')
    // expect(statusSelect.value).toBe('')
  })

  it('should display pagination controls', async () => {
    const multiPageResponse = {
      messages: mockMessages,
      total: 20,
      page: 1,
      pages: 2
    }

    // Override the API mock for this specific test
    apiRequest.mockImplementation((url) => {
      if (url === '/groups') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { id: 1, name: 'Test Group' },
            { id: 2, name: 'Another Group' }
          ])
        })
      } else if (url.includes('/api/sms/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(multiPageResponse)
        })
      }
      return Promise.reject(new Error('Unknown URL'))
    })

    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByTestId('pagination')).toBeInTheDocument()
    })
  })

  it('should change page when pagination is used', async () => {
    const multiPageResponse = {
      messages: mockMessages,
      total: 20,
      page: 1,
      pages: 2
    }

    // Override the API mock for this specific test
    apiRequest.mockImplementation((url) => {
      if (url === '/groups') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { id: 1, name: 'Test Group' },
            { id: 2, name: 'Another Group' }
          ])
        })
      } else if (url.includes('/api/sms/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(multiPageResponse)
        })
      }
      return Promise.reject(new Error('Unknown URL'))
    })

    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByTestId('pagination')).toBeInTheDocument()
    })

    const nextButton = screen.getByText('Next')
    fireEvent.click(nextButton)

    expect(apiRequest).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/sms\/history.*page=2/)
    )
  })

  it('should show correct page information', async () => {
    const multiPageResponse = {
      messages: mockMessages,
      total: 20,
      page: 1,
      pages: 2
    }

    // Override the API mock for this specific test
    apiRequest.mockImplementation((url) => {
      if (url === '/groups') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { id: 1, name: 'Test Group' },
            { id: 2, name: 'Another Group' }
          ])
        })
      } else if (url.includes('/api/sms/history')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(multiPageResponse)
        })
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve([])
      })
    })

    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Page 1 of 2')).toBeInTheDocument()
    })
  })

  it('should reload data when refreshTrigger changes', async () => {
    const { rerender } = render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Test message 1')).toBeInTheDocument()
    })

    const initialCallCount = apiRequest.mock.calls.length

    // Change refresh trigger
    rerender(<MessageHistory {...mockProps} refreshTrigger={1} />)

    await waitFor(() => {
      expect(apiRequest.mock.calls.length).toBeGreaterThan(initialCallCount)
    })
  })

  it('should show empty state when no messages', async () => {
    apiRequest.mockResolvedValue({
      messages: [],
      total: 0,
      page: 1,
      pages: 0
    })

    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText(/No messages found.*Send your first message/)).toBeInTheDocument()
    })
  })

  it('should show filtered empty state when filters return no results', async () => {
    let callCount = 0
    
    // Mock implementation to handle the sequence: groups, initial messages, filtered messages
    apiRequest.mockImplementation((url) => {
      if (url === '/groups') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([
            { id: 1, name: 'Test Group' },
            { id: 2, name: 'Another Group' }
          ])
        })
      } else if (url.includes('/api/sms/history')) {
        callCount++
        if (callCount === 1) {
          // First call: return messages
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              messages: mockMessages,
              total: 2,
              page: 1,
              pages: 1
            })
          })
        } else {
          // Subsequent calls (after filtering): return empty
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              messages: [],
              total: 0,
              page: 1,
              pages: 0
            })
          })
        }
      }
      return Promise.reject(new Error('Unknown URL'))
    })

    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText('Test message 1')).toBeInTheDocument()
    })

    // Apply filter that returns no results
    const statusSelect = screen.getByDisplayValue('All Statuses')
    fireEvent.change(statusSelect, { target: { value: 'failed' } })

    await waitFor(() => {
      expect(screen.getByText(/No messages found.*Send your first message/)).toBeInTheDocument()
    })
  })

  it('should show error message when loading fails', async () => {
    apiRequest.mockRejectedValue(new Error('Network error'))

    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to load message history/)).toBeInTheDocument()
    })
  })

  it('should display delivery timestamps', async () => {
    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText(/Delivered:/)).toBeInTheDocument()
    })
  })

  it('should show appropriate status information', async () => {
    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      const deliveredChip = screen.getByText('delivered')
      const sentChip = screen.getByText('sent')
      expect(deliveredChip).toBeInTheDocument()
      expect(sentChip).toBeInTheDocument()
    })
  })

  it('should display Twilio message IDs for debugging', async () => {
    render(<MessageHistory {...mockProps} />)
    
    await waitFor(() => {
      expect(screen.getByText(/SM123456/)).toBeInTheDocument()
    })
  })
})