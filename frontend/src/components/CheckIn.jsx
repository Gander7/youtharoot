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
  ToggleButton,
  ToggleButtonGroup,
  Paper,
  Stack,
  Alert,
  Snackbar
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import {
  Search as SearchIcon,
  Person as PersonIcon,
  School as SchoolIcon,
  Work as WorkIcon,
  CheckCircle as CheckInIcon,
  ExitToApp as CheckOutIcon,
  Event as EventIcon,
  ArrowBack as BackIcon
} from '@mui/icons-material';
import { apiRequest, authStore } from '../stores/auth';
import { useStore } from '@nanostores/react';
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

export default function CheckIn({ eventId, viewOnly = false }) {
  const [event, setEvent] = useState(null);
  const [allPeople, setAllPeople] = useState([]); // Changed from allYouth to allPeople
  const [attendees, setAttendees] = useState([]);
  const [filteredPeople, setFilteredPeople] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('available'); // 'available', 'checked-in', or 'checked-out'
  const [loading, setLoading] = useState(true);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [checkingOutAll, setCheckingOutAll] = useState(false);
  
  // Get current user from auth store
  const auth = useStore(authStore);

  // Fetch event details and youth data
  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch event details
      const eventResponse = await apiRequest(`/event/${eventId}`);
      if (eventResponse.ok) {
        const eventData = await eventResponse.json();
        setEvent(eventData);
      }

      // Fetch attendance data
      const attendanceResponse = await apiRequest(`/event/${eventId}/attendance`);
      if (attendanceResponse.ok) {
        const attendanceData = await attendanceResponse.json();
        setAttendees(attendanceData);
      }

      // Only fetch all people if not in view-only mode
      if (!viewOnly) {
        // Fetch all people (youth and leaders)
        const allPeopleData = [];
        
        // Fetch youth
        const youthResponse = await apiRequest('/person/youth');
        if (youthResponse.ok) {
          const youthData = await youthResponse.json();
          allPeopleData.push(...youthData.map(person => ({ ...person, person_type: 'youth' })));
        }
        
        // Fetch leaders
        const leadersResponse = await apiRequest('/person/leaders');
        if (leadersResponse.ok) {
          const leadersData = await leadersResponse.json();
          allPeopleData.push(...leadersData.map(person => ({ ...person, person_type: 'leader' })));
        }
        
        setAllPeople(allPeopleData);
      } else {
        // In view-only mode, we don't need all people data
        setAllPeople([]);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setSnackbar({ 
        open: true, 
        message: 'Failed to load data', 
        severity: 'error' 
      });
      // Mock data for development
      setEvent({
        id: eventId,
        name: 'Youth Group',
        date: '2025-09-24',
        start_time: '19:00',
        end_time: '21:00',
        location: 'BLT'
      });
      setAllPeople([
        { id: 1, first_name: 'Alex', last_name: 'Johnson', grade: 10, school_name: 'Central High', person_type: 'youth' },
        { id: 2, first_name: 'Sarah', last_name: 'Smith', grade: 11, school_name: 'North High', person_type: 'youth' },
        { id: 3, first_name: 'Mike', last_name: 'Davis', grade: 9, school_name: 'South High', person_type: 'youth' },
        { id: 4, first_name: 'Pastor', last_name: 'Johnson', role: 'Youth Pastor', person_type: 'leader' },
        { id: 5, first_name: 'Leader', last_name: 'Smith', role: 'Volunteer', person_type: 'leader' }
      ]);
      setAttendees([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (eventId) {
      fetchData();
    }
  }, [eventId]);

  // Filter people based on search and availability
  useEffect(() => {
    let filtered = [];
    
    if (viewOnly) {
      // In view-only mode, show all attendees (people who checked in)
      filtered = attendees.map(attendee => {
        const person = allPeople.find(p => p.id === attendee.person_id);
        return person ? { 
          ...person, 
          check_in: attendee.check_in, 
          check_out: attendee.check_out,
          // Use the data from attendance record if person not found in allPeople
          first_name: person.first_name || attendee.first_name,
          last_name: person.last_name || attendee.last_name,
          grade: person.grade || attendee.grade,
          school_name: person.school_name || attendee.school_name,
          role: person.role || attendee.role,
          person_type: person.person_type || attendee.person_type
        } : {
          id: attendee.person_id,
          first_name: attendee.first_name,
          last_name: attendee.last_name,
          grade: attendee.grade,
          school_name: attendee.school_name,
          role: attendee.role,
          person_type: attendee.person_type,
          check_in: attendee.check_in,
          check_out: attendee.check_out
        };
      });
    } else {
      // Normal mode - filter based on selected tab
      if (filter === 'available') {
        // Show people who are NOT checked in at all
        const checkedInIds = attendees.map(a => a.person_id);
        filtered = allPeople.filter(person => !checkedInIds.includes(person.id));
      } else if (filter === 'checked-in') {
        // Show people who ARE checked in but NOT checked out
        const checkedInPeople = attendees
          .filter(attendee => !attendee.check_out) // Only those who haven't checked out
          .map(attendee => {
            const person = allPeople.find(p => p.id === attendee.person_id);
            return person ? { 
              ...person, 
              check_in: attendee.check_in, 
              check_out: attendee.check_out,
              // Use the data from attendance record if person not found in allPeople
              first_name: person.first_name || attendee.first_name,
              last_name: person.last_name || attendee.last_name,
              grade: person.grade || attendee.grade,
              school_name: person.school_name || attendee.school_name,
              role: person.role || attendee.role,
              person_type: person.person_type || attendee.person_type
            } : {
              id: attendee.person_id,
              first_name: attendee.first_name,
              last_name: attendee.last_name,
              grade: attendee.grade,
              school_name: attendee.school_name,
              check_in: attendee.check_in,
              check_out: attendee.check_out
            };
          });
        filtered = checkedInPeople;
      } else if (filter === 'checked-out') {
        // Show people who ARE checked out
        const checkedOutPeople = attendees
          .filter(attendee => attendee.check_out) // Only those who have checked out
          .map(attendee => {
            const person = allPeople.find(p => p.id === attendee.person_id);
            return person ? { 
              ...person, 
              check_in: attendee.check_in, 
              check_out: attendee.check_out,
              first_name: person.first_name || attendee.first_name,
              last_name: person.last_name || attendee.last_name,
              grade: person.grade || attendee.grade,
              school_name: person.school_name || attendee.school_name,
              role: person.role || attendee.role,
              person_type: person.person_type || attendee.person_type
            } : {
              id: attendee.person_id,
              first_name: attendee.first_name,
              last_name: attendee.last_name,
              grade: attendee.grade,
              school_name: attendee.school_name,
              check_in: attendee.check_in,
              check_out: attendee.check_out
            };
          });
        filtered = checkedOutPeople;
      }
    }

    // Apply search filter
    if (searchTerm) {
      const searchLower = searchTerm.trim().toLowerCase();
      filtered = filtered.filter(person => {
        const fullName = `${person.first_name} ${person.last_name}`.toLowerCase();
        return fullName.includes(searchLower) ||
               (person.school_name && person.school_name.toLowerCase().includes(searchLower)) ||
               (person.role && person.role.toLowerCase().includes(searchLower));
      });
    }

    setFilteredPeople(filtered);
  }, [allPeople, attendees, searchTerm, filter, viewOnly]);

  const handleCheckIn = async (person) => {
    try {
      const response = await apiRequest(`/event/${eventId}/checkin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ person_id: person.id })
      });

      if (response.ok) {
        setSnackbar({ 
          open: true, 
          message: `${person.first_name} checked in successfully!`, 
          severity: 'success' 
        });
        fetchData(); // Refresh data
      } else {
        throw new Error('Check-in failed');
      }
    } catch (error) {
      console.error('Error checking in:', error);
      setSnackbar({ 
        open: true, 
        message: 'Failed to check in. Please try again.', 
        severity: 'error' 
      });
    }
  };

  const handleCheckOut = async (person) => {
    try {
      const response = await apiRequest(`/event/${eventId}/checkout`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ person_id: person.id })
      });

      if (response.ok) {
        setSnackbar({ 
          open: true, 
          message: `${person.first_name} checked out successfully!`, 
          severity: 'success' 
        });
        fetchData(); // Refresh data
      } else {
        throw new Error('Check-out failed');
      }
    } catch (error) {
      console.error('Error checking out:', error);
      setSnackbar({ 
        open: true, 
        message: 'Failed to check out. Please try again.', 
        severity: 'error' 
      });
    }
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const date = new Date(timeStr);
    const time = date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit'
    });
    const timezone = date.toLocaleTimeString('en-US', {
      timeZoneName: 'short'
    }).split(' ').pop();
    return `${time} ${timezone}`;
  };

  // Helper functions to safely parse event date in local timezone
  const parseEventDate = (dateStr) => {
    if (!dateStr) return new Date();
    const [year, month, day] = dateStr.split('-').map(Number);
    return new Date(year, month - 1, day);
  };

  const getEventDisplayDate = (dateStr) => {
    return parseEventDate(dateStr).toLocaleDateString();
  };

  const getEventDisplayDateLong = (dateStr) => {
    return parseEventDate(dateStr).toLocaleDateString('en-US', { 
      weekday: 'long', month: 'long', day: 'numeric' 
    });
  };

  const getAvailableCount = () => {
    const checkedInIds = attendees.map(a => a.person_id);
    return allPeople.filter(person => !checkedInIds.includes(person.id)).length;
  };

  const getCheckedInCount = () => {
    // Only count people who are checked in but NOT checked out
    return attendees.filter(attendee => !attendee.check_out).length;
  };

  const isAdmin = () => {
    return auth.user?.role === 'admin';
  };

  const isEventEnded = () => {
    if (!event) return false;
    
    const now = new Date();
    
    // Parse the event date properly to avoid timezone issues
    // event.date comes as "YYYY-MM-DD" format from the server
    const [year, month, day] = event.date.split('-').map(Number);
    const [hours, minutes] = event.end_time.split(':').map(Number);
    
    // Create the end time in local timezone (not UTC)
    const eventEndTime = new Date(year, month - 1, day, hours, minutes, 0, 0);
    
    return now > eventEndTime;
  };

  const handleCheckOutAll = async () => {
    if (!isAdmin() || !isEventEnded()) return;
    
    // Guard clause: Check if anyone is still checked in before making API call
    const checkedInCount = getCheckedInCount();
    if (checkedInCount === 0) {
      setSnackbar({ 
        open: true, 
        message: 'No one is currently checked in to check out.', 
        severity: 'info' 
      });
      return;
    }
    
    setCheckingOutAll(true);
    
    try {
      // Use the new bulk checkout endpoint
      const response = await apiRequest(`/event/${eventId}/checkout-all`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const result = await response.json();
        
        if (result.checked_out_count === 0) {
          setSnackbar({ 
            open: true, 
            message: 'No one is currently checked in to check out.', 
            severity: 'info' 
          });
        } else {
          setSnackbar({ 
            open: true, 
            message: `Successfully checked out ${result.checked_out_count} people.`, 
            severity: 'success' 
          });
        }
        
        // Refresh the attendance data
        await fetchData();
        
        // If event has ended and we checked out everyone who was checked in,
        // set a flag to refresh EventList when we go back
        if (isEventEnded() && result.checked_out_count > 0 && result.checked_out_count === checkedInCount) {
          // Everyone who was checked in has now been checked out
          localStorage.setItem('refreshEventList', 'true');
        }
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Check-out failed');
      }
    } catch (error) {
      console.error('Error checking out all:', error);
      setSnackbar({ 
        open: true, 
        message: `Error occurred while checking out all people: ${error.message}`, 
        severity: 'error' 
      });
    }
    
    setCheckingOutAll(false);
  };

  const handleGoBack = () => {
    // If there was a bulk checkout that resulted in everyone being checked out,
    // the localStorage flag will already be set by handleCheckOutAll
    window.history.back();
  };

  const getCheckedOutCount = () => {
    // Count people who are checked out
    return attendees.filter(attendee => attendee.check_out).length;
  };

  if (loading) {
    return (
      <ThemeProvider theme={darkTheme}>
        <Box sx={{ maxWidth: 800, margin: '0 auto', padding: 2, textAlign: 'center' }}>
          <Typography>Loading...</Typography>
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ErrorBoundary level="component" title="Check-in System Error">
      <ApiErrorBoundary>
        <ThemeProvider theme={darkTheme}>
          <Box sx={{ maxWidth: 800, margin: '0 auto', padding: 2 }}>
            {/* Header */}
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <IconButton 
            onClick={handleGoBack} 
            sx={{ mr: 2 }}
          >
            <BackIcon />
          </IconButton>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" component="h1" fontWeight="bold">
              {viewOnly ? 'Event Attendance' : 'Check In'}
            </Typography>
            {event && (
              <Typography variant="subtitle1" color="text.secondary">
                {event.name} • {getEventDisplayDate(event.date)}
                {viewOnly && (
                  <Typography component="span" sx={{ ml: 1, color: 'warning.main', fontWeight: 'medium' }}>
                    (View Only)
                  </Typography>
                )}
              </Typography>
            )}
          </Box>
        </Box>

        {/* Event Info Card */}
        {event && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <EventIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6">{event.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    📅 {getEventDisplayDateLong(event.date)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    ⏰ {event.start_time} - {event.end_time}
                    {event.location && ` • 📍 ${event.location}`}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* View Only Attendance Summary */}
        {viewOnly && (
          <Card sx={{ mb: 3, bgcolor: 'primary.dark' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <PersonIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6" color="primary.contrastText">
                    Total Attendance: {attendees.length}
                  </Typography>
                  <Typography variant="body2" color="primary.contrastText" sx={{ opacity: 0.8 }}>
                    {getCheckedOutCount()} completed • {getCheckedInCount()} still checked in
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Admin Check Out All Button */}
        {event && isAdmin() && !viewOnly && isEventEnded() && getCheckedInCount() > 0 && (
          <Card sx={{ mb: 3, bgcolor: 'warning.dark' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6" color="warning.contrastText">
                    Event Has Ended
                  </Typography>
                  <Typography variant="body2" color="warning.contrastText" sx={{ opacity: 0.8 }}>
                    {getCheckedInCount()} people are still checked in
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  color="error"
                  onClick={handleCheckOutAll}
                  disabled={checkingOutAll}
                  sx={{ minWidth: 120 }}
                >
                  {checkingOutAll ? 'Checking Out...' : 'Check Out All'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Search and Filter */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Stack spacing={2}>
            <TextField
              placeholder="Search people..."
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
            {!viewOnly && (
              <ToggleButtonGroup
                value={filter}
                exclusive
                onChange={(e, newFilter) => newFilter && setFilter(newFilter)}
                size="small"
              >
                <ToggleButton value="available">
                  Available ({getAvailableCount()})
                </ToggleButton>
                <ToggleButton value="checked-in">
                  Checked In ({getCheckedInCount()})
                </ToggleButton>
                <ToggleButton value="checked-out">
                  Checked Out ({getCheckedOutCount()})
                </ToggleButton>
              </ToggleButtonGroup>
            )}
          </Stack>
        </Paper>

        {/* People List */}
        {filteredPeople.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <PersonIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              {searchTerm ? 'No attendees found' : 
                viewOnly ? 'No one attended this event' :
                filter === 'available' ? 'No one available to check in' : 
                filter === 'checked-in' ? 'No one checked in yet' : 'No one checked out yet'
              }
            </Typography>
            <Typography color="text.secondary">
              {searchTerm ? 'Try adjusting your search' : 
                viewOnly ? 'Nobody checked in to this event' :
                filter === 'available' ? 'All youth are already checked in' : 
                filter === 'checked-in' ? 'Start checking people in' : 'No one has checked out yet'
              }
            </Typography>
          </Paper>
        ) : (
          <List>
            {filteredPeople.map((person) => (
              <Card key={person.id} sx={{ mb: 1.5 }}>
                <ListItem>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'primary.main' }}>
                      <SchoolIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1" fontWeight="medium">
                          {person.first_name} {person.last_name}
                        </Typography>
                        {viewOnly ? (
                          // In view-only mode, show status chips
                          <Chip
                            icon={person.check_out ? <CheckOutIcon /> : <CheckInIcon />}
                            label={person.check_out ? 'Attended' : 'Checked In'}
                            size="small"
                            color={person.check_out ? 'primary' : 'success'}
                            variant="outlined"
                          />
                        ) : filter === 'checked-in' && (
                          <Chip
                            icon={<CheckInIcon />}
                            label="Checked In"
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                        <Typography variant="body2" color="text.secondary">
                          {person.person_type === 'leader' ? (
                            person.role || 'Leader'
                          ) : person.grade || person.school_name ? (
                            <>
                              {person.grade && `Grade ${person.grade}`}
                              {person.grade && person.school_name && ' • '}
                              {person.school_name}
                            </>
                          ) : (
                            'Youth'
                          )}
                        </Typography>
                        {(viewOnly || filter === 'checked-in' || filter === 'checked-out') && person.check_in && (
                          <Typography variant="body2" color="text.secondary">
                            ⏰ In: {formatTime(person.check_in)}
                            {person.check_out && ` • Out: ${formatTime(person.check_out)}`}
                          </Typography>
                        )}
                      </Stack>
                    }
                  />
                  <ListItemSecondaryAction>
                    {!viewOnly && filter === 'available' ? (
                      <Button
                        variant="contained"
                        color="success"
                        size="small"
                        startIcon={<CheckInIcon />}
                        onClick={() => handleCheckIn(person)}
                        sx={{ borderRadius: 2 }}
                      >
                        Check In
                      </Button>
                    ) : !viewOnly ? (
                      <Button
                        variant="outlined"
                        color="warning"
                        size="small"
                        startIcon={<CheckOutIcon />}
                        onClick={() => handleCheckOut(person)}
                        disabled={!!person.check_out}
                        sx={{ borderRadius: 2 }}
                      >
                        {person.check_out ? 'Checked Out' : 'Check Out'}
                      </Button>
                    ) : (
                      // View-only mode - show status instead of buttons
                      <Typography variant="body2" color="text.secondary">
                        {person.check_out ? 'Attended' : 'Still checked in'}
                      </Typography>
                    )}
                  </ListItemSecondaryAction>
                </ListItem>
              </Card>
            ))}
          </List>
        )}

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={3000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          <Alert 
            severity={snackbar.severity}
            onClose={() => setSnackbar({ ...snackbar, open: false })}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
          </Box>
        </ThemeProvider>
      </ApiErrorBoundary>
    </ErrorBoundary>
  );
}