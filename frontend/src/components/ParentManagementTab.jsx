import React, { useState, useEffect } from 'react';
import {
  Stack,
  Typography,
  Paper,
  Alert,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Avatar,
  IconButton,
  Chip,
  Button,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Divider
} from '@mui/material';
import {
  Person as PersonIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Home as HomeIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Link as LinkIcon
} from '@mui/icons-material';
import { apiRequest } from '../stores/auth';

export default function ParentManagementTab({ youthId, onParentAdded, getToken = null }) {
  const [linkedParents, setLinkedParents] = useState([]);
  const [availableParents, setAvailableParents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showAddNew, setShowAddNew] = useState(false);
  
  // Edit relationship state
  const [editingRelationship, setEditingRelationship] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editData, setEditData] = useState({
    // Parent properties
    first_name: '',
    last_name: '',
    phone_number: '',
    email: '',
    address: '',
    sms_opt_out: false,
    // Relationship properties
    relationship_type: 'parent',
    is_primary_contact: false
  });
  
  // New parent form state
  const [newParentData, setNewParentData] = useState({
    first_name: '',
    last_name: '',
    phone_number: '',
    email: '',
    address: '',
    relationship_type: 'parent',
    is_primary_contact: true
  });

  useEffect(() => {
    if (youthId) {
      fetchLinkedParents();
      fetchAvailableParents();
    }
  }, [youthId]);

  const fetchLinkedParents = async () => {
    try {
      const response = await apiRequest(`/youth/${youthId}/parents`, {}, getToken);
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
      const response = await apiRequest('/parents', {}, getToken);
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
      }, getToken);

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
          email: newParentData.email,
          address: newParentData.address,
          person_type: 'parent'
        })
      }, getToken);

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
        }, getToken);

        if (linkResponse.ok) {
          setSuccess('Parent created and linked successfully!');
          setShowAddNew(false);
          setNewParentData({
            first_name: '',
            last_name: '',
            phone_number: '',
            email: '',
            address: '',
            relationship_type: 'parent',
            is_primary_contact: true
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
      }, getToken);

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

  const handleEditRelationship = (relationship) => {
    setEditingRelationship(relationship);
    setEditData({
      // Parent properties
      first_name: relationship.parent.first_name,
      last_name: relationship.parent.last_name,
      phone_number: relationship.parent.phone_number || '',
      email: relationship.parent.email || '',
      address: relationship.parent.address || '',
      sms_opt_out: relationship.parent.sms_opt_out || false,
      // Relationship properties
      relationship_type: relationship.relationship_type,
      is_primary_contact: relationship.is_primary_contact
    });
    setEditDialogOpen(true);
  };

  const handleSaveRelationshipEdit = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      // First, update the parent's information
      const parentUpdateResponse = await apiRequest(
        `/person/${editingRelationship.parent.id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            id: editingRelationship.parent.id,
            first_name: editData.first_name,
            last_name: editData.last_name,
            phone_number: editData.phone_number,
            email: editData.email || '',
            address: editData.address || '',
            sms_opt_out: editData.sms_opt_out || false,
            person_type: 'parent'
          })
        },
        getToken
      );

      if (!parentUpdateResponse.ok) {
        const error = await parentUpdateResponse.json();
        setError(error.detail || 'Failed to update parent information');
        setLoading(false);
        return;
      }

      // Then, update the relationship properties
      const relationshipUpdateResponse = await apiRequest(
        `/youth/${youthId}/parents/${editingRelationship.parent.id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            relationship_type: editData.relationship_type,
            is_primary_contact: editData.is_primary_contact
          })
        },
        getToken
      );

      if (relationshipUpdateResponse.ok) {
        setSuccess('Parent and relationship updated successfully!');
        setEditDialogOpen(false);
        setEditingRelationship(null);
        fetchLinkedParents();
        onParentAdded(); // Refresh parent list
      } else {
        const error = await relationshipUpdateResponse.json();
        setError(error.detail || 'Failed to update relationship');
      }
    } catch (err) {
      setError('Network error updating parent');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditDialogOpen(false);
    setEditingRelationship(null);
    setEditData({
      first_name: '',
      last_name: '',
      phone_number: '',
      email: '',
      address: '',
      relationship_type: 'parent',
      is_primary_contact: false
    });
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
                  <Stack direction="row" spacing={1}>
                    <IconButton
                      edge="end"
                      color="primary"
                      onClick={() => handleEditRelationship(relationship)}
                      disabled={loading}
                      title="Edit relationship"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      edge="end"
                      color="error"
                      onClick={() => handleUnlinkParent(relationship.parent.id)}
                      disabled={loading}
                      title="Unlink parent"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Stack>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}
      </Paper>

      {/* Edit Parent & Relationship Dialog */}
      <Dialog open={editDialogOpen} onClose={handleCancelEdit} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Parent & Relationship</DialogTitle>
        <DialogContent>
          {editingRelationship && (
            <Stack spacing={3} sx={{ mt: 2 }}>
              <Typography variant="subtitle2" color="primary">
                Parent Information
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    label="First Name"
                    value={editData.first_name}
                    onChange={(e) => setEditData({...editData, first_name: e.target.value})}
                    fullWidth
                    required
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    label="Last Name"
                    value={editData.last_name}
                    onChange={(e) => setEditData({...editData, last_name: e.target.value})}
                    fullWidth
                    required
                  />
                </Grid>
              </Grid>

              <TextField
                label="Phone Number"
                value={editData.phone_number}
                onChange={(e) => setEditData({...editData, phone_number: e.target.value})}
                fullWidth
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <PhoneIcon />
                    </InputAdornment>
                  ),
                }}
              />

              <TextField
                label="Email"
                type="email"
                value={editData.email}
                onChange={(e) => setEditData({...editData, email: e.target.value})}
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
                label="Address"
                value={editData.address}
                onChange={(e) => setEditData({...editData, address: e.target.value})}
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

              {editData.phone_number && (
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={editData.sms_opt_out}
                      onChange={(e) => setEditData({...editData, sms_opt_out: e.target.checked})}
                    />
                  }
                  label="Opt out of SMS messages"
                />
              )}

              <Divider />
              
              <Typography variant="subtitle2" color="primary">
                Relationship Details
              </Typography>
              
              <FormControl fullWidth>
                <InputLabel>Relationship Type</InputLabel>
                <Select
                  value={editData.relationship_type}
                  onChange={(e) => setEditData({...editData, relationship_type: e.target.value})}
                  label="Relationship Type"
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

              <FormControlLabel
                control={
                  <Checkbox
                    checked={editData.is_primary_contact}
                    onChange={(e) => setEditData({...editData, is_primary_contact: e.target.checked})}
                  />
                }
                label="Primary Contact"
              />
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelEdit} disabled={loading}>
            Cancel
          </Button>
          <Button 
            onClick={handleSaveRelationshipEdit} 
            variant="contained" 
            disabled={loading || !editData.first_name || !editData.last_name}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

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
                  <TextField
                    label="Email"
                    type="email"
                    value={newParentData.email || ''}
                    onChange={(e) => setNewParentData({...newParentData, email: e.target.value})}
                    fullWidth
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <EmailIcon />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid item xs={12}>
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
