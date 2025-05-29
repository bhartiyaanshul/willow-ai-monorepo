// src/App.js
import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  const [botReply, setBotReply] = useState('');
  const [leadData, setLeadData] = useState({});
  const [showImage, setShowImage] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [end, setEnd] = useState(false);
  const [typing, setTyping] = useState(false);
  const [displayedBotText, setDisplayedBotText] = useState('');
  const chatBubbleRef = useRef(null);
  const audioRef = useRef(null);

  useEffect(() => {
    // Scroll chat to bottom when conversation updates
    if (chatBubbleRef.current) {
      chatBubbleRef.current.scrollTop = chatBubbleRef.current.scrollHeight;
    }
  }, [conversation, displayedBotText]);

  // Typing effect for bot reply
  useEffect(() => {
    if (botReply && typing) {
      let i = 0;
      setDisplayedBotText('');
      const interval = setInterval(() => {
        setDisplayedBotText(botReply.slice(0, i + 1));
        i++;
        if (i >= botReply.length) {
          clearInterval(interval);
          setTyping(false);
        }
      }, 35); // typing speed
      return () => clearInterval(interval);
    }
  }, [botReply, typing]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    await sendToBackend(input);
  };

  // Helper to send text to backend and handle audio/text response
  const sendToBackend = async (text) => {
    const response = await fetch('http://localhost:8000/talk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await response.json();
    setShowImage(data.showImage);
    setLeadData(data.lead);
    setEnd(data.end);
    setBotReply(data.reply);
    setTyping(true);
    setConversation((prev) => [...prev, { sender: 'user', text }, { sender: 'bot', text: data.reply }]);
    // Play audio (ensure full backend URL)
    if (data.audio_url) {
      const backendUrl = 'http://localhost:8000';
      const audioUrl = data.audio_url.startsWith('http') ? data.audio_url : backendUrl + data.audio_url;
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      audio.play();
    }
    setInput('');
  };

  // Speech-to-text (STT) handler
  const handleSpeechInput = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-US';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      setIsListening(true);
      recognition.onresult = (event) => {
        const speechText = event.results[0][0].transcript;
        setInput(speechText);
        setIsListening(false);
      };
      recognition.onerror = (event) => {
        setIsListening(false);
        console.error('Speech recognition error:', event.error);
      };
      recognition.onend = () => setIsListening(false);
      recognition.start();
    } else {
      alert('Speech recognition is not supported in this browser.');
    }
  };

  return (
    <div className="willow-app">
      <header className="willow-header">
        <div className="willow-logo">willow.</div>
        <div className="willow-help">Need help? <a href="#" target="_blank" rel="noopener noreferrer">Watch this video</a></div>
      </header>
      <main className="willow-main">
        <div className="willow-chat-container">
          <div className="willow-avatar-section">
            <div className="willow-avatar">
              <img src="/avatar.png" alt="Avatar" />
            </div>
            {showImage && (
              <div className="willow-image-demo">
                <img src="/demo-image.jpg" alt="Demo" style={{ borderRadius: '12px', width: '220px', marginTop: '16px' }} />
                <div className="willow-image-caption">Product Demo</div>
              </div>
            )}
          </div>
          <div className="willow-chat-bubble-section willow-chat-scrollable" ref={chatBubbleRef}>
            {conversation.length === 0 && (
              <div className="willow-bot-bubble">Hi! I am Willow, your sales assistant.</div>
            )}
            {conversation.map((msg, idx) => (
              <div key={idx} className={msg.sender === 'bot' ? 'willow-bot-bubble' : 'willow-user-bubble'}>
                {msg.sender === 'bot' && idx === conversation.length - 1 && typing
                  ? displayedBotText
                  : msg.text}
              </div>
            ))}
            {isListening && (
              <div className="willow-listening">● Listening to you..</div>
            )}
          </div>
        </div>
        <div className="willow-bottom-bar">
          <div className="willow-user-avatar">OR</div>
          <button className={isListening ? 'willow-mic-active' : 'willow-mic'} onClick={handleSpeechInput} disabled={isListening}>
            <span role="img" aria-label="mic">🎤</span>
          </button>
          <input
            className="willow-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="For sending any links, spelling something out etc."
            disabled={end}
          />
          <button className="willow-send" onClick={sendMessage} disabled={end || !input.trim()}>Send</button>
        </div>
        <div className="willow-lead-summary">
          <h3>Collected Lead Info</h3>
          <pre>{JSON.stringify(leadData, null, 2)}</pre>
        </div>
      </main>
    </div>
  );
}

export default App;
