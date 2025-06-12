// src/AgentUI.jsx

import React, { useState } from 'react';
import './App.css';

function AgentUI({ agentName, modelName, conversations, setConversations, selectedConversation, setSelectedConversation }) {
  const [input, setInput] = useState("");
  const [error, setError] = useState(null);

  const sendQuery = async () => {
    if (!input.trim()) return;
    const currentConv = conversations[selectedConversation];
    if (!currentConv.id) {
      console.error("Missing conversation_id");
      setError("An error occurred: Missing conversation identifier.");
      return;
    }
    try {
      const response = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          agent_name: agentName, 
          user_input: input, 
          model_name: modelName,
          conversation_id: currentConv.id
        })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to process the request.");
      }
      const data = await response.json();
      if (data.response) {
        const updatedConversations = [...conversations];
        updatedConversations[selectedConversation].messages.push({ role: 'user', text: input });
        updatedConversations[selectedConversation].messages.push({ role: 'assistant', text: data.response });
        setConversations(updatedConversations);
        setError(null);
      } else {
        const updatedConversations = [...conversations];
        updatedConversations[selectedConversation].messages.push({ role: 'user', text: input });
        updatedConversations[selectedConversation].messages.push({ role: 'assistant', text: "• Unable to generate a response." });
        setConversations(updatedConversations);
      }
      setInput("");
    } catch (error) {
      const updatedConversations = [...conversations];
      updatedConversations[selectedConversation].messages.push({ role: 'user', text: input });
      updatedConversations[selectedConversation].messages.push({ role: 'assistant', text: `• ${error.message}` });
      setConversations(updatedConversations);
      setInput("");
      setError(error.message);
      console.error("Error:", error);
    }
  };

  const deleteConversation = () => {
    const updatedConversations = conversations.filter((_, index) => index !== selectedConversation);
    setConversations(updatedConversations);
    if (selectedConversation > 0) {
      setSelectedConversation(selectedConversation - 1);
    } else {
      setSelectedConversation(0);
    }
  };

  // Function to detect YouTube URLs and embed videos
  const renderContent = (text) => {
    const youtubeRegex = /(https?:\/\/www\.youtube\.com\/watch\?v=([\w-]{11}))/g;
    const matches = [...text.matchAll(youtubeRegex)];
    if (matches.length > 0) {
      let content = text;
      return matches.map((match, index) => {
        const videoUrl = match[1];
        const videoId = match[2];
        // Split the text to insert the iframe
        const parts = content.split(videoUrl);
        // Update the remaining content after the first match
        content = parts[1];
        return (
          <div key={index}>
            <p>{parts[0].trim()}</p>
            <iframe
              width="560"
              height="315"
              src={`https://www.youtube.com/embed/${videoId}`}
              title="YouTube video player"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          </div>
        );
      });
    }
    return <p>{text}</p>;
  };

  return (
    <div className="chat-ui">
      <div className="chat-box">
        {conversations[selectedConversation].messages.map((msg, i) => (
          <div key={i} className={`chat-msg ${msg.role}`}>
            <div className="bubble">
              {msg.role === 'assistant' ? renderContent(msg.text) : msg.text}
            </div>
          </div>
        ))}
        {error && <div className="error-msg">Error: {error}</div>}
      </div>
      <div className="input-row">
        <input 
          value={input} 
          onChange={e => setInput(e.target.value)} 
          onKeyDown={e => e.key === 'Enter' && sendQuery()} 
          placeholder="Type your query..." 
        />
        <button onClick={sendQuery}>Send</button>
        <button className="delete-chat-button" onClick={deleteConversation}>Delete Conversation</button>
      </div>
    </div>
  );
}

export default AgentUI;
