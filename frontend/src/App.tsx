import { Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import IncidentList from './components/IncidentList';
import IncidentDetail from './components/IncidentDetail';
import AlertList from './components/AlertList';
import DataUpload from './components/DataUpload';

function App() {
  const location = useLocation();
  
  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/incidents', label: 'Incidents', icon: '🔥' },
    { path: '/alerts', label: 'Alerts', icon: '🔔' },
    { path: '/upload', label: 'Upload Data', icon: '📤' },
  ];

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="logo">
          <span className="logo-icon">🛡️</span>
          <span className="logo-text">Security Triage</span>
        </div>
        <ul className="nav-list">
          {navItems.map(item => (
            <li key={item.path}>
              <Link 
                to={item.path} 
                className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
              >
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-label">{item.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/incidents" element={<IncidentList />} />
          <Route path="/incidents/:id" element={<IncidentDetail />} />
          <Route path="/alerts" element={<AlertList />} />
          <Route path="/upload" element={<DataUpload />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
