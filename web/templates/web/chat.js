/* By Charlotte Grace Harper, v0.0.11 2024-08-22*/
{% load app_filters %}
function copyToClipboard(el) {
        navigator.clipboard.writeText(document.getElementById(el).innerHTML);
}
let otherPerson;
REQ_FACE_HEIGHT = 10;
/**
 * Hides the given element by setting `display: none`.
 * @param {HTMLElement} element The element to hide
 */
function hideElement(element) {
   element.style.display = "none";
}
/**
 * Shows the given element by resetting the display CSS property.
 * @param {HTMLElement} element The element to show
 */
function showElement(element) {
   element.style.display = "";
   element.classList.remove("hide");
}
const callButton = document.getElementById("call-button");
const endButton = document.getElementById("end-button");
const callDiv = document.getElementById("call-div");
const allDiv = document.getElementById("all-div");
const pleaseInteract = document.getElementById("please-interact");
const videoContainer = document.getElementById("video-container");
const theLink = document.getElementById("the-link");
const members = document.getElementById("members");
const ringtone = document.getElementById("ringtone");
const errorMessage = document.getElementById("error-message");
const callPrompt = document.getElementById("accept-div");
const localVideo = document.getElementById("local-video");
const remoteVideo = document.getElementById("remote-video");
const updateUsername = document.getElementById("update-username");
const muteButton = document.getElementById("mute");
const stillButton = document.getElementById("still");
const canvas = document.getElementById("canvas");
var context = canvas.getContext('2d');
var scale = 1;
const callText = document.getElementById("accept-text");
var chatSocket;
function sendMessageToSignallingServer(message) {
   const json = JSON.stringify(message);
   chatSocket.send(json);
}
var callAccepted = false;
var callHandled = false;
remoteVideo.onload = function () {
   remoteVideo.play();
};

function acceptCall() {
   callAccepted = true;
   callHandled = true;
   callPrompt.classList.add("hide");
}

function denyCall() {
   callAccepted = false;
   callHandled = true;
   callPrompt.classList.add("hide");
   sendMessageToSignallingServer({'channel': 'end_call', 'otherPerson': otherPerson});
}

function playSound() {
   ringtone.currentTime = 0;
   ringtone.play();
}

function stopSound() {
   ringtone.pause();
}

hideElement(theLink);


function playVideos() {
   /*
	   try {
	      document.getElementById('remote-video').play();
	   } catch {}*/
   /*  try {
     document.getElementById('local-video').play();
   } catch { }*/
}

muteButton.addEventListener("click", function (event) {
   remoteVideo.muted = !remoteVideo.muted;
   if (remoteVideo.muted) {
      muteButton.innerHTML = '{{ 'Unmute'|etrans }}';
   } else {
      muteButton.innerHTML = '{{ 'Mute'|etrans }}';

   }
});

var calling = false;

var callStarted = false;
var videoStarted = false;
var webrtc;

/**
 * Hides both local and remote video, but shows the "call" button.
 */
function hideVideoCall() {
   if (webrtc && calling) {
      webrtc.close();
      sendMessageToSignallingServer({
         channel: 'end_call',
         otherPerson
      });
   }
   videoStarted = false;
   callStarted = false;
   calling = false;
   hideElement(videoContainer);
   hideElement(allDiv);
   showElement(callButton);
   hideElement(endButton);
   hideElement(stillButton);
   showElement(members);
	stopStream();
}
var inter;
var meminter;
endButton.addEventListener("click", function () {
   hideVideoCall();
   showElement(pleaseInteract);
   showElement(allDiv);
   clearInterval(inter);
});

/**
 * Shows both local and remote video, and hides the "call" button.
 */
function showVideoCall() {
   calling = true;
   hideElement(callButton);
   showElement(videoContainer);
   showElement(endButton);
   showElement(muteButton);
   showElement(stillButton);
   hideElement(callDiv);
   hideElement(members);
}
/** @type {string} */
function RNG(seed) {
   // LCG using GCC's constants
   this.m = 0x80000000; // 2**31;
   this.a = 1103515245;
   this.c = 12345;
   this.state = seed ? seed : Math.floor(Math.random() * (this.m - 1));
}
RNG.prototype.nextInt = function () {
   this.state = (this.a * this.state + this.c) % this.m;
   return this.state;
}
RNG.prototype.nextFloat = function () {
   // returns in range [0,1]
   return this.nextInt() / (this.m - 1);
}
RNG.prototype.nextRange = function (start, end) {
   // returns in range [start, end): including start, excluding end
   // can't modulu nextInt because of weak randomness in lower bits
   let rangeSize = end - start;
   let randomUnder1 = this.nextInt() / this.m;
   return start + Math.floor(randomUnder1 * rangeSize);
}
RNG.prototype.choice = function (array) {
   return array[this.nextRange(0, array.length)];
}
var us = "";
let rng = new RNG(new Date().getTime());
for (var x = 0; x < 6; x++) {
   us = us + String.fromCharCode(97 + rng.nextRange(0, 26));
}
var cs = "";
for (var x = 0; x < 32; x++) {
   cs = cs + String.fromCharCode(97 + rng.nextRange(0, 26));
}

