import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormLabel,
  Switch,
  Collapse,
  Divider
} from '@mui/material';
import { Send, Group, Person, FamilyRestroom } from '@mui/icons-material';
import { apiRequest } from '../stores/auth';
import SimplePhoneInput from './SimplePhoneInput';

function MessageForm({ selectedGroup, onMessageSent, refreshTrigger }) {
  const [messageType, setMessageType] = useState('group'); // 'group' or 'individual'
  const [groups, setGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  // Parent SMS features
  const [includeParents, setIncludeParents] = useState(false);
  const [parentMessage, setParentMessage] = useState('');

  useEffect(() => {
    loadGroups();
  }, [refreshTrigger]); // Add refreshTrigger as dependency

  useEffect(() => {
    if (selectedGroup) {
      setMessageType('group');
      setSelectedGroupId(selectedGroup.id);
    }
  }, [selectedGroup]);

  const loadGroups = async () => {
    try {
      const response = await apiRequest('/groups');
      if (response.ok) {
        const groupsData = await response.json();
        setGroups(groupsData.filter(g => g.is_active));
      }
    } catch (err) {
      console.error('Error loading groups:', err);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (messageType === 'group') {
        if (!selectedGroupId) {
          throw new Error('Please select a group');
        }
        
        const requestBody = {
          group_id: parseInt(selectedGroupId),
          message: message.trim()
        };

        if (includeParents) {
          requestBody.include_parents = true;
          if (parentMessage.trim()) {
            requestBody.parent_message = parentMessage.trim();
          }
        }

        const response = await apiRequest('/api/sms/send-group', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        });

        if (response.ok) {
          const result = await response.json();
          let successMsg = `Message sent to ${result.sent_count} recipients`;
          if (includeParents && result.parent_count > 0) {
            successMsg += ` (including ${result.parent_count} parents)`;
          }
          setSuccess(successMsg);
        } else {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to send message');
        }
        
      } else {
        if (!phoneNumber.trim()) {
          throw new Error('Please enter a phone number');
        }
        
        const response = await apiRequest('/api/sms/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            phone_number: phoneNumber.trim(),
            message: message.trim()
          })
        });

        if (response.ok) {
          const result = await response.json();
          setSuccess('Message sent successfully');
        } else {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to send message');
        }
      }

      // Clear form
      setMessage('');
      setParentMessage('');
      setIncludeParents(false);
      if (messageType === 'individual') {
        setPhoneNumber('');
      }
      
      onMessageSent();

    } catch (err) {
      setError(err.message || 'Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  const handleMessageTypeChange = (event) => {
    setMessageType(event.target.value);
    setError(null);
    setSuccess(null);
  };

  const selectedGroupData = groups.find(g => g.id === parseInt(selectedGroupId));

  const isFormValid = () => {
    if (!message.trim()) return false;
    if (messageType === 'group') {
      return selectedGroupId !== '';
    } else {
      return phoneNumber.trim() !== '';
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Send SMS Message
      </Typography>

      <Card>
        <CardContent>
          <form onSubmit={handleSendMessage}>
            <FormControl component="fieldset" sx={{ mb: 3 }}>
              <FormLabel component="legend">Message Type</FormLabel>
              <RadioGroup
                row
                value={messageType}
                onChange={handleMessageTypeChange}
              >
                <FormControlLabel
                  value="group"
                  control={<Radio />}
                  label={
                    <Box display="flex" alignItems="center">
                      <Group fontSize="small" sx={{ mr: 0.5 }} />
                      Group Message
                    </Box>
                  }
                />
                <FormControlLabel
                  value="individual"
                  control={<Radio />}
                  label={
                    <Box display="flex" alignItems="center">
                      <Person fontSize="small" sx={{ mr: 0.5 }} />
                      Individual Message
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>

            {messageType === 'group' ? (
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Select Group</InputLabel>
                <Select
                  value={selectedGroupId}
                  onChange={(e) => setSelectedGroupId(e?.target?.value || '')}
                  label="Select Group"
                >
                  {groups.map((group) => (
                    <MenuItem key={group.id} value={group.id}>
                      <Box>
                        <Typography>{group.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {group.member_count || 0} members
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            ) : (
              <Box sx={{ mb: 3 }}>
                <SimplePhoneInput
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e?.target?.value || (typeof e === 'string' ? e : ''))}
                  label="Phone Number"
                  placeholder="+1234567890"
                  required
                />
              </Box>
            )}

            {messageType === 'group' && selectedGroupData && (
              <Alert severity="info" sx={{ mb: 2 }}>
                <Box>
                  <Typography variant="subtitle2">
                    Sending to: {selectedGroupData.name}
                  </Typography>
                  <Typography variant="body2">
                    {selectedGroupData.member_count || 0} recipients
                  </Typography>
                </Box>
              </Alert>
            )}

            {/* Parent SMS Features - temporarily disabled for testing
            {messageType === 'group' && (
              <Box sx={{ mb: 3 }}>
                <Box display="flex" alignItems="center" sx={{ mb: 1 }}>
                  <FamilyRestroom fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={includeParents}
                        onChange={(e) => setIncludeParents(e?.target?.checked || false)}
                        color="primary"
                      />
                    }
                    label="Include Parents in Message"
                  />
                </Box>
                
                <Collapse in={includeParents}>
                  <Box sx={{ pl: 4, pt: 1 }}>
                    <TextField
                      fullWidth
                      multiline
                      rows={2}
                      label="Custom Parent Message (Optional)"
                      placeholder="Optional custom message for parents..."
                      value={parentMessage}
                      onChange={(e) => setParentMessage(e?.target?.value || '')}
                      sx={{ mb: 1 }}
                      helperText="Leave empty to send the same message to parents"
                      inputProps={{ maxLength: 1600 }}
                    />
                  </Box>
                </Collapse>
                
                <Divider sx={{ mt: 2 }} />
              </Box>
            )}
            */}

            <TextField
              fullWidth
              multiline
              rows={4}
              label="Message"
              placeholder="Type your message here..."
              value={message}
              onChange={(e) => setMessage(e?.target?.value || '')}
              required
              sx={{ mb: 3 }}
              helperText={`${message.length}/1600 characters`}
              inputProps={{ maxLength: 1600 }}
            />

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {success && (
              <Alert severity="success" sx={{ mb: 2 }}>
                {success}
              </Alert>
            )}

            <Button
              type="submit"
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <Send />}
              disabled={loading || !isFormValid()}
              fullWidth
            >
              {loading ? 'Sending...' : 'Send Message'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}

export default MessageForm;