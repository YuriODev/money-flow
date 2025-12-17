/**
 * Service Icon Library
 *
 * Provides brand colors, icons, and metadata for popular subscription services.
 * Icons are sourced from SimpleIcons (via CDN) for consistency.
 */

export interface ServiceInfo {
  name: string;
  color: string;
  icon: string; // SimpleIcons slug or empty string for fallback
  iconUrl?: string; // Custom icon URL (e.g., Brandfetch)
  category: string;
  aliases: string[]; // Alternative names to match
}

/**
 * Popular subscription services database.
 * Colors are official brand colors.
 * Icons use SimpleIcons slugs for CDN URLs.
 */
export const SERVICES: Record<string, ServiceInfo> = {
  // Streaming - Video
  netflix: {
    name: "Netflix",
    color: "#E50914",
    icon: "netflix",
    category: "streaming",
    aliases: ["netflix"],
  },
  disneyplus: {
    name: "Disney+",
    color: "#113CCF",
    icon: "disneyplus",
    category: "streaming",
    aliases: ["disney+", "disney plus", "disneyplus"],
  },
  hulu: {
    name: "Hulu",
    color: "#1CE783",
    icon: "hulu",
    category: "streaming",
    aliases: ["hulu"],
  },
  primevideo: {
    name: "Prime Video",
    color: "#00A8E1",
    icon: "primevideo",
    category: "streaming",
    aliases: ["prime video", "amazon prime", "primevideo", "amazon video"],
  },
  hbomax: {
    name: "HBO Max",
    color: "#5822B4",
    icon: "hbo",
    category: "streaming",
    aliases: ["hbo max", "hbomax", "hbo", "max"],
  },
  appletv: {
    name: "Apple TV+",
    color: "#000000",
    icon: "appletv",
    category: "streaming",
    aliases: ["apple tv", "appletv", "apple tv+", "appletv+"],
  },
  youtube: {
    name: "YouTube Premium",
    color: "#FF0000",
    icon: "youtube",
    category: "streaming",
    aliases: ["youtube", "youtube premium", "yt premium"],
  },
  peacock: {
    name: "Peacock",
    color: "#000000",
    icon: "peacock",
    category: "streaming",
    aliases: ["peacock", "peacock tv"],
  },
  paramount: {
    name: "Paramount+",
    color: "#0064FF",
    icon: "paramount",
    category: "streaming",
    aliases: ["paramount", "paramount+", "paramount plus"],
  },
  crunchyroll: {
    name: "Crunchyroll",
    color: "#F47521",
    icon: "crunchyroll",
    category: "streaming",
    aliases: ["crunchyroll"],
  },

  // Streaming - Music
  spotify: {
    name: "Spotify",
    color: "#1DB954",
    icon: "spotify",
    category: "music",
    aliases: ["spotify"],
  },
  applemusic: {
    name: "Apple Music",
    color: "#FA243C",
    icon: "applemusic",
    category: "music",
    aliases: ["apple music", "applemusic"],
  },
  tidal: {
    name: "Tidal",
    color: "#000000",
    icon: "tidal",
    category: "music",
    aliases: ["tidal"],
  },
  deezer: {
    name: "Deezer",
    color: "#FEAA2D",
    icon: "deezer",
    category: "music",
    aliases: ["deezer"],
  },
  amazonmusic: {
    name: "Amazon Music",
    color: "#00A8E1",
    icon: "amazonmusic",
    category: "music",
    aliases: ["amazon music", "amazonmusic"],
  },
  soundcloud: {
    name: "SoundCloud",
    color: "#FF5500",
    icon: "soundcloud",
    category: "music",
    aliases: ["soundcloud"],
  },
  youtubemusic: {
    name: "YouTube Music",
    color: "#FF0000",
    icon: "youtubemusic",
    category: "music",
    aliases: ["youtube music", "youtubemusic", "yt music"],
  },

  // Gaming
  xbox: {
    name: "Xbox Game Pass",
    color: "#107C10",
    icon: "xbox",
    category: "gaming",
    aliases: ["xbox", "xbox game pass", "game pass", "gamepass"],
  },
  playstation: {
    name: "PlayStation Plus",
    color: "#003791",
    icon: "playstation",
    category: "gaming",
    aliases: ["playstation", "ps plus", "psplus", "playstation plus", "ps+"],
  },
  nintendoswitch: {
    name: "Nintendo Switch Online",
    color: "#E60012",
    icon: "nintendoswitch",
    category: "gaming",
    aliases: ["nintendo", "nintendo switch", "switch online"],
  },
  steam: {
    name: "Steam",
    color: "#000000",
    icon: "steam",
    category: "gaming",
    aliases: ["steam"],
  },
  epicgames: {
    name: "Epic Games",
    color: "#313131",
    icon: "epicgames",
    category: "gaming",
    aliases: ["epic games", "epic"],
  },
  twitch: {
    name: "Twitch",
    color: "#9146FF",
    icon: "twitch",
    category: "gaming",
    aliases: ["twitch"],
  },
  geforce: {
    name: "GeForce Now",
    color: "#76B900",
    icon: "nvidia",
    category: "gaming",
    aliases: ["geforce now", "nvidia", "geforce"],
  },

  // Cloud & Productivity
  microsoft365: {
    name: "Microsoft 365",
    color: "#D83B01",
    icon: "microsoft",
    category: "productivity",
    aliases: ["microsoft 365", "office 365", "microsoft", "office", "m365"],
  },
  googleone: {
    name: "Google One",
    color: "#4285F4",
    icon: "",
    iconUrl: "https://logo.clearbit.com/google.com",
    category: "productivity",
    aliases: ["google one", "googleone", "google drive", "gdrive", "google one storage"],
  },
  googleworkspace: {
    name: "Google Workspace",
    color: "#4285F4",
    icon: "",
    iconUrl: "https://logo.clearbit.com/google.com",
    category: "business",
    aliases: ["google workspace", "googleworkspace", "gsuite", "g suite", "google workspace business", "google workspace business standard"],
  },
  googledomains: {
    name: "Google Domains",
    color: "#4285F4",
    icon: "",
    iconUrl: "https://logo.clearbit.com/google.com",
    category: "business",
    aliases: ["google domains", "googledomains", "domain registration", "domain"],
  },
  icloud: {
    name: "iCloud+",
    color: "#3693F3",
    icon: "icloud",
    category: "productivity",
    aliases: ["icloud", "icloud+"],
  },
  dropbox: {
    name: "Dropbox",
    color: "#0061FF",
    icon: "dropbox",
    category: "productivity",
    aliases: ["dropbox"],
  },
  notion: {
    name: "Notion",
    color: "#000000",
    icon: "notion",
    category: "productivity",
    aliases: ["notion"],
  },
  evernote: {
    name: "Evernote",
    color: "#00A82D",
    icon: "evernote",
    category: "productivity",
    aliases: ["evernote"],
  },
  slack: {
    name: "Slack",
    color: "#4A154B",
    icon: "slack",
    category: "productivity",
    aliases: ["slack"],
  },
  zoom: {
    name: "Zoom",
    color: "#2D8CFF",
    icon: "zoom",
    category: "productivity",
    aliases: ["zoom"],
  },
  figma: {
    name: "Figma",
    color: "#F24E1E",
    icon: "figma",
    category: "productivity",
    aliases: ["figma"],
  },
  canva: {
    name: "Canva",
    color: "#00C4CC",
    icon: "canva",
    category: "productivity",
    aliases: ["canva"],
  },

  // Development
  github: {
    name: "GitHub",
    color: "#181717",
    icon: "github",
    category: "development",
    aliases: ["github", "github pro", "github copilot"],
  },
  gitlab: {
    name: "GitLab",
    color: "#FC6D26",
    icon: "gitlab",
    category: "development",
    aliases: ["gitlab"],
  },
  jetbrains: {
    name: "JetBrains",
    color: "#000000",
    icon: "jetbrains",
    category: "development",
    aliases: ["jetbrains", "intellij", "pycharm", "webstorm"],
  },
  vercel: {
    name: "Vercel",
    color: "#000000",
    icon: "vercel",
    category: "development",
    aliases: ["vercel"],
  },
  netlify: {
    name: "Netlify",
    color: "#00C7B7",
    icon: "netlify",
    category: "development",
    aliases: ["netlify"],
  },
  digitalocean: {
    name: "DigitalOcean",
    color: "#0080FF",
    icon: "digitalocean",
    category: "development",
    aliases: ["digitalocean", "digital ocean"],
  },
  aws: {
    name: "AWS",
    color: "#232F3E",
    icon: "amazonaws",
    category: "development",
    aliases: ["aws", "amazon web services"],
  },
  heroku: {
    name: "Heroku",
    color: "#430098",
    icon: "heroku",
    category: "development",
    aliases: ["heroku"],
  },

  // Security & VPN
  nordvpn: {
    name: "NordVPN",
    color: "#4687FF",
    icon: "nordvpn",
    category: "security",
    aliases: ["nordvpn", "nord vpn"],
  },
  expressvpn: {
    name: "ExpressVPN",
    color: "#DA3940",
    icon: "expressvpn",
    category: "security",
    aliases: ["expressvpn", "express vpn"],
  },
  surfshark: {
    name: "Surfshark",
    color: "#178BF1",
    icon: "surfshark",
    category: "security",
    aliases: ["surfshark"],
  },
  onepassword: {
    name: "1Password",
    color: "#0094F5",
    icon: "1password",
    category: "security",
    aliases: ["1password", "one password", "onepassword"],
  },
  lastpass: {
    name: "LastPass",
    color: "#D32D27",
    icon: "lastpass",
    category: "security",
    aliases: ["lastpass", "last pass"],
  },
  bitwarden: {
    name: "Bitwarden",
    color: "#175DDC",
    icon: "bitwarden",
    category: "security",
    aliases: ["bitwarden"],
  },

  // Health & Fitness
  peloton: {
    name: "Peloton",
    color: "#000000",
    icon: "peloton",
    category: "fitness",
    aliases: ["peloton"],
  },
  strava: {
    name: "Strava",
    color: "#FC4C02",
    icon: "strava",
    category: "fitness",
    aliases: ["strava"],
  },
  myfitnesspal: {
    name: "MyFitnessPal",
    color: "#0066CC",
    icon: "myfitnesspal",
    category: "fitness",
    aliases: ["myfitnesspal", "my fitness pal"],
  },
  headspace: {
    name: "Headspace",
    color: "#F47D31",
    icon: "headspace",
    category: "fitness",
    aliases: ["headspace"],
  },
  calm: {
    name: "Calm",
    color: "#6BBECD",
    icon: "calm",
    category: "fitness",
    aliases: ["calm"],
  },
  flo: {
    name: "Flo",
    color: "#FF6B9D",
    icon: "",
    iconUrl: "https://logo.clearbit.com/flo.health",
    category: "health",
    aliases: ["flo", "flo health", "flo app", "flo period tracker", "flo cycle", "flo cycle tracker", "flo cycle & period tracker"],
  },

  // Shopping & Delivery
  amazon: {
    name: "Amazon Prime",
    color: "#FF9900",
    icon: "amazonprime",
    category: "shopping",
    aliases: ["amazon", "amazon prime"],
  },
  costco: {
    name: "Costco",
    color: "#E31837",
    icon: "costco",
    category: "shopping",
    aliases: ["costco"],
  },
  instacart: {
    name: "Instacart",
    color: "#43B02A",
    icon: "instacart",
    category: "shopping",
    aliases: ["instacart"],
  },
  doordash: {
    name: "DoorDash",
    color: "#FF3008",
    icon: "doordash",
    category: "shopping",
    aliases: ["doordash", "door dash"],
  },
  ubereats: {
    name: "Uber Eats",
    color: "#06C167",
    icon: "ubereats",
    category: "shopping",
    aliases: ["uber eats", "ubereats"],
  },

  // News & Media
  nytimes: {
    name: "NY Times",
    color: "#000000",
    icon: "",
    iconUrl: "https://logo.clearbit.com/nytimes.com",
    category: "news",
    aliases: ["nytimes", "new york times", "ny times"],
  },
  washingtonpost: {
    name: "Washington Post",
    color: "#000000",
    icon: "washingtonpost",
    category: "news",
    aliases: ["washington post", "washingtonpost", "wapo"],
  },
  medium: {
    name: "Medium",
    color: "#000000",
    icon: "medium",
    category: "news",
    aliases: ["medium", "medium membership"],
  },
  substack: {
    name: "Substack",
    color: "#FF6719",
    icon: "substack",
    category: "news",
    aliases: ["substack"],
  },

  // Education
  skillshare: {
    name: "Skillshare",
    color: "#00FF84",
    icon: "skillshare",
    category: "education",
    aliases: ["skillshare"],
  },
  masterclass: {
    name: "MasterClass",
    color: "#000000",
    icon: "masterclass",
    category: "education",
    aliases: ["masterclass", "master class"],
  },
  coursera: {
    name: "Coursera",
    color: "#0056D2",
    icon: "coursera",
    category: "education",
    aliases: ["coursera"],
  },
  udemy: {
    name: "Udemy",
    color: "#A435F0",
    icon: "udemy",
    category: "education",
    aliases: ["udemy"],
  },
  duolingo: {
    name: "Duolingo",
    color: "#58CC02",
    icon: "duolingo",
    category: "education",
    aliases: ["duolingo"],
  },

  // AI & Tools
  chatgpt: {
    name: "ChatGPT Plus",
    color: "#10A37F",
    icon: "openai",
    category: "ai",
    aliases: ["chatgpt", "openai", "gpt plus", "chatgpt plus"],
  },
  claude: {
    name: "Claude Pro",
    color: "#D97757",
    icon: "anthropic",
    category: "ai",
    aliases: ["claude", "anthropic", "claude pro", "claude.ai", "claude ai"],
  },
  midjourney: {
    name: "Midjourney",
    color: "#000000",
    icon: "midjourney",
    category: "ai",
    aliases: ["midjourney", "mid journey"],
  },
  grammarly: {
    name: "Grammarly",
    color: "#15C39A",
    icon: "grammarly",
    category: "ai",
    aliases: ["grammarly"],
  },

  // Finance & Banking
  emma: {
    name: "Emma",
    color: "#5B5FC7",
    icon: "", // No SimpleIcon available - will use fallback
    category: "finance",
    aliases: ["emma", "emma app"],
  },
  revolut: {
    name: "Revolut Premium",
    color: "#0666EB",
    icon: "revolut",
    category: "finance",
    aliases: ["revolut", "revolut premium", "revolut plus", "revolut metal"],
  },
  monzo: {
    name: "Monzo",
    color: "#FF4F5A",
    icon: "monzo",
    category: "finance",
    aliases: ["monzo", "monzo plus", "monzo premium"],
  },

  // Automation & Development Tools
  make: {
    name: "Make",
    color: "#6D00CC",
    icon: "make",
    category: "automation",
    aliases: ["make", "integromat", "make.com", "automation"],
  },
  zapier: {
    name: "Zapier",
    color: "#FF4A00",
    icon: "zapier",
    category: "automation",
    aliases: ["zapier"],
  },
  overleaf: {
    name: "Overleaf",
    color: "#47A141",
    icon: "overleaf",
    category: "productivity",
    aliases: ["overleaf", "writelatex", "latex"],
  },
  eraser: {
    name: "Eraser",
    color: "#5865F2",
    icon: "",
    iconUrl: "https://logo.clearbit.com/eraser.io",
    category: "productivity",
    aliases: ["eraser", "eraser.io"],
  },

  // Notes & Writing Apps
  goodnotes: {
    name: "Goodnotes",
    color: "#F4B400",
    icon: "",
    iconUrl: "https://logo.clearbit.com/goodnotes.com",
    category: "productivity",
    aliases: ["goodnotes", "goodnotes 6", "good notes", "goodnotes 5"],
  },
  notability: {
    name: "Notability",
    color: "#36C1AF",
    icon: "",
    iconUrl: "https://logo.clearbit.com/notability.com",
    category: "productivity",
    aliases: ["notability"],
  },
  bear: {
    name: "Bear",
    color: "#E74F4F",
    icon: "",
    iconUrl: "https://logo.clearbit.com/bear.app",
    category: "productivity",
    aliases: ["bear", "bear notes", "bear app"],
  },
  obsidian: {
    name: "Obsidian",
    color: "#7C3AED",
    icon: "obsidian",
    category: "productivity",
    aliases: ["obsidian", "obsidian md"],
  },
  roam: {
    name: "Roam Research",
    color: "#336DFF",
    icon: "",
    iconUrl: "https://logo.clearbit.com/roamresearch.com",
    category: "productivity",
    aliases: ["roam", "roam research"],
  },

  // Cloud & Hosting
  hetzner: {
    name: "Hetzner",
    color: "#D50C2D",
    icon: "hetzner",
    category: "development",
    aliases: ["hetzner", "hetzner cloud"],
  },
  linode: {
    name: "Linode",
    color: "#00A95C",
    icon: "linode",
    category: "development",
    aliases: ["linode", "akamai"],
  },

  // Social & Communication
  linkedin: {
    name: "LinkedIn Premium",
    color: "#0A66C2",
    icon: "",
    iconUrl: "https://logo.clearbit.com/linkedin.com",
    category: "social",
    aliases: ["linkedin", "linkedin premium", "linkedin learning"],
  },
  telegram: {
    name: "Telegram Premium",
    color: "#26A5E4",
    icon: "telegram",
    category: "social",
    aliases: ["telegram", "telegram premium"],
  },
  discord: {
    name: "Discord Nitro",
    color: "#5865F2",
    icon: "discord",
    category: "social",
    aliases: ["discord", "discord nitro", "nitro"],
  },

  // Apple Services
  applecare: {
    name: "AppleCare+",
    color: "#000000",
    icon: "apple",
    category: "insurance",
    aliases: ["applecare", "applecare+", "apple care", "applecare+ iphone", "applecare+ ipad", "applecare+ for mac", "ac+ for mac", "ac+", "ac+ for mac mini"],
  },
  appleone: {
    name: "Apple One",
    color: "#000000",
    icon: "apple",
    category: "streaming",
    aliases: ["apple one", "appleone"],
  },

  // News & Games
  nytgames: {
    name: "NYT Games",
    color: "#000000",
    icon: "",
    iconUrl: "https://logo.clearbit.com/nytimes.com",
    category: "entertainment",
    aliases: ["nyt games", "nytimes games", "ny times games", "wordle", "nyt crossword"],
  },
  guardian: {
    name: "The Guardian",
    color: "#052962",
    icon: "theguardian",
    category: "news",
    aliases: ["guardian", "the guardian"],
  },

  // Fitness & Gyms
  betterleisure: {
    name: "Better Leisure",
    color: "#00A651",
    icon: "",
    iconUrl: "https://logo.clearbit.com/better.org.uk",
    category: "fitness",
    aliases: ["better leisure", "better gym", "better", "gll", "better leisure gym"],
  },
  puregym: {
    name: "PureGym",
    color: "#FFCC00",
    icon: "", // No SimpleIcon - will use fallback
    category: "fitness",
    aliases: ["puregym", "pure gym"],
  },
  thegym: {
    name: "The Gym Group",
    color: "#FF6B00",
    icon: "", // No SimpleIcon - will use fallback
    category: "fitness",
    aliases: ["the gym", "gym group", "the gym group"],
  },
  davidlloyd: {
    name: "David Lloyd",
    color: "#003366",
    icon: "", // No SimpleIcon - will use fallback
    category: "fitness",
    aliases: ["david lloyd", "davidlloyd"],
  },
  virginactive: {
    name: "Virgin Active",
    color: "#ED1C24",
    icon: "virgin", // Virgin brand icon exists
    category: "fitness",
    aliases: ["virgin active", "virgin gym"],
  },
  gym: {
    name: "Gym",
    color: "#6366F1",
    icon: "",
    iconUrl: "https://cdn-icons-png.flaticon.com/512/2964/2964514.png",
    category: "fitness",
    aliases: ["gym", "gym membership", "gym sessions", "fitness gym", "local gym"],
  },

  // Health & Wellness
  therapy: {
    name: "Therapy Sessions",
    color: "#7C3AED",
    icon: "",
    iconUrl: "https://cdn-icons-png.flaticon.com/512/3997/3997872.png",
    category: "health",
    aliases: ["therapy", "therapy sessions", "therapy session", "counselling", "counseling", "therapist", "psychologist"],
  },
  personalcoach: {
    name: "Personal Coach",
    color: "#F59E0B",
    icon: "",
    iconUrl: "https://cdn-icons-png.flaticon.com/512/2936/2936886.png",
    category: "health",
    aliases: ["personal coach", "coach", "personal trainer", "pt", "fitness coach", "life coach", "online coach"],
  },
  bupa: {
    name: "Bupa",
    color: "#0075C9",
    icon: "",
    iconUrl: "https://logo.clearbit.com/bupa.co.uk",
    category: "insurance",
    aliases: ["bupa", "bupa health", "bupa health insurance", "bupa insurance"],
  },
  healthinsurance: {
    name: "Health Insurance",
    color: "#10B981",
    icon: "", // No SimpleIcon - will use fallback
    category: "insurance",
    aliases: ["health insurance", "medical insurance", "private health", "vitality", "axa health"],
  },
  dentalplan: {
    name: "Dental Plan",
    color: "#06B6D4",
    icon: "", // No SimpleIcon - will use fallback
    category: "insurance",
    aliases: ["dental", "dental plan", "dentist", "dental insurance"],
  },

  // Storage Services
  googlestorage: {
    name: "Google Storage",
    color: "#4285F4",
    icon: "googledrive",
    category: "productivity",
    aliases: ["google storage", "google drive storage"],
  },

  // UK Utilities
  edf: {
    name: "EDF",
    color: "#FF6B00",
    icon: "",
    iconUrl: "https://logo.clearbit.com/edfenergy.com",
    category: "utilities",
    aliases: ["edf", "edf energy", "edf electricity", "edf gas", "edf debt", "edf debt repayment", "edf repayment"],
  },
  thameswater: {
    name: "Thames Water",
    color: "#00A3E0",
    icon: "",
    iconUrl: "https://logo.clearbit.com/thameswater.co.uk",
    category: "utilities",
    aliases: ["thames water", "thames", "water bill", "thames water"],
  },
  counciltax: {
    name: "Council Tax",
    color: "#1E3A5F",
    icon: "",
    category: "utilities",
    aliases: ["council tax", "council", "local council", "lambeth council", "croydon council", "croydon council tax"],
  },

  // UK Gyms & Leisure
  activelambeth: {
    name: "Active Lambeth",
    color: "#00A651",
    icon: "",
    iconUrl: "https://logo.clearbit.com/better.org.uk",
    category: "fitness",
    aliases: ["active lambeth", "lambeth leisure", "lambeth gym", "active lambeth gym", "lambeth fitness"],
  },

  // Housing
  rent: {
    name: "Rent",
    color: "#4F46E5",
    icon: "",
    iconUrl: "https://cdn-icons-png.flaticon.com/512/2544/2544087.png",
    category: "housing",
    aliases: ["rent", "rent payment", "room rent", "flat rent", "apartment rent", "rent - room share", "room share"],
  },

  // Legal Services
  barrister: {
    name: "Barrister",
    color: "#1E3A8A",
    icon: "",
    iconUrl: "https://cdn-icons-png.flaticon.com/512/3122/3122799.png",
    category: "legal",
    aliases: ["barrister", "lawyer", "solicitor", "legal", "court", "hearing", "conference", "chris barnes"],
  },

  // Debt Collection
  equita: {
    name: "Equita",
    color: "#1A5F4A",
    icon: "",
    iconUrl: "https://logo.clearbit.com/equita.co.uk",
    category: "debt",
    aliases: ["equita", "equita debt", "debt collector", "council tax debt", "bailiff"],
  },

  // Utilities & Telecom
  vodafone: {
    name: "Vodafone",
    color: "#E60000",
    icon: "vodafone",
    category: "utilities",
    aliases: ["vodafone", "vodafone uk"],
  },
  virginmedia: {
    name: "Virgin Media",
    color: "#ED1C24",
    icon: "virginmedia",
    category: "utilities",
    aliases: ["virgin media", "virgin", "virgin broadband"],
  },
  bt: {
    name: "BT",
    color: "#5514B4",
    icon: "bt",
    category: "utilities",
    aliases: ["bt", "bt broadband", "british telecom"],
  },
  ee: {
    name: "EE",
    color: "#007B85",
    icon: "ee",
    category: "utilities",
    aliases: ["ee", "ee mobile"],
  },
  o2: {
    name: "O2",
    color: "#002F6C",
    icon: "o2",
    category: "utilities",
    aliases: ["o2", "o2 mobile"],
  },
  three: {
    name: "Three",
    color: "#000000",
    icon: "three",
    category: "utilities",
    aliases: ["three", "3 mobile", "three mobile"],
  },

  // Ukrainian Banking - Monobank
  monobank: {
    name: "Monobank",
    color: "#000000",
    icon: "",
    iconUrl: "https://logo.clearbit.com/monobank.ua",
    category: "finance",
    aliases: ["monobank", "mono", "монобанк"],
  },
  monobankplatinum: {
    name: "Monobank Platinum",
    color: "#1A1A1A",
    icon: "",
    iconUrl: "https://logo.clearbit.com/monobank.ua",
    category: "finance",
    aliases: [
      "monobank platinum",
      "mono platinum",
      "platinum card",
      "monobank platinum card",
      "платинова картка",
      "обслуговування платинової картки",
    ],
  },
  monobankinstallment: {
    name: "Monobank Installment",
    color: "#4CD964",
    icon: "",
    iconUrl: "https://logo.clearbit.com/monobank.ua",
    category: "finance",
    aliases: [
      "monobank credit",
      "mono credit",
      "monobank installment",
      "частинами",
      "оплата частинами",
      "кредит",
      "розстрочка",
    ],
  },

  // Ukrainian Banking - PrivatBank
  privatbank: {
    name: "PrivatBank",
    color: "#78BE20",
    icon: "",
    iconUrl: "https://logo.clearbit.com/privatbank.ua",
    category: "finance",
    aliases: ["privatbank", "приватбанк", "privat"],
  },

  // Buy Now Pay Later - Klarna
  klarna: {
    name: "Klarna",
    color: "#FFB3C7",
    icon: "klarna",
    category: "shopping",
    aliases: ["klarna", "klarna pay in 3", "klarna pay later", "klarna - desktronic", "klarna - lge uk", "klarna - puma", "klarna - boohoo"],
  },

  // UK Banking - Lloyds
  lloyds: {
    name: "Lloyds Bank",
    color: "#006A4D",
    icon: "",
    iconUrl: "https://logo.clearbit.com/lloydsbank.com",
    category: "finance",
    aliases: ["lloyds", "lloyds bank", "lloyds bank debt"],
  },

  // UK Banking - Airwallex
  airwallex: {
    name: "Airwallex",
    color: "#EE2E24",
    icon: "",
    iconUrl: "https://logo.clearbit.com/airwallex.com",
    category: "finance",
    aliases: ["airwallex", "deel"],
  },

  // Payment Provider - PayPal
  paypal: {
    name: "PayPal",
    color: "#00457C",
    icon: "paypal",
    category: "finance",
    aliases: ["paypal", "paypal debt"],
  },
};

