import React, { useState, useEffect } from 'react';
import {
  Alert,
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
  Stack,
  Checkbox,
  FormControlLabel,
  Tabs,
  Tab
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { apiRequest } from '../stores/auth';
import ErrorBoundary from './ErrorBoundary.jsx';
import ApiErrorBoundary from './ApiErrorBoundary.jsx';
import {
  Search as SearchIcon,
  Person as PersonIcon,
  School as SchoolIcon,
  Work as WorkIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  FilterList as FilterIcon,
  Delete as DeleteIcon,
  Link as LinkIcon,
  Home as HomeIcon
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
    sms_opt_out: false,
    grade: '',
    school_name: '',
    birth_date: '',
    email: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: '',
    emergency_contact_2_name: '',
    emergency_contact_2_phone: '',
    emergency_contact_2_relationship: '',
    allergies: '',
    other_considerations: '',
    role: '',
    address: '', // For parents
    ...person
  });

  const [tabValue, setTabValue] = useState(0);

  // Reset form data when person prop changes
  useEffect(() => {
    console.log('PersonForm useEffect triggered, person:', person);
    const baseData = {
      first_name: '',
      last_name: '',
      phone_number: '',
      sms_opt_out: false,
      school_name: '',
      birth_date: '',
      email: '',
      emergency_contact_name: '',
      emergency_contact_phone: '',
      emergency_contact_relationship: '',
      emergency_contact_2_name: '',
      emergency_contact_2_phone: '',
      emergency_contact_2_relationship: '',
      allergies: '',
      other_considerations: '',
      role: '',
      address: '', // For parents
      ...(person || {}),
    };
    // Convert null/undefined values to appropriate defaults
    Object.keys(baseData).forEach(key => {
      if (baseData[key] === null || baseData[key] === undefined) {
        if (key === 'sms_opt_out') {
          baseData[key] = false;
        } else if (key === 'grade') {
          baseData[key] = '';
        } else {
          baseData[key] = '';
        }
      }
    });
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
        sms_opt_out: false,
        grade: '',
        school_name: '',
        birth_date: '',
        emergency_contact_name: '',
        emergency_contact_phone: '',
        emergency_contact_relationship: '',
        role: '',
        address: '', // For parents
        ...(person || {}),
      };
      // Convert null/undefined values to appropriate defaults
      Object.keys(baseData).forEach(key => {
        if (baseData[key] === null || baseData[key] === undefined) {
          if (key === 'sms_opt_out') {
            baseData[key] = false;
          } else if (key === 'grade') {
            baseData[key] = '';
          } else {
            baseData[key] = '';
          }
        }
      });
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
      sms_opt_out: formData.sms_opt_out || false,
      person_type: personType, // Explicitly set the person type
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
      personData.email = formData.email || '';
      personData.emergency_contact_name = formData.emergency_contact_name || '';
      personData.emergency_contact_phone = formData.emergency_contact_phone || '';
      personData.emergency_contact_relationship = formData.emergency_contact_relationship || '';
      personData.emergency_contact_2_name = formData.emergency_contact_2_name || '';
      personData.emergency_contact_2_phone = formData.emergency_contact_2_phone || '';
      personData.emergency_contact_2_relationship = formData.emergency_contact_2_relationship || '';
      personData.allergies = formData.allergies || '';
      personData.other_considerations = formData.other_considerations || '';
    } else if (personType === 'leader') {
      console.log(formData);
      personData.role = formData.role;
      if (formData.birth_date) {
        personData.birth_date = formData.birth_date;
      }
    } else if (personType === 'parent') {
      // Parent-specific fields
      if (formData.email && formData.email.trim() !== '') {
        personData.email = formData.email;
      }
      if (formData.address && formData.address.trim() !== '') {
        personData.address = formData.address;
      }
      if (formData.birth_date) {
        personData.birth_date = formData.birth_date;
      }
    }

    try {
      let url = '/person';
      let method = 'POST';
      
      // Use parent endpoint for creating parents
      if (personType === 'parent' && !(person && person.id)) {
        url = '/parent';
      } else if (person && person.id) {
        // If editing existing person, use PUT with person ID in URL (works for all types)
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
          {person ? 'Edit' : 'Add'} {personType === 'youth' ? 'Youth' : personType === 'leader' ? 'Leader' : 'Parent'}
        </DialogTitle>
        <DialogContent>
          {personType === 'youth' ? (
            <Box>
              <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 2 }}>
                <Tab label="Personal Info" />
                <Tab label="Parents" />
                <Tab label="Emergency Contacts (Old)" />
                <Tab label="Health and Allergy" />
              </Tabs>
              
              {tabValue === 0 && (
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
                    type="tel"
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
                    inputProps={{
                      pattern: "^(\\+?1[\\-\\s]?)?\\(?[0-9]{3}\\)?[\\-\\s]?[0-9]{3}[\\-\\s]?[0-9]{4}$",
                      title: "Please enter a valid Canadian phone number: 4165551234, (416) 555-1234, +1-416-555-1234"
                    }}
                    fullWidth
                  />


                  <Grid container spacing={2}>
                    <Grid item xs={8} sm={6}>
                      <TextField
                        label="Grade"
                        type="number"
                        value={formData.grade}
                        onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
                        slotProps={{
                          htmlInput: { min: 1, max: 12 },
                          inputLabel: {
                            style: { 
                              fontSize: '1rem',
                              whiteSpace: 'nowrap'
                            }
                          },
                          input: {
                            style: { minWidth: '120px' }
                          }
                        }}
                        fullWidth
                        style={{ minWidth: '120px' }}
                      />
                    </Grid>
                    <Grid item xs={10} sm={6}>
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
                    {formData.phone_number && (
                      <Grid item xs={6} sm={6}>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={formData.sms_opt_out}
                              onChange={(e) => setFormData({ ...formData, sms_opt_out: e.target.checked })}
                            />
                          }
                          label="SMS Opt out"
                        />
                      </Grid>
                    )}
                  </Grid>
                  
                  <TextField
                    label="Email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    fullWidth
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <EmailIcon />
                        </InputAdornment>
                      ),
                    }}
                  />
                  
                  <TextField
                    label="School Name"
                    value={formData.school_name}
                    onChange={(e) => setFormData({ ...formData, school_name: e.target.value })}
                    fullWidth
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SchoolIcon />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Stack>
              )}

              {tabValue === 1 && (
                <ParentManagementTab 
                  youthId={person?.id}
                  onParentAdded={() => {
                    // Refresh parent list
                    console.log('Parent added to youth');
                  }}
                />
              )}

              {tabValue === 2 && (
                <Stack spacing={3} sx={{ mt: 1 }}>
                  <Paper sx={{ p: 3, bgcolor: 'background.default', border: '1px solid', borderColor: 'divider' }}>
                    <Typography variant="h6" color="warning.main" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                      🔒 Legacy Emergency Contacts (Read-Only)
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      This data is preserved for historical reference only. Please use the "Parents" tab above to manage current emergency contacts.
                    </Typography>
                  </Paper>
                  
                  <Typography variant="h6" color="primary">Primary Emergency Contact</Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        label="Contact Name"
                        value={formData.emergency_contact_name || 'Not specified'}
                        InputProps={{ readOnly: true }}
                        fullWidth
                        sx={{ 
                          '& .MuiInputBase-root': { 
                            bgcolor: 'action.hover',
                            '& input': { color: 'text.secondary' }
                          }
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        label="Relationship"
                        value={formData.emergency_contact_relationship || 'Not specified'}
                        InputProps={{ readOnly: true }}
                        fullWidth
                        sx={{ 
                          '& .MuiInputBase-root': { 
                            bgcolor: 'action.hover',
                            '& input': { color: 'text.secondary' }
                          }
                        }}
                      />
                    </Grid>
                  </Grid>
                  
                  <TextField
                    label="Emergency Contact Phone"
                    value={formData.emergency_contact_phone || 'Not specified'}
                    InputProps={{
                      readOnly: true,
                      startAdornment: (
                        <InputAdornment position="start">
                          <PhoneIcon />
                        </InputAdornment>
                      ),
                    }}
                    fullWidth
                    sx={{ 
                      '& .MuiInputBase-root': { 
                        bgcolor: 'action.hover',
                        '& input': { color: 'text.secondary' }
                      }
                    }}
                  />

                  <Divider />
                  <Typography variant="h6" color="primary">Second Emergency Contact</Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        label="Contact Name"
                        value={formData.emergency_contact_2_name || 'Not specified'}
                        InputProps={{ readOnly: true }}
                        fullWidth
                        sx={{ 
                          '& .MuiInputBase-root': { 
                            bgcolor: 'action.hover',
                            '& input': { color: 'text.secondary' }
                          }
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        label="Relationship"
                        value={formData.emergency_contact_2_relationship || 'Not specified'}
                        InputProps={{ readOnly: true }}
                        fullWidth
                        sx={{ 
                          '& .MuiInputBase-root': { 
                            bgcolor: 'action.hover',
                            '& input': { color: 'text.secondary' }
                          }
                        }}
                      />
                    </Grid>
                  </Grid>
                  
                  <TextField
                    label="Second Emergency Contact Phone"
                    value={formData.emergency_contact_2_phone || 'Not specified'}
                    InputProps={{
                      readOnly: true,
                      startAdornment: (
                        <InputAdornment position="start">
                          <PhoneIcon />
                        </InputAdornment>
                      ),
                    }}
                    fullWidth
                    sx={{ 
                      '& .MuiInputBase-root': { 
                        bgcolor: 'action.hover',
                        '& input': { color: 'text.secondary' }
                      }
                    }}
                  />
                </Stack>
              )}
              
              {tabValue === 3 && (
                <Stack spacing={3} sx={{ mt: 1 }}>
                  <Typography variant="h6" color="primary">Health and Allergy Information</Typography>
                  
                  <TextField
                    label="Allergies"
                    multiline
                    rows={4}
                    value={formData.allergies || ''}
                    onChange={(e) => {
                      const value = e.target.value;
                      if (value.length <= 1000) {
                        setFormData({ ...formData, allergies: value });
                      }
                    }}
                    fullWidth
                    placeholder="Please list any known allergies (food, environmental, medications, etc.)"
                    helperText={`${(formData.allergies || '').length}/1000 characters`}
                    inputProps={{ maxLength: 1000 }}
                  />
                  
                  <TextField
                    label="Other Medical Considerations"
                    multiline
                    rows={4}
                    value={formData.other_considerations || ''}
                    onChange={(e) => {
                      const value = e.target.value;
                      if (value.length <= 1000) {
                        setFormData({ ...formData, other_considerations: value });
                      }
                    }}
                    fullWidth
                    placeholder="Please list any other medical conditions, medications, or considerations staff should be aware of"
                    helperText={`${(formData.other_considerations || '').length}/1000 characters`}
                    inputProps={{ maxLength: 1000 }}
                  />
                </Stack>
              )}
            </Box>
          ) : personType === 'leader' ? (
            // Leader form (no tabs needed)
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
              type="tel"
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
              inputProps={{
                pattern: "^(\\+?1[\\-\\s]?)?\\(?[0-9]{3}\\)?[\\-\\s]?[0-9]{3}[\\-\\s]?[0-9]{4}$",
                title: "Please enter a valid Canadian phone number: (416) 555-1234 or +1-416-555-1234"
              }}
              placeholder="(416) 555-1234"
              helperText="Canadian format: (416) 555-1234 or +1-416-555-1234"
              fullWidth
            />

            {formData.phone_number && (
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.sms_opt_out}
                    onChange={(e) => setFormData({ ...formData, sms_opt_out: e.target.checked })}
                  />
                }
                label="Opt out of SMS messages"
              />
            )}

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
              label="Birth Date"
              type="date"
              value={formData.birth_date}
              onChange={(e) => setFormData({ ...formData, birth_date: e.target.value })}
              fullWidth
              InputLabelProps={{ shrink: true }}
            />
            </Stack>
          ) : (
            // Parent form 
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
                type="tel"
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
                inputProps={{
                  pattern: "^(\\+?1[\\-\\s]?)?\\(?[0-9]{3}\\)?[\\-\\s]?[0-9]{3}[\\-\\s]?[0-9]{4}$",
                  title: "Please enter a valid Canadian phone number: (416) 555-1234 or +1-416-555-1234"
                }}
                placeholder="(416) 555-1234"
                helperText="Canadian format: (416) 555-1234 or +1-416-555-1234"
                fullWidth
              />

              <TextField
                type="email"
                label="Email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <EmailIcon />
                    </InputAdornment>
                  ),
                }}
                placeholder="parent@example.com"
                fullWidth
              />

              <TextField
                label="Address"
                multiline
                rows={2}
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                fullWidth
                placeholder="Street address, city, province, postal code"
              />

              {formData.phone_number && (
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.sms_opt_out}
                      onChange={(e) => setFormData({ ...formData, sms_opt_out: e.target.checked })}
                    />
                  }
                  label="Opt out of SMS messages"
                />
              )}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained">
            {person ? 'Update' : 'Add'} {personType === 'youth' ? 'Youth' : personType === 'leader' ? 'Leader' : 'Parent'}
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

      // Fetch parents
      const parentsResponse = await apiRequest('/parents');
      if (parentsResponse.ok) {
        const parentsData = await parentsResponse.json();
        allPersons.push(...parentsData.map(p => ({ ...p, type: 'parent' })));
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
      const searchLower = searchTerm.trim().toLowerCase();
      filtered = filtered.filter(p => {
        const fullName = `${p.first_name} ${p.last_name}`.toLowerCase();
        return fullName.includes(searchLower) ||
               (p.school_name && p.school_name.toLowerCase().includes(searchLower));
      });
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
    if (person.type === 'youth') return <SchoolIcon />;
    if (person.type === 'leader') return <WorkIcon />;
    return <PersonIcon />; // For parents
  };

  const getPersonDetails = (person) => {
    if (person.type === 'youth') {
      const parts = [];
      if (person.grade) parts.push(`Grade ${person.grade}`);
      if (person.school_name) parts.push(person.school_name);
      return parts.length > 0 ? parts.join(' • ') : 'Youth';
    }
    if (person.type === 'leader') {
      return person.role;
    }
    return 'Parent'; // For parents
  };

  return (
    <ErrorBoundary level="component" title="People Management Error">
      <ApiErrorBoundary>
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
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => handleAddPerson('parent')}
              sx={{ borderRadius: 2 }}
            >
              Add Parent
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
              <ToggleButton value="parent">
                Parents ({persons.filter(p => p.type === 'parent').length})
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
                    <Avatar sx={{ 
                      bgcolor: person.type === 'youth' ? 'primary.main' : 
                               person.type === 'leader' ? 'secondary.main' : 
                               'success.main' 
                    }}>
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
                          color={person.type === 'youth' ? 'primary' : 
                                 person.type === 'leader' ? 'secondary' : 
                                 'success'}
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
      </ApiErrorBoundary>
    </ErrorBoundary>
  );
}

