import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Grid
} from '@mui/material';
import { Add, Edit, Delete, Group, Person } from '@mui/icons-material';
import { apiRequest } from '../stores/auth';

function GroupForm({ open, onClose, onSubmit, group = null }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_active: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (group) {
      setFormData({
        name: group.name || '',
        description: group.description || '',
        is_active: group.is_active !== false
      });
    } else {
      setFormData({
        name: '',
        description: '',
        is_active: true
      });
    }
    // Clear error when dialog opens/changes
    setError(null);
  }, [group, open]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      await onSubmit(formData);
      onClose();
    } catch (error) {
      console.error('Error submitting form:', error);
      setError(error.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field) => (event) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.type === 'checkbox' ? event.target.checked : event.target.value
    }));
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          {group ? 'Edit Group' : 'Create New Group'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            autoFocus
            margin="dense"
            name="name"
            label="Group Name"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={handleChange('name')}
            required
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            name="description"
            label="Description"
            type="text"
            fullWidth
            variant="outlined"
            multiline
            rows={3}
            value={formData.description}
            onChange={handleChange('description')}
            sx={{ mb: 2 }}
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.is_active}
                onChange={handleChange('is_active')}
                name="is_active"
              />
            }
            label="Active"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button 
            type="submit" 
            variant="contained" 
            disabled={loading || !formData.name.trim()}
          >
            {loading ? <CircularProgress size={20} /> : (group ? 'Update' : 'Create')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

function GroupList({ onGroupSelect, onGroupCreated, refreshTrigger }) {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState(null);

  useEffect(() => {
    loadGroups();
  }, [refreshTrigger]);

  const loadGroups = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiRequest('/groups');
      if (response.ok) {
        const groupsData = await response.json();
        setGroups(groupsData);
      }
    } catch (err) {
      setError('Failed to load message groups');
      console.error('Error loading groups:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async (formData) => {
    try {
      const response = await apiRequest('/groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        const newGroup = await response.json();
        setGroups(prev => [newGroup, ...prev]);
        onGroupCreated();
      } else {
        // Extract specific error message from response
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create group');
      }
    } catch (err) {
      // Re-throw the error with the specific message
      throw new Error(err.message || 'Failed to create group');
    }
  };

  const handleUpdateGroup = async (formData) => {
    try {
      const response = await apiRequest(`/groups/${editingGroup.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        const updatedGroup = await response.json();
        setGroups(prev => prev.map(g => g.id === editingGroup.id ? updatedGroup : g));
      }
    } catch (err) {
      throw new Error('Failed to update group');
    }
  };

  const handleDeleteGroup = async (groupId) => {
    if (!confirm('Are you sure you want to delete this group?')) {
      return;
    }

    try {
      await apiRequest(`/groups/${groupId}`, {
        method: 'DELETE'
      });
      
      setGroups(prev => prev.filter(g => g.id !== groupId));
    } catch (err) {
      setError('Failed to delete group');
    }
  };

  const openCreateForm = () => {
    setEditingGroup(null);
    setFormOpen(true);
  };

  const openEditForm = (group) => {
    setEditingGroup(group);
    setFormOpen(true);
  };

  const closeForm = () => {
    setFormOpen(false);
    setEditingGroup(null);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h6">Message Groups</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={openCreateForm}
        >
          Create Group
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {groups.length === 0 ? (
        <Alert severity="info">
          No message groups found. Create your first group to get started!
        </Alert>
      ) : (
        <Grid container spacing={2}>
          {groups.map((group) => (
            <Grid item xs={12} md={6} key={group.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                    <Box flex={1}>
                      <Typography variant="h6" gutterBottom>
                        {group.name}
                        {!group.is_active && (
                          <Chip 
                            label="Inactive" 
                            size="small" 
                            color="default" 
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {group.description}
                      </Typography>
                      <Box display="flex" alignItems="center" mt={1}>
                        <Person fontSize="small" color="action" />
                        <Typography variant="caption" sx={{ ml: 0.5 }}>
                          Members: {group.member_count || 0}
                        </Typography>
                      </Box>
                    </Box>
                    <Box>
                      <IconButton 
                        size="small" 
                        onClick={() => openEditForm(group)}
                        color="primary"
                      >
                        <Edit />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        onClick={() => handleDeleteGroup(group.id)}
                        color="error"
                      >
                        <Delete />
                      </IconButton>
                    </Box>
                  </Box>
                  <Box mt={2}>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<Group />}
                      onClick={() => onGroupSelect(group)}
                      disabled={!group.is_active}
                    >
                      Send Message
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <GroupForm
        open={formOpen}
        onClose={closeForm}
        onSubmit={editingGroup ? handleUpdateGroup : handleCreateGroup}
        group={editingGroup}
      />
    </Box>
  );
}

export default GroupList;