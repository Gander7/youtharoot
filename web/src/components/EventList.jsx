import React, { useState, useEffect } from 'react';
import Button from '@mui/material/Button';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { API_BASE_URL } from '../config/api.js';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#181818',
      paper: '#222',
    },
    text: {
      primary: '#f5f5f5',
    },
  },
});

export default function EventList() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/events`)
      .then(res => res.json())
      .then(data => setEvents(data));
  }, []);

  return (
    <ThemeProvider theme={darkTheme}>
      <div className="event-list" style={{ maxWidth: 600, margin: '0 auto', padding: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <Typography variant="h5" component="h1" gutterBottom>
            Events
          </Typography>
          <Button
            variant="contained"
            color="primary"
            size="medium"
            style={{ fontWeight: 600, borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}
            startIcon={<span style={{ fontSize: 20, fontWeight: 700 }}>+</span>}
            aria-label="Add new event"
            onClick={() => alert('Add Event dialog coming soon!')}
          >
            Add Event
          </Button>

        </div>
        <List>
          {events.length === 0 ? (
            <Typography variant="body1">No events found.</Typography>
          ) : (
            events.map(event => (
              <ListItem key={event.id} secondaryAction={
                <Button variant="contained" size="small">View</Button>
              }>
                <ListItemText
                  primary={event.name}
                  secondary={new Date(event.date).toLocaleDateString()}
                />
              </ListItem>
            ))
          )}
        </List>
      </div>
    </ThemeProvider>
  );
}