/**
 * Get the SimpleIcons CDN URL for a service icon
 * Uses cdn.simpleicons.org which serves properly colored SVGs
 */
export function getIconUrl(iconSlug: string, color?: string): string {
  // Use cdn.simpleicons.org for pre-colored icons
  // This serves colored SVGs directly without needing CSS filters
  if (color) {
    const hexColor = color.replace("#", "");
    return `https://cdn.simpleicons.org/${iconSlug}/${hexColor}`;
  }
  // Default to white icons for dark mode compatibility
  return `https://cdn.simpleicons.org/${iconSlug}/white`;
}

/**
 * Get the SimpleIcons CDN URL with a specific color
 */
export function getIconUrlWithColor(iconSlug: string, color: string): string {
  const hexColor = color.replace("#", "");
  return `https://cdn.simpleicons.org/${iconSlug}/${hexColor}`;
}

/**
 * Check if a string contains a word as a whole word (not as a substring of another word)
 * e.g., "edf debt repayment" contains word "edf" but not "bt" (even though "debt" contains "bt")
 */
function containsWord(text: string, word: string): boolean {
  // Create a regex that matches the word with word boundaries
  // For short words (1-2 chars), require exact word match
  // For longer words (3+), allow as substring of longer words
  const escaped = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  if (word.length <= 2) {
    // Short words must be whole words
    const regex = new RegExp(`\\b${escaped}\\b`, 'i');
    return regex.test(text);
  }
  // Longer words can match as substrings (e.g., "netflix" in "netflix premium")
  return text.includes(word);
}

