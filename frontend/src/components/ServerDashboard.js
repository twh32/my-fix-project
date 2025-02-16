import React, { useEffect, useState } from 'react';
import axios from 'axios';

function ServerDashboard() {
  const [logs, setLogs] = useState([]);

  // For demonstration, let's simulate logs from an API endpoint.
  // In a real application, you might use WebSocket or polling.
  useEffect(() => {
    // Simulate fetching logs every 5 seconds.
    const interval = setInterval(async () => {
      try {
        // Replace this with your actual endpoint for logs.
        const response = await axios.get('http://localhost:5002/logs');
        setLogs(response.data.logs);
      } catch (error) {
        console.error('Error fetching logs:', error);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h2>Server Dashboard</h2>
      <div style={{ border: '1px solid #ccc', padding: '1rem', height: '300px', overflowY: 'scroll' }}>
        {logs.length > 0 ? (
          logs.map((log, index) => <p key={index}>{log}</p>)
        ) : (
          <p>No logs available.</p>
        )}
      </div>
    </div>
  );
}

export default ServerDashboard;