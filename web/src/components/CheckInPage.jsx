import React, { useState, useEffect } from 'react';
import CheckIn from './CheckIn.jsx';

const CheckInPage = () => {
  const [eventId, setEventId] = useState(null);

  useEffect(() => {
    // Extract eventId from URL parameters client-side
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('eventId');
    if (id) {
      setEventId(parseInt(id));
    } else {
      // If no eventId parameter, redirect to event list or show error
      window.location.href = '/';
    }
  }, []);

  if (!eventId) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading...</p>
      </div>
    );
  }

  return <CheckIn eventId={eventId} />;
};

export default CheckInPage;