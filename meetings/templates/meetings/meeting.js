// ==========================
// WebRTC Mesh Video Meeting Client
// ==========================
console.log('Starting JS');
const stunConfig = { iceServers: [{urls: "stun:lotteh.com:3478"}] };

const meetingId = window.meetingId || (location.pathname.match(/\/meeting\/([a-zA-Z0-9\-]+)/)||[])[1] || "demo-meeting";
const userId = window.userId || "user_" + Math.random().toString(36).substring(2, 10);
const wsProtocol = location.protocol === "https:" ? "wss:" : "ws:";
const ws = new WebSocket(`${wsProtocol}//${location.host}/ws/meeting/${meetingId}/`);

const videoGrid = document.getElementById('video-grid');
const muteBtn = document.getElementById('muteBtn');
const videoBtn = document.getElementById('videoBtn');
const screenshareBtn = document.getElementById('screenshareBtn');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatSend = document.getElementById('chat-send');
const meetingIdElem = document.getElementById('meeting-id');
if (meetingIdElem) meetingIdElem.textContent = "Meeting ID: " + meetingId;

let localStream = null;
let audioEnabled = true;
let videoEnabled = true;
let screenSharing = false;
let originalVideoTrack = null;

// --- Mesh State ---
let peerConnections = {}; // peerId -> RTCPeerConnection
let peerStreams = {};     // peerId -> MediaStream (remote)
let peerVideoElems = {};  // peerId -> video element

// --- 1. Get local media and join room ---
async function start() {
  localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
  addVideo(userId, localStream, true);
  ws.onopen = () => ws.send(JSON.stringify({ type: 'join', userId }));
  ws.onmessage = handleWSMessage;
}
start();

// --- 2. WebSocket signaling ---
function handleWSMessage(event) {
  const msg = JSON.parse(event.data);

  if (msg.type === 'participants') {
    // List of participants (excluding self) sent on join
    (msg.participants || []).forEach(pid => {
      if (pid !== userId && !peerConnections[pid]) startPeerConnection(pid, true);
    });
  }
  if (msg.type === 'join' && msg.userId !== userId) {
    // New participant joined, create peer connection if not already
    if (!peerConnections[msg.userId]) startPeerConnection(msg.userId, false);
  }
  if (msg.type === 'offer' && msg.to === userId) {
    handleOffer(msg);
  }
  if (msg.type === 'answer' && msg.to === userId) {
    peerConnections[msg.from]?.setRemoteDescription(new RTCSessionDescription(msg.answer));
  }
  if (msg.type === 'ice-candidate' && msg.to === userId) {
    peerConnections[msg.from]?.addIceCandidate(msg.candidate);
  }
  if (msg.type === 'leave' && msg.userId !== userId) {
    removeVideo(msg.userId);
    if (peerConnections[msg.userId]) { peerConnections[msg.userId].close(); delete peerConnections[msg.userId]; }
    if (peerStreams[msg.userId]) delete peerStreams[msg.userId];
  }
  if (msg.type === 'chat') addChatMessage(msg.userId, msg.text, msg.userId === userId);
}

// --- 3. Peer connection mesh, one for each peer ---
function startPeerConnection(peerId, isInitiator) {
  if (peerConnections[peerId]) return;
  const pc = new RTCPeerConnection(stunConfig);

  // Add local tracks
  localStream.getTracks().forEach(track => pc.addTrack(track, localStream));

  // ICE
  pc.onicecandidate = e => {
    if (e.candidate)
      ws.send(JSON.stringify({ type: 'ice-candidate', from: userId, to: peerId, candidate: e.candidate }));
  };

  // Remote tracks: combine all into a single stream per peer
  let remoteStream = peerStreams[peerId] || new MediaStream();
  peerStreams[peerId] = remoteStream;
  pc.ontrack = (e) => {
    // Only add new tracks
    if (!remoteStream.getTracks().some(track => track.id === e.track.id)) {
      remoteStream.addTrack(e.track);
      addVideo(peerId, remoteStream, false);
    }
  };

  // Initiator: negotiation needed
  if (isInitiator) {
    pc.onnegotiationneeded = async () => {
      try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        ws.send(JSON.stringify({ type: 'offer', from: userId, to: peerId, offer }));
      } catch (e) {}
    };
  }

  return pc;
}

async function handleOffer(msg) {
  const pc = startPeerConnection(msg.from, false);
  await pc.setRemoteDescription(new RTCSessionDescription(msg.offer));
  const answer = await pc.createAnswer();
  await pc.setLocalDescription(answer);
  ws.send(JSON.stringify({ type: 'answer', from: userId, to: msg.from, answer }));
}

