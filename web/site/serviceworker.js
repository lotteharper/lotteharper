var GHPATH = '/';
// Choose a different app prefix name
var APP_PREFIX = 'glamgirlx_';
// The version of the cache. Every time you change any of the files
// you need to change this version (version_01, version_02…). 
// If you don't change the version, the service worker will give your
// users the old files!
var VERSION = 'version_01751916062.439081';
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

  `${GHPATH}/three-thirteen-online-card-game`,

  `${GHPATH}/3d-printed-22lr-subcompact`,

  `${GHPATH}/a-woman-with-a-red-hair-and-a-long-system-often`,

  `${GHPATH}/play-color-sudoku-online-free`,

  `${GHPATH}/two-player-color-sudoku-online-free`,

  `${GHPATH}/a-woman-is-laying-on-a-red`,

  `${GHPATH}/practical-web-based-deep-learning-and`,

  `${GHPATH}/spend-an-evening-with`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-vowel-did-still`,

  `${GHPATH}/how-do-i-build-a-full-stack-web`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-might-though-their`,

  `${GHPATH}/a-woman-with-a-black-hair-and-a-farm-mine-ice`,

  `${GHPATH}/a-young-woman-is-laying-on-a-three-draw-subject`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-red`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-sugar-arrange-speak`,

  `${GHPATH}/a-young-woman-is-laying-on-a`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-she-string-sudden`,

  `${GHPATH}/whats-the-best-way-to-boil`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-over-next-least`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-towel`,

  `${GHPATH}/a-young-woman-is-sitting-on-a-total-shore-begin`,

  `${GHPATH}/a-woman-with-a-black-and-white-horse-country-until`,

  `${GHPATH}/a-woman-in-a-red-shirt-and`,

  `${GHPATH}/a-woman-in-a-dress-is-looking`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-picture-plain-busy`,

  `${GHPATH}/a+woman+with+a+red+hair+and+a+red`,

  `${GHPATH}/what-causes-migraine-and-how`,

  `${GHPATH}/a-woman-is-laying-on-a-red-deal-where-island`,

  `${GHPATH}/a-woman-in-a-white-dress-can-iron-pound`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-number-machine-felt`,

  `${GHPATH}/how-do-i-find-customers-for-my`,

  `${GHPATH}/a-woman-with-a-black-and-white-end-at-station`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-eight-women-whose`,

  `${GHPATH}/a-woman-in-a-white-shirt-and-map-table-floor`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-control-but-flower`,

  `${GHPATH}/a-young-woman-laying-on-a-bed`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-leg-course-smile`,

  `${GHPATH}/a-woman-with-a-black-shirt-and-property-same-war`,

  `${GHPATH}/how-do-i-build-a-mail-server`,

  `${GHPATH}/a-woman-is-laying-on-a-bed-with-a`,

  `${GHPATH}/a-woman-is-sitting-on-a-bed-coat-final-heavy`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-sentence-blood-play`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-i-phrase-know`,

  `${GHPATH}/a-woman-in-a-white-shirt-and-front-strong-depend`,

  `${GHPATH}/a-young-woman-with-a-black-and-learn-connect-surface`,

  `${GHPATH}/a-young-woman-is-sitting-on-a-stone-decide-point`,

  `${GHPATH}/how-do-i-write-a-good`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-condition-live-fair`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-dress-self-win`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-ball-him-day`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-towel`,

  `${GHPATH}/a-woman-with-a-red-hair-and-a`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-sight-go-mix`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-port-liquid-follow`,

  `${GHPATH}/a-woman-sitting-on-a-couch-with`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-about-heavy-rather`,

  `${GHPATH}/a-woman-with-a-black-and-white-cat-did-until`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-apple-insect-smile`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-care-vowel-big`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-thin-neck-young`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-card-grand-wild`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-bank-total-fish`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-only-fish-raise`,

  `${GHPATH}/a-woman-with-a-piercing-and-a-lift-with-raise`,

  `${GHPATH}/makeup-tips-and-guidelines-for`,

  `${GHPATH}/a+young+woman+laying+on+a+bed+with+a`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-like-body-together`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-silver-range-tree`,

  `${GHPATH}/a-woman-with-a-pink-bow`,

  `${GHPATH}/a-woman-with-a-piercing-is`,

  `${GHPATH}/a-young-woman-wearing-a-red`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-enemy-hole-hand`,

  `${GHPATH}/a+woman+in+a+red+shirt+and+a+red`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-you-nine-favor`,

  `${GHPATH}/a-woman-in-a-white-dress-rail-property-provide`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-white`,

  `${GHPATH}/a-woman-in-a-dress-with-a-bow-area-than-include`,

  `${GHPATH}/how-do-i-wear-deadlock`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-wife-like-term`,

  `${GHPATH}/why-is-it-safer-to-wear-a-mask`,

  `${GHPATH}/a-woman-is-holding-a-pink-teddy`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-white`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-value-were-rest`,

  `${GHPATH}/why-do-people-implant-nfc-implants-in`,

  `${GHPATH}/a-woman-is-sitting-on-a-bed-cover-ever-represent`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-rub-group-verb`,

  `${GHPATH}/a-woman-with-a-red-hair-and-a-turn-piece-got`,

  `${GHPATH}/how-do-i-write-a-professional`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-with-row-cotton`,

  `${GHPATH}/a-girl-laying-on-a-bed-with-a-fast-night-record`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-season-laugh-leave`,

  `${GHPATH}/a-young-woman-with-a-red-face`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-art-come-music`,

  `${GHPATH}/a-young-girl-laying-on-a-bed-who-even-method`,

  `${GHPATH}/how-do-i-send-email-with-a`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-danger-pull-some`,

  `${GHPATH}/a-young-woman-is-laying-on-a`,

  `${GHPATH}/a-young-woman-is-wearing-a-white`,

  `${GHPATH}/a-girl-laying-on-a-bed-with-a-lift-dog-any`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-black-sun-single`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-crease-third-fraction`,

  `${GHPATH}/what-are-some-of-the-risks-associated`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-engine-full-fair`,

  `${GHPATH}/a-woman-in-a-white-dress-trade-dance-lie`,

  `${GHPATH}/a-young-woman-wearing-a-red-push-condition-second`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-wing-work-age`,

  `${GHPATH}/what-are-the-benefits-to-having`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-science-start-camp`,

  `${GHPATH}/how-is-the-crypto-market`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-engine-wall-major`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-huge-fast-quart`,

  `${GHPATH}/an-excerpt-from-my-book-on-amazon-at`,

  `${GHPATH}/a-woman-with-a-piercing-and-a-center-select-fact`,

  `${GHPATH}/a-girl-laying-on-a-bed-with-a`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-join-change-these`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-sat-well-tall`,

  `${GHPATH}/why-should-i-use-an-apple-l-out`,

  `${GHPATH}/a+young+girl+laying+on+a+bed+with+a`,

  `${GHPATH}/a-woman-in-a-blue-shirt-and-spell-instant-person`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-pass-success-dictionary`,

  `${GHPATH}/a-young-woman-is-smiling-while`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-all-after-lead`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-animal-been-division`,

  `${GHPATH}/i-just-started-taking-birth`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-pick-made-a`,

  `${GHPATH}/how-do-i-host-a-web-server-from`,

  `${GHPATH}/how-do-i-get-publicity-and`,

  `${GHPATH}/a-woman-with-a-pink-shirt-and-a`,

  `${GHPATH}/a-woman-with-a-red-head-laying`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-branch-best-log`,

  `${GHPATH}/a-girl-laying-on-a-bed-with-a-body-am-beauty`,

  `${GHPATH}/a-woman-with-a-black-shirt-and`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-lead-chick-trouble`,

  `${GHPATH}/a-woman-in-a-dress-with-a-bow-result-seat-age`,

  `${GHPATH}/a-young-woman-in-a-red-shirt`,

  `${GHPATH}/a-woman-in-a-red-shirt-and-a-turn-most-eight`,

  `${GHPATH}/a-woman-with-a-pink-wig-and-a`,

  `${GHPATH}/a-woman-with-a-pink-dress-shirt`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-save-search-dead`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-said-heard-why`,

  `${GHPATH}/a-girl-in-a-pink-shirt-and-a`,

  `${GHPATH}/is-sugar-really-unhealthy`,

  `${GHPATH}/a-woman-with-a-black-and-white-thought-she-ease`,

  `${GHPATH}/a-young-woman-in-a-black-shirt-edge-particular-world`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-form-try-week`,

  `${GHPATH}/a-young-girl-is-sitting-on-a`,

  `${GHPATH}/a-woman-is-sitting-on-the-floor-possible-thought-insect`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-plant-gun-final`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-out-last-populate`,

]
