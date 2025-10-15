import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Grid,
  Pagination,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import { 
  CheckCircle, 
  Error, 
  Schedule, 
  Send,
  Group,
  Person,
  Phone
} from '@mui/icons-material';
import { apiRequest } from '../stores/auth';

function MessageStatusChip({ status }) {
  const getStatusProps = (status) => {
    switch (status) {
      case 'delivered':
        return { 
          color: 'success', 
          icon: <CheckCircle fontSize="small" />,
          label: 'Delivered'
        };
      case 'failed':
        return { 
          color: 'error', 
          icon: <Error fontSize="small" />,
          label: 'Failed'
        };
      case 'sent':
        return { 
          color: 'primary', 
          icon: <Send fontSize="small" />,
          label: 'Sent'
        };
      case 'queued':
        return { 
          color: 'default', 
          icon: <Schedule fontSize="small" />,
          label: 'Queued'
        };
      default:
        return { 
          color: 'default', 
          icon: <Schedule fontSize="small" />,
          label: status
        };
    }
  };

  const props = getStatusProps(status);
  
  return (
    <Chip
      size="small"
      icon={props.icon}
      label={props.label.toLowerCase()}
      color={props.color}
      variant="outlined"
    />
  );
}

function MessageCard({ message }) {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const truncateMessage = (text, maxLength = 100) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box flex={1}>
            <Box display="flex" alignItems="center" mb={1}>
              {message.group_id ? (
                <Group fontSize="small" color="action" sx={{ mr: 1 }} />
              ) : (
                <Person fontSize="small" color="action" sx={{ mr: 1 }} />
              )}
              <Typography variant="subtitle2">
                {message.group_name || 'Individual Message'}
              </Typography>
            </Box>
            
            {message.recipient_phone && (
              <Box display="flex" alignItems="center" mb={1}>
                <Phone fontSize="small" color="action" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  {message.recipient_phone}
                </Typography>
              </Box>
            )}
          </Box>
          
          <MessageStatusChip status={message.status} />
        </Box>

        <Typography variant="body2" sx={{ mb: 2 }}>
          {truncateMessage(message.content)}
        </Typography>

        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="caption" color="text.secondary">
            Sent: {formatDate(message.created_at)}
          </Typography>
          
          {message.delivered_at && (
            <Typography variant="caption" color="text.secondary">
              Delivered: {formatDate(message.delivered_at)}
            </Typography>
          )}
          
          {message.twilio_sid && (
            <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
              ID: {message.twilio_sid}
            </Typography>
          )}
          
          {message.error_code && (
            <Chip
              size="small"
              label={`Error: ${message.error_code}`}
              color="error"
              variant="outlined"
            />
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

function MessageHistory({ refreshTrigger }) {
  const [messages, setMessages] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filters
  const [groupFilter, setGroupFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const messagesPerPage = 10;

  useEffect(() => {
    loadGroups();
  }, []);

  useEffect(() => {
    loadMessages();
  }, [refreshTrigger, page, groupFilter, statusFilter, searchTerm]);

  const loadGroups = async () => {
    try {
      const response = await apiRequest('/groups');
      if (response.ok) {
        const groupsData = await response.json();
        setGroups(groupsData);
      }
    } catch (err) {
      console.error('Error loading groups:', err);
    }
  };

  const loadMessages = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        page: page.toString(),
        limit: messagesPerPage.toString()
      });
      
      if (groupFilter) {
        params.append('group_id', groupFilter);
      }
      
      if (statusFilter) {
        params.append('status', statusFilter);
      }
      
      if (searchTerm) {
        params.append('search', searchTerm);
      }

      const response = await apiRequest(`/api/sms/history?${params}`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data.messages || []);
        setTotalPages(Math.ceil((data.total || 0) / messagesPerPage));
      }
      
    } catch (err) {
      setError('Failed to load message history');
      console.error('Error loading messages:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const resetFilters = () => {
    setGroupFilter('');
    setStatusFilter('');
    setSearchTerm('');
    setPage(1);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Message History
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Filter by Group</InputLabel>
                <Select
                  value={groupFilter}
                  onChange={(e) => setGroupFilter(e.target.value)}
                  label="Filter by Group"
                >
                  <MenuItem value="">All Messages</MenuItem>
                  <MenuItem value="individual">Individual Messages</MenuItem>
                  {groups.map((group) => (
                    <MenuItem key={group.id} value={group.id}>
                      {group.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Filter by Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  label="Filter by Status"
                >
                  <MenuItem value="">All Statuses</MenuItem>
                  <MenuItem value="queued">Queued</MenuItem>
                  <MenuItem value="sent">Sent</MenuItem>
                  <MenuItem value="delivered">Delivered</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                size="small"
                label="Search messages"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search in message content..."
                inputProps={{ "aria-label": "Search messages" }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" p={3}>
          <CircularProgress />
        </Box>
      ) : messages.length === 0 ? (
        <Alert severity="info">
          No messages found. {(groupFilter || statusFilter || searchTerm) && 
            'Try adjusting your filters or '}Send your first message to get started!
        </Alert>
      ) : (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Showing {messages.length} messages
          </Typography>
          
          {messages.map((message) => (
            <MessageCard key={message.id} message={message} />
          ))}

          {totalPages > 1 && (
            <Box display="flex" justifyContent="center" mt={3}>
              <Pagination
                data-testid="pagination"
                count={totalPages}
                page={page}
                onChange={handlePageChange}
                color="primary"
              />
            </Box>
          )}
        </>
      )}
    </Box>
  );
}

export default MessageHistory;