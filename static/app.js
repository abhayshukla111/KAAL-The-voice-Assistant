// -------- Speech Recognition (Browser) ---------------------------------------
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const state = {
  listening: false,
  recognition: null
};

const micBtn = document.getElementById('micBtn');
const stopBtn = document.getElementById('stopBtn');
const heardText = document.getElementById('heardText');
const replyText = document.getElementById('replyText');
const statusEl = document.getElementById('status');

function setStatus(msg){ statusEl.textContent = msg; }

function typewriter(el, text, speed=18){
  el.textContent = '';
  let i = 0;
  const tick = () => {
    if (i <= text.length) {
      el.textContent = text.slice(0, i);
      i++;
      setTimeout(tick, speed);
    }
  };
  tick();
}

function speak(text){
  try{
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.02;
    u.pitch = 1.0;
    u.volume = 1.0;
    window.speechSynthesis.cancel(); // stop previous
    window.speechSynthesis.speak(u);
  }catch(err){
    // ignore TTS errors
  }
}

function startListening(){
  if (!SpeechRecognition) {
    alert('Your browser does not support speech recognition. Please use Google Chrome on desktop.');
    return;
  }
  if (state.listening) return;

  const recog = new SpeechRecognition();
  state.recognition = recog;
  recog.lang = 'en-US';
  recog.interimResults = false;
  recog.maxAlternatives = 1;
  state.listening = true;

  micBtn.disabled = true;
  stopBtn.disabled = false;
  setStatus('Listening…');

  recog.onresult = (e) => {
    const transcript = e.results[0][0].transcript.trim();
    heardText.textContent = transcript;
    setStatus('Processing…');
    sendToBackend(transcript);
  };

  recog.onerror = (e) => {
    setStatus('Mic error: ' + (e.error || 'unknown'));
    micBtn.disabled = false;
    stopBtn.disabled = true;
    state.listening = false;
  };

  recog.onend = () => {
    micBtn.disabled = false;
    stopBtn.disabled = true;
    state.listening = false;
    if (statusEl.textContent.startsWith('Listening')) {
      setStatus('Idle');
    }
  };

  try {
    recog.start();
  } catch {
    // Can throw if called too quickly
  }
}

function stopListening(){
  if (state.recognition && state.listening){
    state.recognition.stop();
    setStatus('Stopped. Idle');
  }
}

// -------- Backend API ---------------------------------------------------------
async function sendToBackend(text){
  try{
    const res = await fetch('/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    if (!res.ok){
      const j = await res.json().catch(()=>({reply:'(no details)'}));
      const msg = j.reply || ('HTTP '+res.status);
      typewriter(replyText, msg);
      speak(msg);
      setStatus('Idle');
      return;
    }

    const data = await res.json();
    const reply = data.reply || '…';
    typewriter(replyText, reply);
    speak(reply);

    if (data.action === 'open_url' && data.url){
      // small delay so speech starts first
      setTimeout(()=> window.open(data.url, '_blank'), 400);
    }

    setStatus('Idle');
  }catch(err){
    const msg = 'I could not reach the server. Is app.py running?';
    typewriter(replyText, msg);
    speak(msg);
    setStatus('Idle');
  }
}

// -------- Buttons -------------------------------------------------------------
micBtn.addEventListener('click', startListening);
stopBtn.addEventListener('click', stopListening);

// Warm up TTS voices on load (some browsers require user gesture; this is best effort)
window.addEventListener('load', () => {
  setTimeout(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.getVoices();
    }
  }, 200);
});