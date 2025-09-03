var GHPATH = '/';
 
// Choose a different app prefix name
var APP_PREFIX = 'qoshlli_';
 
// The version of the cache. Every time you change any of the files
// you need to change this version (version_01, version_02…). 
// If you don't change the version, the service worker will give your
// users the old files!
var VERSION = 'version_08';
 
// The files to make available for offline use. make sure to add 
// others to this list
var URLS = [
  `${GHPATH}/`,
  `${GHPATH}/index.html`,
  `${GHPATH}/main.js`,
  `${GHPATH}/qrcode.js`,
  `${GHPATH}/ccv.js`,
  `${GHPATH}/face.js`,
  `${GHPATH}/mirror.html`,
  `${GHPATH}/ringtone.mp3`,
  `${GHPATH}/ringtone.wav`,
  `${GHPATH}/VK_logo.svg.png`,
  `${GHPATH}/pinterest.svg`,
  `${GHPATH}/tumblr-logo.svg`
]
