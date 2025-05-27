import React, { useEffect, useRef, useState } from "react";

const App = () => {
  const ws = useRef(null);
  const [messages, setMessages] = useState([]);
  const mediaRecorderRef = useRef(null);
  const chunks = useRef([]);

  useEffect(() => {
    ws.current = new WebSocket("ws://localhost:8000/ws/audio");

    ws.current.onmessage = (event) => {
      console.log("Received from backend:", event.data);
      setMessages((prev) => [...prev, event.data]);
    };

    return () => {
      ws.current.close();
    };
  }, []);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0 && ws.current.readyState === WebSocket.OPEN) {
        ws.current.send(event.data);
      }
    };

    mediaRecorder.start(250); // send every 250ms
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
  };

  return (
    <div style={{ padding: "2rem" }}>
      <h1>🎙️ AI Voice SDR</h1>
      <button onClick={startRecording}>Start Talking</button>
      <button onClick={stopRecording}>Stop</button>

      <h3>📜 Responses</h3>
      <ul>
        {messages.map((msg, i) => (
          <li key={i}>{msg}</li>
        ))}
      </ul>
    </div>
  );
};

export default App;