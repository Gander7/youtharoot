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
  ToggleButton,
  ToggleButtonGroup,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Paper,
  Divider,
  Stack
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { apiRequest } from '../stores/auth';
import {
  Search as SearchIcon,
  Person as PersonIcon,
  School as SchoolIcon,
  Work as WorkIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';

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

const PersonForm = ({ open, onClose, person, onSave, personType }) => {
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone_number: '',
    grade: '',
    school_name: '',
    birth_date: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: '',
    role: '',
    ...person
  });

  // Reset form data when person prop changes
  useEffect(() => {
    console.log('PersonForm useEffect triggered, person:', person);
    const baseData = {
      first_name: '',
      last_name: '',
      phone_number: '',
      school_name: '',
      birth_date: '',
      emergency_contact_name: '',
      emergency_contact_phone: '',
      emergency_contact_relationship: '',
      role: '',
      ...(person || {}),
    };
    baseData.grade = person?.grade ? String(person.grade) : '';
    setFormData(baseData);
  }, [person]);

  // Also reset form when dialog opens
  useEffect(() => {
    if (open) {
      console.log('PersonForm dialog opened, person:', person);
      const baseData = {
        first_name: '',
        last_name: '',
        phone_number: '',
        grade: '',
        school_name: '',
        birth_date: '',
        emergency_contact_name: '',
        emergency_contact_phone: '',
        emergency_contact_relationship: '',
        role: '',
        ...(person || {}),
      };
      baseData.grade = person?.grade ? String(person.grade) : '';
      setFormData(baseData);
    }
  }, [open, person]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.first_name?.trim() || !formData.last_name?.trim()) {
      alert('First name and last name are required');
      return;
    }
    
    if (personType === 'leader' && !formData.role?.trim()) {
      alert('Role is required for leaders');
      return;
    }
    
    // Prepare data based on person type
    const personData = {
      // Don't include ID for new persons, let backend auto-generate
      first_name: formData.first_name,
      last_name: formData.last_name,
      phone_number: formData.phone_number || null,
    };

    // Include ID only if editing existing person
    if (person && person.id) {
      personData.id = person.id;
    }

    if (personType === 'youth') {
      // Only set grade if provided and valid
      if (formData.grade && formData.grade.toString().trim() !== '') {
        personData.grade = parseInt(formData.grade);
      }
      // Only set school_name if provided
      if (formData.school_name && formData.school_name.trim() !== '') {
        personData.school_name = formData.school_name;
      }
      personData.birth_date = formData.birth_date;
      personData.emergency_contact_name = formData.emergency_contact_name || '';
      personData.emergency_contact_phone = formData.emergency_contact_phone || '';
      personData.emergency_contact_relationship = formData.emergency_contact_relationship || '';
    } else {
      console.log(formData);
      personData.role = formData.role;
      if (formData.birth_date) {
        personData.birth_date = formData.birth_date;
      }
    }

    try {
      let url = '/person';
      let method = 'POST';
      
      // If editing existing person, use PUT with person ID in URL
      if (person && person.id) {
        url = `/person/${person.id}`;
        method = 'PUT';
      }
      
      console.log('🚀 About to send request:', {
        url,
        method,
        personType,
        payload: personData
      });
      
      const response = await apiRequest(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(personData),
      });
      
      console.log('📡 Response received:', {
        ok: response.ok,
        status: response.status,
        statusText: response.statusText
      });
      
      if (response.ok) {
        const responseData = await response.json();
        console.log('✅ Person saved successfully:', responseData);
        onSave();
        onClose();
      } else {
        // Log the error response for debugging
        const errorText = await response.text();
        console.error('❌ Failed to save person:', {
          status: response.status,
          statusText: response.statusText,
          error: errorText,
          payload: personData
        });
        alert(`Failed to save ${personType}: ${response.status} - ${response.statusText}\n\nError: ${errorText}`);
      }
    } catch (error) {
      console.error('❌ Network error saving person:', error);
      alert(`Network error saving ${personType}: ${error.message}`);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          {person ? 'Edit' : 'Add'} {personType === 'youth' ? 'Youth' : 'Leader'}
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  label="First Name"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  required
                  fullWidth
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Last Name"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  required
                  fullWidth
                />
              </Grid>
            </Grid>
            
            <TextField
              label="Phone Number"
              value={formData.phone_number}
              onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PhoneIcon />
                  </InputAdornment>
                ),
              }}
              fullWidth
            />

            {personType === 'youth' ? (
              <>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      label="Grade"
                      type="number"
                      value={formData.grade}
                      onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
                      fullWidth
                      inputProps={{ min: 1, max: 12 }}
                      helperText="Optional"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      label="Birth Date"
                      type="date"
                      value={formData.birth_date}
                      onChange={(e) => setFormData({ ...formData, birth_date: e.target.value })}
                      required
                      fullWidth
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>
                </Grid>
                
                <TextField
                  label="School Name"
                  value={formData.school_name}
                  onChange={(e) => setFormData({ ...formData, school_name: e.target.value })}
                  fullWidth
                  helperText="Optional"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SchoolIcon />
                      </InputAdornment>
                    ),
                  }}
                />

                <Divider />
                <Typography variant="h6" color="primary">Emergency Contact</Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Contact Name (Optional)"
                      value={formData.emergency_contact_name}
                      onChange={(e) => setFormData({ ...formData, emergency_contact_name: e.target.value })}
                      fullWidth
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Relationship (Optional)"
                      value={formData.emergency_contact_relationship}
                      onChange={(e) => setFormData({ ...formData, emergency_contact_relationship: e.target.value })}
                      fullWidth
                    />
                  </Grid>
                </Grid>
                
                <TextField
                  label="Emergency Contact Phone (Optional)"
                  value={formData.emergency_contact_phone}
                  onChange={(e) => setFormData({ ...formData, emergency_contact_phone: e.target.value })}
                  fullWidth
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PhoneIcon />
                      </InputAdornment>
                    ),
                  }}
                />
              </>
            ) : (
              <>
                <TextField
                  label="Role"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  required
                  fullWidth
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <WorkIcon />
                      </InputAdornment>
                    ),
                  }}
                />
                <TextField
                  label="Birth Date (Optional)"
                  type="date"
                  value={formData.birth_date}
                  onChange={(e) => setFormData({ ...formData, birth_date: e.target.value })}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
              </>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained">
            {person ? 'Update' : 'Add'} {personType === 'youth' ? 'Youth' : 'Leader'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default function PersonList() {
  const [persons, setPersons] = useState([]);
  const [filteredPersons, setFilteredPersons] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('youth');
  const [formOpen, setFormOpen] = useState(false);
  const [editingPerson, setEditingPerson] = useState(null);
  const [personType, setPersonType] = useState('youth');

  const fetchPersons = async () => {
    try {
      const allPersons = [];
      
      // Fetch youth
      const youthResponse = await apiRequest('/person/youth');
      if (youthResponse.ok) {
        const youthData = await youthResponse.json();
        allPersons.push(...youthData.map(p => ({ ...p, type: 'youth' })));
      }
      
      // Fetch leaders
      const leadersResponse = await apiRequest('/person/leaders');
      if (leadersResponse.ok) {
        const leadersData = await leadersResponse.json();
        allPersons.push(...leadersData.map(p => ({ ...p, type: 'leader' })));
      }
      
      setPersons(allPersons);
    } catch (error) {
      console.error('Error fetching persons:', error);
      // Set some mock data for demo
      setPersons([
        {
          id: 1,
          first_name: 'Alex',
          last_name: 'Johnson',
          phone_number: '555-0123',
          grade: 10,
          school_name: 'Lincoln High School',
          type: 'youth'
        },
        {
          id: 2,
          first_name: 'Sarah',
          last_name: 'Wilson',
          phone_number: '555-0456',
          role: 'Youth Pastor',
          type: 'leader'
        }
      ]);
    }
  };

  useEffect(() => {
    fetchPersons();
  }, []);

  useEffect(() => {
    // Filter by person type (youth or leader)
    let filtered = persons.filter(p => p.type === filter);
    
    if (searchTerm) {
      filtered = filtered.filter(p => 
        p.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (p.school_name && p.school_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (p.role && p.role.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    
    setFilteredPersons(filtered);
  }, [persons, searchTerm, filter]);

  const handleAddPerson = (type) => {
    setPersonType(type);
    setEditingPerson(null);
    setFormOpen(true);
  };

  const handleEditPerson = (person) => {
    setPersonType(person.type);
    setEditingPerson(person);
    setFormOpen(true);
  };

  const handleSave = () => {
    fetchPersons();
  };

  const getPersonIcon = (person) => {
    return person.type === 'youth' ? <SchoolIcon /> : <WorkIcon />;
  };

  const getPersonDetails = (person) => {
    if (person.type === 'youth') {
      const parts = [];
      if (person.grade) parts.push(`Grade ${person.grade}`);
      if (person.school_name) parts.push(person.school_name);
      return parts.length > 0 ? parts.join(' • ') : 'Youth';
    }
    return person.role;
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <Box sx={{ maxWidth: 800, margin: '0 auto', padding: 2 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1" fontWeight="bold">
            People
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleAddPerson('youth')}
              sx={{ borderRadius: 2 }}
            >
              Add Youth
            </Button>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => handleAddPerson('leader')}
              sx={{ borderRadius: 2 }}
            >
              Add Leader
            </Button>
          </Box>
        </Box>

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
            <ToggleButtonGroup
              value={filter}
              exclusive
              onChange={(e, newFilter) => newFilter && setFilter(newFilter)}
              size="small"
            >
              <ToggleButton value="youth">
                Youth ({persons.filter(p => p.type === 'youth').length})
              </ToggleButton>
              <ToggleButton value="leader">
                Leaders ({persons.filter(p => p.type === 'leader').length})
              </ToggleButton>
            </ToggleButtonGroup>
          </Stack>
        </Paper>

        {/* Person List */}
        {filteredPersons.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <PersonIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              {searchTerm ? 'No people found' : 'No people added yet'}
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              {searchTerm ? 'Try adjusting your search' : 'Add your first youth or leader to get started'}
            </Typography>
          </Paper>
        ) : (
          <List>
            {filteredPersons.map((person) => (
              <Card key={person.id} sx={{ mb: 1.5 }}>
                <ListItem>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: person.type === 'youth' ? 'primary.main' : 'secondary.main' }}>
                      {getPersonIcon(person)}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1" fontWeight="medium">
                          {person.first_name} {person.last_name}
                        </Typography>
                        <Chip
                          label={person.type}
                          size="small"
                          color={person.type === 'youth' ? 'primary' : 'secondary'}
                          variant="outlined"
                        />
                      </Box>
                    }
                    secondary={
                      <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                        <Typography variant="body2" color="text.secondary">
                          {getPersonDetails(person)}
                        </Typography>
                        {person.phone_number && (
                          <Typography variant="body2" color="text.secondary">
                            📱 {person.phone_number}
                          </Typography>
                        )}
                      </Stack>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={() => handleEditPerson(person)}
                      size="small"
                    >
                      <EditIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              </Card>
            ))}
          </List>
        )}

        {/* Add Person Form */}
        <PersonForm
          open={formOpen}
          onClose={() => setFormOpen(false)}
          person={editingPerson}
          onSave={handleSave}
          personType={personType}
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
            onClick={() => handleAddPerson('youth')}
          >
            <AddIcon />
          </Fab>
        </Box>
      </Box>
    </ThemeProvider>
  );
}