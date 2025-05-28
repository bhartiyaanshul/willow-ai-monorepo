// src/App.js
import React, { useState } from 'react';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [botReply, setBotReply] = useState('');
  const [leadData, setLeadData] = useState({});

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Send message to backend
    const response = await fetch('http://localhost:8000/talk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input }),
    });

    const blob = await response.blob();
    console.log('Received audio blob:', blob);
    if (!blob || blob.size === 0) {
      console.error('Received empty audio blob');
      return;
    }

    const audioURL = URL.createObjectURL(blob);
    console.log('Audio URL:', audioURL);
    const audio = new Audio(audioURL);
    audio.oncanplaythrough = () => {
      console.log('Audio is ready to play');
    };
    audio.play();
    

    // Fetch bot's text response (assume backend exposes /last-response for now)
    const textResponse = await fetch('http://localhost:8000/last-response');
    const botText = await textResponse.text();
    setBotReply(botText);

    // Collect lead data
    collectLeadInfo(input, botText);
    setInput('');
  };

  const collectLeadInfo = (question, answer) => {
    const q = question.toLowerCase();
    if (q.includes('company') || q.includes('domain') || q.includes('problem') || q.includes('budget')) {
      setLeadData((prev) => ({ ...prev, [q]: answer }));
    }
  };

  return (
    <div className="App">
      <h1>🗣️ Willow AI Voice SDR</h1>

      <textarea
        rows="3"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type your message..."
      />

      <br />
      <button onClick={sendMessage}>Send</button>

      {botReply && (
        <div className="bot-response">
          <strong>Bot:</strong> {botReply}
        </div>
      )}

      <div className="lead-form">
        <h3>Collected Lead Info</h3>
        <pre>{JSON.stringify(leadData, null, 2)}</pre>
      </div>
    </div>
  );
}

export default App;
