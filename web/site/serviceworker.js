var GHPATH = '/';
// Choose a different app prefix name
var APP_PREFIX = 'glamgirlx_';
// The version of the cache. Every time you change any of the files
// you need to change this version (version_01, version_02…). 
// If you don't change the version, the service worker will give your
// users the old files!
var VERSION = 'version_01754822727.3714125';
// The files to make available for offline use. make sure to add 
// others to this list
var URLS = [
  `${GHPATH}/favicon.ico`,
  `${GHPATH}/index.html`,
  `${GHPATH}/static/main.js`,
  `${GHPATH}/static/main.css`,
  `${GHPATH}/static/fonts/bootstrap-icons.css`,
  `${GHPATH}/static/prism.js`,
  `${GHPATH}/static/prism.css`,
  `${GHPATH}/static/qrcode.min.js`,
  `${GHPATH}/media/lips.png`,
  `${GHPATH}/media/icons/VK_logo.svg.png`,
  `${GHPATH}/media/icons/pinterest.svg`,
  `${GHPATH}/media/icons/tumblr-logo.svg`,

  `${GHPATH}/`,

  `${GHPATH}/news`,

  `${GHPATH}/landing`,

  `${GHPATH}/private`,

  `${GHPATH}/index`,

  `${GHPATH}/contact`,

  `${GHPATH}/chat`,

  `${GHPATH}/links`,

  `${GHPATH}/the-photo-appears-to-show-part-of-a`,

  `${GHPATH}/spend-an-evening-with`,

  `${GHPATH}/two-player-color-sudoku-online-free`,

  `${GHPATH}/this-photo-shows-a-person-with-curly`,

  `${GHPATH}/practical-web-based-deep-learning-and`,

  `${GHPATH}/a-woman-is-laying-on-a-red`,

  `${GHPATH}/play-color-sudoku-online-free`,

  `${GHPATH}/3d-printed-22lr-subcompact`,

  `${GHPATH}/the-photo-shows-a-person-with-short`,

  `${GHPATH}/the-photo-shows-a-young-person-with`,

  `${GHPATH}/how-do-i-build-a-full-stack-web`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-with-short`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/whats-the-best-way-to-boil`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/a+woman+with+a+red+hair+and+a+red`,

  `${GHPATH}/the-photo-shows-a-person-with-short`,

  `${GHPATH}/post`,

  `${GHPATH}/what-causes-migraine-and-how`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-with-short`,

  `${GHPATH}/this-photo-shows-a-person-sitting-on`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/how-do-i-find-customers-for-my`,

  `${GHPATH}/this-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/a-woman-in-a-white-shirt-and-map-table-floor`,

  `${GHPATH}/the-photo-shows-a-person-lying-on`,

  `${GHPATH}/the-photo-shows-a-person-sitting-on-a`,

  `${GHPATH}/how-do-i-build-a-mail-server`,

  `${GHPATH}/this-photo-shows-a-person-with-short`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/a-woman-is-laying-on-a-bed-with-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/this-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/a-woman-in-a-white-shirt-and-front-strong-depend`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/how-do-i-write-a-good`,

  `${GHPATH}/the-image-shows-a-person-lying-down`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-condition-live-fair`,

  `${GHPATH}/this-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/post`,

  `${GHPATH}/the-image-shows-a-person-with-light`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/post`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/post`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-image-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-is-a-closeup-selfie-of-a`,

  `${GHPATH}/the-photo-shows-a-person-with-light`,

  `${GHPATH}/makeup-tips-and-guidelines-for`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-taking-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/this-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/post`,

  `${GHPATH}/this-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/this-photo-shows-a-person-with-curly`,

  `${GHPATH}/this-photo-shows-a-person-with-curly`,

  `${GHPATH}/this-photo-shows-a-person-sitting-on`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/how-do-i-wear-deadlock`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/why-is-it-safer-to-wear-a-mask`,

  `${GHPATH}/a-woman-is-holding-a-pink-teddy`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/post`,

  `${GHPATH}/this-photo-shows-a-person-with-curly`,

  `${GHPATH}/why-do-people-implant-nfc-implants-in`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/how-do-i-write-a-professional`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/this-photo-shows-a-person-with-short`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/how-do-i-send-email-with-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/post`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-danger-pull-some`,

  `${GHPATH}/a-young-girl-laying-on-a-bed-who-even-method`,

  `${GHPATH}/post`,

  `${GHPATH}/the-photo-shows-a-person-with-fair`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/what-are-some-of-the-risks-associated`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-sitting-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-features-a-person-lying-on`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/what-are-the-benefits-to-having`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/how-is-the-crypto-market`,

  `${GHPATH}/the-photo-shows-a-person-with-short`,

  `${GHPATH}/an-excerpt-from-my-book-on-amazon-at`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/a-girl-laying-on-a-bed-with-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/this-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-sitting-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/why-should-i-use-an-apple-l-out`,

  `${GHPATH}/the-image-shows-a-person-with-curly`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/a-young-woman-is-smiling-while`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/i-just-started-taking-birth`,

  `${GHPATH}/the-photo-is-a-closeup-selfie-of-a`,

  `${GHPATH}/how-do-i-host-a-web-server-from`,

  `${GHPATH}/how-do-i-get-publicity-and`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/the-photo-features-a-person-lying-on`,

  `${GHPATH}/the-photo-shows-a-person-lying-on`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/the-photo-features-a-person-with`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/post`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/this-photo-shows-a-person-lying-down`,

  `${GHPATH}/this-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/this-photo-shows-a-person-lying-down`,

  `${GHPATH}/is-sugar-really-unhealthy`,

  `${GHPATH}/the-photo-shows-a-person-with-curly`,

  `${GHPATH}/this-photo-shows-a-person-wearing-a`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-person-with-short`,

  `${GHPATH}/the-image-shows-a-person-lying-on-a`,

  `${GHPATH}/this-photo-shows-a-person-with-curly`,

  `${GHPATH}/the-photo-shows-a-person-lying-on`,

  `${GHPATH}/the-photo-shows-a-person-lying-down`,

  `${GHPATH}/the-photo-shows-a-person-lying-on-a`,

]
