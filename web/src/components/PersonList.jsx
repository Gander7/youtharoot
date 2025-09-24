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
    id: Date.now(), // Simple ID generation
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Prepare data based on person type
    const personData = {
      id: formData.id,
      first_name: formData.first_name,
      last_name: formData.last_name,
      phone_number: formData.phone_number || null,
    };

    if (personType === 'youth') {
      personData.grade = parseInt(formData.grade);
      personData.school_name = formData.school_name;
      personData.birth_date = formData.birth_date;
      personData.emergency_contact_name = formData.emergency_contact_name || '';
      personData.emergency_contact_phone = formData.emergency_contact_phone || '';
      personData.emergency_contact_relationship = formData.emergency_contact_relationship || '';
    } else {
      personData.role = formData.role;
      if (formData.birth_date) {
        personData.birth_date = formData.birth_date;
      }
    }

    try {
      const response = await fetch('/person', {
        method: person ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(personData),
      });
      
      if (response.ok) {
        onSave();
        onClose();
      }
    } catch (error) {
      console.error('Error saving person:', error);
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
                      required
                      fullWidth
                      inputProps={{ min: 1, max: 12 }}
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
                  required
                  fullWidth
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
  const [filter, setFilter] = useState('all');
  const [formOpen, setFormOpen] = useState(false);
  const [editingPerson, setEditingPerson] = useState(null);
  const [personType, setPersonType] = useState('youth');

  const fetchPersons = async () => {
    try {
      // For now, we'll fetch youth since that endpoint exists
      const response = await fetch('/person/youth');
      if (response.ok) {
        const data = await response.json();
        setPersons(data.map(p => ({ ...p, type: 'youth' })));
      }
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
    let filtered = persons;
    
    if (filter !== 'all') {
      filtered = persons.filter(p => p.type === filter);
    }
    
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
      return `Grade ${person.grade} • ${person.school_name}`;
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
              <ToggleButton value="all">All ({persons.length})</ToggleButton>
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