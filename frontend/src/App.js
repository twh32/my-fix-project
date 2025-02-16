import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ClientOrderUI from './components/ClientOrderUI';
import ServerDashboard from './components/ServerDashboard';
import InternalSystemUI from './components/InternalSystemUI';

function App() {
  return (
    <Router>
      <div>
        <nav>
          <ul>
            <li><Link to="/">Client Order UI</Link></li>
            <li><Link to="/server">Server Dashboard</Link></li>
            <li><Link to="/internal">Internal System UI</Link></li>
          </ul>
        </nav>
        <Routes>
          <Route path="/" element={<ClientOrderUI />} />
          <Route path="/server" element={<ServerDashboard />} />
          <Route path="/internal" element={<InternalSystemUI />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;