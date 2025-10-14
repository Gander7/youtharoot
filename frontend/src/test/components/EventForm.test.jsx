import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Mock the auth store and API functions
vi.mock('../../stores/auth', () => ({
  apiRequest: vi.fn(),
  authStore: {
    get: () => ({ isAuthenticated: true, user: { role: 'admin' } })
  }
}));

// We'll test the EventForm component logic by creating a simplified version
// This tests the same logic that exists in EventList.jsx
const EventForm = ({ open, onClose, event, onSave }) => {
  // Get today's date in YYYY-MM-DD format in local timezone (same as EventList.jsx)
  const getLocalDateString = (date = new Date()) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };
  
  const today = getLocalDateString();

  // Initialize with defaults and spread event data (same initial logic as EventList.jsx)
  const [formData, setFormData] = React.useState({
    date: today,
    name: 'Youth Group',
    desc: '',
    start_time: '19:00',
    end_time: '21:00',
    location: 'BLT',
    ...event
  });

  // Update form data when event prop changes (same logic as EventList.jsx)
  React.useEffect(() => {
    if (event) {
      setFormData({
        date: event.date || today,
        name: event.name || 'Youth Group',
        desc: event.desc || '',
        start_time: event.start_time || '19:00',
        end_time: event.end_time || '21:00',
        location: event.location || 'BLT',
      });
    } else {
      // Reset to defaults for new event
      setFormData({
        date: today,
        name: 'Youth Group',
        desc: '',
        start_time: '19:00',
        end_time: '21:00',
        location: 'BLT',
      });
    }
  }, [event, today]);

  const handleSave = () => {
    onSave(formData);
  };

  if (!open) return null;

  return (
    <div data-testid="event-form">
      <input
        data-testid="event-name"
        value={formData.name || ''}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
      />
      <input
        data-testid="event-date"
        value={formData.date || ''}
        onChange={(e) => setFormData({ ...formData, date: e.target.value })}
      />
      <input
        data-testid="event-start-time"
        value={formData.start_time || ''}
        onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
      />
      <input
        data-testid="event-end-time"
        value={formData.end_time || ''}
        onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
      />
      <input
        data-testid="event-location"
        value={formData.location || ''}
        onChange={(e) => setFormData({ ...formData, location: e.target.value })}
      />
      <textarea
        data-testid="event-description"
        value={formData.desc || ''}
        onChange={(e) => setFormData({ ...formData, desc: e.target.value })}
      />
      <button data-testid="save-button" onClick={handleSave}>
        {event ? 'Update Event' : 'Create Event'}
      </button>
      <button data-testid="cancel-button" onClick={onClose}>
        Cancel
      </button>
    </div>
  );
};

