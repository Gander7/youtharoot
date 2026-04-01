import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Stack,
  Grid,
  Box,
  Tabs,
  Tab,
  Typography,
  InputAdornment,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import {
  Phone as PhoneIcon,
  Email as EmailIcon,
  School as SchoolIcon,
  Work as WorkIcon
} from '@mui/icons-material';
import { apiRequest } from '../stores/auth';
import ParentManagementTab from './ParentManagementTab';

const PersonForm = ({ open, onClose, person, onSave, personType, getToken = null }) => {
  console.log('PersonForm received:', { person, personType });
  
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    phone_number: '',
    sms_opt_out: false,
    parental_permission_2026: false,
    photo_consent_2026: false,
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
      parental_permission_2026: false,
      photo_consent_2026: false,
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
        if (key === 'sms_opt_out' || key === 'parental_permission_2026' || key === 'photo_consent_2026') {
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
      // Reset to first tab
      setTabValue(0);
        const baseData = {
        first_name: '',
        last_name: '',
        phone_number: '',
        sms_opt_out: false,
        parental_permission_2026: false,
        photo_consent_2026: false,
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
        ...(person || {}),
      };
      // Convert null/undefined values to appropriate defaults
      Object.keys(baseData).forEach(key => {
        if (baseData[key] === null || baseData[key] === undefined) {
          if (key === 'sms_opt_out' || key === 'parental_permission_2026' || key === 'photo_consent_2026') {
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
      personData.parental_permission_2026 = formData.parental_permission_2026 || false;
      personData.photo_consent_2026 = formData.photo_consent_2026 || false;
    } else if (personType === 'leader') {
      console.log(formData);
      personData.role = formData.role;
      if (formData.birth_date) {
        personData.birth_date = formData.birth_date;
      }
    } else if (personType === 'parent') {
      // Parent-specific fields - always include even if empty
      personData.email = formData.email || '';
      personData.address = formData.address || '';
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
      }, getToken);
      
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
                <Tab label="Contacts" />
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
                    {personType === 'youth' && (
                      <Grid item xs={6} sm={6}>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={formData.parental_permission_2026}
                              onChange={(e) => setFormData({ ...formData, parental_permission_2026: e.target.checked })}
                            />
                          }
                          label="Parental Permission"
                        />
                      </Grid>
                    )}
                    {personType === 'youth' && (
                      <Grid item xs={6} sm={6}>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={formData.photo_consent_2026}
                              onChange={(e) => setFormData({ ...formData, photo_consent_2026: e.target.checked })}
                            />
                          }
                          label="Photo Consent"
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
                  getToken={getToken}
                  onParentAdded={() => {
                    // Refresh parent list
                    console.log('Parent added to youth');
                  }}
                />
              )}

              {tabValue === 2 && (
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

export default PersonForm;