function setCookie(cname, cvalue, exdays) {
   const d = new Date();
   d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
   let expires = "expires=" + d.toUTCString();
   document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
   let name = cname + "=";
   let decodedCookie = decodeURIComponent(document.cookie);
   let ca = decodedCookie.split(';');
   for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') {
         c = c.substring(1);
      }
      if (c.indexOf(name) == 0) {
         return c.substring(name.length, c.length);
      }
   }
   return "";
}
var cu = getCookie("username");
if (!cu) {
   setCookie("username", us, 28);
   cu = us;
}
var ck = getCookie("key");
if (!ck) {
   setCookie("key", cs, 28);
   ck = cs;
}
var username = cu;
theLink.innerHTML = "https://glamgirlx.com/chat?key=" + username;
document.getElementById("thename").innerHTML = username;
const socketUrl = 'wss://lotteh.com/ws/chat/video/';

function stopStream() {
if (!window.streamReference) return;

window.streamReference.getAudioTracks().forEach(function(track) {
    track.stop();
});

window.streamReference.getVideoTracks().forEach(function(track) {
    track.stop();
});

window.streamReference = null;
}
async function startMedia() {
		 navigator
         .mediaDevices
         .getUserMedia({
            video: true,
            audio: {
               echoCancellation: true
            }
         })
         .then((localStream) => {
            /** @type {HTMLVideoElement} */
            for (const track of localStream.getTracks()) {
               webrtc.addTrack(track, localStream);
            }
            localVideo.srcObject = localStream;
		window.streamReference = localStream;
            localVideo.play();

         }).catch(function (err) {
            navigator
               .mediaDevices
               .getUserMedia({
                  video: true,
                  audio: true
               })
               .then((localStream) => {
                  /** @type {HTMLVideoElement} */
                  for (const track of localStream.getTracks()) {
                     webrtc.addTrack(track, localStream);
                  }
                  localVideo.srcObject = localStream;
		        window.streamReference = localStream;
                  localVideo.play();

               }).catch(function (err) {
                  navigator
                     .mediaDevices
                     .getUserMedia({
                        audio: true
                     })
                     .then((localStream) => {
                        /** @type {HTMLVideoElement} */
                        for (const track of localStream.getTracks()) {
                           webrtc.addTrack(track, localStream);
                        }
                        localVideo.srcObject = localStream;
			             window.streamReference = localStream;
                        localVideo.play();
                     }).catch(function (err) {
                        navigator
                           .mediaDevices
                           .getUserMedia({
                              video: true
                           })
                           .then((localStream) => {
                              /** @type {HTMLVideoElement} */
                              for (const track of localStream.getTracks()) {
                                 webrtc.addTrack(track, localStream);
                              }
                              localVideo.srcObject = localStream;
            				   window.streamReference = localStream;
                              localVideo.play();

                           }).catch(function (err) {
                              console.log("An error occurred: " + err);
                              errorMessage.classList.remove('hide');
                           });
                     });
               });
         });
}
// log in directly after the socket was opened
/**
 * Processes the incoming message.
 * @param {WebSocketMessage} message The incoming message
 */