/**
 * Find a service by name (case-insensitive, alias matching)
 */
export function findService(name: string): ServiceInfo | null {
  const normalized = name.toLowerCase().trim();

  // Direct match by key
  if (SERVICES[normalized]) {
    return SERVICES[normalized];
  }

  // Search by exact alias match
  for (const [, service] of Object.entries(SERVICES)) {
    if (service.aliases.some((alias) => alias.toLowerCase() === normalized)) {
      return service;
    }
  }

  // Check if name contains any alias (e.g., "Amazon Prime" contains "amazon")
  // Sort by alias length descending to match longer aliases first
  const allServices = Object.entries(SERVICES)
    .map(([key, service]) => ({
      key,
      service,
      maxAliasLen: Math.max(...service.aliases.map(a => a.length))
    }))
    .sort((a, b) => b.maxAliasLen - a.maxAliasLen);

  for (const { service } of allServices) {
    // Check if name contains the service name (as whole word for short names)
    if (containsWord(normalized, service.name.toLowerCase())) {
      return service;
    }
    // Check if name contains any alias (as whole word for short aliases)
    for (const alias of service.aliases) {
      if (containsWord(normalized, alias.toLowerCase())) {
        return service;
      }
    }
  }

  // Reverse check: if any alias contains the name (for short names)
  for (const [, service] of Object.entries(SERVICES)) {
    if (
      containsWord(service.name.toLowerCase(), normalized) ||
      service.aliases.some((alias) => containsWord(alias.toLowerCase(), normalized))
    ) {
      return service;
    }
  }

  return null;
}

