// Home.js

import React from 'react';
import { useNavigate } from 'react-router-dom';
import agents from './agentsConfig';
import './App.css';

function Home() {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      <h1>Prism: Multi Modal Agents</h1>
      <div className="cards-grid">
        {agents.map(agent => (
          <div 
            key={agent.name} 
            className="agent-card"
            onClick={() => navigate(`/agent/${encodeURIComponent(agent.name)}`)}
          >
            <span className="agent-emoji">{agent.emoji}</span>
            <h2>{agent.name}</h2>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Home;
