cket.onopen = async () => {
            document.getElementById("localVideo").srcObject = localStream;
            navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
              const volumeMeter = createAudioStreamVolumeMeter(stream);
              setInterval(() => {
                const volume = audioEnabled ? volumeMeter.getCurrentVolume() : 0
                totalVolume+=volume;
                samples++;
                if(samples > 20) {
                    const averagedVolume = totalVolume / samples;
                    samples = 0;
                    totalVolume = 0;
                    send("volume", {type: "volume", volume: averagedVolume}, null);
                }
              }, 50);
            });
        };
        socket.onerror = function() {
            if(socketReconnectTimeout) clearTimeout(socketReconnectTimeout);
            meetingSocketReconnectTimeout = setTimeout(openMeetingSocket, {{ reload_time }});
        };

        socket.onclose = function() {
            if(socketReconnectTimeout) clearTimeout(socketReconnectTimeout);
            meetingSocketReconnectTimeout = setTimeout(openMeetingSocket, {{ reload_time }});
        };
        function updatePeerName(peer_id, username) {
            peerUsernames[peer_id] = username;
            const nameElem = document.getElementById("video-name-" + peer_id);
            if (nameElem) nameElem.textContent = username || 'Guest';
        }
        socket.onmessage = async (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === "peer-joined") {
                // Don't create a peer or video for yourself!
                if (msg.peer_id === 'local' || msg.peer_id === '{{ request.user.pk }}') return;
                if (msg.peer_id in peers) return;
                let pc = createPeer(msg.peer_id, true, msg.peer_name);
                let offer = await pc.createOffer();
                await pc.setLocalDescription(offer);
                send("signal", {type: "offer", sdp: offer}, msg.peer_id);
            } else if (msg.type === "peer-left") {
                if (msg.peer_id in peers) {
                    peers[msg.peer_id].close();
                    delete peers[msg.peer_id];
                }
                removeVideo(msg.peer_id);
                delete streams[msg.peer_id];
                delete peerVolumes[msg.peer_id];
                delete peerUsernames[msg.peer_id];

             } else if(msg.type === "audio") {
                const from = msg.from;
                const data = msg.data;
                if (msg.from) updateAudioOffIcon(msg.from, data.on);
             } else if(msg.type == "video") {
                const from = msg.from;
                const data = msg.data;
                if (msg.from) updateVideoOffIcon(msg.from, data.on);
             } else if (msg.type === "signal") {
                const from = msg.from;
                const data = msg.data;
                const username = msg.username;
                peerUsernames[from] = username;
                if (data.type === "offer") {
                    let pc = createPeer(from, false, username);
                    if (pc.signalingState === "stable" && data.sdp.type === "offer") {
                        await pc.setRemoteDescription(data.sdp);
                        let answer = await pc.createAnswer();
                        await pc.setLocalDescription(answer);
                        send("signal", {type: "answer", sdp: answer}, from);
                    }
                } else if (data.type === "answer") {
                    let pc = peers[from];
                    // Defensive: Only apply answer if in the right state
                    if (pc && pc.signalingState === "have-local-offer" && data.sdp.type === "answer") {
                        await pc.setRemoteDescription(data.sdp);
                    }
                } else if (data.type === "candidate") {
                    let pc = peers[from];
                    if (pc && data.candidate) await pc.addIceCandidate(data.candidate);
                }

            }
        };
    }

    await openMeetingSocket();
    // Controls
    document.getElementById("videoBtn").onclick = () => {
        videoEnabled = !videoEnabled;
        localStream.getVideoTracks().forEach(track => track.enabled = videoEnabled);
        document.getElementById("videoBtn").textContent = videoEnabled ? "{{ 'Disable Video'|etrans }}" : "{{ 'Enable Video'|etrans }}";
        updateVideoOffIcon('local', videoEnabled);
        for (const [peer_id, rtc] of Object.entries(peers)) {
            send("video", {type: "video", on: videoEnabled}, null);
        }
    };
    document.getElementById("audioBtn").onclick = () => {
        audioEnabled = !audioEnabled;
        localStream.getAudioTracks().forEach(track => track.enabled = audioEnabled);
        document.getElementById("audioBtn").textContent = audioEnabled ? "{{ 'Disable Mic'|etrans }}" : "{{ 'Enable Mic'|etrans }}";
        if(document.getElementById('muted-icon-local')) document.getElementById('muted-icon-local').style.display = !audioEnabled ? 'block' : 'none';
        for (const [peer_id, rtc] of Object.entries(peers)) {
            send("audio", {type: "audio", on: audioEnabled}, null);
        }
    };
    document.getElementById("autofocusBtn").onclick = () => {
        autofocusEnabled = !autofocusEnabled;
        document.getElementById("autofocusBtn").textContent = autofocusEnabled ? "{{ 'Disable Autofocus'|etrans }}" : "{{ 'Enable Autofocus'|etrans }}";
    };
    function openChatSocket() {
        chatSocket = new WebSocket(
            "wss://" + window.location.host + ":443/ws/meeting/chat/{{ meeting_id }}/?lang={{ lang }}"
        );
        chatSocket.onerror = function() {
            if(chatSocketReconnectTimeout) clearTimeout(chatSocketReconnectTimeout);
            chatSocketReconnectTimeout = setTimeout(openChatSocket, {{ reload_time }});
        };
        chatSocket.onclose = function() {
            if(chatSocketReconnectTimeout) clearTimeout(chatSocketReconnectTimeout);
            chatSocketReconnectTimeout = setTimeout(openChatSocket, {{ reload_time }});
        };
        chatSocket.onmessage = function(event) {
            let data = JSON.parse(event.data);
            let chatbox = document.getElementById('chatbox');
            chatbox.innerHTML += `<div class="bg-light text-dark"><b>${data.username}:</b> ${data.message}</div>`;
            chatbox.scrollBy(0, 1000);
        };
    }
    openChatSocket();
    const inputField = document.getElementById('chatinput');
    inputField.addEventListener('keydown', function(event) {
        if (event.keyCode === 13) { // 13 is the keyCode for the Enter key
            event.preventDefault(); // Prevent default Enter key behavior
            sendChat();
        }
    });
    let chatbox = document.getElementById('chatbox');
    chatbox.scrollBy(0, 9999999);
});
function sendChat() {
    let input = document.getElementById('chatinput');
    if(input.value != "" && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            message: input.value,
            username: "{% if request.user.is_authenticated %}@{{ request.user.profile.name }}"{% else %}Guest " + guestID{% endif %}
        }));
        input.value = "";
    }
}
const container = document.getElementById('videos');
var fullscreenButton = document.getElementById('fullscreenToggle');
fullscreenButton.addEventListener('click', () => {
  if (!document.fullscreenElement) {
    fullscreenButton.innerHTML = '<i class="bi bi-fullscreen-exit" style="color: white !important;"></i>';
    // Enter fullscreen mode
    if (container.requestFullscreen) {
      container.requestFullscreen();
    } else if (container.mozRequestFullScreen) { // Firefox
      container.mozRequestFullScreen();
    } else if (container.webkitRequestFullscreen) { // Chrome, Safari and Opera
      container.webkitRequestFullscreen();
    } else if (container.msRequestFullscreen) { // IE/Edge
      container.msRequestFullscreen();
    }
  } else {
    fullscreenButton.innerHTML = '<i class="bi bi-arrows-fullscreen" style="color: white !important;"></i>';
    // Exit fullscreen mode
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.mozCancelFullScreen) { // Firefox
      document.mozCancelFullScreen();
    } else if (document.webkitExitFullscreen) { // Chrome, Safari and Opera
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) { // IE/Edge
      document.msExitFullscreen();
    }
  }
});
var updateInterval;
function createAudioStreamVolumeMeter(stream) {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)();
  const source = audioContext.createMediaStreamSource(stream);
  const analyser = audioContext.createAnalyser();
  analyser.fftSize = 256;
  source.connect(analyser);
  const dataArray = new Uint8Array(analyser.fftSize);

  // This method will give the current volume level (average of samples)
  function getCurrentVolume() {
    analyser.getByteTimeDomainData(dataArray);
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      const normalized = dataArray[i] / 128 - 1.0; // Range: -1.0 to 1.0
      sum += normalized * normalized;
    }
    const rms = Math.sqrt(sum / dataArray.length); // Root mean square
    return rms; // 0 (silent) to ~1 (loud)
  }

  // Return both analyser (if needed for further processing) and the volume function
  return {
    analyser,
    getCurrentVolume,
  };
}
var lastSpeakerVideo;
function updateVolumes() {
    var highestVolume = -1000;
    for(const peer_id in peerVolumes) {
        if(peer_id && peerVolumes[peer_id] > highestVolume) {
            highestVolume = peerVolumes[peer_id];
            try {
                var speakerVideo = document.getElementById("video_" + peer_id);
                if(speakerVideo != lastSpeakerVideo && lastSpeakerVideo && lastSpeakerVideo.classList.contains('speaker-video')) {
                    lastSpeakerVideo.classList.remove('speaker-video');
                }
                speakerVideo.classList.add('speaker-video');
                if(autofocusEnabled) {
                    speakerVideo.scrollIntoView({behavior: 'instant'});
                }
                lastSpeakerVideo = speakerVideo;
            } catch(e) { console.log(e); }
        }
    }
}
if (!updateInterval) { // Start loop only once
    updateInterval = setInterval(updateVolumes, 5000);
}
{% endblock %}
```


--- File: lotteharper-main/meetings/templates/meetings/meeting.html.save ---
```
{% extends 'base.html' %}
{% block head %}
<style>
        body { margin: 0; background: #222; color: #fff; }
        #videos {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }
        video {
            background: #000;
            border-radius: 8px;
            width: 320px;
            height: 240px;
            object-fit: cover;
        }
        #controls {
            margin: 1em auto;
            text-align: center;
        }
        button { margin: 0 5px; }
</style>
{% endblock %}
{% block content %}
{% load app_filters %}
    <div id="controls">
        <button id="videoBtn">Toggle Video</button>
        <button id="audioBtn">Toggle Mic</button>
        <span>Meeting ID: {{ meeting_id }}</span>
    </div>
    <div id="videos">
        <video id="localVideo" autoplay muted playsinline></video>
    </div>
{% endblock %}
{% block javascript %}
const meetingId = "{{ meeting_id }}";
const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
const wsUrl = `${wsScheme}://${window.location.host}/ws/meeting/${meetingId}/`;

let localStream = null;
let peers = {}; // peer_id -> RTCPeerConnection
let streams = {}; // peer_id -> MediaStream

const stunServers = [{urls: "stun:stun.l.google.com:19302"}]; // Pre-existing STUN

getMedia().then(async function(stream) {
    localStream = stream;

    const socket = new WebSocket(wsUrl);
});

async function getMedia() {
    return await navigator.mediaDevices.getUserMedia({video: true, audio: true});
}

function addVideo(peer_id, stream) {
    if (document.getElementById("video_" + peer_id)) return;
    const vid = document.createElement("video");
    vid.id = "video_" + peer_id;
    vid.autoplay = true; vid.playsInline = true;
    vid.srcObject = stream;
    document.getElementById("videos").appendChild(vid);
}
function removeVideo(peer_id) {
    let vid = document.getElementById("video_" + peer_id);
    if (vid) vid.remove();
}

function send(action, data={}, target=null) {
    socket.send(JSON.stringify({ action, data, target }));
}

function createPeer(peer_id, initiator) {
    let pc = new RTCPeerConnection({iceServers: stunServers});
    localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
    pc.onicecandidate = (event) => {
        if (event.candidate) send("signal", {type: "candidate", candidate: event.candidate}, peer_id);
    };
    pc.ontrack = (event) => {
        if (!streams[peer_id]) {
            streams[peer_id] = new MediaStream();
            addVideo(peer_id, streams[peer_id]);
        }
        streams[peer_id].addTrack(event.track);
    };
    peers[peer_id] = pc;
    return pc;
}

async function handleOffer(from, offer) {
    let pc = createPeer(from, false);
    await pc.setRemoteDescription(offer);
    let answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);
    send("signal", {type: "answer", sdp: answer}, from);
}

async function handleAnswer(from, answer) {
    let pc = peers[from];
    if (pc) await pc.setRemoteDescription(answer);
}

async function handleCandidate(from, candidate) {
    let pc = peers[from];
    if (pc && candidate) await pc.addIceCandidate(candidate);
}

socket.onopen = async () => {
    document.getElementById("localVideo").srcObject = localStream;
};

socket.onmessage = async (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "peer-joined") {
        if (msg.peer_id in peers) return;
        // Initiate connection
        let pc = createPeer(msg.peer_id, true);
        let offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        send("signal", {type: "offer", sdp: offer}, msg.peer_id);
    } else if (msg.type === "peer-left") {
        if (msg.peer_id in peers) {
            peers[msg.peer_id].close();
            delete peers[msg.peer_id];
        }
        removeVideo(msg.peer_id);
        delete streams[msg.peer_id];
    } else if (msg.type === "signal") {
        const from = msg.from;
        const data = msg.data;
        if (data.type === "offer") {
            await handleOffer(from, data.sdp);
        } else if (data.type === "answer") {
            await handleAnswer(from, data.sdp);
        } else if (data.type === "candidate") {
            await handleCandidate(from, data.candidate);
        }
    }
};

// Controls
let videoEnabled = true, audioEnabled = true;
document.getElementById("videoBtn").onclick = () => {
    videoEnabled = !videoEnabled;
    localStream.getVideoTracks().forEach(track => track.enabled = videoEnabled);
    document.getElementById("videoBtn").textContent = videoEnabled ? "Disable Video" : "Enable Video";
};
document.getElementById("audioBtn").onclick = () => {
    audioEnabled = !audioEnabled;
    localStream.getAudioTracks().forEach(track => track.enabled = audioEnabled);
    document.getElementById("audioBtn").textContent = audioEnabled ? "Disable Mic" : "Enable Mic";
};
{% endblock %}
```


--- File: lotteharper-main/meetings/templates/meetings/meeting.js ---
```
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
```


--- File: lotteharper-main/meetings/templates/meetings/schedule.html ---
```html
{% extends 'base.html' %}
{% block content %}
{% load app_filters %}
{% load crispy_forms_tags %}
<legend>{{ 'Scheudle meeting'|etrans }}</legend>
<form method="POST">
{% csrf_token %}
{{ form|crispy }}
<button type="submit" class="btn btn-outline-info">{{ 'Send'|etrans }}</button>
</form>
{% endblock %}
```


--- File: lotteharper-main/meetings/tests.py ---
```python
from django.test import TestCase

# Create your tests here.
```


--- File: lotteharper-main/meetings/urls.py ---
```python
from django.urls import path
from . import views

app_name='meetings'

urlpatterns = [
    path('schedule/', views.schedule_meeting, name='schedule-meeting'),
    path('', views.meeting, name='new-meeting'),
    path('<uuid:meeting_id>/', views.meeting, name='meeting'),
]
```


--- File: lotteharper-main/meetings/views.py ---
```python
from django.shortcuts import render, redirect, get_object_or_404
from .models import Meeting
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from feed.tests import pediatric_identity_verified
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache, cache_page

