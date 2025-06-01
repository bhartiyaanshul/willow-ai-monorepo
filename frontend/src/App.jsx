// src/App.js
// Main React component for WillowAI frontend
// Handles chat UI, user input, bot responses, error handling, and transcript logging

import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import Leads from './Leads';
import ReactPlayer from 'react-player/youtube';

function App() {
  // --- State variables ---
  const [input, setInput] = useState('');
  const [botReply, setBotReply] = useState('');
  const [leadData, setLeadData] = useState({});
  const [showImage, setShowImage] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [end, setEnd] = useState(false);
  const [typing, setTyping] = useState(false);
  const [displayedBotText, setDisplayedBotText] = useState('');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [error, setError] = useState(null); // For user-friendly error banners
  const chatBubbleRef = useRef(null);
  const audioRef = useRef(null);
  const inactivityTimer = useRef(null);

  // --- Scroll chat to bottom on new message ---
  useEffect(() => {
    if (chatBubbleRef.current) {
      chatBubbleRef.current.scrollTop = chatBubbleRef.current.scrollHeight;
    }
  }, [conversation]);

  // --- Typing effect for bot reply ---
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
      }, 35);
      return () => clearInterval(interval);
    }
  }, [botReply, typing]);

  // --- UI state helpers ---
  const showThinking = typing && !isListening;
  const waitingForBot = conversation.length > 0 && conversation[conversation.length - 1].sender === 'user' && !typing && !isListening;

  // --- Send user message to backend and handle response ---
  const sendMessage = async () => {
    if (!input.trim()) return;
    setConversation((prev) => [...prev, { sender: 'user', text: input }]);
    logTranscript('user', input);
    setInput('');
    await sendToBackend(input);
  };

  // --- Helper to send text to backend and handle audio/text response ---
  const sendToBackend = async (text) => {
    setError(null); // Clear previous errors
    try {
      const response = await fetch('http://localhost:8000/talk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      if (!response.ok) {
        throw new Error('Backend error: ' + response.statusText);
      }
      const data = await response.json();
      setShowImage(data.showImage);
      setLeadData(data.lead);
      setEnd(data.end);
      setBotReply(data.reply);
      setTyping(true);
      setConversation((prev) => [...prev, { sender: 'bot', text: data.reply }]);
      logTranscript('bot', data.reply);
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
      setYoutubeUrl(data.youtube_url || '');
      setInput('');
    } catch (err) {
      setError('Could not reach Willow backend. Please check your connection and try again.');
      setTyping(false);
    }
  };

  // --- Speech-to-text (STT) handler ---
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
        setError('Speech recognition error: ' + event.error);
      };
      recognition.onend = () => setIsListening(false);
      recognition.start();
    } else {
      setError('Speech recognition is not supported in this browser.');
    }
  };

  // --- End conversation and store lead if user says 'bye', etc. ---
  useEffect(() => {
    if (conversation.length > 0) {
      const lastMsg = conversation[conversation.length - 1];
      const endKeywords = [
        'bye', 'ok bye', 'thank you', 'thankyou', 'thanks', 'see you', 'goodbye', 'talk later', 'end chat', 'end conversation', "that's all", 'done', 'finish', 'no more', "that's it"
      ];
      if (
        lastMsg.sender === 'user' &&
        endKeywords.some(kw => lastMsg.text.toLowerCase().includes(kw))
      ) {
        setEnd(true);
      }
    }
  }, [conversation]);

  // --- Store lead in localStorage ONLY when backend ends chat and provides summary ---
  useEffect(() => {
    async function fetchLeadIfEnded() {
      if (end) {
        try {
          const response = await fetch('http://localhost:8000/lead', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
          });
          if (!response.ok) throw new Error('Backend error: ' + response.statusText);
          const data = await response.json();
          if (data.lead && data.lead.summary) {
            const prev = JSON.parse(localStorage.getItem('willow_leads') || '[]');
            if (!prev.length || prev[prev.length - 1].summary !== data.lead.summary) {
              localStorage.setItem('willow_leads', JSON.stringify([...prev, data.lead]));
            }
          }
        } catch (e) {
          setError('Could not save lead. Please try again.');
        }
      }
    }
    fetchLeadIfEnded();
  }, [end]);

  // --- Restore chat/lead from localStorage if within 5 min ---
  useEffect(() => {
    const saved = localStorage.getItem('willow_chat_state');
    if (saved) {
      const { conversation, leadData, end, lastActivity } = JSON.parse(saved);
      if (Date.now() - lastActivity < 300000) {
        setConversation(conversation || []);
        setLeadData(leadData || {});
        setEnd(!!end);
      } else {
        localStorage.removeItem('willow_chat_state');
      }
    }
  }, []);

  // --- Persist chat/lead to localStorage on every update ---
  useEffect(() => {
    localStorage.setItem(
      'willow_chat_state',
      JSON.stringify({
        conversation,
        leadData,
        end,
        lastActivity: Date.now(),
      })
    );
  }, [conversation, leadData, end]);

  // --- Inactivity timer: clear after 5 min of inactivity ---
  useEffect(() => {
    if (inactivityTimer.current) clearTimeout(inactivityTimer.current);
    if (conversation.length === 0 && !input) return;
    inactivityTimer.current = setTimeout(() => {
      setConversation([]);
      setLeadData({});
      setEnd(false);
      setBotReply('');
      setTyping(false);
      setDisplayedBotText('');
      localStorage.removeItem('willow_chat_state');
      fetch('http://localhost:8000/reset', { method: 'POST' });
    }, 300000);
    return () => clearTimeout(inactivityTimer.current);
  }, [conversation, input]);

  // --- Log transcript to localStorage for review/recovery ---
  function logTranscript(sender, text) {
    const prev = JSON.parse(localStorage.getItem('willow_transcript') || '[]');
    const entry = { sender, text, timestamp: new Date().toISOString() };
    localStorage.setItem('willow_transcript', JSON.stringify([...prev, entry]));
  }

  // --- Retry handler for backend errors ---
  const handleRetry = () => {
    setError(null);
    if (conversation.length > 0 && conversation[conversation.length - 1].sender === 'user') {
      sendToBackend(conversation[conversation.length - 1].text);
    }
  };

  // --- Render UI ---
  return (
    <div className="willow-app">
      {/* Error banner for user-friendly error messages */}
      {error && (
        <div className="error-banner">
          {error}
          <button onClick={handleRetry} className="retry-btn">Retry</button>
          <button onClick={() => setError(null)} className="close-btn">&times;</button>
        </div>
      )}
      <header className="willow-header">
        <div className="willow-logo">
          <span className="willow-logo-mark">\</span> willow.
        </div>
        <button
          className="willow-end-chat-btn"
          onClick={async () => {
            // Call the /lead endpoint to finalize and fetch the lead before reset
            try {
              // Send the user's last message (if any) to /lead for summary generation
              const lastUserMsg = conversation.length > 0 ? conversation.filter(m => m.sender === 'user').slice(-1)[0]?.text : '';
              const response = await fetch('http://localhost:8000/lead', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: lastUserMsg || '' })
              });
              const data = await response.json();
              console.log('Lead data:', data);
              // If the backend returns a lead with summary, store it in localStorage

              if (data.lead && data.lead.summary) {
                const prev = JSON.parse(localStorage.getItem('willow_leads') || '[]');
                if (!prev.length || prev[prev.length - 1].summary !== data.lead.summary) {
                  localStorage.setItem('willow_leads', JSON.stringify([...prev, data.lead]));
                }
              }
            } catch (e) {
              // Optionally handle error
            }
            // Now reset the chat state and backend
            setConversation([]);
            setLeadData({});
            setEnd(false);
            setBotReply('');
            setTyping(false);
            setDisplayedBotText('');
            setYoutubeUrl('');
            localStorage.removeItem('willow_chat_state');
            fetch('http://localhost:8000/reset', { method: 'POST' });
          }}
        >
          End Chat
        </button>
      </header>
      <main className="willow-main">
        <div className="willow-chat-container">
          <div className="willow-chat-bubble-section willow-chat-scrollable" ref={chatBubbleRef}>
            {/* Only show the initial bot message if conversation is empty */}
            {conversation.length === 0 && (
              <div className="willow-bot-bubble willow-bot-bubble-initial">Hi! I am Willow, your sales assistant.</div>
            )}
            {conversation.map((msg, idx) => (
              <div key={idx} className={msg.sender === 'bot' ? 'willow-bot-bubble' : 'willow-user-bubble'}>
                {msg.sender === 'bot' && idx === conversation.length - 1 && typing
                  ? displayedBotText
                  : msg.text}
              </div>
            ))}
            {/* Show 'Willow is thinking...' when AI is typing */}
            {typing && !isListening && (
              <div className="willow-listening">
                <span className="willow-listening-dot"></span>
                Willow is answering...
              </div>
            )}
            {/* Show 'Listening to you...' when user is speaking */}
            {isListening && (
              <div className="willow-listening">
                <span className="willow-listening-dot"></span>
                Listening to you...
              </div>
            )}
            {/* Show 'Waiting for Willow...' when waiting for bot reply */}
            {waitingForBot && (
              <div className="willow-listening">
                <span className="willow-listening-dot"></span>
                Waiting for Willow...
              </div>
            )}
            {youtubeUrl && (
              <div className="willow-youtube-demo">
                <ReactPlayer url={youtubeUrl} controls width="360px" height="202px" />
              </div>
            )}
          </div>
          <div className="willow-bottom-bar">
            {/* <div className="willow-user-avatar">OR</div> */}
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
        </div>
      </main>
    </div>
  );
}

export default App;
