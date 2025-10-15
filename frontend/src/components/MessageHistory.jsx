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
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton
} from '@mui/material';
import { 
  CheckCircle, 
  Error, 
  Schedule, 
  Send,
  Group,
  Person,
  Phone,
  Visibility,
  Close
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
      case 'sending':
        return { 
          color: 'default', 
          icon: <Schedule fontSize="small" />,
          label: 'Pending'
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

function GroupMessageDetailsDialog({ open, onClose, groupId, messageContent, sendTime }) {
  const [loading, setLoading] = useState(false);
  const [recipients, setRecipients] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (open && groupId && messageContent && sendTime) {
      loadRecipientDetails();
    }
  }, [open, groupId, messageContent, sendTime]);

  const loadRecipientDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        message_content: messageContent,
        send_time: sendTime
      });
      
      const response = await apiRequest(`/api/sms/history/group/${groupId}/details?${params}`);
      if (response.ok) {
        const data = await response.json();
        setRecipients(data);
      } else {
        throw new Error('Failed to load recipient details');
      }
    } catch (err) {
      setError('Failed to load recipient details');
      console.error('Error loading recipient details:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Group Message Recipients</Typography>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent>
        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Recipient</TableCell>
                  <TableCell>Phone Number</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Sent At</TableCell>
                  <TableCell>Delivered At</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {recipients.map((recipient, index) => (
                  <TableRow key={index}>
                    <TableCell>{recipient.person_name}</TableCell>
                    <TableCell>{recipient.phone_number || 'N/A'}</TableCell>
                    <TableCell>
                      <MessageStatusChip status={recipient.status} />
                      {recipient.failure_reason && (
                        <Typography variant="caption" color="error" display="block">
                          {recipient.failure_reason}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>{formatDate(recipient.sent_at)}</TableCell>
                    <TableCell>{formatDate(recipient.delivered_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}

function TopLevelMessageCard({ message, onViewDetails }) {
  console.log('Rendering TopLevelMessageCard with message:', message);
  
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const truncateMessage = (text, maxLength = 100) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const isGroupMessage = message.message_type === 'group';

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box flex={1}>
            <Box display="flex" alignItems="center" mb={1}>
              {isGroupMessage ? (
                <Group fontSize="small" color="action" sx={{ mr: 1 }} />
              ) : (
                <Person fontSize="small" color="action" sx={{ mr: 1 }} />
              )}
              <Typography variant="subtitle2">
                {isGroupMessage ? message.group_name : message.recipient_name}
              </Typography>
            </Box>
            
            {!isGroupMessage && message.recipient_phone && (
              <Box display="flex" alignItems="center" mb={1}>
                <Phone fontSize="small" color="action" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  {message.recipient_phone}
                </Typography>
              </Box>
            )}

            {isGroupMessage && (
              <Box display="flex" alignItems="center" mb={1}>
                <Typography variant="body2" color="text.secondary">
                  {message.total_recipients} recipients
                </Typography>
              </Box>
            )}
          </Box>
          
          {!isGroupMessage ? (
            <MessageStatusChip status={message.status} />
          ) : (
            <Box display="flex" gap={0.5} flexWrap="wrap">
              {message.delivered_count > 0 && (
                <Chip size="small" color="success" label={`${message.delivered_count} delivered`} />
              )}
              {message.sent_count > 0 && (
                <Chip size="small" color="primary" label={`${message.sent_count} sent`} />
              )}
              {message.failed_count > 0 && (
                <Chip size="small" color="error" label={`${message.failed_count} failed`} />
              )}
              {message.pending_count > 0 && (
                <Chip size="small" color="default" label={`${message.pending_count} pending`} />
              )}
            </Box>
          )}
        </Box>

        <Typography variant="body2" sx={{ mb: 2 }}>
          {truncateMessage(message.content)}
        </Typography>

        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="caption" color="text.secondary">
            Sent: {formatDate(message.created_at)}
          </Typography>
          
          {isGroupMessage && (
            <Button
              size="small"
              startIcon={<Visibility />}
              onClick={() => onViewDetails(message)}
              variant="outlined"
            >
              View Details
            </Button>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

function MessageHistory({ refreshTrigger }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Dialog state for group message details
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [selectedGroupMessage, setSelectedGroupMessage] = useState(null);
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const messagesPerPage = 20;

  useEffect(() => {
    loadMessages();
  }, [refreshTrigger, page]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        limit: messagesPerPage.toString(),
        offset: ((page - 1) * messagesPerPage).toString(),
        days: '30'  // Default to last 30 days
      });

      console.log('Loading messages from:', `/api/sms/history/top-level?${params}`);
      const response = await apiRequest(`/api/sms/history/top-level?${params}`);
      if (response.ok) {
        const data = await response.json();
        console.log('Received message data:', data);
        setMessages(data.messages || []);
        setTotalPages(Math.ceil((data.total_count || 0) / messagesPerPage));
      } else {
        const errorText = await response.text();
        console.error('API error:', response.status, errorText);
        throw new Error(`API returned ${response.status}`);
      }
      
    } catch (err) {
      setError('Failed to load message history');
      console.error('Error loading messages:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (message) => {
    setSelectedGroupMessage(message);
    setDetailsDialogOpen(true);
  };

  const handleCloseDetails = () => {
    setDetailsDialogOpen(false);
    setSelectedGroupMessage(null);
  };

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Message History
        <Typography variant="body2" color="text.secondary" component="span" sx={{ ml: 1 }}>
          (Last 30 days)
        </Typography>
      </Typography>

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
          No messages found in the last 30 days. Send your first message to get started!
        </Alert>
      ) : (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Showing {messages.length} messages
          </Typography>
          
          {console.log('Rendering messages:', messages)}
          
          {messages.map((message) => (
            <TopLevelMessageCard 
              key={message.id} 
              message={message} 
              onViewDetails={handleViewDetails}
            />
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

      {/* Group Message Details Dialog */}
      <GroupMessageDetailsDialog
        open={detailsDialogOpen}
        onClose={handleCloseDetails}
        groupId={selectedGroupMessage?.group_id}
        messageContent={selectedGroupMessage?.content}
        sendTime={selectedGroupMessage?.created_at}
      />
    </Box>
  );
}

export default MessageHistory;