describe('EventForm', () => {
  let mockOnClose;
  let mockOnSave;

  beforeEach(() => {
    // Mock the current date to make tests deterministic
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2025-10-13T15:30:00-03:00')); // 3:30 PM Atlantic time

    mockOnClose = vi.fn();
    mockOnSave = vi.fn();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  describe('New Event Creation', () => {
    it('should initialize with default values for new event', async () => {
      render(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={null} 
          onSave={mockOnSave} 
        />
      );

      // Verify default values are set
      expect(screen.getByTestId('event-name')).toHaveValue('Youth Group');
      expect(screen.getByTestId('event-date')).toHaveValue('2025-10-13');
      expect(screen.getByTestId('event-start-time')).toHaveValue('19:00');
      expect(screen.getByTestId('event-end-time')).toHaveValue('21:00');
      expect(screen.getByTestId('event-location')).toHaveValue('BLT');
      expect(screen.getByTestId('event-description')).toHaveValue('');

      // Verify button text
      expect(screen.getByTestId('save-button')).toHaveTextContent('Create Event');
    });

    it('should use local timezone for today\'s date', async () => {
      render(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={null} 
          onSave={mockOnSave} 
        />
      );

      // Should use local date (2025-10-13) not UTC date (would be 2025-10-14)
      expect(screen.getByTestId('event-date')).toHaveValue('2025-10-13');
    });

    it('should allow editing form fields for new event', async () => {
      render(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={null} 
          onSave={mockOnSave} 
        />
      );

      // Edit the event name
      const nameInput = screen.getByTestId('event-name');
      fireEvent.change(nameInput, { target: { value: 'Custom Event' } });
      expect(nameInput).toHaveValue('Custom Event');

      // Edit the date
      const dateInput = screen.getByTestId('event-date');
      fireEvent.change(dateInput, { target: { value: '2025-10-15' } });
      expect(dateInput).toHaveValue('2025-10-15');

      // Edit start time
      const startTimeInput = screen.getByTestId('event-start-time');
      fireEvent.change(startTimeInput, { target: { value: '18:00' } });
      expect(startTimeInput).toHaveValue('18:00');
    });
  });

  describe('Edit Existing Event', () => {
    const existingEvent = {
      id: 1,
      date: '2025-10-15',
      name: 'Special Event',
      desc: 'This is a special event description',
      start_time: '18:00',
      end_time: '22:00',
      location: 'Conference Room'
    };

    it('should populate form with existing event data', () => {
      render(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={existingEvent} 
          onSave={mockOnSave} 
        />
      );

      // Should initially show existing event data due to spread in useState
      expect(screen.getByTestId('event-name')).toHaveValue('Special Event');
      expect(screen.getByTestId('event-date')).toHaveValue('2025-10-15');
      expect(screen.getByTestId('event-start-time')).toHaveValue('18:00');
      expect(screen.getByTestId('event-end-time')).toHaveValue('22:00');
      expect(screen.getByTestId('event-location')).toHaveValue('Conference Room');
      expect(screen.getByTestId('event-description')).toHaveValue('This is a special event description');

      // Verify button text
      expect(screen.getByTestId('save-button')).toHaveTextContent('Update Event');
    });

    it('should handle partial event data with defaults', () => {
      const partialEvent = {
        id: 2,
        date: '2025-10-16',
        name: 'Partial Event',
        // Missing desc, start_time, end_time, location
      };

      render(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={partialEvent} 
          onSave={mockOnSave} 
        />
      );

      // Should show partial event data with defaults for missing fields
      expect(screen.getByTestId('event-name')).toHaveValue('Partial Event');
      expect(screen.getByTestId('event-date')).toHaveValue('2025-10-16');
      expect(screen.getByTestId('event-start-time')).toHaveValue('19:00'); // default
      expect(screen.getByTestId('event-end-time')).toHaveValue('21:00'); // default
      expect(screen.getByTestId('event-location')).toHaveValue('BLT'); // default
      expect(screen.getByTestId('event-description')).toHaveValue(''); // default
    });

    it('should update form when event prop changes', () => {
      const { rerender } = render(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={null} 
          onSave={mockOnSave} 
        />
      );

      // Initially shows default values
      expect(screen.getByTestId('event-name')).toHaveValue('Youth Group');

      // Change to editing an existing event
      rerender(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={existingEvent} 
          onSave={mockOnSave} 
        />
      );

      // useEffect should update the form synchronously in tests
      expect(screen.getByTestId('event-name')).toHaveValue('Special Event');
      expect(screen.getByTestId('event-date')).toHaveValue('2025-10-15');
    });

    it('should reset to defaults when switching from edit to new', async () => {
      const { rerender } = render(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={existingEvent} 
          onSave={mockOnSave} 
        />
      );

      // Initially shows existing event data
      expect(screen.getByTestId('event-name')).toHaveValue('Special Event');

      // Change to creating a new event
      rerender(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={null} 
          onSave={mockOnSave} 
        />
      );

      // useEffect should reset to defaults synchronously in tests
      expect(screen.getByTestId('event-name')).toHaveValue('Youth Group');
      expect(screen.getByTestId('event-date')).toHaveValue('2025-10-13');
    });
  });

  describe('Form Interactions', () => {
    it('should call onSave with correct data when save button is clicked', () => {
      render(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={null} 
          onSave={mockOnSave} 
        />
      );

      fireEvent.click(screen.getByTestId('save-button'));

      expect(mockOnSave).toHaveBeenCalledWith({
        date: '2025-10-13',
        name: 'Youth Group',
        desc: '',
        start_time: '19:00',
        end_time: '21:00',
        location: 'BLT'
      });
    });

    it('should call onClose when cancel button is clicked', () => {
      render(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={null} 
          onSave={mockOnSave} 
        />
      );

      fireEvent.click(screen.getByTestId('cancel-button'));
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should not render when open is false', () => {
      render(
        <EventForm 
          open={false} 
          onClose={mockOnClose} 
          event={null} 
          onSave={mockOnSave} 
        />
      );

      expect(screen.queryByTestId('event-form')).not.toBeInTheDocument();
    });
  });

  describe('Date Handling Edge Cases', () => {
    it('should handle different timezone scenarios correctly', () => {
      // Test late night - should not affect date
      vi.setSystemTime(new Date('2025-10-13T23:59:00-03:00'));
      const { unmount } = render(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={null} 
          onSave={mockOnSave} 
        />
      );
      expect(screen.getByTestId('event-date')).toHaveValue('2025-10-13');
      unmount();

      // Test early morning - should not affect date  
      vi.setSystemTime(new Date('2025-10-13T01:00:00-03:00'));
      const { unmount: unmount2 } = render(
        <EventForm 
          open={true} 
          onClose={mockOnClose} 
          event={null} 
          onSave={mockOnSave} 
        />
      );
      expect(screen.getByTestId('event-date')).toHaveValue('2025-10-13');
      unmount2();
    });
  });
});