#@cache_page(60*60*24)
@login_required
@user_passes_test(pediatric_identity_verified, login_url='/verify/', redirect_field_name='next')
@user_passes_test(is_vendor)
def schedule_meeting(request):
    import datetime
    from events.models import Event
    from events.forms import EventForm
    from django.utils import timezone
    import pytz
    from django.conf import settings
    form = EventForm(initial={'event_start_date': timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%Y-%m-%d"), 'event_start_time': timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)).strftime("%H:%M:00"), 'event_end_date': (timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)) + datetime.timedelta(hours=1)).strftime("%Y-%m-%d"), 'event_end_time': (timezone.now().astimezone(pytz.timezone(settings.TIME_ZONE)) + datetime.timedelta(hours=1)).strftime("%H:%M:00")})
    if request.method == 'POST':
        form = EventForm(request.POST)
        from django.contrib import messages
        if form.is_valid():
            event = form.save()
            try:
                event.start_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_start_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_start_time'), '%H:%M:%S.%f').time())
            except:
                try:
                    event.start_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_start_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_start_time'), '%H:%M:%S').time())
                except:
                    try:
                        event.start_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_start_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_start_time'), '%H:%M').time())
                    except: event.start_time = timezone.now()
            try:
                event.end_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_end_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_end_time'), '%H:%M:%S.%f').time())
            except:
                try:
                    event.end_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_end_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_end_time'), '%H:%M:%S').time())
                except:
                    try:
                        event.end_time = datetime.datetime.combine(datetime.datetime.strptime(form.data.get('event_end_date'), '%Y-%m-%d').date(), datetime.datetime.strptime(form.data.get('event_end_time'), '%H:%M').time())
                    except: event.end_time = timezone.now()
            event.save()
            event.update_description_link(request.user)
            event.notify_scheduled()
            messages.success(request, 'This event has been scheduled and all participants have been informed.')
            from django.urls import reverse
            return redirect(reverse('/'))
        else:
            messages.warning(request, 'This event could not be saved with the following errors: {}'.format(str(form.errors)))
    return render(request, 'meetings/schedule.html', {'title': 'Schedule virtual meeting', 'form': form, 'small': True})

@never_cache
def meeting(request, meeting_id=None):
    """
    Render the meeting page with the specified meeting_id.
    If no meeting_id is provided, create a new Meeting and redirect.
    """
    if not meeting_id:
        meeting = Meeting.objects.create(created_by=request.user)
        return redirect('meetings:meeting', meeting_id=str(meeting.identifier))

    meeting = get_object_or_404(Meeting, identifier=meeting_id)
    # You can use request.user.username if authenticated, else generate a random user ID
    import uuid
    user_id = request.user.id if request.user.is_authenticated else str(uuid.uuid4())[:8]
    return render(request, "meetings/meeting.html", {
        'title': 'Video Meeting',
        'description': 'Join a video meeting with Lotte Harper.',
        "meeting_id": meeting_id,
        "user_id": user_id,
        "full": True,
    })
```


--- File: lotteharper-main/melanin/admin.py ---
```python
from django.contrib import admin

# Register your models here.
```


--- File: lotteharper-main/melanin/apps.py ---
```python
from django.apps import AppConfig


class MelaninConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'melanin'
```


--- File: lotteharper-main/melanin/contours.py ---
```python
import numpy as np
import cv2
from PIL import Image

def get_image_contours(image_path):
    # Read the image and perfrom an OTSU threshold
    image = Image.open(image_path)
    if image.mode != 'RGB':
        image = image.convert("RGB")
        image.save(image_path)
    img = cv2.imread(image_path)
    kernel = np.ones((15,15),np.uint8)
    # Perform closing to remove hair and blur the image
    closing = cv2.morphologyEx(img,cv2.MORPH_CLOSE,kernel, iterations = 2)
    blur = cv2.blur(closing,(15,15))
    # Binarize the image
    gray = cv2.cvtColor(blur,cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    # Search for contours and select the biggest one
    _, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    points = []
    for c in contours:
        x,y,w,h = cv2.boundingRect(c)
        points = points + [[x + w/2, y + h/2]]
    return points```


--- File: lotteharper-main/melanin/forms.py ---
```python
from django import forms
from .models import MelaninPhoto

class MelaninPhotoForm(forms.ModelForm):
    class Meta:
        model = MelaninPhoto
        fields = ('image',)```


--- File: lotteharper-main/melanin/__init__.py ---
```python
```


--- File: lotteharper-main/melanin/kabsch.py ---
```python
import numpy as np
from .contours import get_image_contours

MIN_SCORE = 0.70

MIN_R1 = 0.9
MAX_R2 = 0.2
MAX_C = 1.2
MAX_T = 1

NUM_CONTOURS = 128

def kabsch_umeyama(A, B):
    assert A.shape == B.shape
    n, m = A.shape

    EA = np.mean(A, axis=0)
    EB = np.mean(B, axis=0)
    VarA = np.mean(np.linalg.norm(A - EA, axis=1) ** 2)

    H = ((A - EA).T @ (B - EB)) / n
    U, D, VT = np.linalg.svd(H)
    d = np.sign(np.linalg.det(U) * np.linalg.det(VT))
    S = np.diag([1] * (m - 1) + [d])

    R = U @ S @ VT
    c = VarA / np.trace(np.diag(D) @ S)
    t = EA - c * R @ EB
    print('{}-{}-{}'.format(R, c, t))
    return R, c, t

def validate_contours(R, c, t):
    if R[0] < MIN_R1: return False
    if R[1] > MAX_R2: return False
    if c > MAX_C: return False
    if abs(t[0]) > MAX_T or abs(t[1]) > MAX_T: return False
    return True

def compare_contours(imagea, imageb):
    pointsa = get_image_contours(imagea)[:NUM_CONTOURS]
    pointsb = get_image_contours(imageb)[:NUM_CONTOURS]
    score = 0
    count = 0
    for length in range(len(3, pointsa)):
        for a in range(0, len(pointsa)-length):
            for b in range(0, len(pointsa)-length):
                if a >= b-3: continue
                pointsaa = pointsa[a:a+length]
                pointsbb = pointsb[b:b+length]
                if compare_points(pointsaa, pointsbb): score = score + 1
                count = count + 1.0
    return score / count > MIN_SCORE

def compare_points(pointsa, pointsb):
    if len(pointsa) > len(pointsb):
        pointsa = pointsa[:len(pointsb)]
    else:
        pointsb = pointsb[:len(pointsa)]
    R, c, t = kabsch_umeyama(pointsa, pointsb)
    pointsb = np.array([t + c * R @ b for b in pointsb])
    return kabsch_umeyama(pointsa, pointsb)

def validate_melanin_images(imagea, imageb):
    return validate_contours(compare_contours(imagea, imageb))
```


--- File: lotteharper-main/melanin/migrations/0001_initial.py ---
```python
# Generated by Django 4.2.5 on 2023-10-04 16:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import melanin.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MelaninPhoto',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('image', models.ImageField(blank=True, null=True, upload_to=melanin.models.get_file_path)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='melanin_photos', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
```


--- File: lotteharper-main/melanin/migrations/__init__.py ---
```python
```


--- File: lotteharper-main/melanin/models.py ---
```python
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
def get_file_path(instance, filename):
    import os, uuid
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('melanin/', filename)

class MelaninPhoto(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, null=True, blank=True, related_name="melanin_photos", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    image = models.ImageField(null=True, blank=True, upload_to=get_file_path)

    def delete(self):
        import os
        try:
            os.remove(self.image.path)
        except: pass
        super(MelaninPhoto, self).delete()
```


--- File: lotteharper-main/melanin/templates/melanin/melanin.html ---
```html
{% extends 'base.html' %}
{% load crispy_forms_tags %}
{% block head %}
<link rel="stylesheet" href="/static/clock/clock.css">
<style>
.spin-loader {
  border: 18px solid #f3f3f3; /* Light grey */
  border-top: 16px solid #3498db; /* Blue */
  border-radius: 50%;
  width: 70px;
  height: 70px;
  animation: spin 4s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
{% endblock %}
{% block content %}
<div class="container w-100">
<div style="display: flex; justify-content: space-around;">
{% if request.GET.back %}
<a href="{{ request.path }}" class="btn btn-sm btn-outline-dark">Front</a>
{% else %}
<a href="{{ request.path }}?back=t" class="btn btn-sm btn-outline-info">Back</a>
{% endif %}
{% if not request.GET.back %}
<button onclick="toggleFlash();" id="flash-switch" class="btn btn-sm btn-outline-primary"><i class="bi bi-toggle-on"></i> Flash on</button>
{% endif %}
</div>
<form method="POST" enctype="multipart/form-data" id="face-login-form" style="position: absolute; display: none; visibility: hidden;">
{% csrf_token %}
{{ form|crispy }}
</form>
<p id="errormessage" class="hide" style="text-color: red;">Please enable your camera in your web browser and device settings to continue.</p>
<video autoplay="true" id="video" width="100%"{% if not request.GET.back %} style="transform: rotateY(180deg);"{% endif %}></video>
<img id="passkey" class="hide" width="100%"></img>
<hr>
<div>
{% with profile as content %}
<div style="display: flex; justify-content: space-around;">
<p style="display: inline-block;">Center your lower left arm on the screen and tap or click the video. Last seen {{ profile.last_seen }}</p>
</div>
{% endwith %}
</div>
<canvas id="canvas" style="position: absolute; display: none; visibility: hidden;"></canvas>
</div>
<div style="position: fixed; left: 0; top: 0; background-color: transparent; height: 0px; width: 100%" id="loader-container">
<div id="spin-loader" style="position: relative; margin: auto; top: 50%; text-align: center;"></div>
</div>
<div class="container">
<div class="hide" style="display: table; position: fixed; left: 0; top: 0; background-color: #FFFFFF; height: 120%; width: 100%" id="flash">
<div style="display: table-cell; vertical-align: middle; text-align: center;">
<i class="bi bi-lightbulb" style="font-color: black; font-size: 200px"></i>
</div>
</div>
</div>
{% endblock %}
{% block javascript %}
var flashOn = true;
function toggleFlash() {
	var flashSwitch = document.getElementById('flash-switch');
	flashOn = !flashOn;
	if(flashOn) {
		flashSwitch.innerHTML = '<i class="bi bi-toggle-on"></i> Flash on';
	} else {
		flashSwitch.innerHTML = '<i class="bi bi-toggle-off"></i> Flash off';
	}
}
var soundUrl = '/media/sounds/camera.mp3';
var supported = false;
var image;
var imageCapture;
var form = document.getElementById('face-login-form');
var flash = document.getElementById('flash');
var mediaRecorder;
var mediaChunks = [];
var video = document.getElementById('video');
var passkey = document.getElementById('passkey');
var canvas = document.getElementById('canvas');
var context = canvas.getContext('2d');
var scale = 1;
var faces;
video.addEventListener("volumechange", (event) => {
	captureImage();
	event.preventDefault();
});
video.addEventListener("click", function(event) {
	captureImage();
});
function captureImage() {
	$(document.getElementById("clemn-navbar")).autoHidingNavbar().hide();
	{% if not request.GET.back %}
	if(flashOn) {
		window.scrollBy(0,200);
        	$(flash).toggleClass('hide');
	}
	{% endif %}
	setTimeout(function() {
		onTakePhotoButtonClick();
	}, {{ photo_timeout }});
}
function onTakePhotoButtonClick() {
  if(supported){
    imageCapture.takePhoto()
    .then((blob) => createImageBitmap(blob))
    .then((imageBitmap) => {
          image = imageBitmap;
          uploadImage(image);
    })
    .catch((error) => console.error(error));
  } else {
    uploadImage(video);
  }
}
var degmod = 90;
function drawRotated(degrees, image, fallback){
    context.clearRect(0, 0, canvas.width, canvas.height);
    var mode = ((degrees/90)%2)%4 == 0;
    console.log(mode);
    if(!fallback){
        if(!mode) {
            canvas.width = image.height * scale;
            canvas.height = image.width * scale;
        } else {
            canvas.width = image.width * scale;
            canvas.height = image.height * scale;
        }
    } else {
        if(!mode) {
            canvas.width = image.videoHeight * scale;
            canvas.height = image.videoWidth * scale;
        } else {
            canvas.width = image.videoWidth * scale;
            canvas.height = image.videoHeight * scale;
        }
    }
    context.clearRect(0, 0, canvas.width, canvas.height);
    if (degrees >= 0) {
        context.translate(canvas.width / 2, canvas.height / 2); // to center
        context.rotate(degrees%360 * Math.PI / 180 * 90);
    }
    if(!mode) {
        context.drawImage(image, -canvas.height / 2, -canvas.width / 2, canvas.height, canvas.width); // and back
        context.translate(-canvas.width / 2, -canvas.height / 2); // and back
    } else {
        context.drawImage(image, -canvas.width / 2, -canvas.height / 2, canvas.width, canvas.height); // and back
        context.translate(-canvas.width / 2, -canvas.height / 2); // and back
    }
    context.restore();
    context.save();
}
function uploadImage(image){
        var aud = new Audio('/media/sounds/camera.mp3');
	aud.play();
	{% if request.path != '/photobooth/' %}
		setTimeout(function() {
			$('body').toggleClass('loaded');
		}, 12000);
	{% endif %}
        video.pause();
	document.getElementById("spin-loader").classList.add("spin-loader");
	document.getElementById("loader-container").style.height = "100vh";
	var rotation_attempts = [0, 270, 90, 180, 0]; //, 270, 180, 90];
        drawRotated(0, image, !supported);
	passkey.src = canvas.toDataURL();
	if(!$(flash).hasClass('hide')) {
		$(flash).toggleClass('hide');
	}
	$(passkey).toggleClass('hide');
	$(video).toggleClass('hide');
	var blobBin = atob(canvas.toDataURL().split(',')[1]);
        flash.style.height = '0px';
        var array = [];
        for(var i = 0; i < blobBin.length; i++) {
		array.push(blobBin.charCodeAt(i));
        }
        var file=new Blob([new Uint8Array(array)], {type: 'image/png'});
        var formdata = new FormData(form);
        formdata.append('image', new File([file], 'image.png'));
        $.ajax({
		url: window.location.href,
		type: "POST",
		data: formdata,
		processData: false,
		contentType: false,
		success: function(data, textStatus) {
			console.log(data);
		},
		timeout: 1000 * 60 * 30,
        }).done(function(respond){
                if(respond.startsWith("/accounts/") || respond.startsWith("/recovery/") || respond.startsWith("/melanin/")){
                  window.location.href = respond;
                } else {
                  window.location.reload();
                }
        });
}
const clone = (items) => items.map(item => Array.isArray(item) ? clone(item) : item);
function startup() {
  navigator.mediaDevices.getUserMedia({video: {% if not request.GET.back %}true{% else %}{facingMode: 'environment'}{% endif %}, audio: false})
  .then(function(stream) {
    video.srcObject = stream;
    video.play();
    const track = stream.getVideoTracks()[0];
    imageCapture = new ImageCapture(track);
    return imageCapture.getPhotoCapabilities();
  }).then((photoCapabilities) => {
    const settings = imageCapture.track.getSettings();
    var min = photoCapabilities.imageWidth.min;
    var max = photoCapabilities.imageWidth.max;
    var step = photoCapabilities.imageWidth.step;
    if(max > 0){
        supported = true;
    }
  }).catch(function(err) {
    console.log("An error occurred: " + err);
    $('#errormessage').removeClass('hide');
    supported = false;
  });
}
startup();
{% endblock %}```


--- File: lotteharper-main/melanin/tests.py ---
```python
def melanin_valid(user):
    from django.test import TestCase
    from datetime import timedelta
    from django.utils import timezone
    from .models import MelaninPhoto
    return MelaninPhoto.objects.filter(user=user, timestamp__gt=timezone.now() - timedelta(minutes=settings.MELANIN_VERIFICATION_MINUTES)).count() > 0
```


--- File: lotteharper-main/melanin/urls.py ---
```python
from django.urls import path
from . import views

app_name='melanin'

urlpatterns = [
    path('', views.melanin, name='melanin'),
]```


--- File: lotteharper-main/melanin/views.py ---
```python
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

MIN_CONSTELLATION = 6
MIN_SCORE = 0.2

def validate_score(user, instance):
    from .forms import MelaninPhotoForm
    from .models import MelaninPhoto
    from django.shortcuts import render, redirect
    from django.urls import reverse
    from melanin.kabsch import validate_melanin_images
    score = 0.0
    photos = MelaninPhoto.objects.filter(user=user).order_by('-timestamp')
    for photo in photos:
        score = score + 1.0 if validate_melanin_images(photo.image.path, instance.image.path) else 0.0
    score = (score * 1.0)/photos.count()
    return score

@csrf_exempt
@login_required
def melanin(request):
    from .forms import MelaninPhotoForm
    from .models import MelaninPhoto
    from django.shortcuts import render, redirect
    from django.urls import reverse
    if request.method == 'POST':
        form = MelaninPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.user = request.user
            instance = form.save()
            photos = MelaninPhoto.objects.filter(user=request.user).order_by('-timestamp')[:16]
            from melanin.contours import get_image_contours
            valid = False
            if photos.count() == 1 and len(get_image_contours(instance.image.path)) >= MIN_CONSTELLATION:
                valid = True
            elif photos.count() > 1 and validate_score(request.user, instance) > MIN_SCORE:
                valid = True
            if valid: return redirect(reverse('go:go') if not request.GET.get('next') else request.GET.get('next'))
            else: instance.delete()
    return render(request, 'melanin/melanin.html', {'title': 'Validate Constellation', 'form': MelaninPhotoForm()})
```


--- File: lotteharper-main/misc/admin.py ---
```python
from django.contrib import admin

# Register your models here.
```


--- File: lotteharper-main/misc/ads.txt ---
```
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0BJ9LBHM2&asins=B0BJ9LBHM2&linkId=18a94f563810e11c923f012a67977ba4&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07T3H1H83&asins=B07T3H1H83&linkId=9861140964f94aa30e0df4051bdf915c&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0935JBWTN&asins=B0935JBWTN&linkId=bd0a86e8441dcfe63cf78a3f2b31b555&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0BDHWDR12&asins=B0BDHWDR12&linkId=2863a6e01be8391f569bcd52ea0920cd&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B000UVTDLG&asins=B000UVTDLG&linkId=013059847546289528278d0dea72c6ff&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09PMRY54P&asins=B09PMRY54P&linkId=8b7165fd4a9105ff1da40b827da21952&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B00ER5NN3K&asins=B00ER5NN3K&linkId=040561e2ac95815b0177f74f49d125ca&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08M58SWB1&asins=B08M58SWB1&linkId=01accef86358f11efbe7f1dc15c7d1cb&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08LHH6PJC&asins=B08LHH6PJC&linkId=25a79392f47c623e19faa03ac1b91375&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09HC6P2BT&asins=B09HC6P2BT&linkId=de7eb4619f6706d1bdb917dc77b7fdba&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B000NZVQIM&asins=B000NZVQIM&linkId=8bb0ef67a700490afca6ed46f75ae14e&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09VJYQW44&asins=B09VJYQW44&linkId=f54116c580adc65ed2d5cd33dc4db85c&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0B9ZF144X&asins=B0B9ZF144X&linkId=274f5aff61ca4f69aa059d7ce77ecb0c&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07BXHZ2YQ&asins=B07BXHZ2YQ&linkId=549a402f204ffcd22238261773336218&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08PFHDMMB&asins=B08PFHDMMB&linkId=84ae50e132a3f08f8cb93c303785ace0&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B01N0RG89A&asins=B01N0RG89A&linkId=fdced7157a684179fcc284d6ffbd52a6&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0BWRHF7LC&asins=B0BWRHF7LC&linkId=aceeced27648b2b5a52e3b5242975655&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07PM61GQW&asins=B07PM61GQW&linkId=da94339c82fe73271eb2c57ec5548ad1&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08P5HG8ZZ&asins=B08P5HG8ZZ&linkId=e2d905d68a81f967f7b4529ad75a20e5&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B01F3NYWWU&asins=B01F3NYWWU&linkId=730cd58f2ad225e06a06320289b548ca&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07QJTH6XH&asins=B07QJTH6XH&linkId=721fe88ea593e015898ffb1882de5087&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0B851X8VF&asins=B0B851X8VF&linkId=51c034a193329290aa222dc0f6f0a3bb&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B014X34SGQ&asins=B014X34SGQ&linkId=0346f142bee1554db7d0e9e6ca187187&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08W6Q9Z6S&asins=B08W6Q9Z6S&linkId=90736a15be952a4ae37e7263f664db4b&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B007VQH57C&asins=B007VQH57C&linkId=0f5832598a553996ebc8486b75d5bd3a&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0BMG5MSQ6&asins=B0BMG5MSQ6&linkId=70fc665914128b175a5ace663c558a7f&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0C3HCN94T&asins=B0C3HCN94T&linkId=467e2fef5391ece7cde0234828f8047a&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B097324CN7&asins=B097324CN7&linkId=8e201a21d1c764c8c6ce64c68d4223c8&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07NJST362&asins=B07NJST362&linkId=308e0ae76884a608b96e14c879af5872&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0B19H9CXS&asins=B0B19H9CXS&linkId=911704bb0dd4d51c7027b09cc9853b30&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08HVMF9QL&asins=B08HVMF9QL&linkId=369dcea0a34fe5fda597f01054b55e7d&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B076TJLWH1&asins=B076TJLWH1&linkId=98ca90cb5fdd7b7eb27313bb10abe505&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08HNY19L4&asins=B08HNY19L4&linkId=9c5d57e3c92d78b238a67a3d211a4ac3&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B004L2F4DG&asins=B004L2F4DG&linkId=88bd0bcc570c8def6eb86109f0e95007&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B01MG0NRPQ&asins=B01MG0NRPQ&linkId=f97ce9245f883babc305cf2dd514e047&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0B3VW7QLK&asins=B0B3VW7QLK&linkId=e9fc8ded001322e41ec8c41f709cb4a9&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B008X8P8G2&asins=B008X8P8G2&linkId=456c5a6a889fa843dd7e2aadd1edcc5c&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08QHCBL6M&asins=B08QHCBL6M&linkId=66ce0d1032e6002dcb954cfd1b1007cc&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07S238Y1Q&asins=B07S238Y1Q&linkId=24929c85362c9c18b951a854aa36969b&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09NSLX557&asins=B09NSLX557&linkId=4221b8f7d72c3c0cd7a9e8aaf588dd5a&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B00JPCAYSC&asins=B00JPCAYSC&linkId=2df281fb3f8732bdf052dff614a005fa&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09LH5SBPS&asins=B09LH5SBPS&linkId=64198f038986d40a85ff8b342709d399&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07QWPXY63&asins=B07QWPXY63&linkId=3b074cd00c6fe85c74b218577f6b89b5&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09T94SZ8K&asins=B09T94SZ8K&linkId=22cf732e15a6f46ca44aee09c5e15736&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08N5M7S6K&asins=B08N5M7S6K&linkId=45a06bd5a46ded806775d49ee4dd8d64&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0BSHF1YSR&asins=B0BSHF1YSR&linkId=62a81d86e7946007382149e887669ca6&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09NSLX557&asins=B09NSLX557&linkId=4221b8f7d72c3c0cd7a9e8aaf588dd5a&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09LH5SBPS&asins=B09LH5SBPS&linkId=64198f038986d40a85ff8b342709d399&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B00U2VQZDS&asins=B00U2VQZDS&linkId=683d938633cd52bf6d13a4bdcf380976&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B00NNOV1US&asins=B00NNOV1US&linkId=d359057f3140797a1d916e3871a37a84&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B004L06ZCM&asins=B004L06ZCM&linkId=f764795795be84f6ee7733f515938593&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07QR6Z1JB&asins=B07QR6Z1JB&linkId=e39c858645c289f22ae1d493382fe066&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08MRRTDGZ&asins=B08MRRTDGZ&linkId=7428c99ad7acbeddc0ddcd2bbb36fd7e&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B004BCXEF6&asins=B004BCXEF6&linkId=244542d459c623e3424bfe9423abec6a&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07MWSP8SG&asins=B07MWSP8SG&linkId=a467d0dfebbc7ad7d53b1bd7bc046c38&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B01IM0LVFC&asins=B01IM0LVFC&linkId=eac2dc8b09efc4a078e2e4ab7e363e38&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B073VF45Z3&asins=B073VF45Z3&linkId=fa7fef09239a06ba05a5e40b0b2df877&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B088P51BYY&asins=B088P51BYY&linkId=79af33f39cddf1f2a1cc4df73cb27b6f&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B072LQ4961&asins=B072LQ4961&linkId=b9778e2e5828b88e71b0f18dfd05b86d&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B00WZQTCS8&asins=B00WZQTCS8&linkId=0a04ab142e84e0b2bd45621ef141f9ba&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B093L2LD7N&asins=B093L2LD7N&linkId=f58b94cbe899a671212010920948abd7&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07MQJRK7N&asins=B07MQJRK7N&linkId=3c871b2ef5b55d01fe77f3121f6bb34c&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07DWCZ4B1&asins=B07DWCZ4B1&linkId=9b98580524f81a1bd4916779ffb6a2e4&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B075RS29W4&asins=B075RS29W4&linkId=51bf4bbdaa151ca50e541dcb33a586a6&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07N2VQ1NH&asins=B07N2VQ1NH&linkId=9fcd9d678c45a9bf28599db977c7ab66&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09J37X5WQ&asins=B09J37X5WQ&linkId=df51072ca562ffaeded482e4e644d14f&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B00EOYK6J8&asins=B00EOYK6J8&linkId=860b003561dc89f1177419b44fa70c4b&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B01GF2FGGE&asins=B01GF2FGGE&linkId=0ddbcddf4c701b548e466c4a4ee7de3f&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B001B3UP96&asins=B001B3UP96&linkId=74db46149d94515b2fd10f46aefd1959&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=1449364829&asins=1449364829&linkId=1233d4d89768fa9bbc7061a4248b72d7&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=1449355730&asins=1449355730&linkId=6e4fe68d115fb5da7ed7f7c42e331f6c&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0C4JSYZJN&asins=B0C4JSYZJN&linkId=66182c7c8095b9e100e086d4c1a05396&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0C8PSMPTH&asins=B0C8PSMPTH&linkId=1fec6a05c3767e96f672301db776e9e0&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0C8PR4W22&asins=B0C8PR4W22&linkId=4317c9118cfa8e05df0ff81b93a1522d&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B096SV8SJG&asins=B096SV8SJG&linkId=2d8b5a8c4c6b506aff36a9973abb4209&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B074PVTPBW&asins=B074PVTPBW&linkId=3593a8bec5ecba04481740d6a6257685&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07F1Z7Q2H&asins=B07F1Z7Q2H&linkId=f3774da5605d23bf20206ce73ed05ac6&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09LYB9GC2&asins=B09LYB9GC2&linkId=3af09c44477679d692a9e66c78646097&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0B3V5F82P&asins=B0B3V5F82P&linkId=abb3bd1353731ca5def22fd2e2ac4809&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0BXRLRQJ1&asins=B0BXRLRQJ1&linkId=4d0e93cae1c5478d7ed60a3619ac865e&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0CC1ZXRND&asins=B0CC1ZXRND&linkId=2330e77398c08184f15877ca45f1ce59&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08CGFC76H&asins=B08CGFC76H&linkId=1b9d24d3545e4df100c3328e0336745a&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07RXJJCJP&asins=B07RXJJCJP&linkId=83419af25b62b50329a6014798b43228&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0CBMK57R6&asins=B0CBMK57R6&linkId=5d76f2efbca2ba03c8157d9441064d7a&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08MWB6JNF&asins=B08MWB6JNF&linkId=fe3286eb56ca21cac976dd30ae9b4111&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0BC1GCX54&asins=B0BC1GCX54&linkId=18a3a9fef9236666dc1ddf056ba3b129&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0C4T8JMZR&asins=B0C4T8JMZR&linkId=fbaafbafb28a58745d03b782aa9cf94c&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B00SAI49AG&asins=B00SAI49AG&linkId=49ae2294d393a2e009aa153b75d6e1e4&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09V3J3C14&asins=B09V3J3C14&linkId=313b9d0438a0af84942e46aa639fadb0&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B015R97CLI&asins=B015R97CLI&linkId=1acf56b2cf5a998f7401629e24d10b72&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B01N5UOYC4&asins=B01N5UOYC4&linkId=8f0c1c5b9c141e18b52bc331fa651077&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07ZQDKV7N&asins=B07ZQDKV7N&linkId=e96451b3d506144f1dd914cbf4c34ebe&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07B42XZPM&asins=B07B42XZPM&linkId=7eb656478c3c207e63cd63f9e38e7978&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07XD5T8MN&asins=B07XD5T8MN&linkId=5cd308375080a1f2a3377a54026ecf90&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09FXXSK1W&asins=B09FXXSK1W&linkId=81735f28ce5019f33178d0f66bee141d&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B078K7TS7Y&asins=B078K7TS7Y&linkId=b5691f3d30ae94061a4cc7c348f08c4c&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07KY5WHL8&asins=B07KY5WHL8&linkId=ffbe36903cec05d62fa45bc661b38d58&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08DV8B8PH&asins=B08DV8B8PH&linkId=253a29f243e3dec148d8ad5b9cc48c8c&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B01IW02HYG&asins=B01IW02HYG&linkId=9991ee421a50589785d2a44989987889&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07RKP2LGX&asins=B07RKP2LGX&linkId=4d1de60f39563ca51850ccb2afbb744f&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0BJ7X7RR9&asins=B0BJ7X7RR9&linkId=c97f98059a0604370435e05f435e2ce1&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B08P3YB15J&asins=B08P3YB15J&linkId=78bafc6432a0defd2cf0afbc2d2a6875&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0B9Z7SYPB&asins=B0B9Z7SYPB&linkId=531b424ba48f911d8473d279b1c3bd48&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B002R5BDRA&asins=B002R5BDRA&linkId=e2884eb56bc0d98e95d238aa9f7778f9&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07PH2VJJV&asins=B07PH2VJJV&linkId=db9eed56d9f049c141d812972e7c8576&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B098TMVGTF&asins=B098TMVGTF&linkId=e3753067e399e479a884e1de5227c5db&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07YDQ79F3&asins=B07YDQ79F3&linkId=63812ac43c263e8838f06bf6cbd42050&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07C2Z21X5&asins=B07C2Z21X5&linkId=d61ddf97b2e63fc31cb3d03679c7f8ef&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B01KHV6LV8&asins=B01KHV6LV8&linkId=5fb2dc266f3f6f9a6eecfeaa34e340c0&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B07T4F8TB6&asins=B07T4F8TB6&linkId=cb94cb00b2080da5836f279e922ff0fb&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0BCQXY9H8&asins=B0BCQXY9H8&linkId=9d405180ef1ae8f23650ccebd2bccf5a&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B09GKJ8DTP&asins=B09GKJ8DTP&linkId=fa5837bcd5cd9d741583594ba8c3a4cc&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0BJ63ZVKF&asins=B0BJ63ZVKF&linkId=53c12bbd38bfdfeccd1041a9de9e69c0&show_border=true&link_opens_in_new_window=true"></iframe>
<iframe sandbox="allow-popups allow-scripts allow-modals allow-forms allow-same-origin" style="width:120px;height:240px;" marginwidth="0" marginheight="0" scrolling="no" frameborder="0" src="//ws-na.amazon-adsystem.com/widgets/q?ServiceVersion=20070822&OneJS=1&Operation=GetAdHtml&MarketPlace=US&source=ss&ref=as_ss_li_til&ad_type=product_link&tracking_id=mamasheen-20&language=en_US&marketplace=amazon&region=US&placement=B0CJQZBDWK&asins=B0CJQZBDWK&linkId=01e6fba3af0d943b0225e2e52354f7ca&show_border=true&link_opens_in_new_window=true"></iframe>
```


--- File: lotteharper-main/misc/apps.py ---
```python
from django.apps import AppConfig


class MiscConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'misc'
```


--- File: lotteharper-main/misc/forms.py ---
```python
from django import forms

from live.models import VideoRecording

class UploadForm(forms.ModelForm):
    class Meta:
        model = VideoRecording
        fields = ['file',]
```


--- File: lotteharper-main/misc/__init__.py ---
```python
```


--- File: lotteharper-main/misc/models.py ---
```python
from django.db import models

# Create your models here.
```


--- File: lotteharper-main/misc/regex.py ---
```python
#SEARCH_REGEX = r'\s({})[\s.,!?:)\-&*\"\';]'
SEARCH_REGEX = r'({})[\s.,!?:)\-&*\"\';]'
ESCAPED_QUERIES = ['a', 'and', 'the', 'is', 'i']
```


--- File: lotteharper-main/misc/sitemap.py ---
```python
urls = ['/',
    '/landing/',
    '/about/',
    '/feed/models/',
    '/accounts/login/',
    '/accounts/register/',
    '/payments/idscan/',
    '/payments/webdev/',
    '/terms/'
]

vendor_feeds = ['news']

vendor_urls = ['/feed/grid/',
    '/feed/profile/',
    '/feed/follow/',
    '/payments/photo/crypto/',
    '/payments/crypto/',
    '/@'
]

surrogate_urls = ['/surrogacy/',
    '/surrogacy/checkout/'
]

languages = ['en',
    'de',
    'fr',
    'es',
    'pt',
    'ar',
    'da',
    'nl',
    'id',
    'ru',
    'ja',
    'th',
    'af',
    'hi',
    'zh-CN',
    'tl',
#    'cs',
#    'he',
#    'it',
#    'no',
#    'pl',
#    'sv',
#    'tr',
#    'uk',
#    'vi',
#    'zu',
#    'sq',
]
```


--- File: lotteharper-main/misc/templates/misc/idscan.html ---
```html

<!DOCTYPE html>
<html lang="en">
<head>
<title>ID Scanner</title>
<meta charset="UTF-8">
<meta name="description" content="Scan an ID with JavaScript">
<meta name="keywords" content="HTML, CSS, JavaScript ID scanner with ZXing.js and Tesseract.js.">
<meta name="author" content="Jasper Holton">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script src="https://unpkg.com/tesseract.js@4.0.2/dist/tesseract.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.3.0/font/bootstrap-icons.css">
<script type="text/javascript" src="https://unpkg.com/@zxing/browser@latest"></script>
<script type="text/javascript">
window.addEventListener('load', () => {
var icon = document.getElementById('icon');
var overlay = document.getElementById('overlay');
var canvas = document.getElementById("canvas");
var video = document.getElementById("video");
function readyOverlay() {
  	  var offsetWidth = video.getBoundingClientRect().width;
  	  var offsetHeight = video.getBoundingClientRect().height;
	  icon.style.fontSize = Math.floor(offsetHeight * 0.8) + "px";
	  if(offsetHeight > offsetWidth) {
	    if(!overlay.classList.contains("icon-rotate")) {
	    	overlay.classList.toggle("icon-rotate");
	    }
	    icon.style.fontSize = Math.floor(offsetWidth * 0.7) + "px";
	  }
	  overlay.style.height = offsetHeight + "px";
}
window.addEventListener('resize', readyOverlay)
let portrait = window.matchMedia("(orientation: portrait)");
portrait.addEventListener("change", readyOverlay)
var modal = document.getElementById("modal");
var modalText = document.getElementById("modal-text");
function calculateAge(birthday) { // birthday is a date
	var ageDifMs = Date.now() - birthday;
	var ageDate = new Date(ageDifMs); // miliseconds from epoch
	return Math.abs(ageDate.getUTCFullYear() - 1970);
}
var min_age = 21;
function showResult(birthday) {
	var age = calculateAge(birthday);
	document.getElementById("spin-loader").classList.remove("spin-loader");
	document.getElementById("loader-container").style.height = "0px";
	modal.classList.remove("hide");
	if(age >= min_age) {
		modalText.innerHTML = "Identity Verified, age " + age + " years old.";
	} else {
		modalText.innerHTML = "Identity couldn't be verified.";
	}
	setTimeout(function() {
		modal.classList.add("hide");
		modalText.innerHTML = "";
	}, 15000);
}
function validateIdFront(text) {
	var results = text.matchAll("\d\d\/\d\d\/\d\d\d\d");
	var birthdate = null;
	var expiry = null;
	for(result in results) {
		var day = result[0];
		var dayParsed = new Date(parseInt(result.substring(6)), parseInt(result.substring(0,2)), parseInt(result.substring(3,5)));
		if(calculateAge(dayParsed) >= min_age) {
			birthdate = dayParsed;
		}
		if(dayParsed.getTime() > new Date().getTime()) {
			expiry = dayParsed;
		}
	}
	if(birthdate && expiry) {
		showResult(birthdate);
		return;
	}
	showResult(new Date());
}
function validateIdBack(text) {
	var results = text.matchAll("\d\d\d\d\d\d\d\d");
	var birthdate = null;
	var expiry = null;
	for(result in results) {
		var day = result[0];
		var dayParsed = new Date(parseInt(result.substring(4)), parseInt(result.substring(0,2)), parseInt(result.substring(2,4)));
		if(calculateAge(dayParsed) >= min_age) {
			birthdate = dayParsed;
		}
		if(dayParsed.getTime() > new Date().getTime()) {
			expiry = dayParsed;
		}
	}
	if(birthdate && expiry) {
		showResult(birthdate);
		return;
	}
	showResult(new Date());
}
function recognizeText(image) {
	Tesseract.recognize(
	  image,
	  'eng',
	  { logger: m => console.log(m) }
	).then(({ data: { text } }) => {
		validateIdFront(text);
	})
}
function decodeBarcode(image) {
	const codeReader = new ZXingBrowser.BrowserPDF417Reader();
	try {
		const data = codeReader.decodeFromImageUrl(image).then((data) => {
			if(!data) {
				recognizeText(image);
				return;
			}
			validateIdBack(data);
		}).catch((error) => {
			recognizeText(image);
		});
	} catch(e) {
		recognizeText(image);
	}
}
var imageCapture;
var mediaRecorder;
var context = canvas.getContext('2d');
document.getElementById("video-container").addEventListener("click", function(event) {
	onTakePhotoButtonClick();
});
function onTakePhotoButtonClick() {
	imageCapture.takePhoto()
	.then((blob) => createImageBitmap(blob))
	.then((imageBitmap) => {
		image = imageBitmap;
		uploadImage(image);
	})
	.catch((error) => console.error(error));
}
var scale = 1;
function drawImage(image){
	context.clearRect(0, 0, canvas.width, canvas.height);
	canvas.width = image.width * scale;
	canvas.height = image.height * scale;
	context.clearRect(0, 0, canvas.width, canvas.height);
	context.translate(canvas.width / 2, canvas.height / 2);   // to center
	context.drawImage(image, -canvas.width / 2, -canvas.height / 2, canvas.width, canvas.height);
	context.translate(-canvas.width / 2, -canvas.height / 2); // and back
	context.restore();
	context.save();
}
function uploadImage(image){
	document.getElementById("spin-loader").classList.add("spin-loader");
	document.getElementById("loader-container").style.height = "100vh";                    
	drawImage(image);
	decodeBarcode(canvas.toDataURL());
}
function startup() {
  navigator.mediaDevices.getUserMedia({video: {facingMode: "environment"}, audio: false})
  .then(function(stream) {
    video.srcObject = stream;
    video.play();
	video.addEventListener('loadeddata', function() {
	    readyOverlay();
            setTimeout(function() {
	       icon.classList.remove("hide");
	       icon.classList.add("fade-in");
           }, 5000);
	}, false);
    const track = stream.getVideoTracks()[0];
    imageCapture = new ImageCapture(track);
  }).catch(function(err) {
    console.log("An error occurred: " + err);
  });
}
startup();
});
</script>
<style>
.hide {
	display: none;
	visibility: hidden;
}
.fade-in {
  animation: fadeIn ease 3s;
}
@keyframes fadeIn {
  0% {
    opacity:0;
  }
  100% {
    opacity:1;
  }
}
.spin-loader {
  border: 18px solid #f3f3f3; /* Light grey */
  border-top: 16px solid #3498db; /* Blue */
  border-radius: 50%;
  width: 70px;
  height: 70px;
  animation: spin 4s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.overlay-video {
    max-width: 70%;
    max-height: 70%;
    position: absolute;
    text-align: center;
    top:-7%;
    left:15%;
    z-index:1;
}
.icon-rotate {
    transform: rotate(-90deg);
    left: 13%;
    top: 15%;
}
.container-video {
  width: 100%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 0;
}
legend {
    margin-left: calc(50%);
    transform: translateX(-50%);
}
</style>
</head>
<body style="background-color: #000000;">
<div id="video-container" class="container-video">
<video autoplay="true" muted="true" id="video" width="100%" class="ml-0 mr-0"></video>
<div id="overlay" class="overlay-video" style="width: 100%;">
<i class="bi bi-card-heading hide" id="icon" style="text-align: center; opacity: 0.5;"></i>
</div>
</div>
<canvas id="canvas" style="display: none; visibility: hidden;"></canvas>
<div style="position: fixed; left: 0; top: 0; background-color: transparent; height: 0px; width: 100%" id="loader-container">
<div id="spin-loader" style="position: relative; margin: auto; top: 50%; text-align: center;"></div>
</div>
<div style="width: 100vw; height: 100vh; position: fixed; left: 0; top: 0; background-color: #cccccc" id="modal" class="hide">
<div id="modal-text" style="margin: 0; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 20px;">
</div>
</div>
</body>
</html>
```


--- File: lotteharper-main/misc/templates/misc/logo.html ---
```html
<!doctype HTML>
<html>
        <head>
                <script type="text/javascript" src="https://code.createjs.com/1.0.0/createjs.min.js"></script>
                <script
                  src="https://code.jquery.com/jquery-4.0.0.min.js"
                  integrity="sha256-OaVG6prZf4v69dPg6PhVattBXkcOWQB62pdZ3ORyrao="
                  crossorigin="anonymous"></script>
                <style>
                        @font-face { font-family: 'VendorSpecified'; src: url('/media/font/d8c91b9c-aa45-46d0-affc-2ebef6501287.ttf'); }
                </style>
        </head>
        <body>
                <canvas id="canvas" height="1500" width="1500"></canvas>
                <script>
                    const myFont = new FontFace('VendorSpecified', 'url(/media/font/d8c91b9c-aa45-46d0-affc-2ebef6501287.ttf)');
                    myFont.load().then(function(loaded_face) {
                        document.fonts.add(loaded_face);
                        console.log('Font loaded and ready for use in CreateJS');
                        $(document).ready(function() {
                                var stage = new createjs.Stage("canvas");
                                var colors = ['red','green','blue','yellow','purple','orange','brown','black'];
                                var median = 740;
                                var rectangle = new createjs.Shape();
                                rectangle.graphics.beginFill('#FFFFFF').drawRect(0,0,1500,1500);
                                rectangle.x = 0; // + Math.sin(ste>
                                rectangle.y = 0;
/*                                stage.addChild(rectangle);*/
                                function drawRectangles(step) {
                                        var rectangle = new createjs.Shape();
                                        rectangle.graphics.beginFill(colors[step]).drawRect(0, 0, 500, 500);
                                        rectangle.x = median; // + Math.sin(step*5)*200;
                                        rectangle.y = median; // + Math.sin(step*5)*200;
                                        rectangle.rotation = 45 * step;
                                        rectangle.alpha = 0.7;
                                        stage.addChild(rectangle);
                                        stage.update();
                                        step -= 1;
                                        if(step >= 0) drawRectangles(step);
                                }
                                drawRectangles(7);
                                var title = new createjs.Text("Lotte", "360px VendorSpecified", "#000000");
                                title.x = median-280;
                                title.y = median-330;
                                stage.addChild(title);
                                var title2 = new createjs.Text("Harper", "360px VendorSpecified", "#000000");
                                title2.x = median-400;
                                title2.y = median+50;
                                stage.addChild(title2);
                                stage.update();
                        });
                    }).catch(function(error) {
                        console.error('Font failed to load:', error);
                    });
                </script>
        </body>
</html>
```


--- File: lotteharper-main/misc/templates/misc/map.html ---
```html
{% extends 'base.html' %}
{% block head %}
<script src="https://maps.googleapis.com/maps/api/js?key={{ maps_api_key }}"></script>
{% endblock %}
{% block content %}
{% load app_filters %}
<legend>{{ 'Visitor IP Location'|etrans }}</legend>
<div id="map" style="z-index: 100; width: 100%; height: 85vh;"></div>
{% endblock %}
{% block javascript %}
const points = [
    {% for lat, lng in latlngs %}
    { lat: {{ lat }}, lng: {{ lng }} },
    {% endfor %}
];
function initMap() {
    const map = new google.maps.Map(document.getElementById('map'), {
        zoom: 4,
        center: points[0],
    });
    points.forEach((point) => {
        new google.maps.Marker({
            position: point,
            map: map,
        });
    });
}
window.onload = initMap;
{% endblock %}
```


--- File: lotteharper-main/misc/templates/misc/news.xml ---
```
{% load feed_filters %}<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
  {% for lang in languages %}
  {% for post in posts %}
  <url>
   <loc>{{ base_url }}/feed/post/{{ post.uuid }}/</loc>
   <news:news>
   <news:publication>
     <news:name>{{ the_site_name }}</news:name>
     <news:language>{{ lang }}</news:language>
   </news:publication>
   <news:publication_date>{{ post.date_posted|sitemapdate }}</news:publication_date>
   <news:title>{{ post.id|shorttitle|translang:lang }}</news:title>
   </news:news>
  </url>
  {% endfor %}
  {% endfor %}
</urlset>
```


--- File: lotteharper-main/misc/templates/misc/search.html ---
```html
{% extends 'base.html' %}
{% block head %}
{% if use_prism %}
<script type="text/javascript" src="/static/js/prism.js"></script>
<script type="text/javascript" src="/static/qrcode.min.js"></script>
<link rel="stylesheet" href="/static/css/prism.css">
{% endif %}
{% endblock %}
{% block content %}
{% load app_filters %}
<h1>{{ 'Search'|etrans }}</h1>
{% if request.GET.q %}
<p>{% blocktrans %}Your search, "{{ request.GET.q }}", returned {{ count|nts }} results.{% endblocktrans %}</p>
<a class="btn btn-sm btn-outline-info" title="Grid view" href="{{ request.path }}?grid=true&{% get_qs %}">Grid</a>
{% include 'language.html' %}
<hr style="background-color: red;">
{% for post in posts %}
{% include 'feed/_post.html' %}
{% endfor %}
{% include 'pagelinks.html' %}
{% include 'search.html' %}
{% include 'social.html' %}
{% include 'banner_ad.html' %}
{% else %}
<p>{{ 'Please enter a query in the navbar to begin your search.'|etrans }}</p>
{% include 'search.html' %}
{% endif %}
{% endblock %}
{% block javascript %}
{% if use_prism %}Prism.highlightAll();{% endif %}
{% include 'reader.js' %}
{% endblock %}
```


--- File: lotteharper-main/misc/templates/misc/serviceworker.js ---
```
var GHPATH = '/';
var APP_PREFIX = 'lotteh_';
var VERSION = 'version_08_' + new String(new Date.now());
var URLS = [
  `${GHPATH}/`,
  `${GHPATH}/index.html`,
  `${GHPATH}/static/main.js`,
  `${GHPATH}/static/qrcode.js`,
  `${GHPATH}/static/opencv.min.js`,
  `${GHPATH}/static/tesseract.min.js`,
  `${GHPATH}/static/handtrack.min.js`,
  `${GHPATH}/static/crypto-js.min.js`,
  `${GHPATH}/static/head.js`,
  `${GHPATH}/static/css/darkmode.css`,
  `${GHPATH}/static/css/prism.css`,
  `${GHPATH}/static/js/prism.js`,
  `${GHPATH}/static/js/createjs.min.js`,
  `${GHPATH}/static/js/django_jsignature.js`,
]
```


--- File: lotteharper-main/misc/templates/misc/sitemap.html ---
```html
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    {% for url in urls %}
    <loc>{{ base_url }}{{ url }}</loc>
    {% for lang in languages %}
    <xhtml:link rel="alternate" hreflang="{{ lang }}" href="{{ base_url }}{{ url }}" />
    {% endfor %}
    <lastmod>2022-06-04</lastmod>
    {% endfor %}
    {% for vendor in vendors %}
    {% for url in vendor_urls %}
    <loc>{{ base_url }}{{ url }}{{ vendor.profile.name }}/</loc>
    {% for lang in languages %}
    <xhtml:link rel="alternate" hreflang="{{ lang }}" href="{{ base_url }}{{ url }}{{ vendor.profile.name }}/" />
    {% endfor %}
    <lastmod>{{ date }}</lastmod>
    {% endfor %}
    {% endfor %}
  </url>
</urlset>
```


--- File: lotteharper-main/misc/templates/misc/sitemap.xml ---
```
{% load feed_filters %}<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
  {% for url in urls %}
  <url>
    <loc>{{ base_url }}{{ url }}</loc>
    {% for lang in languages %}
    <xhtml:link rel="alternate" hreflang="{{ lang }}" href="{{ base_url }}{{ url }}" />
    {% endfor %}
    <lastmod>{{ date|sitemapdate }}</lastmod>
  </url>
  {% endfor %}
{% for vendor in vendors %}
  {% for feed in vendor_feeds %}
  <url>
    <loc>{{ base_url }}/feed/profile/{{ vendor.profile.name }}/?feed={{ feed }}</loc>
    {% for lang in languages %}
    <xhtml:link rel="alternate" hreflang="{{ lang }}" href="{{ base_url }}/feed/profile/{{ vendor.profile.name }}/?feed={{ feed }}" />
    {% endfor %}
    <lastmod>{{ vendor.profile.date_joined|sitemapdate }}</lastmod>
  </url>
  {% endfor %}
  {% for url in vendor_urls %}
  <url>
    <loc>{{ base_url }}{{ url }}{{ vendor.profile.name }}{% if not url == '/@' %}/{% endif %}</loc>
    {% for lang in languages %}
    <xhtml:link rel="alternate" hreflang="{{ lang }}" href="{{ base_url }}{{ url }}{{ vendor.profile.name }}{% if not url == '/@' %}/{% endif %}" />
    {% endfor %}
    <lastmod>{{ vendor.profile.date_joined|sitemapdate }}</lastmod>
  </url>
  {% endfor %}
{% endfor %}
{% for vendor in surrogates %}
  {% for url in surrogate_urls %}
  <url>
    <loc>{{ base_url }}{{ url }}{{ vendor.profile.name }}/</loc>
    {% for lang in languages %}
    <xhtml:link rel="alternate" hreflang="{{ lang }}" href="{{ base_url }}{{ url }}{{ vendor.profile.name }}/" />
    {% endfor %}
    <lastmod>{{ vendor.profile.date_joined|sitemapdate }}</lastmod>
  </url>
  {% endfor %}
{% endfor %}
  {% for post in posts %}
  <url>
    <loc>{{ base_url }}/feed/post/{{ post.uuid }}/</loc>
    {% for lang in languages %}
    <xhtml:link rel="alternate" hreflang="{{ lang }}" href="{{ base_url }}{{ post.get_absolute_url }}/" />
    {% endfor %}
    <lastmod>{{ post.date_posted|sitemapdate }}</lastmod>
  </url>
  {% endfor %}
</urlset>
```


--- File: lotteharper-main/misc/templates/misc/site.webmanifest ---
```
{
    "name": "{{ the_site_name }}",
    "short_name": "{{ the_site_name }}",
    "description": "{{ base_description }}",
    "scope": "/",
    "start_url": "/",
    "icons": [
        {
            "src": "/media/static/android-chrome-192x192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/media/static/android-chrome-256x256.png",
            "sizes": "256x256",
            "type": "image/png"
        }
    ],
    "theme_color": "#c93443",
    "background_color": "#b31717",
    "display": "standalone"
}
```


--- File: lotteharper-main/misc/templates/misc/tac.html ---
```html
{% extends 'base.html' %}
{% block content %}
<h1>TERMS AND CONDITIONS</h1>
<div style="white-space: pre-wrap;">
Last updated April 30, 2022

TABLE OF CONTENTS

1. AGREEMENT TO TERMS
2. INTELLECTUAL PROPERTY RIGHTS
3. USER REPRESENTATIONS
4. USER REGISTRATION
5. PROHIBITED ACTIVITIES
6. USER GENERATED CONTRIBUTIONS
7. CONTRIBUTION LICENSE
8. SUBMISSIONS
9. THIRD-PARTY WEBSITE AND CONTENT
10. SITE MANAGEMENT
11. PRIVACY POLICY
12. DIGITAL MILLENNIUM COPYRIGHT ACT (DMCA) NOTICE AND POLICY
13. TERM AND TERMINATION
14. MODIFICATIONS AND INTERRUPTIONS
15. GOVERNING LAW
16. DISPUTE RESOLUTION
17. CORRECTIONS
18. DISCLAIMER
19. LIMITATIONS OF LIABILITY
20. INDEMNIFICATION
21. USER DATA
22. ELECTRONIC COMMUNICATIONS, TRANSACTIONS, AND SIGNATURES
23. CALIFORNIA USERS AND RESIDENTS
24. MISCELLANEOUS
25. CONTACT US


1. AGREEMENT TO TERMS

These Terms of Use constitute a legally binding agreement made between you, whether personally or on behalf of an entity ("you") and {{ company_name }} (UBI {{ the_ubi }}), doing business as {{ the_site_name }} ("Company," "we," "us," or "our"), concerning your access to and use of the {{ domain_name }} website as well as any other media form, media channel, mobile website or mobile application related, linked, or otherwise connected thereto (collectively, the "Site"). We are registered in Washington, United States and have our registered office at 7112 8th Ave NE, Seattle, WA 98115. You agree that by accessing the Site, you have read, understood, and agreed to be bound by all of these Terms of Use. IF YOU DO NOT AGREE WITH ALL OF THESE TERMS OF USE, THEN YOU ARE EXPRESSLY PROHIBITED FROM USING THE SITE AND YOU MUST DISCONTINUE USE IMMEDIATELY.

Supplemental terms and conditions or documents that may be posted on the Site from time to time are hereby expressly incorporated herein by reference. We reserve the right, in our sole discretion, to make changes or modifications to these Terms of Use at any time and for any reason. We will alert you about any changes by updating the "Last updated" date of these Terms of Use, and you waive any right to receive specific notice of each such change. Please ensure that you check the applicable Terms every time you use our Site so that you understand which Terms apply. You will be subject to, and will be deemed to have been made aware of and to have accepted, the changes in any revised Terms of Use by your continued use of the Site after the date such revised Terms of Use are posted.

The information provided on the Site is not intended for distribution to or use by any person or entity in any jurisdiction or country where such distribution or use would be contrary to law or regulation or which would subject us to any registration requirement within such jurisdiction or country. Accordingly, those persons who choose to access the Site from other locations do so on their own initiative and are solely responsible for compliance with local laws, if and to the extent local laws are applicable.

The Site is not tailored to comply with industry-specific regulations (Health Insurance Portability and Accountability Act (HIPAA), Federal Information Security Management Act (FISMA), etc.), so if your interactions would be subjected to such laws, you may not use this Site. You may not use the Site in a way that would violate the Gramm-Leach-Bliley Act (GLBA).

The Site is intended for users who are at least {{ min_age }} years old. Persons under the age of {{ min_age }} are not permitted to use or register for the Site.


2. INTELLECTUAL PROPERTY RIGHTS

Unless otherwise indicated, the Site is our proprietary property and all source code, databases, functionality, software, website designs, audio, video, text, photographs, and graphics on the Site (collectively, the "Content") and the trademarks, service marks, and logos contained therein (the "Marks") are owned or controlled by us or licensed to us, and are protected by copyright and trademark laws and various other intellectual property rights and unfair competition laws of the United States, international copyright laws, and international conventions. The Content and the Marks are provided on the Site "AS IS" for your information and personal use only. Except as expressly provided in these Terms of Use, no part of the Site and no Content or Marks may be copied, reproduced, aggregated, republished, uploaded, posted, publicly displayed, encoded, translated, transmitted, distributed, sold, licensed, or otherwise exploited for any commercial purpose whatsoever, without our express prior written permission.

Provided that you are eligible to use the Site, you are granted a limited license to access and use the Site and to download or print a copy of any portion of the Content to which you have properly gained access solely for your personal, non-commercial use. We reserve all rights not expressly granted to you in and to the Site, the Content and the Marks.


3. USER REPRESENTATIONS

By using the Site, you represent and warrant that: (1) all registration information you submit will be true, accurate, current, and complete; (2) you will maintain the accuracy of such information and promptly update such registration information as necessary; (3) you have the legal capacity and you agree to comply with these Terms of Use; (4) you are not a minor in the jurisdiction in which you reside; (5) you will not access the Site through automated or non-human means, whether through a bot, script, or otherwise; (6) you will not use the Site for any illegal or unauthorized purpose; and (7) your use of the Site will not violate any applicable law or regulation.

If you provide any information that is untrue, inaccurate, not current, or incomplete, we have the right to suspend or terminate your account and refuse any and all current or future use of the Site (or any portion thereof).


4. USER REGISTRATION

You may be required to register with the Site. You agree to keep your password confidential and will be responsible for all use of your account and password. We reserve the right to remove, reclaim, or change a username you select if we determine, in our sole discretion, that such username is inappropriate, obscene, or otherwise objectionable.


5. PROHIBITED ACTIVITIES

You may not access or use the Site for any purpose other than that for which we make the Site available. The Site may not be used in connection with any commercial endeavors except those that are specifically endorsed or approved by us.

As a user of the Site, you agree not to:
Systematically retrieve data or other content from the Site to create or compile, directly or indirectly, a collection, compilation, database, or directory without written permission from us.
Trick, defraud, or mislead us and other users, especially in any attempt to learn sensitive account information such as user passwords.
Circumvent, disable, or otherwise interfere with security-related features of the Site, including features that prevent or restrict the use or copying of any Content or enforce limitations on the use of the Site and/or the Content contained therein.
Disparage, tarnish, or otherwise harm, in our opinion, us and/or the Site.
Use any information obtained from the Site in order to harass, abuse, or harm another person.
Make improper use of our support services or submit false reports of abuse or misconduct.
Use the Site in a manner inconsistent with any applicable laws or regulations.
Engage in unauthorized framing of or linking to the Site.
Upload or transmit (or attempt to upload or to transmit) viruses, Trojan horses, or other material, including excessive use of capital letters and spamming (continuous posting of repetitive text), that interferes with any party"™s uninterrupted use and enjoyment of the Site or modifies, impairs, disrupts, alters, or interferes with the use, features, functions, operation, or maintenance of the Site.
Engage in any automated use of the system, such as using scripts to send comments or messages, or using any data mining, robots, or similar data gathering and extraction tools.
Delete the copyright or other proprietary rights notice from any Content.
Attempt to impersonate another user or person or use the username of another user.
Upload or transmit (or attempt to upload or to transmit) any material that acts as a passive or active information collection or transmission mechanism, including without limitation, clear graphics interchange formats ("gifs"), 1—1 pixels, web bugs, cookies, or other similar devices (sometimes referred to as "spyware" or "passive collection mechanisms" or "pcms").
Interfere with, disrupt, or create an undue burden on the Site or the networks or services connected to the Site.
Harass, annoy, intimidate, or threaten any of our employees or agents engaged in providing any portion of the Site to you.
Attempt to bypass any measures of the Site designed to prevent or restrict access to the Site, or any portion of the Site.
Copy or adapt the Site"™s software, including but not limited to Flash, PHP, HTML, JavaScript, or other code.
Except as permitted by applicable law, decipher, decompile, disassemble, or reverse engineer any of the software comprising or in any way making up a part of the Site.
Except as may be the result of standard search engine or Internet browser usage, use, launch, develop, or distribute any automated system, including without limitation, any spider, robot, cheat utility, scraper, or offline reader that accesses the Site, or using or launching any unauthorized script or other software.
Use a buying agent or purchasing agent to make purchases on the Site.
Make any unauthorized use of the Site, including collecting usernames and/or email addresses of users by electronic or other means for the purpose of sending unsolicited email, or creating user accounts by automated means or under false pretenses.
Use the Site as part of any effort to compete with us or otherwise use the Site and/or the Content for any revenue-generating endeavor or commercial enterprise.


6. USER GENERATED CONTRIBUTIONS

The Site may invite you to chat, contribute to, or participate in blogs, message boards, online forums, and other functionality, and may provide you with the opportunity to create, submit, post, display, transmit, perform, publish, distribute, or broadcast content and materials to us or on the Site, including but not limited to text, writings, video, audio, photographs, graphics, comments, suggestions, or personal information or other material (collectively, "Contributions"). Contributions may be viewable by other users of the Site and through third-party websites. As such, any Contributions you transmit may be treated as non-confidential and non-proprietary. When you create or make available any Contributions, you thereby represent and warrant that:
The creation, distribution, transmission, public display, or performance, and the accessing, downloading, or copying of your Contributions do not and will not infringe the proprietary rights, including but not limited to the copyright, patent, trademark, trade secret, or moral rights of any third party.
You are the creator and owner of or have the necessary licenses, rights, consents, releases, and permissions to use and to authorize us, the Site, and other users of the Site to use your Contributions in any manner contemplated by the Site and these Terms of Use.
You have the written consent, release, and/or permission of each and every identifiable individual person in your Contributions to use the name or likeness of each and every such identifiable individual person to enable inclusion and use of your Contributions in any manner contemplated by the Site and these Terms of Use.
Your Contributions are not false, inaccurate, or misleading.
Your Contributions are not unsolicited or unauthorized advertising, promotional materials, pyramid schemes, chain letters, spam, mass mailings, or other forms of solicitation.
Your Contributions are not obscene, lewd, lascivious, filthy, violent, harassing, libelous, slanderous, or otherwise objectionable (as determined by us).
Your Contributions do not ridicule, mock, disparage, intimidate, or abuse anyone.
Your Contributions are not used to harass or threaten (in the legal sense of those terms) any other person and to promote violence against a specific person or class of people.
Your Contributions do not violate any applicable law, regulation, or rule.
Your Contributions do not violate the privacy or publicity rights of any third party.
Your Contributions do not violate any applicable law concerning child pornography, or otherwise intended to protect the health or well-being of minors.
Your Contributions do not include any offensive comments that are connected to race, national origin, gender, sexual preference, or physical handicap.
Your Contributions do not otherwise violate, or link to material that violates, any provision of these Terms of Use, or any applicable law or regulation.
Any use of the Site in violation of the foregoing violates these Terms of Use and may result in, among other things, termination or suspension of your rights to use the Site.


7. CONTRIBUTION LICENSE

By posting your Contributions to any part of the Site, you automatically grant, and you represent and warrant that you have the right to grant, to us an unrestricted, unlimited, irrevocable, perpetual, non-exclusive, transferable, royalty-free, fully-paid, worldwide right, and license to host, use, copy, reproduce, disclose, sell, resell, publish, broadcast, retitle, archive, store, cache, publicly perform, publicly display, reformat, translate, transmit, excerpt (in whole or in part), and distribute such Contributions (including, without limitation, your image and voice) for any purpose, commercial, advertising, or otherwise, and to prepare derivative works of, or incorporate into other works, such Contributions, and grant and authorize sublicenses of the foregoing. The use and distribution may occur in any media formats and through any media channels.

This license will apply to any form, media, or technology now known or hereafter developed, and includes our use of your name, company name, and franchise name, as applicable, and any of the trademarks, service marks, trade names, logos, and personal and commercial images you provide. You waive all moral rights in your Contributions, and you warrant that moral rights have not otherwise been asserted in your Contributions.

We do not assert any ownership over your Contributions. You retain full ownership of all of your Contributions and any intellectual property rights or other proprietary rights associated with your Contributions. We are not liable for any statements or representations in your Contributions provided by you in any area on the Site. You are solely responsible for your Contributions to the Site and you expressly agree to exonerate us from any and all responsibility and to refrain from any legal action against us regarding your Contributions.

We have the right, in our sole and absolute discretion, (1) to edit, redact, or otherwise change any Contributions; (2) to re-categorize any Contributions to place them in more appropriate locations on the Site; and (3) to pre-screen or delete any Contributions at any time and for any reason, without notice. We have no obligation to monitor your Contributions.


8. SUBMISSIONS

You acknowledge and agree that any questions, comments, suggestions, ideas, feedback, or other information regarding the Site ("Submissions") provided by you to us are non-confidential and shall become our sole property. We shall own exclusive rights, including all intellectual property rights, and shall be entitled to the unrestricted use and dissemination of these Submissions for any lawful purpose, commercial or otherwise, without acknowledgment or compensation to you. You hereby waive all moral rights to any such Submissions, and you hereby warrant that any such Submissions are original with you or that you have the right to submit such Submissions. You agree there shall be no recourse against us for any alleged or actual infringement or misappropriation of any proprietary right in your Submissions.


9. THIRD-PARTY WEBSITE AND CONTENT

The Site may contain (or you may be sent via the Site) links to other websites ("Third-Party Websites") as well as articles, photographs, text, graphics, pictures, designs, music, sound, video, information, applications, software, and other content or items belonging to or originating from third parties ("Third-Party Content"). Such Third-Party Websites and Third-Party Content are not investigated, monitored, or checked for accuracy, appropriateness, or completeness by us, and we are not responsible for any Third-Party Websites accessed through the Site or any Third-Party Content posted on, available through, or installed from the Site, including the content, accuracy, offensiveness, opinions, reliability, privacy practices, or other policies of or contained in the Third-Party Websites or the Third-Party Content. Inclusion of, linking to, or permitting the use or installation of any Third-Party Websites or any Third-Party Content does not imply approval or endorsement thereof by us. If you decide to leave the Site and access the Third-Party Websites or to use or install any Third-Party Content, you do so at your own risk, and you should be aware these Terms of Use no longer govern. You should review the applicable terms and policies, including privacy and data gathering practices, of any website to which you navigate from the Site or relating to any applications you use or install from the Site. Any purchases you make through Third-Party Websites will be through other websites and from other companies, and we take no responsibility whatsoever in relation to such purchases which are exclusively between you and the applicable third party. You agree and acknowledge that we do not endorse the products or services offered on Third-Party Websites and you shall hold us harmless from any harm caused by your purchase of such products or services. Additionally, you shall hold us harmless from any losses sustained by you or harm caused to you relating to or resulting in any way from any Third-Party Content or any contact with Third-Party Websites.


10. SITE MANAGEMENT

We reserve the right, but not the obligation, to: (1) monitor the Site for violations of these Terms of Use; (2) take appropriate legal action against anyone who, in our sole discretion, violates the law or these Terms of Use, including without limitation, reporting such user to law enforcement authorities; (3) in our sole discretion and without limitation, refuse, restrict access to, limit the availability of, or disable (to the extent technologically feasible) any of your Contributions or any portion thereof; (4) in our sole discretion and without limitation, notice, or liability, to remove from the Site or otherwise disable all files and content that are excessive in size or are in any way burdensome to our systems; and (5) otherwise manage the Site in a manner designed to protect our rights and property and to facilitate the proper functioning of the Site.


11. PRIVACY POLICY

We care about data privacy and security. By using the Site, you agree to be bound by our Privacy Policy posted on the Site, which is incorporated into these Terms of Use. Please be advised the Site is hosted in the United States. If you access the Site from any other region of the world with laws or other requirements governing personal data collection, use, or disclosure that differ from applicable laws in the United States, then through your continued use of the Site, you are transferring your data to the United States, and you agree to have your data transferred to and processed in the United States.


12. DIGITAL MILLENNIUM COPYRIGHT ACT (DMCA) NOTICE AND POLICY

Notifications

We respect the intellectual property rights of others. If you believe that any material available on or through the Site infringes upon any copyright you own or control, please immediately notify our Designated Copyright Agent using the contact information provided below (a "Notification"). A copy of your Notification will be sent to the person who posted or stored the material addressed in the Notification. Please be advised that pursuant to federal law you may be held liable for damages if you make material misrepresentations in a Notification. Thus, if you are not sure that material located on or linked to by the Site infringes your copyright, you should consider first contacting an attorney.

All Notifications should meet the requirements of DMCA 17 U.S.C. § 512(c)(3) and include the following information: (1) A physical or electronic signature of a person authorized to act on behalf of the owner of an exclusive right that is allegedly infringed; (2) identification of the copyrighted work claimed to have been infringed, or, if multiple copyrighted works on the Site are covered by the Notification, a representative list of such works on the Site; (3) identification of the material that is claimed to be infringing or to be the subject of infringing activity and that is to be removed or access to which is to be disabled, and information reasonably sufficient to permit us to locate the material; (4) information reasonably sufficient to permit us to contact the complaining party, such as an address, telephone number, and, if available, an email address at which the complaining party may be contacted; (5) a statement that the complaining party has a good faith belief that use of the material in the manner complained of is not authorized by the copyright owner, its agent, or the law; and (6) a statement that the information in the notification is accurate, and under penalty of perjury, that the complaining party is authorized to act on behalf of the owner of an exclusive right that is allegedly infringed upon.

Counter Notification

If you believe your own copyrighted material has been removed from the Site as a result of a mistake or misidentification, you may submit a written counter notification to our Designated Copyright Agent using the contact information provided below (a "Counter Notification"). To be an effective Counter Notification under the DMCA, your Counter Notification must include substantially the following: (1) identification of the material that has been removed or disabled and the location at which the material appeared before it was removed or disabled; (2) a statement that you consent to the jurisdiction of the Federal District Court in which your address is located, or if your address is outside the United States, for any judicial district in which we are located; (3) a statement that you will accept service of process from the party that filed the Notification or the party's agent; (4) your name, address, and telephone number; (5) a statement under penalty of perjury that you have a good faith belief that the material in question was removed or disabled as a result of a mistake or misidentification of the material to be removed or disabled; and (6) your physical or electronic signature.

If you send us a valid, written Counter Notification meeting the requirements described above, we will restore your removed or disabled material, unless we first receive notice from the party filing the Notification informing us that such party has filed a court action to restrain you from engaging in infringing activity related to the material in question. Please note that if you materially misrepresent that the disabled or removed content was removed by mistake or misidentification, you may be liable for damages, including costs and attorney's fees. Filing a false Counter Notification constitutes perjury.

Designated Copyright Agent
Jasper Holton
Attn: Copyright Agent
7112 8th Ave NE
Seattle, WA 98115
United States
team@clemn.com
+1 (970) 585-7901


13. TERM AND TERMINATION

These Terms of Use shall remain in full force and effect while you use the Site. WITHOUT LIMITING ANY OTHER PROVISION OF THESE TERMS OF USE, WE RESERVE THE RIGHT TO, IN OUR SOLE DISCRETION AND WITHOUT NOTICE OR LIABILITY, DENY ACCESS TO AND USE OF THE SITE (INCLUDING BLOCKING CERTAIN IP ADDRESSES), TO ANY PERSON FOR ANY REASON OR FOR NO REASON, INCLUDING WITHOUT LIMITATION FOR BREACH OF ANY REPRESENTATION, WARRANTY, OR COVENANT CONTAINED IN THESE TERMS OF USE OR OF ANY APPLICABLE LAW OR REGULATION. WE MAY TERMINATE YOUR USE OR PARTICIPATION IN THE SITE OR DELETE YOUR ACCOUNT AND ANY CONTENT OR INFORMATION THAT YOU POSTED AT ANY TIME, WITHOUT WARNING, IN OUR SOLE DISCRETION.

If we terminate or suspend your account for any reason, you are prohibited from registering and creating a new account under your name, a fake or borrowed name, or the name of any third party, even if you may be acting on behalf of the third party. In addition to terminating or suspending your account, we reserve the right to take appropriate legal action, including without limitation pursuing civil, criminal, and injunctive redress.


14. MODIFICATIONS AND INTERRUPTIONS

We reserve the right to change, modify, or remove the contents of the Site at any time or for any reason at our sole discretion without notice. However, we have no obligation to update any information on our Site. We also reserve the right to modify or discontinue all or part of the Site without notice at any time. We will not be liable to you or any third party for any modification, price change, suspension, or discontinuance of the Site.

We cannot guarantee the Site will be available at all times. We may experience hardware, software, or other problems or need to perform maintenance related to the Site, resulting in interruptions, delays, or errors. We reserve the right to change, revise, update, suspend, discontinue, or otherwise modify the Site at any time or for any reason without notice to you. You agree that we have no liability whatsoever for any loss, damage, or inconvenience caused by your inability to access or use the Site during any downtime or discontinuance of the Site. Nothing in these Terms of Use will be construed to obligate us to maintain and support the Site or to supply any corrections, updates, or releases in connection therewith.


15. GOVERNING LAW

These Terms of Use and your use of the Site are governed by and construed in accordance with the laws of the State of Washington applicable to agreements made and to be entirely performed within the State of Washington, without regard to its conflict of law principles.


16. DISPUTE RESOLUTION

Any legal action of whatever nature brought by either you or us (collectively, the "Parties" and individually, a "Party") shall be commenced or prosecuted in the state and federal courts located in King, Washington, and the Parties hereby consent to, and waive all defenses of lack of personal jurisdiction and forum non conveniens with respect to venue and jurisdiction in such state and federal courts. Application of the United Nations Convention on Contracts for the International Sale of Goods and the Uniform Computer Information Transaction Act (UCITA) are excluded from these Terms of Use. In no event shall any claim, action, or proceeding brought by either Party related in any way to the Site be commenced more than twenty (20) years after the cause of action arose.


17. CORRECTIONS

There may be information on the Site that contains typographical errors, inaccuracies, or omissions, including descriptions, pricing, availability, and various other information. We reserve the right to correct any errors, inaccuracies, or omissions and to change or update the information on the Site at any time, without prior notice.


18. DISCLAIMER

THE SITE IS PROVIDED ON AN AS-IS AND AS-AVAILABLE BASIS. YOU AGREE THAT YOUR USE OF THE SITE AND OUR SERVICES WILL BE AT YOUR SOLE RISK. TO THE FULLEST EXTENT PERMITTED BY LAW, WE DISCLAIM ALL WARRANTIES, EXPRESS OR IMPLIED, IN CONNECTION WITH THE SITE AND YOUR USE THEREOF, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. WE MAKE NO WARRANTIES OR REPRESENTATIONS ABOUT THE ACCURACY OR COMPLETENESS OF THE SITE"™S CONTENT OR THE CONTENT OF ANY WEBSITES LINKED TO THE SITE AND WE WILL ASSUME NO LIABILITY OR RESPONSIBILITY FOR ANY (1) ERRORS, MISTAKES, OR INACCURACIES OF CONTENT AND MATERIALS, (2) PERSONAL INJURY OR PROPERTY DAMAGE, OF ANY NATURE WHATSOEVER, RESULTING FROM YOUR ACCESS TO AND USE OF THE SITE, (3) ANY UNAUTHORIZED ACCESS TO OR USE OF OUR SECURE SERVERS AND/OR ANY AND ALL PERSONAL INFORMATION AND/OR FINANCIAL INFORMATION STORED THEREIN, (4) ANY INTERRUPTION OR CESSATION OF TRANSMISSION TO OR FROM THE SITE, (5) ANY BUGS, VIRUSES, TROJAN HORSES, OR THE LIKE WHICH MAY BE TRANSMITTED TO OR THROUGH THE SITE BY ANY THIRD PARTY, AND/OR (6) ANY ERRORS OR OMISSIONS IN ANY CONTENT AND MATERIALS OR FOR ANY LOSS OR DAMAGE OF ANY KIND INCURRED AS A RESULT OF THE USE OF ANY CONTENT POSTED, TRANSMITTED, OR OTHERWISE MADE AVAILABLE VIA THE SITE. WE DO NOT WARRANT, ENDORSE, GUARANTEE, OR ASSUME RESPONSIBILITY FOR ANY PRODUCT OR SERVICE ADVERTISED OR OFFERED BY A THIRD PARTY THROUGH THE SITE, ANY HYPERLINKED WEBSITE, OR ANY WEBSITE OR MOBILE APPLICATION FEATURED IN ANY BANNER OR OTHER ADVERTISING, AND WE WILL NOT BE A PARTY TO OR IN ANY WAY BE RESPONSIBLE FOR MONITORING ANY TRANSACTION BETWEEN YOU AND ANY THIRD-PARTY PROVIDERS OF PRODUCTS OR SERVICES. AS WITH THE PURCHASE OF A PRODUCT OR SERVICE THROUGH ANY MEDIUM OR IN ANY ENVIRONMENT, YOU SHOULD USE YOUR BEST JUDGMENT AND EXERCISE CAUTION WHERE APPROPRIATE.


19. LIMITATIONS OF LIABILITY

IN NO EVENT WILL WE OR OUR DIRECTORS, EMPLOYEES, OR AGENTS BE LIABLE TO YOU OR ANY THIRD PARTY FOR ANY DIRECT, INDIRECT, CONSEQUENTIAL, EXEMPLARY, INCIDENTAL, SPECIAL, OR PUNITIVE DAMAGES, INCLUDING LOST PROFIT, LOST REVENUE, LOSS OF DATA, OR OTHER DAMAGES ARISING FROM YOUR USE OF THE SITE, EVEN IF WE HAVE BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. NOTWITHSTANDING ANYTHING TO THE CONTRARY CONTAINED HEREIN, OUR LIABILITY TO YOU FOR ANY CAUSE WHATSOEVER AND REGARDLESS OF THE FORM OF THE ACTION, WILL AT ALL TIMES BE LIMITED TO THE AMOUNT PAID, IF ANY, BY YOU TO US DURING THE SIX (6) MONTH PERIOD PRIOR TO ANY CAUSE OF ACTION ARISING. CERTAIN US STATE LAWS AND INTERNATIONAL LAWS DO NOT ALLOW LIMITATIONS ON IMPLIED WARRANTIES OR THE EXCLUSION OR LIMITATION OF CERTAIN DAMAGES. IF THESE LAWS APPLY TO YOU, SOME OR ALL OF THE ABOVE DISCLAIMERS OR LIMITATIONS MAY NOT APPLY TO YOU, AND YOU MAY HAVE ADDITIONAL RIGHTS.


20. INDEMNIFICATION

You agree to defend, indemnify, and hold us harmless, including our subsidiaries, affiliates, and all of our respective officers, agents, partners, and employees, from and against any loss, damage, liability, claim, or demand, including reasonable attorneys"™ fees and expenses, made by any third party due to or arising out of: (1) your Contributions; (2) use of the Site; (3) breach of these Terms of Use; (4) any breach of your representations and warranties set forth in these Terms of Use; (5) your violation of the rights of a third party, including but not limited to intellectual property rights; or (6) any overt harmful act toward any other user of the Site with whom you connected via the Site. Notwithstanding the foregoing, we reserve the right, at your expense, to assume the exclusive defense and control of any matter for which you are required to indemnify us, and you agree to cooperate, at your expense, with our defense of such claims. We will use reasonable efforts to notify you of any such claim, action, or proceeding which is subject to this indemnification upon becoming aware of it.


21. USER DATA

We will maintain certain data that you transmit to the Site for the purpose of managing the performance of the Site, as well as data relating to your use of the Site. Although we perform regular routine backups of data, you are solely responsible for all data that you transmit or that relates to any activity you have undertaken using the Site. You agree that we shall have no liability to you for any loss or corruption of any such data, and you hereby waive any right of action against us arising from any such loss or corruption of such data.


22. ELECTRONIC COMMUNICATIONS, TRANSACTIONS, AND SIGNATURES

Visiting the Site, sending us emails, and completing online forms constitute electronic communications. You consent to receive electronic communications, and you agree that all agreements, notices, disclosures, and other communications we provide to you electronically, via email and on the Site, satisfy any legal requirement that such communication be in writing. YOU HEREBY AGREE TO THE USE OF ELECTRONIC SIGNATURES, CONTRACTS, ORDERS, AND OTHER RECORDS, AND TO ELECTRONIC DELIVERY OF NOTICES, POLICIES, AND RECORDS OF TRANSACTIONS INITIATED OR COMPLETED BY US OR VIA THE SITE. You hereby waive any rights or requirements under any statutes, regulations, rules, ordinances, or other laws in any jurisdiction which require an original signature or delivery or retention of non-electronic records, or to payments or the granting of credits by any means other than electronic means.


23. CALIFORNIA USERS AND RESIDENTS

If any complaint with us is not satisfactorily resolved, you can contact the Complaint Assistance Unit of the Division of Consumer Services of the California Department of Consumer Affairs in writing at 1625 North Market Blvd., Suite N 112, Sacramento, California 95834 or by telephone at (800) 952-5210 or (916) 445-1254.


24. MISCELLANEOUS

These Terms of Use and any policies or operating rules posted by us on the Site or in respect to the Site constitute the entire agreement and understanding between you and us. Our failure to exercise or enforce any right or provision of these Terms of Use shall not operate as a waiver of such right or provision. These Terms of Use operate to the fullest extent permissible by law. We may assign any or all of our rights and obligations to others at any time. We shall not be responsible or liable for any loss, damage, delay, or failure to act caused by any cause beyond our reasonable control. If any provision or part of a provision of these Terms of Use is determined to be unlawful, void, or unenforceable, that provision or part of the provision is deemed severable from these Terms of Use and does not affect the validity and enforceability of any remaining provisions. There is no joint venture, partnership, employment or agency relationship created between you and us as a result of these Terms of Use or use of the Site. You agree that these Terms of Use will not be construed against us by virtue of having drafted them. You hereby waive any and all defenses you may have based on the electronic form of these Terms of Use and the lack of signing by the parties hereto to execute these Terms of Use.


25. CONTACT US

In order to resolve a complaint regarding the Site or to receive further information regarding use of the Site, please contact us at:


Clemn
ATTN: Jasper Holton
7112 8th Ave NE
Seattle, WA 98115
United States
Phone: +1 (970) 585-7901
team@clemn.com
</div>
{% endblock %}
```


--- File: lotteharper-main/misc/templates/misc/terms.html ---
```html
{% extends 'base.html' %}
{% block content %}
{% load app_filters %}
<h1>{{ 'TERMS AND CONDITIONS'|etrans }}</h1>
{% blocktrans en %}
<div style="white-space: pre-wrap;">
Last updated November 25, 2025

TABLE OF CONTENTS

1. AGREEMENT TO TERMS
2. INTELLECTUAL PROPERTY RIGHTS
3. USER REPRESENTATIONS
4. USER REGISTRATION
5. PROHIBITED ACTIVITIES
6. USER GENERATED CONTRIBUTIONS
7. CONTRIBUTION LICENSE
8. SUBMISSIONS
9. THIRD-PARTY WEBSITE AND CONTENT
10. SITE MANAGEMENT
11. PRIVACY POLICY
12. DIGITAL MILLENNIUM COPYRIGHT ACT (DMCA) NOTICE AND POLICY
13. TERM AND TERMINATION
14. MODIFICATIONS AND INTERRUPTIONS
15. GOVERNING LAW
16. DISPUTE RESOLUTION
17. CORRECTIONS
18. DISCLAIMER
19. LIMITATIONS OF LIABILITY
20. INDEMNIFICATION
21. USER DATA
22. ELECTRONIC COMMUNICATIONS, TRANSACTIONS, AND SIGNATURES
23. CALIFORNIA USERS AND RESIDENTS
24. MISCELLANEOUS
25. RETURN AND REFUND POLICY
26. CONTACT US


1. AGREEMENT TO TERMS

These Terms of Use constitute a legally binding agreement made between you, whether personally or on behalf of an entity ("you") and {{ company_name }} (UBI {{ the_ubi }}) doing business as {{ the_site_name }} ("Company," "we," "us," or "our"), concerning your access to and use of the {{ domain_name }} website as well as any other media form, media channel, mobile website or mobile application related, linked, or otherwise connected thereto (collectively, the "Site"). We are registered in Washington, United States and have our registered office at {{ address }}. You agree that by accessing the Site, you have read, understood, and agreed to be bound by all of these Terms of Use. IF YOU DO NOT AGREE WITH ALL OF THESE TERMS OF USE, THEN YOU ARE EXPRESSLY PROHIBITED FROM USING THE SITE AND YOU MUST DISCONTINUE USE IMMEDIATELY.

Supplemental terms and conditions or documents that may be posted on the Site from time to time are hereby expressly incorporated herein by reference. We reserve the right, in our sole discretion, to make changes or modifications to these Terms of Use at any time and for any reason. We will alert you about any changes by updating the "Last updated" date of these Terms of Use, and you waive any right to receive specific notice of each such change. Please ensure that you check the applicable Terms every time you use our Site so that you understand which Terms apply. You will be subject to, and will be deemed to have been made aware of and to have accepted, the changes in any revised Terms of Use by your continued use of the Site after the date such revised Terms of Use are posted. Additional Terms of Use apply to certain features including the <a href="{% url 'payments:surrogacy' profileusername %}" title="Surrogacy agreement terms">Surrogacy Agreement</a>, and the <a href="https://www.djangoproject.com/conduct/" title="Django Code of Conduct">Django Code of Conduct</a> apply here, as well as all applicable juristictional, national and international law.

The information provided on the Site is not intended for distribution to or use by any person or entity in any jurisdiction or country where such distribution or use would be contrary to law or regulation or which would subject us to any registration requirement within such jurisdiction or country. Accordingly, those persons who choose to access the Site from other locations do so on their own initiative and are solely responsible for compliance with local laws, if and to the extent local laws are applicable.

The Site is not tailored to comply with industry-specific regulations (Health Insurance Portability and Accountability Act (HIPAA), Federal Information Security Management Act (FISMA), etc.), so if your interactions would be subjected to such laws, you may not use this Site. You may not use the Site in a way that would violate the Gramm-Leach-Bliley Act (GLBA).

The Site is intended for users who are at least {{ min_age }} years old. Persons under the age of {{ min_age }} are not permitted to use or register for the Site.


2. INTELLECTUAL PROPERTY RIGHTS

Unless otherwise indicated, the Site is our proprietary property and all source code, databases, functionality, software, website designs, audio, video, text, photographs, and graphics on the Site (collectively, the "Content") and the trademarks, service marks, and logos contained therein (the "Marks") are owned or controlled by us or licensed to us, and are protected by copyright and trademark laws and various other intellectual property rights and unfair competition laws of the United States, international copyright laws, and international conventions. The Content and the Marks are provided on the Site "AS IS" for your information and personal use only. Except as expressly provided in these Terms of Use, no part of the Site and no Content or Marks may be copied, reproduced, aggregated, republished, uploaded, posted, publicly displayed, encoded, translated, transmitted, distributed, sold, licensed, or otherwise exploited for any commercial purpose whatsoever, without our express prior written permission.

Provided that you are eligible to use the Site, you are granted a limited license to access and use the Site and to download or print a copy of any portion of the Content to which you have properly gained access solely for your personal, non-commercial use. We reserve all rights not expressly granted to you in and to the Site, the Content and the Marks.


3. USER REPRESENTATIONS

By using the Site, you represent and warrant that: (1) all registration information you submit will be true, accurate, current, and complete; (2) you will maintain the accuracy of such information and promptly update such registration information as necessary; (3) you have the legal capacity and you agree to comply with these Terms of Use; (4) you are not a minor in the jurisdiction in which you reside; (5) you will not access the Site through automated or non-human means, whether through a bot, script, or otherwise; (6) you will not use the Site for any illegal or unauthorized purpose; and (7) your use of the Site will not violate any applicable law or regulation.

If you provide any information that is untrue, inaccurate, not current, or incomplete, we have the right to suspend or terminate your account and refuse any and all current or future use of the Site (or any portion thereof).


4. USER REGISTRATION

You may be required to register with the Site. You agree to keep your password confidential and will be responsible for all use of your account and password. We reserve the right to remove, reclaim, or change a username you select if we determine, in our sole discretion, that such username is inappropriate, obscene, or otherwise objectionable.


5. PROHIBITED ACTIVITIES

You may not access or use the Site for any purpose other than that for which we make the Site available. The Site may not be used in connection with any commercial endeavors except those that are specifically endorsed or approved by us.

As a user of the Site, you agree not to:
Systematically retrieve data or other content from the Site to create or compile, directly or indirectly, a collection, compilation, database, or directory without written permission from us.
Trick, defraud, or mislead us and other users, especially in any attempt to learn sensitive account information such as user passwords.
Circumvent, disable, or otherwise interfere with security-related features of the Site, including features that prevent or restrict the use or copying of any Content or enforce limitations on the use of the Site and/or the Content contained therein.
Disparage, tarnish, or otherwise harm, in our opinion, us and/or the Site.
Use any information obtained from the Site in order to harass, abuse, or harm another person.
Make improper use of our support services or submit false reports of abuse or misconduct.
Use the Site in a manner inconsistent with any applicable laws or regulations.
Engage in unauthorized framing of or linking to the Site.
Upload or transmit (or attempt to upload or to transmit) viruses, Trojan horses, or other material, including excessive use of capital letters and spamming (continuous posting of repetitive text), that interferes with any party"s uninterrupted use and enjoyment of the Site or modifies, impairs, disrupts, alters, or interferes with the use, features, functions, operation, or maintenance of the Site.
Engage in any automated use of the system, such as using scripts to send comments or messages, or using any data mining, robots, or similar data gathering and extraction tools.
Delete the copyright or other proprietary rights notice from any Content.
Attempt to impersonate another user or person or use the username of another user.
Upload or transmit (or attempt to upload or to transmit) any material that acts as a passive or active information collection or transmission mechanism, including without limitation, clear graphics interchange formats ("gifs"), 1x1 pixels, web bugs, cookies, or other similar devices (sometimes referred to as "spyware" or "passive collection mechanisms" or "pcms").
Interfere with, disrupt, or create an undue burden on the Site or the networks or services connected to the Site.
Harass, annoy, intimidate, or threaten any of our employees or agents engaged in providing any portion of the Site to you.
Attempt to bypass any measures of the Site designed to prevent or restrict access to the Site, or any portion of the Site.
Copy or adapt the Site"s software, including but not limited to Flash, PHP, HTML, JavaScript, or other code.
Except as permitted by applicable law, decipher, decompile, disassemble, or reverse engineer any of the software comprising or in any way making up a part of the Site.
Except as may be the result of standard search engine or Internet browser usage, use, launch, develop, or distribute any automated system, including without limitation, any spider, robot, cheat utility, scraper, or offline reader that accesses the Site, or using or launching any unauthorized script or other software.
Use a buying agent or purchasing agent to make purchases on the Site.
Make any unauthorized use of the Site, including collecting usernames and/or email addresses of users by electronic or other means for the purpose of sending unsolicited email, or creating user accounts by automated means or under false pretenses.
Use the Site as part of any effort to compete with us or otherwise use the Site and/or the Content for any revenue-generating endeavor or commercial enterprise.


6. USER GENERATED CONTRIBUTIONS

The Site may invite you to chat, contribute to, or participate in blogs, message boards, online forums, and other functionality, and may provide you with the opportunity to create, submit, post, display, transmit, perform, publish, distribute, or broadcast content and materials to us or on the Site, including but not limited to text, writings, video, audio, photographs, graphics, comments, suggestions, or personal information or other material (collectively, "Contributions"). Contributions may be viewable by other users of the Site and through third-party websites. As such, any Contributions you transmit may be treated as non-confidential and non-proprietary. When you create or make available any Contributions, you thereby represent and warrant that:
The creation, distribution, transmission, public display, or performance, and the accessing, downloading, or copying of your Contributions do not and will not infringe the proprietary rights, including but not limited to the copyright, patent, trademark, trade secret, or moral rights of any third party.
You are the creator and owner of or have the necessary licenses, rights, consents, releases, and permissions to use and to authorize us, the Site, and other users of the Site to use your Contributions in any manner contemplated by the Site and these Terms of Use.
You have the written consent, release, and/or permission of each and every identifiable individual person in your Contributions to use the name or likeness of each and every such identifiable individual person to enable inclusion and use of your Contributions in any manner contemplated by the Site and these Terms of Use.
Your Contributions are not false, inaccurate, or misleading.
Your Contributions are not unsolicited or unauthorized advertising, promotional materials, pyramid schemes, chain letters, spam, mass mailings, or other forms of solicitation.
Your Contributions are not obscene, lewd, lascivious, filthy, violent, harassing, libelous, slanderous, or otherwise objectionable (as determined by us).
Your Contributions do not ridicule, mock, disparage, intimidate, or abuse anyone.
Your Contributions are not used to harass or threaten (in the legal sense of those terms) any other person and to promote violence against a specific person or class of people.
Your Contributions do not violate any applicable law, regulation, or rule.
Your Contributions do not violate the privacy or publicity rights of any third party.
Your Contributions do not violate any applicable law concerning child pornography, or otherwise intended to protect the health or well-being of minors.
Your Contributions do not include any offensive comments that are connected to race, national origin, gender, sexual preference, or physical handicap.
Your Contributions do not otherwise violate, or link to material that violates, any provision of these Terms of Use, or any applicable law or regulation.
Any use of the Site in violation of the foregoing violates these Terms of Use and may result in, among other things, termination or suspension of your rights to use the Site.

7. CONTRIBUTION LICENSE

By posting your Contributions to any part of the Site, you automatically grant, and you represent and warrant that you have the right to grant, to us an unrestricted, unlimited, irrevocable, perpetual, non-exclusive, transferable, royalty-free, fully-paid, worldwide right, and license to host, use, copy, reproduce, disclose, sell, resell, publish, broadcast, retitle, archive, store, cache, publicly perform, publicly display, reformat, translate, transmit, excerpt (in whole or in part), and distribute such Contributions (including, without limitation, your image and voice) for any purpose, commercial, advertising, or otherwise, and to prepare derivative works of, or incorporate into other works, such Contributions, and grant and authorize sublicenses of the foregoing. The use and distribution may occur in any media formats and through any media channels.

This license will apply to any form, media, or technology now known or hereafter developed, and includes our use of your name, company name, and franchise name, as applicable, and any of the trademarks, service marks, trade names, logos, and personal and commercial images you provide. You waive all moral rights in your Contributions, and you warrant that moral rights have not otherwise been asserted in your Contributions.

We do not assert any ownership over your Contributions. You retain full ownership of all of your Contributions and any intellectual property rights or other proprietary rights associated with your Contributions. We are not liable for any statements or representations in your Contributions provided by you in any area on the Site. You are solely responsible for your Contributions to the Site and you expressly agree to exonerate us from any and all responsibility and to refrain from any legal action against us regarding your Contributions.

We have the right, in our sole and absolute discretion, (1) to edit, redact, or otherwise change any Contributions; (2) to re-categorize any Contributions to place them in more appropriate locations on the Site; and (3) to pre-screen or delete any Contributions at any time and for any reason, without notice. We have no obligation to monitor your Contributions.


8. SUBMISSIONS

You acknowledge and agree that any questions, comments, suggestions, ideas, feedback, or other information regarding the Site ("Submissions") provided by you to us are non-confidential and shall become our sole property. We shall own exclusive rights, including all intellectual property rights, and shall be entitled to the unrestricted use and dissemination of these Submissions for any lawful purpose, commercial or otherwise, without acknowledgment or compensation to you. You hereby waive all moral rights to any such Submissions, and you hereby warrant that any such Submissions are original with you or that you have the right to submit such Submissions. You agree there shall be no recourse against us for any alleged or actual infringement or misappropriation of any proprietary right in your Submissions.


9. THIRD-PARTY WEBSITE AND CONTENT

The Site may contain (or you may be sent via the Site) links to other websites ("Third-Party Websites") as well as articles, photographs, text, graphics, pictures, designs, music, sound, video, information, applications, software, and other content or items belonging to or originating from third parties ("Third-Party Content"). Such Third-Party Websites and Third-Party Content are not investigated, monitored, or checked for accuracy, appropriateness, or completeness by us, and we are not responsible for any Third-Party Websites accessed through the Site or any Third-Party Content posted on, available through, or installed from the Site, including the content, accuracy, offensiveness, opinions, reliability, privacy practices, or other policies of or contained in the Third-Party Websites or the Third-Party Content. Inclusion of, linking to, or permitting the use or installation of any Third-Party Websites or any Third-Party Content does not imply approval or endorsement thereof by us. If you decide to leave the Site and access the Third-Party Websites or to use or install any Third-Party Content, you do so at your own risk, and you should be aware these Terms of Use no longer govern. You should review the applicable terms and policies, including privacy and data gathering practices, of any website to which you navigate from the Site or relating to any applications you use or install from the Site. Any purchases you make through Third-Party Websites will be through other websites and from other companies, and we take no responsibility whatsoever in relation to such purchases which are exclusively between you and the applicable third party. You agree and acknowledge that we do not endorse the products or services offered on Third-Party Websites and you shall hold us harmless from any harm caused by your purchase of such products or services. Additionally, you shall hold us harmless from any losses sustained by you or harm caused to you relating to or resulting in any way from any Third-Party Content or any contact with Third-Party Websites.


10. SITE MANAGEMENT

We reserve the right, but not the obligation, to: (1) monitor the Site for violations of these Terms of Use; (2) take appropriate legal action against anyone who, in our sole discretion, violates the law or these Terms of Use, including without limitation, reporting such user to law enforcement authorities; (3) in our sole discretion and without limitation, refuse, restrict access to, limit the availability of, or disable (to the extent technologically feasible) any of your Contributions or any portion thereof; (4) in our sole discretion and without limitation, notice, or liability, to remove from the Site or otherwise disable all files and content that are excessive in size or are in any way burdensome to our systems; and (5) otherwise manage the Site in a manner designed to protect our rights and property and to facilitate the proper functioning of the Site.


11. PRIVACY POLICY

We care about data privacy and security. By using the Site, you agree to be bound by our Privacy Policy posted on the Site, which is incorporated into these Terms of Use. Please be advised the Site is hosted in the United States. If you access the Site from any other region of the world with laws or other requirements governing personal data collection, use, or disclosure that differ from applicable laws in the United States, then through your continued use of the Site, you are transferring your data to the United States, and you agree to have your data transferred to and processed in the United States.


12. DIGITAL MILLENNIUM COPYRIGHT ACT (DMCA) NOTICE AND POLICY

Notifications

We respect the intellectual property rights of others. If you believe that any material available on or through the Site infringes upon any copyright you own or control, please immediately notify our Designated Copyright Agent using the contact information provided below (a "Notification"). A copy of your Notification will be sent to the person who posted or stored the material addressed in the Notification. Please be advised that pursuant to federal law you may be held liable for damages if you make material misrepresentations in a Notification. Thus, if you are not sure that material located on or linked to by the Site infringes your copyright, you should consider first contacting an attorney.

All Notifications should meet the requirements of DMCA 17 U.S.C. § 512(c)(3) and include the following information: (1) A physical or electronic signature of a person authorized to act on behalf of the owner of an exclusive right that is allegedly infringed; (2) identification of the copyrighted work claimed to have been infringed, or, if multiple copyrighted works on the Site are covered by the Notification, a representative list of such works on the Site; (3) identification of the material that is claimed to be infringing or to be the subject of infringing activity and that is to be removed or access to which is to be disabled, and information reasonably sufficient to permit us to locate the material; (4) information reasonably sufficient to permit us to contact the complaining party, such as an address, telephone number, and, if available, an email address at which the complaining party may be contacted; (5) a statement that the complaining party has a good faith belief that use of the material in the manner complained of is not authorized by the copyright owner, its agent, or the law; and (6) a statement that the information in the notification is accurate, and under penalty of perjury, that the complaining party is authorized to act on behalf of the owner of an exclusive right that is allegedly infringed upon.

Counter Notification

If you believe your own copyrighted material has been removed from the Site as a result of a mistake or misidentification, you may submit a written counter notification to our Designated Copyright Agent using the contact information provided below (a "Counter Notification"). To be an effective Counter Notification under the DMCA, your Counter Notification must include substantially the following: (1) identification of the material that has been removed or disabled and the location at which the material appeared before it was removed or disabled; (2) a statement that you consent to the jurisdiction of the Federal District Court in which your address is located, or if your address is outside the United States, for any judicial district in which we are located; (3) a statement that you will accept service of process from the party that filed the Notification or the party's agent; (4) your name, address, and telephone number; (5) a statement under penalty of perjury that you have a good faith belief that the material in question was removed or disabled as a result of a mistake or misidentification of the material to be removed or disabled; and (6) your physical or electronic signature.

If you send us a valid, written Counter Notification meeting the requirements described above, we will restore your removed or disabled material, unless we first receive notice from the party filing the Notification informing us that such party has filed a court action to restrain you from engaging in infringing activity related to the material in question. Please note that if you materially misrepresent that the disabled or removed content was removed by mistake or misidentification, you may be liable for damages, including costs and attorney's fees. Filing a false Counter Notification constitutes perjury.
</div>
{% endblocktrans %}
<div style="white-space: pre-wrap;">
Designated Copyright Agent
{{ agent_name }}
Attn: Copyright Agent
{{ address }}
{{ phone_number }}
{{ email_address }}
</div>
{% blocktrans en %}
<div style="white-space: pre-wrap;">
13. TERM AND TERMINATION

These Terms of Use shall remain in full force and effect while you use the Site. WITHOUT LIMITING ANY OTHER PROVISION OF THESE TERMS OF USE, WE RESERVE THE RIGHT TO, IN OUR SOLE DISCRETION AND WITHOUT NOTICE OR LIABILITY, DENY ACCESS TO AND USE OF THE SITE (INCLUDING BLOCKING CERTAIN IP ADDRESSES), TO ANY PERSON FOR ANY REASON OR FOR NO REASON, INCLUDING WITHOUT LIMITATION FOR BREACH OF ANY REPRESENTATION, WARRANTY, OR COVENANT CONTAINED IN THESE TERMS OF USE OR OF ANY APPLICABLE LAW OR REGULATION. WE MAY TERMINATE YOUR USE OR PARTICIPATION IN THE SITE OR DELETE YOUR ACCOUNT AND ANY CONTENT OR INFORMATION THAT YOU POSTED AT ANY TIME, WITHOUT WARNING, IN OUR SOLE DISCRETION.

If we terminate or suspend your account for any reason, you are prohibited from registering and creating a new account under your name, a fake or borrowed name, or the name of any third party, even if you may be acting on behalf of the third party. In addition to terminating or suspending your account, we reserve the right to take appropriate legal action, including without limitation pursuing civil, criminal, and injunctive redress.


14. MODIFICATIONS AND INTERRUPTIONS

We reserve the right to change, modify, or remove the contents of the Site at any time or for any reason at our sole discretion without notice. However, we have no obligation to update any information on our Site. We also reserve the right to modify or discontinue all or part of the Site without notice at any time. We will not be liable to you or any third party for any modification, price change, suspension, or discontinuance of the Site.

We cannot guarantee the Site will be available at all times. We may experience hardware, software, or other problems or need to perform maintenance related to the Site, resulting in interruptions, delays, or errors. We reserve the right to change, revise, update, suspend, discontinue, or otherwise modify the Site at any time or for any reason without notice to you. You agree that we have no liability whatsoever for any loss, damage, or inconvenience caused by your inability to access or use the Site during any downtime or discontinuance of the Site. Nothing in these Terms of Use will be construed to obligate us to maintain and support the Site or to supply any corrections, updates, or releases in connection therewith.


15. GOVERNING LAW

These Terms of Use and your use of the Site are governed by and construed in accordance with the laws of the State of Washington applicable to agreements made and to be entirely performed within the State of Washington, without regard to its conflict of law principles.


16. DISPUTE RESOLUTION

Any legal action of whatever nature brought by either you or us (collectively, the "Parties" and individually, a "Party") shall be commenced or prosecuted in the state and federal courts located in King, Washington, and the Parties hereby consent to, and waive all defenses of lack of personal jurisdiction and forum non conveniens with respect to venue and jurisdiction in such state and federal courts. Application of the United Nations Convention on Contracts for the International Sale of Goods and the Uniform Computer Information Transaction Act (UCITA) are excluded from these Terms of Use. In no event shall any claim, action, or proceeding brought by either Party related in any way to the Site be commenced more than twenty (20) years after the cause of action arose.


17. CORRECTIONS

There may be information on the Site that contains typographical errors, inaccuracies, or omissions, including descriptions, pricing, availability, and various other information. We reserve the right to correct any errors, inaccuracies, or omissions and to change or update the information on the Site at any time, without prior notice.


18. DISCLAIMER

THE SITE IS PROVIDED ON AN AS-IS AND AS-AVAILABLE BASIS. YOU AGREE THAT YOUR USE OF THE SITE AND OUR SERVICES WILL BE AT YOUR SOLE RISK. TO THE FULLEST EXTENT PERMITTED BY LAW, WE DISCLAIM ALL WARRANTIES, EXPRESS OR IMPLIED, IN CONNECTION WITH THE SITE AND YOUR USE THEREOF, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. WE MAKE NO WARRANTIES OR REPRESENTATIONS ABOUT THE ACCURACY OR COMPLETENESS OF THE SITE"S CONTENT OR THE CONTENT OF ANY WEBSITES LINKED TO THE SITE AND WE WILL ASSUME NO LIABILITY OR RESPONSIBILITY FOR ANY (1) ERRORS, MISTAKES, OR INACCURACIES OF CONTENT AND MATERIALS, (2) PERSONAL INJURY OR PROPERTY DAMAGE, OF ANY NATURE WHATSOEVER, RESULTING FROM YOUR ACCESS TO AND USE OF THE SITE, (3) ANY UNAUTHORIZED ACCESS TO OR USE OF OUR SECURE SERVERS AND/OR ANY AND ALL PERSONAL INFORMATION AND/OR FINANCIAL INFORMATION STORED THEREIN, (4) ANY INTERRUPTION OR CESSATION OF TRANSMISSION TO OR FROM THE SITE, (5) ANY BUGS, VIRUSES, TROJAN HORSES, OR THE LIKE WHICH MAY BE TRANSMITTED TO OR THROUGH THE SITE BY ANY THIRD PARTY, AND/OR (6) ANY ERRORS OR OMISSIONS IN ANY CONTENT AND MATERIALS OR FOR ANY LOSS OR DAMAGE OF ANY KIND INCURRED AS A RESULT OF THE USE OF ANY CONTENT POSTED, TRANSMITTED, OR OTHERWISE MADE AVAILABLE VIA THE SITE. WE DO NOT WARRANT, ENDORSE, GUARANTEE, OR ASSUME RESPONSIBILITY FOR ANY PRODUCT OR SERVICE ADVERTISED OR OFFERED BY A THIRD PARTY THROUGH THE SITE, ANY HYPERLINKED WEBSITE, OR ANY WEBSITE OR MOBILE APPLICATION FEATURED IN ANY BANNER OR OTHER ADVERTISING, AND WE WILL NOT BE A PARTY TO OR IN ANY WAY BE RESPONSIBLE FOR MONITORING ANY TRANSACTION BETWEEN YOU AND ANY THIRD-PARTY PROVIDERS OF PRODUCTS OR SERVICES. AS WITH THE PURCHASE OF A PRODUCT OR SERVICE THROUGH ANY MEDIUM OR IN ANY ENVIRONMENT, YOU SHOULD USE YOUR BEST JUDGMENT AND EXERCISE CAUTION WHERE APPROPRIATE.


19. LIMITATIONS OF LIABILITY

IN NO EVENT WILL WE OR OUR DIRECTORS, EMPLOYEES, OR AGENTS BE LIABLE TO YOU OR ANY THIRD PARTY FOR ANY DIRECT, INDIRECT, CONSEQUENTIAL, EXEMPLARY, INCIDENTAL, SPECIAL, OR PUNITIVE DAMAGES, INCLUDING LOST PROFIT, LOST REVENUE, LOSS OF DATA, OR OTHER DAMAGES ARISING FROM YOUR USE OF THE SITE, EVEN IF WE HAVE BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. NOTWITHSTANDING ANYTHING TO THE CONTRARY CONTAINED HEREIN, OUR LIABILITY TO YOU FOR ANY CAUSE WHATSOEVER AND REGARDLESS OF THE FORM OF THE ACTION, WILL AT ALL TIMES BE LIMITED TO THE AMOUNT PAID, IF ANY, BY YOU TO US DURING THE SIX (6) MONTH PERIOD PRIOR TO ANY CAUSE OF ACTION ARISING. CERTAIN US STATE LAWS AND INTERNATIONAL LAWS DO NOT ALLOW LIMITATIONS ON IMPLIED WARRANTIES OR THE EXCLUSION OR LIMITATION OF CERTAIN DAMAGES. IF THESE LAWS APPLY TO YOU, SOME OR ALL OF THE ABOVE DISCLAIMERS OR LIMITATIONS MAY NOT APPLY TO YOU, AND YOU MAY HAVE ADDITIONAL RIGHTS.


20. INDEMNIFICATION

You agree to defend, indemnify, and hold us harmless, including our subsidiaries, affiliates, and all of our respective officers, agents, partners, and employees, from and against any loss, damage, liability, claim, or demand, including reasonable attorneys" fees and expenses, made by any third party due to or arising out of: (1) your Contributions; (2) use of the Site; (3) breach of these Terms of Use; (4) any breach of your representations and warranties set forth in these Terms of Use; (5) your violation of the rights of a third party, including but not limited to intellectual property rights; or (6) any overt harmful act toward any other user of the Site with whom you connected via the Site. Notwithstanding the foregoing, we reserve the right, at your expense, to assume the exclusive defense and control of any matter for which you are required to indemnify us, and you agree to cooperate, at your expense, with our defense of such claims. We will use reasonable efforts to notify you of any such claim, action, or proceeding which is subject to this indemnification upon becoming aware of it.


21. USER DATA

We will maintain certain data that you transmit to the Site for the purpose of managing the performance of the Site, as well as data relating to your use of the Site. Although we perform regular routine backups of data, you are solely responsible for all data that you transmit or that relates to any activity you have undertaken using the Site. You agree that we shall have no liability to you for any loss or corruption of any such data, and you hereby waive any right of action against us arising from any such loss or corruption of such data.


22. ELECTRONIC COMMUNICATIONS, TRANSACTIONS, AND SIGNATURES

Visiting the Site, sending us emails, and completing online forms constitute electronic communications. You consent to receive electronic communications, and you agree that all agreements, notices, disclosures, and other communications we provide to you electronically, via email and on the Site, satisfy any legal requirement that such communication be in writing. YOU HEREBY AGREE TO THE USE OF ELECTRONIC SIGNATURES, CONTRACTS, ORDERS, AND OTHER RECORDS, AND TO ELECTRONIC DELIVERY OF NOTICES, POLICIES, AND RECORDS OF TRANSACTIONS INITIATED OR COMPLETED BY US OR VIA THE SITE. You hereby waive any rights or requirements under any statutes, regulations, rules, ordinances, or other laws in any jurisdiction which require an original signature or delivery or retention of non-electronic records, or to payments or the granting of credits by any means other than electronic means.


23. CALIFORNIA USERS AND RESIDENTS

If any complaint with us is not satisfactorily resolved, you can contact the Complaint Assistance Unit of the Division of Consumer Services of the California Department of Consumer Affairs in writing at 1625 North Market Blvd., Suite N 112, Sacramento, California 95834 or by telephone at (800) 952-5210 or (916) 445-1254.


24. MISCELLANEOUS

These Terms of Use and any policies or operating rules posted by us on the Site or in respect to the Site constitute the entire agreement and understanding between you and us. Our failure to exercise or enforce any right or provision of these Terms of Use shall not operate as a waiver of such right or provision. These Terms of Use operate to the fullest extent permissible by law. We may assign any or all of our rights and obligations to others at any time. We shall not be responsible or liable for any loss, damage, delay, or failure to act caused by any cause beyond our reasonable control. If any provision or part of a provision of these Terms of Use is determined to be unlawful, void, or unenforceable, that provision or part of the provision is deemed severable from these Terms of Use and does not affect the validity and enforceability of any remaining provisions. There is no joint venture, partnership, employment or agency relationship created between you and us as a result of these Terms of Use or use of the Site. You agree that these Terms of Use will not be construed against us by virtue of having drafted them. You hereby waive any and all defenses you may have based on the electronic form of these Terms of Use and the lack of signing by the parties hereto to execute these Terms of Use.

25. RETURN AND REFUND POLICY

Products, services, goods, and other purchases made on this site may not be returned. No refunds may be issued for subscriptions or purchases with us on {{ the_site_name }}. {{ the_site_name }} reserves the right to refuse any refund of payment made with us on this website or otherwise.

26. CONTACT US

In order to resolve a complaint regarding the Site or to receive further information regarding use of the Site, please contact us at:
</div>
{% endblocktrans %}

<div style="white-space: pre-wrap;">
{{ site_name }}
ATTN: {{ agent_name }}
{{ address }}
Phone: {{ phone_number }} {% blocktrans en %}(press option 6 for information, or use the menu to call me){% endblocktrans %}
{{ email_address }}
</div>
{% endblock %}
```


--- File: lotteharper-main/misc/tests.py ---
```python
```


--- File: lotteharper-main/misc/urls.py ---
```python
from django.urls import path

from . import views

app_name='misc'

urlpatterns = [
    path('search/', views.search, name='search'),
    path('terms/', views.terms, name='terms'),
    path('auth/', views.authenticated, name='auth'),
    path('logo/', views.logo, name='logo'),
    path('time/', views.time, name='time'),
    path('ad/', views.ad, name='ad'),
    path('ads.txt', views.adstxt, name='adstxt'),
    path('robots.txt', views.robotstxt, name='robotstxt'),
    path('idscan/', views.idscan, name='idscan'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
    path('news.xml', views.news, name='news'),
    path('map/', views.map, name='map'),
    path('opendkimkey/', views.opendkimkey, name='opendkimkey'),
    path('publickeys/', views.publickeys, name='publickeys'),
    path('upload/', views.upload_video_api, name='upload'),
    path('site.webmanifest', views.webmanifest, name='webmanifest'),
    path('serviceworker.js', views.service_worker, name='serviceworker'),
]
```


--- File: lotteharper-main/misc/views.py ---
```python
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from vendors.tests import is_vendor
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache, cache_page
from users.tests import is_superuser_or_vendor

@never_cache
def logo(request):
    from django.shortcuts import render
    return render(request, 'misc/logo.html')

@login_required
@user_passes_test(is_superuser_or_vendor)
def publickeys(request):
    from django.http import HttpResponse
    import subprocess
    return HttpResponse(subprocess.check_output("catkeys", shell=True))

@cache_page(60*60*24*28)
def opendkimkey(request):
    from django.http import HttpResponse
    import subprocess
    return HttpResponse(subprocess.check_output("opendkimkey", shell=True))

@cache_page(60*60*24*30)
def webmanifest(request):
    from django.shortcuts import render
    return render(request, 'misc/site.webmanifest', {})

@cache_page(60*60*24*28)
def map(request):
    from django.shortcuts import render
    from security.models import UserIpAddress, Session
    latlngs = []
    from django.conf import settings
    for ip in UserIpAddress.objects.all():
        if ip.latitude and ip.longitude: latlngs = latlngs + [(ip.latitude, ip.longitude)]
    import numpy as np
    from sklearn.cluster import DBSCAN
    coords = np.array(latlngs)
    # Haversine metric requires radians:
    kms_per_radian = 6371.0088
    epsilon = 50 / kms_per_radian # 50km radius
    db = DBSCAN(eps=epsilon, min_samples=2, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
    labels = db.labels_
    groups = {}
    for label, point in zip(labels, latlngs):
        groups.setdefault(label, []).append(point)
    pts = []
    for x in range(len(groups)-1):
        pts = pts + [groups[x][0]]
#    print(pts)
    return render(request, 'misc/map.html', {'title': 'Visitor Map', 'latlngs': pts, 'maps_api_key': settings.GOOGLE_API_KEY})

@cache_page(60*60*24*30)
def adstxt(request):
    from django.shortcuts import render
    return render(request, 'ads.txt')

@cache_page(60*60*24*30)
def service_worker(request):
    from django.http import HttpResponse
    from django.conf import settings
    import os
    sw_path = os.path.join(settings.BASE_DIR, 'templates', 'serviceworker.js')
    try:
        from django.template.loader import render_to_string
        from datetime import datetime
        context = {'timestamp': str(datetime.now().timestamp()).split('.')[0]}
        sw_js = render_to_string('serviceworker.js', context)
        return HttpResponse(sw_js, content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse("Service worker not found", status=404)

@ca