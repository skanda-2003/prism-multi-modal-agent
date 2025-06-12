// AgentPage.js

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AgentUI from './AgentUI';
import Sidebar from './Sidebar';
import './App.css';
import { v4 as uuidv4 } from 'uuid';

function AgentPage() {
  const { agentName } = useParams();
  const navigate = useNavigate();
  
  const [modelName, setModelName] = useState("gemini"); 
  const [conversations, setConversations] = useState(() => {
    const saved = localStorage.getItem(`conversations_${agentName}`);
    return saved ? JSON.parse(saved) : [{ id: uuidv4(), title: "New Chat", messages: [] }];
  });
  const [selectedConversation, setSelectedConversation] = useState(0);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    localStorage.setItem(`conversations_${agentName}`, JSON.stringify(conversations));
  }, [conversations, agentName]);

  const toggleModel = () => {
    setModelName(prev => (prev === "gemini" ? "qwen" : "gemini"));
  };

  const renameConversation = (index, newTitle) => {
    const updated = [...conversations];
    updated[index].title = newTitle;
    setConversations(updated);
  };

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const clearChat = () => {
    const updated = [...conversations];
    updated[selectedConversation].messages = [];
    setConversations(updated);
  };

  const startNewChat = () => {
    const newChat = { id: uuidv4(), title: `Chat ${conversations.length + 1}`, messages: [] };
    setConversations([...conversations, newChat]);
    setSelectedConversation(conversations.length);
  };

  // Clear chat when switching agents
  useEffect(() => {
    clearChat();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentName]);

  return (
    <div className="agent-page">
      <Sidebar 
        agentName={agentName} 
        conversations={conversations} 
        renameConversation={renameConversation} 
        setSelectedConversation={setSelectedConversation}
        collapsed={sidebarCollapsed}
      />
      <div className="main-area">
        <div className="top-bar">
          <div className="left-buttons">
            <button className="home-button" onClick={() => navigate('/')}>Home</button>
            <button className="collapse-button" onClick={toggleSidebar}>
              {sidebarCollapsed ? 'Expand' : 'Collapse'}
            </button>
          </div>
          <h1>{agentName}</h1>
          <div className="model-toggle">
            <span>{modelName === "gemini" ? "Gemini" : "Qwen"}</span>
            <button onClick={toggleModel}>
              Switch to {modelName === "gemini" ? "Qwen" : "Gemini"}
            </button>
            <button className="clear-button" onClick={clearChat}>
              Clear Chat
            </button>
            <button className="new-chat-button" onClick={startNewChat}>
              New Chat
            </button>
          </div>
        </div>
        <AgentUI 
          agentName={agentName} 
          modelName={modelName}
          conversations={conversations}
          setConversations={setConversations}
          selectedConversation={selectedConversation}
          setSelectedConversation={setSelectedConversation} // Passed here
        />
      </div>
    </div>
  );
}

export default AgentPage;
