import React from 'react';
import agents from './agentsConfig';
import { useNavigate } from 'react-router-dom';

function Sidebar({ 
  agentName, 
  conversations, 
  renameConversation, 
  setSelectedConversation, 
  collapsed 
}) {
  const navigate = useNavigate();
  
  return (
    <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      {!collapsed && <h2>Agents</h2>}
      <ul className="agent-list">
        {agents.map(agent => (
          <li 
            key={agent.name} 
            className={agent.name === agentName ? 'active' : ''}
            onClick={() => {
              navigate(`/agent/${encodeURIComponent(agent.name)}`);
            }}
            title={collapsed ? agent.name : ''}
          >
            {collapsed ? agent.emoji : agent.name}
          </li>
        ))}
      </ul>
      {!collapsed && <h3>Your Conversations</h3>}
      <ul className="conversation-list">
        {conversations.map((conv, index) => (
          <li key={index} onClick={() => setSelectedConversation(index)}>
            {collapsed ? (
              <span title={conv.title}>💬</span>
            ) : (
              <input 
                value={conv.title} 
                onChange={e => renameConversation(index, e.target.value)}
              />
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Sidebar;
