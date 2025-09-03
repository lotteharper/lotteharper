var GHPATH = '/';
// Choose a different app prefix name
var APP_PREFIX = 'glamgirlx_';
// The version of the cache. Every time you change any of the files
// you need to change this version (version_01, version_02…). 
// If you don't change the version, the service worker will give your
// users the old files!
var VERSION = 'version_01756433361.1935136';
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

  `${GHPATH}/practical-web-based-deep-learning-and`,

  `${GHPATH}/two-player-color-sudoku-online-free`,

  `${GHPATH}/spend-an-evening-with`,

  `${GHPATH}/play-color-sudoku-online-free`,

  `${GHPATH}/3d-printed-22lr-subcompact-pistol-cad`,

  `${GHPATH}/three-thirteen-online-free`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-wife-like-term`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-coat-final-heavy`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-stead-hair-get`,

  `${GHPATH}/the-image-shows-a-woman-lying-down-on`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-fill-time-dead`,

  `${GHPATH}/post-very-feet-else`,

  `${GHPATH}/the-photo-features-a-woman-with-curly`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-her-body-am-beauty`,

  `${GHPATH}/the-image-shows-a-woman-with-light`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-color-his-tiny`,

  `${GHPATH}/how-do-i-host-a-web-server-from-my`,

  `${GHPATH}/the-photo-shows-a-woman-with-short-your-jump-triangle`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-rail-property-provide`,

  `${GHPATH}/the-photo-features-a-woman-lying-on-a-huge-fast-quart`,

  `${GHPATH}/a-woman-in-a-white-shirt-and-black`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-dress-self-win`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-over-next-least`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-value-were-rest`,

  `${GHPATH}/this-photo-shows-a-woman-with-curly-long-system-often`,

  `${GHPATH}/this-photo-shows-a-woman-sitting-on-a-possible-thought-insect`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-about-heavy-rather`,

  `${GHPATH}/post-crop-chief-both`,

  `${GHPATH}/this-photo-shows-a-woman-lying-on-a-with-row-cotton`,

  `${GHPATH}/how-do-i-write-a-professional-blog`,

  `${GHPATH}/a-woman-is-laying-on-a-bed-with-a`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-father-sense-populate`,

  `${GHPATH}/how-do-i-write-a-good`,

  `${GHPATH}/this-photo-shows-a-woman-with-short-mix-skin-organ`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-engine-wall-major`,

  `${GHPATH}/the-image-shows-a-woman-lying-on-a-card-grand-wild`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-pass-success-dictionary`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-said-heard-why`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-property-same-war`,

  `${GHPATH}/the-photo-shows-a-woman-sitting-on-a-cover-ever-represent`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-center-select-fact`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-enemy-hole-hand`,

  `${GHPATH}/the-photo-shows-a-woman-sitting-on-a-can-iron-pound`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-sat-well-tall`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-thought-she-ease`,

  `${GHPATH}/the-photo-is-a-closeup-selfie-of-a`,

  `${GHPATH}/the-photo-shows-a-woman-with-short-minute-grow-took`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-horse-country-until`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-apple-insect-smile`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-stood-though-on`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-start-copy-you`,

  `${GHPATH}/is-sugar-really-unhealth`,

  `${GHPATH}/post-radio-bell-sea`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-animal-been-division`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-keep-big-foot`,

  `${GHPATH}/this-photo-shows-a-woman-lying-down-picture-plain-busy`,

  `${GHPATH}/this-photo-shows-a-woman-lying-on-a-mind-strange-rest`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-sight-go-mix`,

  `${GHPATH}/the-photo-shows-a-woman-with-short-cook-human-flat`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-like-body-together`,

  `${GHPATH}/why-should-i-use-an-apple-l-out-at`,

  `${GHPATH}/a-woman-is-laying-on-a-red`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-crease-third-fraction`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-thin-neck-young`,

  `${GHPATH}/a-woman-in-a-white-shirt-and-black-front-strong-depend`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on`,

  `${GHPATH}/this-photo-shows-a-woman-with-curly-turn-most-eight`,

  `${GHPATH}/how-do-i-find-customers-for-my-web`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-cat-did-until`,

  `${GHPATH}/the-photo-features-a-woman-lying-on-a`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-time-climb-small`,

  `${GHPATH}/whats-the-best-way-to-boil`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-in-fear-broke`,

  `${GHPATH}/i-just-started-taking-birth-control`,

  `${GHPATH}/this-photo-shows-a-woman-with-curly-whether-oh-machine`,

  `${GHPATH}/the-photo-is-a-closeup-selfie-of-a-case-stop-push`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-save-search-dead`,

  `${GHPATH}/post-have-five-room`,

  `${GHPATH}/why-is-it-safer-to-wear-a-mask-in`,

  `${GHPATH}/this-photo-shows-a-woman-lying-on-a-hunt-pose-dance`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-I-phrase-know`,

  `${GHPATH}/post-slave-both-ran`,

  `${GHPATH}/how-do-i-build-a-mail-server-with`,

  `${GHPATH}/this-photo-shows-a-woman-lying-down-fair-develop-has`,

  `${GHPATH}/a-woman-is-holding-a-pink-teddy`,

  `${GHPATH}/this-photo-shows-a-woman-lying-down-sentence-blood-play`,

  `${GHPATH}/post-know-when-bird`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-lift-with-raise`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-season-laugh-leave`,

  `${GHPATH}/makeup-tips-and-guidelines-for`,

  `${GHPATH}/this-photo-shows-a-woman-lying-on-a-wing-work-age`,

  `${GHPATH}/the-photo-shows-a-woman-with-light-spell-instant-person`,

  `${GHPATH}/this-photo-shows-a-woman-with-short-stone-decide-point`,

  `${GHPATH}/how-do-i-send-email-with-a-compliant`,

  `${GHPATH}/the-image-shows-a-woman-with-curly`,

  `${GHPATH}/why-do-people-implant-nfc-implants-in`,

  `${GHPATH}/the-image-shows-a-woman-lying-down-on-put-stretch-yellow`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-science-start-camp`,

  `${GHPATH}/how-is-the-crypto-market-growing-so`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-pink`,

  `${GHPATH}/the-photo-shows-a-woman-with-short-total-shore-begin`,

  `${GHPATH}/the-photo-shows-a-woman-taking-a`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-and-lift-double`,

  `${GHPATH}/a-woman-laying-on-a-bed-with-a-pink-condition-live-fair`,

  `${GHPATH}/this-photo-shows-a-woman-with-curly-show-own-event`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-form-try-week`,

  `${GHPATH}/this-photo-shows-a-woman-with-curly-result-seat-age`,

  `${GHPATH}/how-do-i-build-a-full-stack-web-app`,

  `${GHPATH}/what-causes-migraine-and-how-are-they`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-lift-dog-any`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-number-machine-felt`,

  `${GHPATH}/how-do-i-wear-deadloc`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-six-unit-help`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-trade-dance-lie`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-bank-total-fish`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-pound-match-ready`,

  `${GHPATH}/post-division-stop-team`,

  `${GHPATH}/the-photo-shows-a-woman-with-short-end-at-station`,

  `${GHPATH}/a-woman-with-a-red-hair-and-a-red`,

  `${GHPATH}/an-excerpt-from-my-book-on-amazon-at`,

  `${GHPATH}/a-girl-laying-on-a-bed-with-a-pink`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-engine-full-fair`,

  `${GHPATH}/what-are-the-benefits-to-having-a`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-branch-best-log`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-black-sun-single`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-her`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-nothing-answer-ten`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-deal-where-island`,

  `${GHPATH}/the-photo-shows-a-woman-with-fair`,

  `${GHPATH}/this-photo-shows-a-woman-wearing-a`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-her-bread-gray-claim`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-eight-women-whose`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-plant-gun-final`,

  `${GHPATH}/post-cat-post-liquid`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-area-than-include`,

  `${GHPATH}/the-photo-shows-a-young-woman-with`,

  `${GHPATH}/a-young-woman-is-smiling-while`,

  `${GHPATH}/this-photo-shows-a-woman-sitting-on-a`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-join-change-these`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-art-come-music`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-lead-chick-trouble`,

  `${GHPATH}/the-photo-shows-a-woman-with-curly-three-draw-subject`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-leg-course-smile`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-group-sense-depend`,

  `${GHPATH}/post-thought-life-found`,

  `${GHPATH}/post-shell-nothing-story`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-fast-night-record`,

  `${GHPATH}/what-are-some-of-the-risks-associated`,

  `${GHPATH}/this-photo-shows-a-woman-lying-on-a-old-written-land`,

  `${GHPATH}/the-photo-shows-a-woman-with-short-farm-mine-ice`,

  `${GHPATH}/the-photo-shows-a-woman-sitting-on-a-skill-lift-this`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-rub-group-verb`,

  `${GHPATH}/this-photo-shows-a-woman-lying-down-sugar-arrange-speak`,

  `${GHPATH}/the-photo-shows-a-woman-lying-on-a-port-liquid-follow`,

  `${GHPATH}/the-photo-shows-a-woman-lying-down-on-you-nine-favor`,

  `${GHPATH}/how-do-i-get-publicity-and-organic`,

]
