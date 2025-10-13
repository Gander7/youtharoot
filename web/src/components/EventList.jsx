import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Chip,
  IconButton,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Paper,
  Divider,
  Stack,
  Alert
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import {
  Search as SearchIcon,
  Event as EventIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  LocationOn as LocationIcon,
  AccessTime as TimeIcon,
  CalendarMonth as CalendarIcon,
  People as PeopleIcon,
  CheckCircle as CheckInIcon
} from '@mui/icons-material';
import { apiRequest } from '../stores/auth';
import ErrorBoundary from './ErrorBoundary.jsx';
import ApiErrorBoundary from './ApiErrorBoundary.jsx';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
    background: {
      default: '#181818',
      paper: '#242424',
    },
    text: {
      primary: '#f5f5f5',
      secondary: '#b0b0b0',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
  },
});

const EventForm = ({ open, onClose, event, onSave }) => {
  // Get today's date in YYYY-MM-DD format
  const today = new Date().toISOString().split('T')[0];
  
  const [formData, setFormData] = useState({
    date: today,
    name: 'Youth Group',
    desc: '',
    start_time: '19:00',
    end_time: '21:00',
    location: 'BLT',
    ...event
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const eventData = {
      date: formData.date,
      name: formData.name,
      desc: formData.desc,
      start_time: formData.start_time,
      end_time: formData.end_time,
      location: formData.location || null,
    };

    // Include ID only if editing existing event
    if (event && event.id) {
      eventData.id = event.id;
    }

    try {
      const url = event && event.id ? `/event/${event.id}` : '/event';
      const method = event && event.id ? 'PUT' : 'POST';
      
      const response = await apiRequest(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventData),
      });
      
      if (response.ok) {
        onSave();
        onClose();
      } else {
        console.error('Failed to save event:', await response.text());
      }
    } catch (error) {
      console.error('Error saving event:', error);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          {event ? 'Edit Event' : 'Create New Event'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Event Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              fullWidth
            />
            
            <TextField
              label="Date"
              type="date"
              value={formData.date}
              onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              required
              fullWidth
              InputLabelProps={{ shrink: true }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <CalendarIcon />
                  </InputAdornment>
                ),
              }}
            />

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  label="Start Time"
                  type="time"
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  required
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <TimeIcon />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="End Time"
                  type="time"
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  required
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
            </Grid>
            
            <TextField
              label="Location"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              fullWidth
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LocationIcon />
                  </InputAdornment>
                ),
              }}
            />

            <TextField
              label="Description"
              value={formData.desc}
              onChange={(e) => setFormData({ ...formData, desc: e.target.value })}
              multiline
              rows={3}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained">
            {event ? 'Update Event' : 'Create Event'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

const DeleteConfirmDialog = ({ open, onClose, event, onConfirm }) => {
  const [canDelete, setCanDelete] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && event) {
      checkCanDelete();
    }
  }, [open, event]);

  const checkCanDelete = async () => {
    setLoading(true);
    try {
      const response = await apiRequest(`/event/${event.id}/can-delete`);
      if (response.ok) {
        const data = await response.json();
        setCanDelete(data);
      }
    } catch (error) {
      console.error('Error checking if event can be deleted:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm">
      <DialogTitle>Delete Event</DialogTitle>
      <DialogContent>
        <Typography gutterBottom>
          Are you sure you want to delete "{event?.name}"?
        </Typography>
        
        {loading ? (
          <Typography color="text.secondary">Checking attendance records...</Typography>
        ) : canDelete !== null && !canDelete.can_delete ? (
          <Alert severity="warning" sx={{ mt: 2 }}>
            This event cannot be deleted because it has attendance records. 
            You must remove all attendees first.
          </Alert>
        ) : (
          <Typography color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone.
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        {canDelete?.can_delete && (
          <Button 
            onClick={onConfirm} 
            color="error" 
            variant="contained"
            disabled={loading}
          >
            Delete Event
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default function EventList() {
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [eventAttendance, setEventAttendance] = useState({}); // Store attendance data for each event
  const [searchTerm, setSearchTerm] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [deletingEvent, setDeletingEvent] = useState(null);

  const fetchEvents = async () => {
    const startTime = performance.now();
    console.log('🔄 Starting to fetch events...');
    
    try {
      const fetchStart = performance.now();
      console.log(`📡 Making API request to: /events`);
      
      const response = await apiRequest(`/events`);
      const fetchEnd = performance.now();
      console.log(`📡 Fetch completed in ${fetchEnd - fetchStart}ms, status: ${response.status}`);
      
      if (response.ok) {
        const jsonStart = performance.now();
        const data = await response.json();
        const jsonEnd = performance.now();
        console.log(`📋 JSON parsing took ${jsonEnd - jsonStart}ms, got ${data.length} events`);
        
        setEvents(data);
        
        // Fetch attendance data for each event
        await fetchAttendanceData(data);
        
        const totalTime = performance.now() - startTime;
        console.log(`✅ Total fetchEvents took ${totalTime}ms`);
      }
    } catch (error) {
      console.error('Error fetching events:', error);
      // Set some mock data for demo
      setEvents([
        {
          id: 1,
          date: '2025-09-27',
          name: 'Friday Night Youth Group',
          desc: 'Fun games and fellowship',
          start_time: '19:00',
          end_time: '21:00',
          location: 'Youth Room',
          youth: [],
          leaders: []
        },
        {
          id: 2,
          date: '2025-10-04',
          name: 'Youth Group',
          desc: '',
          start_time: '19:00',
          end_time: '21:00',
          location: null,
          youth: [{ person_id: 1, check_in: '2025-10-04T19:05:00' }],
          leaders: []
        }
      ]);
    }
  };

  useEffect(() => {
    console.log('🔄 EventList useEffect triggered at:', new Date().toISOString());
    console.log('🔄 About to call fetchEvents...');
    fetchEvents();
  }, []);

  // Check for refresh flag from CheckIn component
  useEffect(() => {
    const checkRefreshFlag = () => {
      const shouldRefresh = localStorage.getItem('refreshEventList');
      if (shouldRefresh === 'true') {
        console.log('🔄 Refreshing EventList due to bulk checkout');
        localStorage.removeItem('refreshEventList'); // Clear the flag
        fetchEvents(); // Refresh events and attendance data
      }
    };

    // Check immediately
    checkRefreshFlag();

    // Also check when the window regains focus (user returns from CheckIn page)
    const handleFocus = () => checkRefreshFlag();
    window.addEventListener('focus', handleFocus);

    return () => {
      window.removeEventListener('focus', handleFocus);
    };
  }, []);

  useEffect(() => {
    let filtered = events;
    
    if (searchTerm) {
      const searchLower = searchTerm.trim().toLowerCase();
      filtered = events.filter(e => {
        // Combine all searchable text for better multi-word matching
        const searchableText = `${e.name} ${e.desc || ''} ${e.location || ''}`.toLowerCase();
        return searchableText.includes(searchLower);
      });
    }
    
    // Sort by date (most recent first) - date strings in YYYY-MM-DD format sort correctly
    filtered.sort((a, b) => b.date.localeCompare(a.date));
    
    setFilteredEvents(filtered);
  }, [events, searchTerm]);

  const handleAddEvent = () => {
    setEditingEvent(null);
    setFormOpen(true);
  };

  const handleEditEvent = (event) => {
    setEditingEvent(event);
    setFormOpen(true);
  };

  const handleDeleteEvent = (event) => {
    setDeletingEvent(event);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!deletingEvent) return;
    
    try {
      const response = await apiRequest(`/event/${deletingEvent.id}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        fetchEvents(); // Refresh the list
        setDeleteDialogOpen(false);
        setDeletingEvent(null);
      } else {
        console.error('Failed to delete event:', await response.text());
      }
    } catch (error) {
      console.error('Error deleting event:', error);
    }
  };

  const handleSave = () => {
    fetchEvents();
  };

  const formatDate = (dateStr) => {
    // Parse as local date to avoid timezone issues
    const [year, month, day] = dateStr.split('-').map(Number);
    const date = new Date(year, month - 1, day); // month is 0-indexed
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatEventTime = (startTime, endTime) => {
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const shortTz = new Date().toLocaleTimeString('en-US', {
      timeZoneName: 'short'
    }).split(' ').pop();
    return `${startTime} - ${endTime} ${shortTz}`;
  };

  const getAttendeeCount = (event) => {
    return (event.youth?.length || 0) + (event.leaders?.length || 0);
  };

  const fetchAttendanceData = async (eventsData) => {
    const attendanceMap = {};
    
    // Fetch attendance for each event that might need it
    await Promise.all(eventsData.map(async (event) => {
      try {
        const attendanceResponse = await apiRequest(`/event/${event.id}/attendance`);
        if (attendanceResponse.ok) {
          const attendanceData = await attendanceResponse.json();
          attendanceMap[event.id] = attendanceData;
        }
      } catch (error) {
        console.error(`Error fetching attendance for event ${event.id}:`, error);
        attendanceMap[event.id] = [];
      }
    }));
    
    setEventAttendance(attendanceMap);
  };

  const hasEveryoneCheckedOut = (eventId) => {
    const attendance = eventAttendance[eventId] || [];
    if (attendance.length === 0) return true; // No one checked in
    
    // Check if all attendees have been checked out
    return attendance.every(attendee => attendee.check_out);
  };

  const isEventEnded = (event) => {
    // Parse event date and time to get the exact event end time
    const [year, month, day] = event.date.split('-').map(Number);
    const eventDate = new Date(year, month - 1, day);
    
    // Parse end time and set it on the event date
    const [hours, minutes] = event.end_time.split(':').map(Number);
    const eventEndTime = new Date(eventDate);
    eventEndTime.setHours(hours, minutes, 0, 0);
    
    const now = new Date();
    return now > eventEndTime;
  };

  const canManageAttendance = (event) => {
    // Parse event date to check if it's accessible (from event day onward)
    const [year, month, day] = event.date.split('-').map(Number);
    const eventDate = new Date(year, month - 1, day);
    const eventStartOfDay = new Date(eventDate);
    eventStartOfDay.setHours(0, 0, 0, 0);
    
    const now = new Date();
    
    // Must be on or after event day
    if (now < eventStartOfDay) return false;
    
    // If event hasn't ended yet, always allow management
    if (!isEventEnded(event)) return true;
    
    // If event has ended, only allow management if someone is still checked in
    return !hasEveryoneCheckedOut(event.id);
  };

  const canViewAttendance = (event) => {
    // Parse event date to check if it's accessible (from event day onward)  
    const [year, month, day] = event.date.split('-').map(Number);
    const eventDate = new Date(year, month - 1, day);
    const eventStartOfDay = new Date(eventDate);
    eventStartOfDay.setHours(0, 0, 0, 0);
    
    const now = new Date();
    
    // Must be on or after event day
    if (now < eventStartOfDay) return false;
    
    // If event has ended and everyone is checked out, show view-only
    return isEventEnded(event) && hasEveryoneCheckedOut(event.id);
  };

  const handleCheckIn = (event) => {
    // Navigate to check-in page with eventId as query parameter
    if (typeof window !== 'undefined') {
      window.location.href = `/checkin?eventId=${event.id}`;
    }
  };

  const handleViewAttendance = (event) => {
    // Navigate to check-in page with read-only mode
    if (typeof window !== 'undefined') {
      window.location.href = `/checkin?eventId=${event.id}&viewOnly=true`;
    }
  };

  return (
    <ErrorBoundary level="component" title="Events System Error">
      <ApiErrorBoundary>
        <ThemeProvider theme={darkTheme}>
      <Box sx={{ maxWidth: 800, margin: '0 auto', padding: 2 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1" fontWeight="bold">
            Events
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleAddEvent}
            sx={{ borderRadius: 2 }}
          >
            Create Event
          </Button>
        </Box>

        {/* Search */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <TextField
            placeholder="Search events..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            fullWidth
          />
        </Paper>

        {/* Event List */}
        {filteredEvents.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <EventIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              {searchTerm ? 'No events found' : 'No events scheduled'}
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              {searchTerm ? 'Try adjusting your search' : 'Create your first event to get started'}
            </Typography>
          </Paper>
        ) : (
          <List>
            {filteredEvents.map((event) => (
              <Card key={event.id} sx={{ mb: 1.5 }}>
                <ListItem>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'primary.main' }}>
                      <EventIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1" fontWeight="medium">
                          {event.name}
                        </Typography>
                        {getAttendeeCount(event) > 0 && (
                          <Chip
                            icon={<PeopleIcon />}
                            label={getAttendeeCount(event)}
                            size="small"
                            color="secondary"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <>
                        📅 {formatDate(event.date)}
                        <br />
                        ⏰ {formatEventTime(event.start_time, event.end_time)}
                        {event.location && (
                          <>
                            <br />
                            📍 {event.location}
                          </>
                        )}
                        {event.desc && (
                          <>
                            <br />
                            <br />
                            {event.desc}
                          </>
                        )}
                      </>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {canManageAttendance(event) && (
                        <Button
                          variant="contained"
                          color="success"
                          size="small"
                          startIcon={<CheckInIcon />}
                          onClick={() => handleCheckIn(event)}
                          sx={{ mr: 1 }}
                        >
                          Manage Attendance
                        </Button>
                      )}
                      {canViewAttendance(event) && (
                        <Button
                          variant="outlined"
                          color="primary"
                          size="small"
                          startIcon={<CheckInIcon />}
                          onClick={() => handleViewAttendance(event)}
                          sx={{ mr: 1 }}
                        >
                          View Attendance
                        </Button>
                      )}
                      <IconButton
                        edge="end"
                        onClick={() => handleEditEvent(event)}
                        size="small"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        edge="end"
                        onClick={() => handleDeleteEvent(event)}
                        size="small"
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </ListItemSecondaryAction>
                </ListItem>
              </Card>
            ))}
          </List>
        )}

        {/* Event Form Dialog */}
        <EventForm
          open={formOpen}
          onClose={() => setFormOpen(false)}
          event={editingEvent}
          onSave={handleSave}
        />

        {/* Delete Confirmation Dialog */}
        <DeleteConfirmDialog
          open={deleteDialogOpen}
          onClose={() => {
            setDeleteDialogOpen(false);
            setDeletingEvent(null);
          }}
          event={deletingEvent}
          onConfirm={confirmDelete}
        />

        {/* Floating Action Button for Mobile */}
        <Box sx={{ display: { xs: 'block', sm: 'none' } }}>
          <Fab
            color="primary"
            sx={{
              position: 'fixed',
              bottom: 16,
              right: 16,
            }}
            onClick={handleAddEvent}
          >
            <AddIcon />
          </Fab>
        </Box>
      </Box>
        </ThemeProvider>
      </ApiErrorBoundary>
    </ErrorBoundary>
  );
}