async function handleMessage(message) {
   switch (message.channel) {
      case "start_call":
		   if(!calling) {
         playSound();
         callPrompt.classList.remove("hide");
         callText.innerHTML = message.otherPerson + " is calling you, accept?";
         const urParams = new URLSearchParams(window.location.search);
         var key = urParams.get('key');
         if (key == message.otherPerson || confirm(message.otherPerson + " {{ 'is calling you, accept?'|etrans }}")) {
            ringtone.pause();
		       webrtc = new RTCPeerConnection({
         iceServers: [{
            urls: [
               "stun:lotteh.com",
            ],
         }, ],
      });
      webrtc.addEventListener("icecandidate", (event) => {
         if (!event.candidate) {
            return;
         }
         sendMessageToSignallingServer({
            channel: "webrtc_ice_candidate",
            candidate: event.candidate,
            otherPerson,
         });
      });
      webrtc.addEventListener("track", (event) => {
         /** @type {HTMLVideoElement} */
         remoteVideo.srcObject = event.streams[0];
      });
	await startMedia();
			 setTimeout(async function() {
            acceptCall();
            otherPerson = message.otherPerson;
            showVideoCall();
            const offer = await webrtc.createOffer();
            await webrtc.setLocalDescription(offer);
            sendMessageToSignallingServer({"channel" : "webrtc_offer",
               offer,
               otherPerson,
            });
            startModeration();
			 }, 1000);
         } else {
            var i = setInterval(async function () {
               if (callAccepted && callHandled) {
		              webrtc = new RTCPeerConnection({
         iceServers: [{
            urls: [
               "stun:lotteh.com",
            ],
         }, ],
      });
      webrtc.addEventListener("icecandidate", (event) => {
         if (!event.candidate) {
            return;
         }
         sendMessageToSignallingServer({
            "channel": "webrtc_ice_candidate",
            candidate: event.candidate,
            otherPerson,
         });
      });
      webrtc.addEventListener("track", (event) => {
         /** @type {HTMLVideoElement} */
         remoteVideo.srcObject = event.streams[0];
      });
		       await startMedia();
                  clearInterval(i);
		       setTimeout(async function() {
                  otherPerson = message.otherPerson;
                  showVideoCall();
                  const offer = await webrtc.createOffer();
                  await webrtc.setLocalDescription(offer);
                  sendMessageToSignallingServer({
                     channel: "webrtc_offer",
                     offer,
                     otherPerson,
                  });
		       }, 3000);
                  ringtone.pause();
               } else if (!callAccepted && callHandled) {
                  clearInterval(i);
                  ringtone.pause();
               }
            }, 1000);
         }
	}
	break;
      case "webrtc_ice_candidate":
         console.log("received ice candidate");
         await webrtc.addIceCandidate(message.candidate);
         break;
      case "webrtc_offer":
         console.log("received webrtc offer");
         await webrtc.setRemoteDescription(message.offer);
         const answer = await webrtc.createAnswer();
         await webrtc.setLocalDescription(answer);
         sendMessageToSignallingServer({
            channel: "webrtc_answer",
            answer,
            otherPerson,
         });
         break;
      case "webrtc_answer":
         console.log("received webrtc answer");
         await webrtc.setRemoteDescription(message.answer);
         break;
      case "members":
         members.innerHTML = "{{ 'Members online:'|etrans }} " + message.members;
         break;
      case "key":
         ck = message.key;
	 cs = message.key;
	 setCookie(key, message.key, 28*12*3);
         break;
      case "end_call":
         endButton.click();
         break;
      default:
         console.log("unknown message", message);
         break;
   }
}

function startMembersUpdate() {
   clearInterval(meminter);
   meminter = setInterval(function () {
      sendMessageToSignallingServer({
         channel: 'members'
      });
   }, 10000);
   setTimeout(function () {
      sendMessageToSignallingServer({
         channel: 'members'
      });
   }, 3000);
}

function moderate() {
   drawRotated(0, localVideo, true);
   var faces = ccv.detect_objects({
      "canvas": ccv.pre(canvas),
      "cascade": cascade,
      "interval": 2,
      "min_neighbors": 1
   });
   if (!(faces.length < 1)) {
      var height = faces[0].height;
      console.log(height);
      if (height > REQ_FACE_HEIGHT) {
         var blobBin = new String(canvas.toDataURL());
         sendMessageToSignallingServer({
            channel: 'age',
            data: blobBin
         });
      }
   }
}

function startModeration() {
   clearInterval(inter);
   inter = setInterval(function () {
      /*	      localVideo.play(); */
      moderate();
   }, 15000);
   setTimeout(function () {
      moderate();
   }, 3000);
}
var degmod = 90;

function openVideoWebsocket() {
	chatSocket = new WebSocket(socketUrl);
         chatSocket.addEventListener("close", () => {
            console.log("websocket closed");
            setTimeout(function () {
               openVideoWebsocket();
            }, 10000);
         });
         chatSocket.addEventListener("open", () => {
            console.log("websocket connected");
            sendMessageToSignallingServer({
               channel: "login",
               name: username,
	           key: ck,
            });
            startMembersUpdate();
         });
         chatSocket.addEventListener("message", (event) => {
            const message = JSON.parse(event.data.toString());
            handleMessage(message);
            playVideos();
         });
}

