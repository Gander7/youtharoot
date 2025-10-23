import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import React, { useState, useEffect } from 'react';
import { animate } from 'animejs';
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
  // --- Card Flip Random Selector ---
  const [randomSelectorOpen, setRandomSelectorOpen] = useState(false);
  const [isSpinning, setIsSpinning] = useState(false);
  const [winner, setWinner] = useState(null);
  const [cardFrontName, setCardFrontName] = useState('');
  const [cardBackName, setCardBackName] = useState('');
  const [isCardFront, setIsCardFront] = useState(true);
  const cardRef = React.useRef(null);

  // Get checked-in youth
  const getCheckedInYouth = () => {
    return attendees
      .filter(attendee => !attendee.check_out)
      .map(attendee => {
        const person = allPeople.find(p => p.id === attendee.person_id);
        const isYouth = (person && (person.type === 'youth' || person.person_type === 'youth'));
        return isYouth ? person : null;
      })
      .filter(Boolean);
  };

  // Generate 36 random names from checked-in youth
  const getRandomNames = (checkedInYouth, count = 36) => {
    const names = [];
    for (let i = 0; i < count; i++) {
      const person = checkedInYouth[Math.floor(Math.random() * checkedInYouth.length)];
      names.push(`${person.first_name} ${person.last_name}`);
    }
    return names;
  };

  // Card flip animation logic
  const spinForRandomYouth = async () => {
    if (isSpinning || getCheckedInYouth().length === 0) return;
    setIsSpinning(true);
    setWinner(null);
    const checkedInYouth = getCheckedInYouth();
    const names = getRandomNames(checkedInYouth, 36);
    setCardFrontName(names[0]);
    setCardBackName(names[1]);
    setIsCardFront(true);
    for (let i = 1; i < names.length; i++) {
      await new Promise(resolve => {
        if (isCardFront) setCardBackName(names[i]);
        else setCardFrontName(names[i]);
        setIsCardFront(prev => !prev);
        animate(cardRef.current, {
          scale: [1, 1.4, 1],
          rotateY: '+=180',
          easing: 'easeInOutSine',
          duration: 400,
          complete: () => setTimeout(resolve, 300)
        });
      });
    }
    setWinner(names[names.length - 1]);
    setCardFrontName(names[names.length - 1]);
    setIsCardFront(true);
    animate(cardRef.current, {
      scale: [1, 1.4, 1],
      rotateY: '+=180',
      backgroundColor: '#FFD700',
      easing: 'easeInOutSine',
      duration: 600,
      complete: () => setIsSpinning(false)
    });
  };

  const openRandomSelector = () => {
    if (getCheckedInYouth().length === 0) {
      setSnackbar({ open: true, message: 'No youth are currently checked in!', severity: 'warning' });
      return;
    }
    setRandomSelectorOpen(true);
    setWinner(null);
    setCardFrontName('');
    setCardBackName('');
    setIsCardFront(true);
  };

  const closeRandomSelector = () => {
    setRandomSelectorOpen(false);
    setIsSpinning(false);
    setWinner(null);
  };
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
    
    // Backend sends UTC timestamps without timezone info
    // We need to explicitly treat them as UTC and convert to Halifax timezone
    let utcDate;
    
    if (timeStr.includes('T')) {
      // ISO format: "2025-10-15T12:34:00" or "2025-10-15T12:34:00Z"
      if (timeStr.endsWith('Z')) {
        utcDate = new Date(timeStr);
      } else {
        // Assume UTC if no timezone specified
        utcDate = new Date(timeStr + 'Z');
      }
    } else {
      // Simple format, assume UTC
      utcDate = new Date(timeStr + 'Z');
    }
    
    // Convert to Halifax timezone (America/Halifax)
    const halifaxTime = utcDate.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      timeZone: 'America/Halifax'
    });
    
    // Get timezone abbreviation for Halifax
    const timezone = utcDate.toLocaleTimeString('en-US', {
      timeZoneName: 'short',
      timeZone: 'America/Halifax'
    }).split(' ').pop();
    
    return `${halifaxTime} ${timezone}`;
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
    
    // Use new UTC datetime field if available, otherwise fall back to legacy date/time
    if (event.end_datetime) {
      // Compare UTC datetimes directly
      const now = new Date();
      const eventEndUtc = new Date(event.end_datetime);
      return now > eventEndUtc;
    } else {
      // Legacy fallback - treat date/time as Halifax timezone
      const now = new Date();
      const nowHalifaxString = now.toLocaleString("sv-SE", {timeZone: "America/Halifax"});
      const nowHalifax = new Date(nowHalifaxString);
      
      // Parse the event date and time, treating them as Halifax timezone
      const [year, month, day] = event.date.split('-').map(Number);
      const [hours, minutes] = event.end_time.split(':').map(Number);
      
      // Create event end time in Halifax timezone
      const eventEndString = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')} ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:00`;
      const eventEndHalifax = new Date(eventEndString);
      
      return nowHalifax > eventEndHalifax;
    }
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

  // Helper function to format datetime in Halifax timezone
  const formatEventDateTime = (utcDatetime) => {
    if (!utcDatetime) return '';
    
    const utcDate = new Date(utcDatetime);
    
    // Convert to Halifax timezone for display
    const halifaxDateTime = utcDate.toLocaleString('en-US', {
      timeZone: 'America/Halifax',
      weekday: 'long',
      year: 'numeric', 
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
    
    return halifaxDateTime;
  };

  const formatEventTime = (utcDatetime) => {
    if (!utcDatetime) return '';
    
    const utcDate = new Date(utcDatetime);
    
    // Convert to Halifax timezone for display
    const halifaxTime = utcDate.toLocaleString('en-US', {
      timeZone: 'America/Halifax',
      hour: 'numeric',
      minute: '2-digit'
    });
    
    return halifaxTime;
  };

  // Update the event display to use new datetime fields
  const getEventDisplayDateLong = () => {
    if (!event) return '';
    
    if (event.start_datetime) {
      // Use new UTC datetime field
      return formatEventDateTime(event.start_datetime);
    } else {
      // Legacy fallback
      return parseEventDate(event.date).toLocaleDateString('en-US', { 
        weekday: 'long', month: 'long', day: 'numeric' 
      });
    }
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
                    📅 {getEventDisplayDateLong()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    ⏰ {event.start_datetime ? 
                         `${formatEventTime(event.start_datetime)} - ${formatEventTime(event.end_datetime)}` :
                         `${event.start_time} - ${event.end_time}`}
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
        {/* --- Random Youth Selector --- */}
        {event && !viewOnly && getCheckedInYouth().length >= 1 && (
          <>
            <Card sx={{ mb: 3, mx: { xs: 2, sm: 0 }, bgcolor: 'success.dark', borderRadius: 3, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
              <CardContent sx={{ px: { xs: 2, sm: 3 }, py: { xs: 2, sm: 2.5 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 2, sm: 0 } }}>
                  <Box sx={{ textAlign: { xs: 'center', sm: 'left' } }}>
                    <Typography variant="h6" color="success.contrastText">
                      🎲 Random Selector
                    </Typography>
                    <Typography variant="body2" color="success.contrastText" sx={{ opacity: 0.8 }}>
                      Randomly choose from {getCheckedInYouth().length} checked-in youth
                    </Typography>
                  </Box>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={openRandomSelector}
                    disabled={isSpinning}
                    sx={{ minWidth: 120, width: { xs: '100%', sm: 'auto' } }}
                  >
                    🎯 Pick Random Youth
                  </Button>
                </Box>
              </CardContent>
            </Card>
            {/* Card Flip Dialog */}
            <Dialog open={randomSelectorOpen} onClose={closeRandomSelector} maxWidth="sm" fullWidth>
              <DialogContent style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 32 }}>
                <div className="card-container" style={{ width: 400, height: 250, margin: '0 auto', perspective: '1400px' }}>
                  <div
                    className="card"
                    ref={cardRef}
                    style={{
                      position: 'relative',
                      height: '100%',
                      borderRadius: 10,
                      width: '100%',
                      transformStyle: 'preserve-3d',
                      transition: 'background 0.3s',
                      background: winner ? '#FFD700' : isCardFront ? '#2196f3' : '#fff',
                    }}
                  >
                    <div
                      className="front"
                      style={{
                        display: 'flex',
                        width: '100%',
                        height: '100%',
                        borderRadius: 10,
                        justifyContent: 'center',
                        alignItems: 'center',
                        backfaceVisibility: 'hidden',
                        color: '#fff',
                        background: '#2196f3',
                        fontSize: 120,
                        fontWeight: 'bold',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        opacity: isCardFront ? 1 : 0,
                        transition: 'opacity 0.2s',
                      }}
                    >
                      {cardFrontName}
                    </div>
                    <div
                      className="back"
                      style={{
                        display: 'flex',
                        width: '100%',
                        height: '100%',
                        borderRadius: 10,
                        justifyContent: 'center',
                        alignItems: 'center',
                        backfaceVisibility: 'hidden',
                        color: '#2196f3',
                        background: '#fff',
                        fontSize: 120,
                        fontWeight: 'bold',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        transform: 'rotateY(180deg)',
                        opacity: isCardFront ? 0 : 1,
                        transition: 'opacity 0.2s',
                      }}
                    >
                      {cardBackName}
                    </div>
                  </div>
                </div>
                <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                  <Button
                    onClick={spinForRandomYouth}
                    disabled={isSpinning}
                    variant="contained"
                    size="large"
                  >
                    {isSpinning ? '🌪️ Spinning...' : '🎯 SPIN!'}
                  </Button>
                  <Button
                    onClick={closeRandomSelector}
                    disabled={isSpinning}
                    variant="outlined"
                    size="large"
                  >
                    Close
                  </Button>
                </Box>
                {winner && (
                  <Typography variant="h4" sx={{ mt: 3, color: '#FFD700', fontWeight: 'bold' }}>
                    🎉 Winner: {winner} 🎉
                  </Typography>
                )}
              </DialogContent>
            </Dialog>
          </>
        )}
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