// --- 4. Video grid dynamic sizing ---
function renderVideoGrid() {
  // Clear
  while (videoGrid.firstChild) videoGrid.removeChild(videoGrid.firstChild);

  // All userIds (local first)
  const allIds = [userId, ...Object.keys(peerStreams).filter(pid => pid !== userId)];
  const count = allIds.length;
  if (count === 0) return;

  let cols = Math.ceil(Math.sqrt(count));
  let rows = Math.ceil(count / cols);

  videoGrid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
  videoGrid.style.gridTemplateRows = `repeat(${rows}, 1fr)`;

  allIds.forEach(pid => {
    const v = peerVideoElems[pid];
    if (v) videoGrid.appendChild(v);
  });
}

// Add or update a video element for a participant
function addVideo(id, stream, isLocal) {
  let v = peerVideoElems[id];
  if (!v) {
    v = document.createElement('video');
    v.autoplay = true;
    v.playsInline = true;
    v.id = `video-${id}`;
    if (isLocal) v.muted = true;
    peerVideoElems[id] = v;
  }
  if (v.srcObject !== stream) v.srcObject = stream;
  renderVideoGrid();
}

// Remove video for a participant
function removeVideo(id) {
  const v = peerVideoElems[id];
  if (v && v.parentElement) v.parentElement.removeChild(v);
  delete peerVideoElems[id];
  delete peerStreams[id];
  renderVideoGrid();
}

// --- 5. Media Controls ---
muteBtn.onclick = () => {
  audioEnabled = !audioEnabled;
  localStream.getAudioTracks().forEach(t => t.enabled = audioEnabled);
  muteBtn.textContent = audioEnabled ? 'Mute' : 'Unmute';
};
videoBtn.onclick = () => {
  videoEnabled = !videoEnabled;
  localStream.getVideoTracks().forEach(t => t.enabled = videoEnabled);
  videoBtn.textContent = videoEnabled ? 'Hide Video' : 'Show Video';
};
screenshareBtn.onclick = async () => {
  if (!screenSharing) {
    try {
      const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true });
      const screenTrack = screenStream.getVideoTracks()[0];
      originalVideoTrack = localStream.getVideoTracks()[0];
      Object.values(peerConnections).forEach(pc => {
        const sender = pc.getSenders().find(s => s.track && s.track.kind === "video");
        if (sender) sender.replaceTrack(screenTrack);
      });
      localStream.removeTrack(originalVideoTrack);
      localStream.addTrack(screenTrack);
      addVideo(userId, localStream, true);
      screenSharing = true;
      screenshareBtn.textContent = "Stop Sharing";
      screenTrack.onended = () => stopScreenshare();
    } catch (e) { alert("Screen sharing failed."); }
  } else {
    stopScreenshare();
  }
};
function stopScreenshare() {
  if (!screenSharing) return;
  if (!originalVideoTrack) return;
  Object.values(peerConnections).forEach(pc => {
    const sender = pc.getSenders().find(s => s.track && s.track.kind === "video");
    if (sender) sender.replaceTrack(originalVideoTrack);
  });
  localStream.getVideoTracks().forEach(t => localStream.removeTrack(t));
  localStream.addTrack(originalVideoTrack);
  addVideo(userId, localStream, true);
  screenSharing = false;
  screenshareBtn.textContent = "Share Screen";
  originalVideoTrack = null;
}

// --- 6. Chat ---
chatSend.onclick = sendChat;
chatInput.onkeydown = e => { if (e.key === "Enter") sendChat(); };
function sendChat() {
  const text = chatInput.value.trim();
  if (text) {
    ws.send(JSON.stringify({ type: 'chat', userId, text }));
    addChatMessage(userId, text, true);
    chatInput.value = "";
  }
}
function addChatMessage(senderId, text, isSelf) {
  const msgElem = document.createElement("div");
  msgElem.className = "chat-msg";
  msgElem.innerHTML = `<span class="chat-user${isSelf ? ' chat-self' : ''}">${isSelf ? "You" : senderId}:</span> ${escapeHtml(text)}`;
  chatMessages.appendChild(msgElem);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}
function escapeHtml(str) {
  return str.replace(/[&<>"']/g, m => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[m]));
}

// --- 7. Cleanup on leave ---
window.onbeforeunload = () => {
  ws.send(JSON.stringify({ type: 'leave', userId }));
  ws.close();
  Object.values(peerConnections).forEach(pc => pc.close());
};
