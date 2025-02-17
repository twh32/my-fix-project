import React, { useEffect, useState } from 'react';
import axios from 'axios';

function ServerDashboard() {
  const [logs, setLogs] = useState([]);

  // For a prototype, we'll simulate log fetching with an API call.
  // Ideally, your FIX server could expose a /logs endpoint.
  const fetchLogs = async () => {
    try {
      // Replace this URL with your actual logs endpoint if available.
      const response = await axios.get('http://localhost:5002/logs');
      setLogs(response.data.logs);
    } catch (error) {
      console.error('Error fetching logs:', error);
      // For now, we can simulate log data:
      setLogs(prevLogs => [
        ...prevLogs,
        `Log entry at ${new Date().toLocaleTimeString()}: No logs endpoint configured.`
      ]);
    }
  };

  useEffect(() => {
    fetchLogs();
    // Poll every 5 seconds for new logs.
    const interval = setInterval(fetchLogs, 5000);
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