/**
 * Get service info with icon URL
 */
export function getServiceWithIcon(
  name: string
): (ServiceInfo & { iconUrl: string }) | null {
  const service = findService(name);
  if (!service) return null;

  return {
    ...service,
    iconUrl: getIconUrl(service.icon),
  };
}

/**
 * Get all services in a category
 */
export function getServicesByCategory(category: string): ServiceInfo[] {
  return Object.values(SERVICES).filter(
    (service) => service.category === category
  );
}

/**
 * Get all available categories
 */
export function getCategories(): string[] {
  return [...new Set(Object.values(SERVICES).map((s) => s.category))];
}

/**
 * Category display names and colors
 */
export const CATEGORY_INFO: Record<
  string,
  { label: string; color: string; gradient: string }
> = {
  streaming: {
    label: "Streaming",
    color: "#E50914",
    gradient: "from-red-500 to-orange-500",
  },
  music: {
    label: "Music",
    color: "#1DB954",
    gradient: "from-green-500 to-emerald-500",
  },
  gaming: {
    label: "Gaming",
    color: "#9146FF",
    gradient: "from-purple-500 to-violet-500",
  },
  productivity: {
    label: "Productivity",
    color: "#0066FF",
    gradient: "from-blue-500 to-cyan-500",
  },
  development: {
    label: "Development",
    color: "#F05032",
    gradient: "from-orange-500 to-red-500",
  },
  security: {
    label: "Security",
    color: "#4687FF",
    gradient: "from-blue-500 to-indigo-500",
  },
  fitness: {
    label: "Health & Fitness",
    color: "#FF5722",
    gradient: "from-orange-500 to-pink-500",
  },
  shopping: {
    label: "Shopping",
    color: "#FF9900",
    gradient: "from-yellow-500 to-orange-500",
  },
  news: {
    label: "News & Media",
    color: "#333333",
    gradient: "from-gray-600 to-gray-800",
  },
  education: {
    label: "Education",
    color: "#0056D2",
    gradient: "from-blue-600 to-purple-500",
  },
  ai: {
    label: "AI Tools",
    color: "#10A37F",
    gradient: "from-emerald-500 to-teal-500",
  },
  finance: {
    label: "Finance & Banking",
    color: "#0666EB",
    gradient: "from-blue-500 to-indigo-600",
  },
  automation: {
    label: "Automation",
    color: "#6D00CC",
    gradient: "from-purple-600 to-violet-500",
  },
  social: {
    label: "Social & Communication",
    color: "#0A66C2",
    gradient: "from-blue-500 to-cyan-500",
  },
  insurance: {
    label: "Insurance",
    color: "#10B981",
    gradient: "from-emerald-500 to-green-500",
  },
  health: {
    label: "Health & Wellness",
    color: "#7C3AED",
    gradient: "from-purple-500 to-pink-500",
  },
  entertainment: {
    label: "Entertainment",
    color: "#F59E0B",
    gradient: "from-amber-500 to-orange-500",
  },
  utilities: {
    label: "Utilities",
    color: "#6366F1",
    gradient: "from-indigo-500 to-violet-500",
  },
  business: {
    label: "Business",
    color: "#059669",
    gradient: "from-emerald-500 to-teal-500",
  },
  storage: {
    label: "Storage",
    color: "#3B82F6",
    gradient: "from-blue-500 to-sky-500",
  },
  communication: {
    label: "Communication",
    color: "#06B6D4",
    gradient: "from-cyan-500 to-teal-500",
  },
  financial: {
    label: "Financial",
    color: "#0666EB",
    gradient: "from-blue-500 to-indigo-600",
  },
  technology: {
    label: "Technology",
    color: "#8B5CF6",
    gradient: "from-violet-500 to-purple-500",
  },
  hosting: {
    label: "Hosting",
    color: "#DC2626",
    gradient: "from-red-500 to-orange-500",
  },
  housing: {
    label: "Housing",
    color: "#4F46E5",
    gradient: "from-indigo-500 to-purple-500",
  },
  debt: {
    label: "Debt",
    color: "#EF4444",
    gradient: "from-red-500 to-rose-500",
  },
  legal: {
    label: "Legal",
    color: "#1E3A8A",
    gradient: "from-blue-800 to-indigo-700",
  },
};