// Parent Management Tab Component
function ParentManagementTab({ youthId, onParentAdded }) {
  const [linkedParents, setLinkedParents] = useState([]);
  const [availableParents, setAvailableParents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showAddNew, setShowAddNew] = useState(false);
  
  // New parent form state
  const [newParentData, setNewParentData] = useState({
    first_name: '',
    last_name: '',
    phone_number: '',
    address: '',
    relationship_type: 'parent',
    is_primary_contact: false
  });

  useEffect(() => {
    if (youthId) {
      fetchLinkedParents();
      fetchAvailableParents();
    }
  }, [youthId]);

  const fetchLinkedParents = async () => {
    try {
      const response = await apiRequest(`/youth/${youthId}/parents`);
      if (response.ok) {
        const parents = await response.json();
        setLinkedParents(parents);
      }
    } catch (err) {
      console.error('Failed to fetch linked parents:', err);
    }
  };

  const fetchAvailableParents = async () => {
    try {
      const response = await apiRequest('/parents');
      if (response.ok) {
        const allParents = await response.json();
        setAvailableParents(allParents);
      }
    } catch (err) {
      console.error('Failed to fetch available parents:', err);
    }
  };

  const handleLinkExistingParent = async (parentId, relationshipType = 'parent') => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await apiRequest(`/youth/${youthId}/parents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          parent_id: parentId,
          relationship_type: relationshipType,
          is_primary_contact: linkedParents.length === 0 // First parent is primary
        })
      });

      if (response.ok) {
        setSuccess('Parent linked successfully!');
        fetchLinkedParents();
        onParentAdded();
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to link parent');
      }
    } catch (err) {
      setError('Network error linking parent');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAndLink = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      // First create the parent
      const createResponse = await apiRequest('/parent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: newParentData.first_name,
          last_name: newParentData.last_name,
          phone_number: newParentData.phone_number,
          address: newParentData.address,
          person_type: 'parent'
        })
      });

      if (createResponse.ok) {
        const newParent = await createResponse.json();
        
        // Then link the parent to youth
        const linkResponse = await apiRequest(`/youth/${youthId}/parents`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            parent_id: newParent.id,
            relationship_type: newParentData.relationship_type,
            is_primary_contact: newParentData.is_primary_contact
          })
        });

        if (linkResponse.ok) {
          setSuccess('Parent created and linked successfully!');
          setShowAddNew(false);
          setNewParentData({
            first_name: '',
            last_name: '',
            phone_number: '',
            address: '',
            relationship_type: 'parent',
            is_primary_contact: false
          });
          fetchLinkedParents();
          fetchAvailableParents();
          onParentAdded();
        } else {
          const error = await linkResponse.json();
          setError(error.detail || 'Failed to link new parent');
        }
      } else {
        const error = await createResponse.json();
        setError(error.detail || 'Failed to create parent');
      }
    } catch (err) {
      setError('Network error creating parent');
    } finally {
      setLoading(false);
    }
  };

  const handleUnlinkParent = async (parentId) => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await apiRequest(`/youth/${youthId}/parents/${parentId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setSuccess('Parent unlinked successfully!');
        fetchLinkedParents();
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to unlink parent');
      }
    } catch (err) {
      setError('Network error unlinking parent');
    } finally {
      setLoading(false);
    }
  };

  if (!youthId) {
    return (
      <Stack spacing={3} sx={{ mt: 1 }}>
        <Typography variant="h6" color="primary">Parent Information</Typography>
        <Paper sx={{ p: 3, bgcolor: 'background.default' }}>
          <Typography variant="body2" color="text.secondary">
            Please save this youth first to manage parent relationships.
          </Typography>
        </Paper>
      </Stack>
    );
  }

  return (
    <Stack spacing={3} sx={{ mt: 1 }}>
      <Typography variant="h6" color="primary">Parent Information</Typography>
      
      {error && <Alert severity="error">{error}</Alert>}
      {success && <Alert severity="success">{success}</Alert>}
      
      {/* Linked Parents */}
      <Paper sx={{ p: 3, bgcolor: 'background.default' }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Linked Parents</Typography>
        
        {linkedParents.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            No parents linked to this youth yet.
          </Typography>
        ) : (
          <List>
            {linkedParents.map((relationship) => (
              <ListItem key={relationship.id} divider>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: 'success.main' }}>
                    <PersonIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={`${relationship.parent.first_name} ${relationship.parent.last_name}`}
                  secondary={
                    <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                      <Chip 
                        label={relationship.relationship_type} 
                        size="small" 
                        color="primary" 
                      />
                      {relationship.is_primary_contact && (
                        <Chip 
                          label="Primary Contact" 
                          size="small" 
                          color="success" 
                        />
                      )}
                      {relationship.parent.phone_number && (
                        <Chip 
                          icon={<PhoneIcon />}
                          label={relationship.parent.phone_number} 
                          size="small" 
                          variant="outlined"
                        />
                      )}
                    </Stack>
                  }
                />
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    color="error"
                    onClick={() => handleUnlinkParent(relationship.parent.id)}
                    disabled={loading}
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}
      </Paper>

      {/* Add Parent Options */}
      <Paper sx={{ p: 3, bgcolor: 'background.default' }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Add Parent</Typography>
        
        <Stack spacing={2}>
          <Button
            variant="outlined"
            startIcon={<LinkIcon />}
            onClick={() => setShowAddNew(!showAddNew)}
            disabled={loading}
          >
            {showAddNew ? 'Cancel' : 'Create New Parent'}
          </Button>

          {/* Create New Parent Form */}
          {showAddNew && (
            <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
              <Typography variant="subtitle2" sx={{ mb: 2 }}>New Parent Information</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    label="First Name"
                    value={newParentData.first_name}
                    onChange={(e) => setNewParentData({...newParentData, first_name: e.target.value})}
                    fullWidth
                    required
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    label="Last Name"
                    value={newParentData.last_name}
                    onChange={(e) => setNewParentData({...newParentData, last_name: e.target.value})}
                    fullWidth
                    required
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    label="Phone"
                    value={newParentData.phone_number}
                    onChange={(e) => setNewParentData({...newParentData, phone_number: e.target.value})}
                    fullWidth
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <PhoneIcon />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControl fullWidth>
                    <InputLabel>Relationship</InputLabel>
                    <Select
                      value={newParentData.relationship_type}
                      onChange={(e) => setNewParentData({...newParentData, relationship_type: e.target.value})}
                    >
                      <MenuItem value="mother">Mother</MenuItem>
                      <MenuItem value="father">Father</MenuItem>
                      <MenuItem value="parent">Parent</MenuItem>
                      <MenuItem value="guardian">Guardian</MenuItem>
                      <MenuItem value="step-parent">Step-parent</MenuItem>
                      <MenuItem value="grandparent">Grandparent</MenuItem>
                      <MenuItem value="other">Other</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Address"
                    value={newParentData.address}
                    onChange={(e) => setNewParentData({...newParentData, address: e.target.value})}
                    fullWidth
                    multiline
                    rows={2}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <HomeIcon />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={newParentData.is_primary_contact}
                        onChange={(e) => setNewParentData({...newParentData, is_primary_contact: e.target.checked})}
                      />
                    }
                    label="Set as primary contact"
                  />
                </Grid>
              </Grid>
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  onClick={handleCreateAndLink}
                  disabled={loading || !newParentData.first_name || !newParentData.last_name}
                >
                  Create & Link Parent
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => setShowAddNew(false)}
                  disabled={loading}
                >
                  Cancel
                </Button>
              </Box>
            </Box>
          )}

          {/* Link Existing Parent */}
          {availableParents.length > 0 && (
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Or link an existing parent:
              </Typography>
              <List sx={{ maxHeight: 200, overflow: 'auto', bgcolor: 'background.paper', borderRadius: 1 }}>
                {availableParents
                  .filter(parent => !linkedParents.some(rel => rel.parent.id === parent.id))
                  .map((parent) => (
                  <ListItem 
                    key={parent.id} 
                    button
                    onClick={() => handleLinkExistingParent(parent.id)}
                    disabled={loading}
                  >
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        <PersonIcon />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={`${parent.first_name} ${parent.last_name}`}
                      secondary={parent.phone_number}
                    />
                    <ListItemSecondaryAction>
                      <IconButton edge="end" disabled>
                        <LinkIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </Stack>
      </Paper>
    </Stack>
  );
}