function drawRotated(degrees, image, fallback) {
   context.clearRect(0, 0, canvas.width, canvas.height);
   var mode = ((degrees / 90) % 2) % 4 == 0;
   if (!mode) {
      canvas.width = image.videoHeight * scale;
      canvas.height = image.videoWidth * scale;
   } else {
      canvas.width = image.videoWidth * scale;
      canvas.height = image.videoHeight * scale;
   }
   context.clearRect(0, 0, canvas.width, canvas.height);
   if (degrees >= 0) {
      context.translate(canvas.width / 2, canvas.height / 2); // to center
      context.rotate(degrees % 360 * Math.PI / 180 * 90);
   }
   if (!mode) {
      context.drawImage(image, -canvas.height / 2, -canvas.width / 2, canvas.height, canvas.width); // and back
      context.translate(-canvas.width / 2, -canvas.height / 2); // and back
   } else {
      context.drawImage(image, -canvas.width / 2, -canvas.height / 2, canvas.width, canvas.height); // and back
      context.translate(-canvas.width / 2, -canvas.height / 2); // and back
   }
   context.restore();
   context.save();
}
var isVideoSetup = false;
document.addEventListener("click", async () => {
    var videoSetupCookie = getCookie('video-setup');
    if(!videoSetupCookie && !isVideoSetup) {
        navigator
        .mediaDevices
        .getUserMedia({ video: true, audio: true})
        .then((localStream) => {
          const localVideo = document.getElementById("test-video");
          localVideo.srcObject = localStream;
          localVideo.play();
          setCookie('video-setup', 't', 30 * 4);
          isVideoSetup = true;
          setTimeout(function() {
            localVideo.pause();
            localVideo.srcObject = null;
            localStream.getTracks().forEach(track => {
              track.stop()
              track.enabled = false
            });
            stopStream();
          }, 1000);
       });
    }
   if (!videoStarted) {
      if (!chatSocket) {
         openVideoWebsocket();
      }
      hideElement(pleaseInteract);
      showElement(allDiv);
      showElement(callDiv);
      hideElement(pleaseInteract);
      showElement(allDiv);
      showElement(callDiv);
      videoStarted = true;
   } else if (!callStarted) {
      const urParams = new URLSearchParams(window.location.search);
      var key = urParams.get('key');
      if (key) {
	      callButton.click();
      }
      callStarted = true;
   }
});
hideVideoCall();
callButton.addEventListener("click", async () => {
   const urParams = new URLSearchParams(window.location.search);
   var key = urParams.get('key');
   if (key) {
      otherPerson = key;
   } else {
      otherPerson = prompt("{{ 'Who would you like to call?'|etrans }}");
   }
   if (otherPerson) {
	         webrtc = new RTCPeerConnection({
         iceServers: [{
            urls: [
               "stun:lotteh.com",
            ],
         }, ],
      });
      webrtc.addEventListener("icecandidate", (event) => {
         if (!event.candidate) {
            return;
         }
         sendMessageToSignallingServer({
            channel: "webrtc_ice_candidate",
            candidate: event.candidate,
            otherPerson,
         });
      });
      webrtc.addEventListener("track", (event) => {
         /** @type {HTMLVideoElement} */
         remoteVideo.srcObject = event.streams[0];
      });
	await startMedia();
	   setTimeout(function() {
      showVideoCall();
      sendMessageToSignallingServer({
         channel: "start_call",
         otherPerson,
      });
      startModeration();
	   }, 3000);
   }
});
updateUsername.addEventListener("click", async () => {
   var input = prompt('{{ 'Please enter a new username'|etrans }}');
   if (input) {
      var k = getCookie("key");
      document.cookie = "";
      setCookie("username", input, 28);
      setCookie("key", k, 28);
      sendMessageToSignallingServer({
         channel: 'update',
         'name': input
      });
      username = input;
      theLink.innerHTML = "https://glamgirlx.com/chat?key=" + username;
      document.getElementById("thename").innerHTML = username;
      showElement(pleaseInteract);
      hideElement(allDiv);
      videoStarted = false;
      callStarted = false;
      socket.close();
      socket = null;
      window.location.reload();
   }
});

const download = function (canvas) {
    const link = document.createElement('a');
    link.download = 'Glam Girl X - {{ 'Photo'|etrans }} ' + new String(new Date()) + '.png';
    link.href = canvas.toDataURL()
    link.click();
}
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
stillButton.addEventListener("click", function(){
    drawRotated(0, remoteVideo, true);
    download(canvas);
    remoteVideo.play();
    setTimeout(function() {
        remoteVideo.play();
    }, 1000);
});
remoteVideo.addEventListener("pause", (event) => {event.target.play();});
localVideo.addEventListener("pause", (event) => {event.target.play();});
const container = document.getElementById('video-container');
var fullscreenButton = document.getElementById('fullscreenToggle');
fullscreenButton.addEventListener('click', () => {
  if (!document.fullscreenElement) {
    fullscreenButton.innerHTML = '<i class="bi bi-fullscreen-exit"></i>';
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
    fullscreenButton.innerHTML = '<i class="bi bi-arrows-fullscreen"></i>';
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
