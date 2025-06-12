import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './Home';
import AgentPage from './AgentPage';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/agent/:agentName" element={<AgentPage />} />
      </Routes>
    </Router>
  );
}

export default App;
