import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  Checkbox,
  FormControlLabel,
  Grid,
  Card,
  CardContent,
  TextField,
  InputAdornment
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import {
  Delete,
  PersonAdd,
  Search,
  Close
} from '@mui/icons-material';
import { apiRequest } from '../stores/auth';

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
      secondary: '#e0e0e0',
    },
  },
});

function PersonSelectionDialog({ open, onClose, onConfirm, availablePeople, loading }) {
  const [selectedPeople, setSelectedPeople] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredPeople = availablePeople.filter(person =>
    `${person.first_name} ${person.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
    person.phone_number?.includes(searchTerm)
  );

  const handlePersonToggle = (personId) => {
    setSelectedPeople(prev => 
      prev.includes(personId) 
        ? prev.filter(id => id !== personId)
        : [...prev, personId]
    );
  };

  const handleSelectAll = () => {
    const filteredIds = filteredPeople.map(person => person.id);
    setSelectedPeople(filteredIds);
  };

  const handleDeselectAll = () => {
    setSelectedPeople([]);
  };

  const areAllFilteredSelected = filteredPeople.length > 0 && 
    filteredPeople.every(person => selectedPeople.includes(person.id));

  const areSomeFilteredSelected = filteredPeople.some(person => selectedPeople.includes(person.id));

  const handleConfirm = () => {
    onConfirm(selectedPeople);
    setSelectedPeople([]);
    setSearchTerm('');
  };

  const handleClose = () => {
    setSelectedPeople([]);
    setSearchTerm('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Add Members</DialogTitle>
      <DialogContent>
        <TextField
          fullWidth
          placeholder="Search people..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ mb: 2 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            )
          }}
        />
        
        {/* Select All / Deselect All buttons */}
        {filteredPeople.length > 0 && (
          <Box display="flex" gap={1} mb={2}>
            <Button
              size="small"
              variant={areAllFilteredSelected ? "contained" : "outlined"}
              onClick={areAllFilteredSelected ? handleDeselectAll : handleSelectAll}
              disabled={loading}
            >
              {areAllFilteredSelected ? "Deselect All" : "Select All"}
              {!areAllFilteredSelected && ` (${filteredPeople.length})`}
            </Button>
            {areSomeFilteredSelected && !areAllFilteredSelected && (
              <Button
                size="small"
                variant="outlined"
                onClick={handleDeselectAll}
                disabled={loading}
              >
                Clear Selection
              </Button>
            )}
          </Box>
        )}
        
        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : filteredPeople.length === 0 ? (
          <Alert severity="info">
            {searchTerm ? 'No people match your search.' : 'No people available to add.'}
          </Alert>
        ) : (
          <Grid container spacing={1}>
            {filteredPeople.map((person) => (
              <Grid item xs={12} sm={6} key={person.id}>
                <Card variant="outlined" sx={{ cursor: 'pointer' }}>
                  <CardContent sx={{ p: 2 }}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={selectedPeople.includes(person.id)}
                          onChange={() => handlePersonToggle(person.id)}
                          name={`${person.first_name} ${person.last_name}`}
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body1">
                            {person.first_name} {person.last_name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {person.phone_number}
                          </Typography>
                          <Chip 
                            label={person.person_type === 'youth' ? 'Youth' : 
                                   person.person_type === 'leader' ? 'Leader' : 'Parent'} 
                            size="small" 
                            color={person.person_type === 'youth' ? 'primary' : 
                                   person.person_type === 'leader' ? 'secondary' : 'success'}
                          />
                        </Box>
                      }
                      sx={{ width: '100%', m: 0 }}
                    />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
        
        {selectedPeople.length > 0 && (
          <Alert severity="success" sx={{ mt: 2 }}>
            {selectedPeople.length} people selected
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button 
          onClick={handleConfirm} 
          variant="contained" 
          disabled={selectedPeople.length === 0}
        >
          Add Selected
        </Button>
      </DialogActions>
    </Dialog>
  );
}

function GroupMemberManager({ open, onClose, group, onMembershipChange }) {
  const [members, setMembers] = useState([]);
  const [availablePeople, setAvailablePeople] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingPeople, setLoadingPeople] = useState(false);
  const [error, setError] = useState(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);

  const loadMembers = useCallback(async () => {
    if (!group) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiRequest(`/groups/${group.id}/members`);
      if (response.ok) {
        const membersData = await response.json();
        setMembers(membersData);
      } else {
        throw new Error('Failed to load members');
      }
    } catch (err) {
      console.error('Error loading members:', err);
      setError('Failed to load group members');
    } finally {
      setLoading(false);
    }
  }, [group]);

  useEffect(() => {
    if (open && group) {
      loadMembers();
    }
  }, [open, loadMembers]);

  const loadAvailablePeople = async () => {
    try {
      setLoadingPeople(true);
      
      // Fetch youth, leaders, and parents
      const [youthResponse, leadersResponse, parentsResponse] = await Promise.all([
        apiRequest('/person/youth'),
        apiRequest('/person/leaders'),
        apiRequest('/parents')
      ]);
      
      if (youthResponse.ok && leadersResponse.ok && parentsResponse.ok) {
        const youth = await youthResponse.json();
        const leaders = await leadersResponse.json();
        const parents = await parentsResponse.json();
        
        // Add person_type to each person to ensure correct display
        const youthWithType = youth.map(person => ({ ...person, person_type: 'youth' }));
        const leadersWithType = leaders.map(person => ({ ...person, person_type: 'leader' }));
        const parentsWithType = parents.map(person => ({ ...person, person_type: 'parent' }));
        const allPeople = [...youthWithType, ...leadersWithType, ...parentsWithType];
        
        // Filter out people who are already members
        const memberPersonIds = members.map(m => m.person_id);
        const available = allPeople.filter(person => !memberPersonIds.includes(person.id));
        
        setAvailablePeople(available);
      }
    } catch (err) {
      console.error('Error loading people:', err);
      setError('Failed to load available people');
    } finally {
      setLoadingPeople(false);
    }
  };

  const handleAddMember = async () => {
    await loadAvailablePeople();
    setAddDialogOpen(true);
  };

  const handleConfirmAddMembers = async (selectedPersonIds) => {
    try {
      if (selectedPersonIds.length === 1) {
        // Single member addition
        const response = await apiRequest(`/groups/${group.id}/members`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ person_id: selectedPersonIds[0] })
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to add member');
        }
      } else {
        // Bulk member addition
        const response = await apiRequest(`/groups/${group.id}/members/bulk`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ person_ids: selectedPersonIds })
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to add members');
        }
      }
      
      // Refresh members list
      await loadMembers();
      onMembershipChange?.();
      setAddDialogOpen(false);
      
    } catch (err) {
      console.error('Error adding members:', err);
      setError(err.message);
    }
  };

  const handleRemoveMember = async (member) => {
    const confirmed = window.confirm(`Remove ${member.person.first_name} ${member.person.last_name} from ${group.name}?`);
    
    if (!confirmed) {
      return;
    }

    try {
      const response = await apiRequest(`/groups/${group.id}/members/${member.person_id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error('Failed to remove member');
      }
      
      // Refresh members list
      await loadMembers();
      onMembershipChange?.();
      
    } catch (err) {
      console.error('Error removing member:', err);
      setError('Failed to remove member');
    }
  };

  const formatJoinDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (!group) {
    return null;
  }

  return (
    <ThemeProvider theme={darkTheme}>
      <>
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
          <DialogTitle>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="h6">
                Manage Members - {group.name}
            </Typography>
            <IconButton onClick={onClose} size="small">
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Current Members ({members.length})
            </Typography>
            <Button
              variant="contained"
              startIcon={<PersonAdd />}
              onClick={handleAddMember}
              disabled={loading}
            >
              Add Member
            </Button>
          </Box>
          
          {loading ? (
            <Box display="flex" justifyContent="center" p={3}>
              <CircularProgress />
            </Box>
          ) : members.length === 0 ? (
            <Alert severity="info">
              No members in this group yet.
            </Alert>
          ) : (
            <List>
              {members.map((member, index) => (
                <React.Fragment key={member.id}>
                  <ListItem>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body1">
                            {member.person.first_name} {member.person.last_name}
                          </Typography>
                          <Chip 
                            label={member.person.person_type === 'youth' ? 'Youth' : 
                                   member.person.person_type === 'leader' ? 'Leader' : 'Parent'} 
                            size="small" 
                            color={member.person.person_type === 'youth' ? 'primary' : 
                                   member.person.person_type === 'leader' ? 'secondary' : 'success'}
                          />
                        </Box>
                      }
                      secondary={
                        <Typography variant="body2">
                          {member.person.phone_number}
                        </Typography>
                      }
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        aria-label={`Remove ${member.person.first_name} ${member.person.last_name} from group`}
                        onClick={() => handleRemoveMember(member)}
                        color="error"
                      >
                        <Delete />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < members.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={onClose}>Close</Button>
        </DialogActions>
      </Dialog>
      
      <PersonSelectionDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        onConfirm={handleConfirmAddMembers}
        availablePeople={availablePeople}
        loading={loadingPeople}
      />
      </>
    </ThemeProvider>
  );
}

export default GroupMemberManager;