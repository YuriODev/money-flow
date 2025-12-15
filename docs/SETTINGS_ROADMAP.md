# Money Flow - Settings & Features Roadmap

> Comprehensive vision for user settings, AI-powered features, and integrations.

**Last Updated:** 2024-12-15
**Status:** Planning Phase

---

## Table of Contents

1. [Settings Page Structure](#settings-page-structure)
2. [AI-Powered Features](#ai-powered-features)
3. [Additional App Features](#additional-app-features)
4. [Implementation Phases](#implementation-phases)
5. [Technical Requirements](#technical-requirements)
6. [API Endpoints Needed](#api-endpoints-needed)

---

## Settings Page Structure

The Settings page will be accessible from the user dropdown menu in the header. It uses a tabbed interface for organization.

### Tab 1: Profile

**Purpose:** Manage personal account information and security.

| Feature | Description | Priority |
|---------|-------------|----------|
| Edit full name | Update display name | P1 |
| View email | Read-only, shows account email | P1 |
| Avatar upload | Upload profile picture, crop tool | P2 |
| Account created date | Shows when account was created | P1 |
| Change password | Current + new password form with validation | P1 |
| Two-factor authentication | Enable/disable 2FA with authenticator app | P3 |
| Connected accounts | Link Google/Apple for SSO login | P3 |
| Login history | View recent login attempts with IP/device | P3 |
| Active sessions | See and revoke active sessions | P3 |

**UI Components:**
- Profile card with avatar and basic info
- Editable form fields with inline validation
- Password change modal with strength indicator
- 2FA setup wizard with QR code

---

### Tab 2: Preferences

**Purpose:** Customize display and default behaviors.

#### Display Settings

| Setting | Options | Default |
|---------|---------|---------|
| Default currency | GBP, USD, EUR, UAH + 50 more | GBP |
| Date format | DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD | DD/MM/YYYY |
| Number format | 1,234.56 (UK/US) vs 1.234,56 (EU) | 1,234.56 |
| Week starts on | Monday, Sunday | Monday |
| Theme | Light, Dark, System | System |
| Compact view | Toggle for denser UI | Off |
| Language | English, Ukrainian, Spanish, French, German | English |

#### Default Values for New Payments

| Setting | Options | Default |
|---------|---------|---------|
| Reminder days | 1, 3, 7, 14, 30 days before | 3 |
| Payment type | Any payment type | Subscription |
| Default card | Any saved card | None |
| Auto-renew | On/Off | On |

**Storage:** User preferences stored in `users.preferences` JSON field.

---

### Tab 3: Payment Cards

**Purpose:** Manage payment methods used for subscriptions.

#### Features

| Feature | Description | Priority |
|---------|-------------|----------|
| List all cards | Grid/list view with monthly totals per card | P1 |
| Add new card | Modal form with fields below | P1 |
| Edit card | Update any card details | P1 |
| Delete card | Remove card (reassign payments first) | P1 |
| Set default card | Mark one card as default for new payments | P1 |
| Reorder cards | Drag-and-drop to change display order | P2 |
| Card icons | Upload custom or select from library | P2 |
| Link cards | Associate credit card with funding debit card | P2 |

#### Card Fields

```typescript
interface PaymentCard {
  id: string;
  name: string;              // "Monzo Personal"
  card_type: CardType;       // debit, credit, prepaid, bank_account, cash, crypto
  last_four: string | null;  // "4242"
  bank_name: string;         // "Monzo"
  currency: string;          // "GBP"
  color: string;             // "#FF5722"
  icon_url: string | null;   // Custom or bank logo
  is_active: boolean;
  notes: string | null;
  sort_order: number;
  funding_card_id: string | null;  // Links to another card
}
```

#### Card Types

| Type | Description | Icon |
|------|-------------|------|
| Debit | Bank debit card | 💳 |
| Credit | Credit card | 💳 |
| Prepaid | Prepaid/gift card | 🎁 |
| Bank Account | Direct debit from account | 🏦 |
| Cash | Cash payments | 💵 |
| Crypto Wallet | Cryptocurrency wallet | ₿ |

---

### Tab 4: Categories

**Purpose:** Organize payments into categories for better insights.

#### Features

| Feature | Description | Priority |
|---------|-------------|----------|
| View categories | List with payment counts and totals | P1 |
| Add custom category | Create new category with name/color/icon | P1 |
| Edit category | Rename, change color/icon | P1 |
| Delete category | Remove (reassign payments first) | P1 |
| Merge categories | Combine two categories into one | P2 |
| Category budgets | Set monthly spending limit per category | P3 |
| Icon library | Browse/search icons for categories | P2 |

#### Default Categories

| Category | Color | Icon | Examples |
|----------|-------|------|----------|
| Entertainment | Purple | 🎬 | Netflix, Spotify, Disney+ |
| Productivity | Blue | 💼 | Microsoft 365, Notion, Slack |
| Finance & Banking | Green | 🏦 | Revolut, Trading apps |
| Health & Fitness | Red | ❤️ | Gym, Health apps |
| News & Media | Orange | 📰 | NYT, Medium, Substack |
| Gaming | Indigo | 🎮 | Xbox, PlayStation, Steam |
| Cloud & Storage | Cyan | ☁️ | iCloud, Google One, Dropbox |
| Security | Gray | 🔒 | VPN, Password managers |
| Education | Yellow | 📚 | Coursera, Skillshare |
| Utilities | Teal | 💡 | Electric, Water, Internet |
| Shopping | Pink | 🛍️ | Amazon Prime |
| Food & Delivery | Amber | 🍔 | Deliveroo, Uber Eats |
| Transportation | Lime | 🚗 | Uber, Car insurance |
| Housing | Brown | 🏠 | Rent, Mortgage |
| Other | Gray | 📦 | Uncategorized |

---

### Tab 5: Notifications

**Purpose:** Configure how and when to receive alerts.

#### Payment Reminders

| Setting | Description | Default |
|---------|-------------|---------|
| Enable reminders | Master toggle for all reminders | On |
| Default days before | When to send reminder | 3 days |
| Reminder time | Time of day to send | 9:00 AM |
| Overdue alerts | Alert for missed payments | On |

#### Notification Channels

| Channel | Description | Priority |
|---------|-------------|----------|
| Email | Send to account email | P1 |
| Browser push | Desktop/mobile browser notifications | P2 |
| Telegram bot | Connect Telegram for instant alerts | P2 |
| WhatsApp | WhatsApp Business API notifications | P3 |
| SMS | Text message alerts (premium feature) | P4 |
| Slack | Workspace notifications | P3 |
| Discord | Server/DM notifications | P3 |

#### Reports

| Report | Frequency | Content |
|--------|-----------|---------|
| Weekly summary | Every Monday | Upcoming payments, spending so far |
| Monthly report | 1st of month | Full month breakdown, comparisons |
| Annual report | January 1st | Year in review, trends, insights |

#### Smart Alerts

| Alert | Trigger | Description |
|-------|---------|-------------|
| Spending threshold | Monthly spend > X | "You've spent £500 this month" |
| Payment failed | Bank decline | "Netflix payment failed" |
| Price increase | Amount changed | "Spotify increased by £2" |
| Unusual activity | Anomaly detected | "Duplicate charge detected" |
| New subscription | Auto-detected | "New subscription found: Disney+" |

---

### Tab 6: Icons & Branding

**Purpose:** Customize payment icons and visual appearance.

#### Icon Library

| Feature | Description | Priority |
|---------|-------------|----------|
| Pre-loaded icons | 1000+ service logos (Netflix, Spotify, etc.) | P1 |
| Search icons | Find by service name | P1 |
| Browse by category | Filter icons by type | P2 |
| Recently used | Quick access to recent icons | P2 |

#### AI Icon Generator

| Feature | Description | Priority |
|---------|-------------|----------|
| Generate from name | "Generate icon for PureGym" | P2 |
| Style options | Flat, 3D, Minimal, Colorful, Gradient | P2 |
| Color customization | Match brand or custom colors | P2 |
| Regenerate | Get new variations | P2 |

**Technical:** Uses DALL-E 3 or Stable Diffusion API.

#### Auto Icon Fetching

```
Priority order:
1. Match against known services database
2. Fetch favicon from service URL
3. Clearbit Logo API (logo.clearbit.com)
4. Brandfetch API (brandfetch.com)
5. AI-generated fallback
6. Default category icon
```

#### Brand Colors

| Feature | Description |
|---------|-------------|
| Auto-detect | Extract primary color from icon |
| Color picker | Manual color selection |
| Palette suggestions | Complementary colors |
| Apply to card | Set payment card color from brand |

---

### Tab 7: AI Assistant Settings

**Purpose:** Configure AI behavior and smart features.

#### Natural Language Preferences

| Setting | Options | Default |
|---------|---------|---------|
| Response style | Concise, Balanced, Detailed | Balanced |
| Language | Match app language | English |
| Suggestions | Show AI suggestions | On |
| Voice input | Enable speech-to-text | Off |

#### Smart Features

| Feature | Description | Default |
|---------|-------------|---------|
| Auto-categorization | AI assigns categories to new payments | On |
| Smart detection | Detect payment type from name | On |
| Duplicate detection | Warn about potential duplicates | On |
| Price alerts | Notify when prices change | On |
| Spending insights | Proactive spending analysis | On |

#### Learning Preferences

| Setting | Description | Default |
|---------|-------------|---------|
| Learn naming | Remember user's naming conventions | On |
| Learn from corrections | Improve from user feedback | On |
| Personalized suggestions | Tailor recommendations | On |
| Data retention | How long to keep learning data | 1 year |

---

### Tab 8: Data Import

**Purpose:** Import payments from various sources.

#### Manual Import

| Method | Description | Priority |
|--------|-------------|----------|
| JSON file | Upload Money Flow export | P1 (exists) |
| CSV file | Upload spreadsheet export | P1 (exists) |
| Paste from clipboard | Paste CSV/JSON data | P2 |
| Manual wizard | Step-by-step entry guide | P2 |

#### Bank Statement Import (AI-Powered)

| Feature | Description | Priority |
|---------|-------------|----------|
| PDF upload | Upload bank statement PDF | P2 |
| CSV upload | Upload bank CSV export | P2 |
| AI extraction | Automatically find recurring payments | P2 |
| Pattern detection | Identify payment frequency | P2 |
| Review interface | Confirm/reject detected payments | P2 |

**Supported Banks (Initial):**
- Monzo (UK)
- Revolut (UK/EU)
- Barclays (UK)
- HSBC (UK)
- Lloyds (UK)
- NatWest (UK)
- Santander (UK)
- Chase (UK/US)
- Bank of America (US)
- Wells Fargo (US)

**How It Works:**
```
1. User uploads PDF bank statement
2. AI extracts all transactions using OCR + NLP
3. Algorithm identifies recurring patterns:
   - Same merchant appearing monthly
   - Similar amounts at regular intervals
   - Known subscription services
4. AI matches to known services database
5. AI suggests payment type, category, icon
6. User reviews detected subscriptions
7. User confirms which to add
8. Payments created with all details
```

#### Email Scanning (AI-Powered)

| Feature | Description | Priority |
|---------|-------------|----------|
| Connect Gmail | OAuth connection to Gmail | P3 |
| Connect Outlook | OAuth connection to Outlook | P3 |
| Scan receipts | Find subscription emails | P3 |
| Auto-detect | Find new subscriptions | P3 |
| Parse renewals | Extract renewal notices | P3 |
| Price tracking | Detect price changes in emails | P3 |

**Email Patterns Detected:**
- "Your subscription has been renewed"
- "Payment receipt for [Service]"
- "Your [Service] membership"
- "Thank you for your payment"
- "Your bill is ready"
- "Upcoming renewal notice"

#### App Imports

| App | Format | Priority |
|-----|--------|----------|
| Apple Subscriptions | Apple ID export | P3 |
| Google Play | Play Store export | P3 |
| Mint | CSV export | P3 |
| YNAB | API or export | P3 |
| Truebill/Rocket Money | CSV export | P4 |
| Copilot | Export file | P4 |

---

### Tab 9: Data Export & Backup

**Purpose:** Export data and configure backups.

#### Export Formats

| Format | Description | Priority |
|--------|-------------|----------|
| JSON | Full data export, re-importable | P1 (exists) |
| CSV | Spreadsheet compatible | P1 (exists) |
| PDF report | Formatted printable report | P2 |
| Excel | .xlsx with charts and formatting | P3 |

#### Export Options

| Option | Description |
|--------|-------------|
| Include inactive | Export cancelled/paused payments |
| Date range | Export specific time period |
| Filter by type | Export only certain payment types |
| Filter by category | Export specific categories |
| Include history | Export payment history records |

#### Scheduled Backups

| Destination | Description | Priority |
|-------------|-------------|----------|
| Email | Send backup to email weekly/monthly | P2 |
| Google Drive | Auto-sync to Drive folder | P3 |
| Dropbox | Auto-sync to Dropbox folder | P3 |
| iCloud | Auto-sync to iCloud Drive | P3 |
| OneDrive | Auto-sync to OneDrive | P4 |

#### Danger Zone

| Action | Description | Confirmation |
|--------|-------------|--------------|
| Delete all payments | Remove all subscription data | Type "DELETE" |
| Reset categories | Restore default categories | Checkbox confirm |
| Clear payment history | Remove all history records | Type "CLEAR" |
| Delete account | Permanently delete account | Password + "DELETE" |

---

### Tab 10: Integrations

**Purpose:** Connect external services.

#### Open Banking Connections

| Provider | Coverage | Priority |
|----------|----------|----------|
| TrueLayer | UK, EU | P3 |
| Plaid | US, Canada, UK, EU | P3 |
| Tink | Europe | P4 |

**Features:**
- Connect bank accounts securely
- Auto-import transactions
- Real-time balance updates
- Automatic subscription detection
- Payment verification

#### Calendar Sync

| Calendar | Description | Priority |
|----------|-------------|----------|
| Google Calendar | Add payment dates as events | P2 |
| Apple Calendar | iCal feed subscription | P2 |
| Outlook | Office 365 calendar | P3 |

**Event Details:**
- Title: "[Payment] Netflix - £15.99"
- Date: Payment due date
- Reminder: Based on user preference
- Description: Payment details, card used
- Recurring: Matches payment frequency

#### Automation Platforms

| Platform | Description | Priority |
|----------|-------------|----------|
| Zapier | 5000+ app connections | P3 |
| Make (Integromat) | Complex workflows | P4 |
| IFTTT | Simple automations | P4 |
| Webhooks | Custom integrations | P2 |

**Webhook Events:**
- `payment.created` - New payment added
- `payment.updated` - Payment modified
- `payment.deleted` - Payment removed
- `payment.due_soon` - Payment due within X days
- `payment.overdue` - Payment past due date
- `payment.price_changed` - Price increase/decrease

#### Messaging Integrations

| Platform | Description | Priority |
|----------|-------------|----------|
| Telegram Bot | Personal notifications | P2 |
| Slack | Workspace notifications | P3 |
| Discord | Server or DM notifications | P3 |
| Microsoft Teams | Team notifications | P4 |

---

## AI-Powered Features

### Smart Payment Detection

**Flow:**
```
User uploads bank statement (PDF/CSV)
           ↓
   AI extracts all transactions
   - OCR for PDF documents
   - Parse CSV structure
   - Clean and normalize data
           ↓
   AI identifies recurring patterns
   - Same merchant monthly
   - Similar amounts weekly
   - Known service names
           ↓
   AI matches to known services
   - Netflix, Spotify, etc.
   - Local services database
   - Fuzzy name matching
           ↓
   AI suggests details
   - Payment type (subscription/utility/etc)
   - Category (entertainment/productivity)
   - Icon and brand colors
   - Frequency detection
           ↓
   User reviews and confirms
   - Edit any suggestions
   - Accept/reject each
   - Add missing details
           ↓
   Payments created automatically
```

### Email Receipt Scanning

**Flow:**
```
User connects Gmail/Outlook (OAuth)
           ↓
AI scans inbox for keywords
- "subscription renewed"
- "payment receipt"
- "your bill"
- "membership"
           ↓
AI parses email content
- Extract service name
- Extract amount
- Extract date
- Extract frequency
           ↓
AI checks for existing
- Match against current payments
- Detect price changes
- Identify new subscriptions
           ↓
User receives notification
- "Found new subscription: Hulu $7.99/month"
- "Netflix price increased: $15.99 → $17.99"
           ↓
User confirms additions/updates
```

### Icon Intelligence

**Flow:**
```
User adds payment: "Gym - PureGym"
           ↓
Step 1: Known services DB
- Check local database
- ~5000 known services
           ↓
Step 2: Domain search
- Search for puregym.com
- Fetch favicon
           ↓
Step 3: Logo APIs
- Clearbit: logo.clearbit.com/puregym.com
- Brandfetch: brandfetch.com/puregym.com
           ↓
Step 4: AI Generation
- DALL-E: "Minimalist gym logo, letter P, purple"
- Style: Match app aesthetic
           ↓
Step 5: Color extraction
- Dominant color from icon
- Apply to payment card
           ↓
Icon applied automatically
```

### Smart Suggestions Engine

**Types of Suggestions:**

| Type | Example | Trigger |
|------|---------|---------|
| Spending insight | "You spend £50/month on streaming" | Monthly summary |
| Savings opportunity | "Cancel X to save £120/year" | Unused service detected |
| Price alert | "Netflix increased by £2" | Price change detected |
| Duplicate warning | "Possible duplicate: Spotify" | Similar payment added |
| Category suggestion | "Move gym to Health category?" | Miscategorized detected |
| Reminder | "3 payments due this week: £45" | Upcoming payments |
| Trend | "Spending up 15% vs last month" | Monthly comparison |
| Anomaly | "Unusual: Charged twice for Hulu" | Pattern break |

### Natural Language Queries

**Example Queries:**
```
"How much do I spend on entertainment?"
→ Shows entertainment category total with breakdown

"Show payments due next week"
→ Lists payments with due dates in next 7 days

"What subscriptions did I add this year?"
→ Shows payments created in current year

"Compare my spending to last month"
→ Shows month-over-month comparison chart

"Which payments increased in price?"
→ Lists payments with price change history

"What's my biggest expense?"
→ Shows highest cost payment(s)

"Show me all annual payments"
→ Filters to yearly frequency payments

"How much will I spend next month?"
→ Projects next month based on due dates

"Find duplicate subscriptions"
→ Scans for similar/duplicate entries

"Summarize my debts"
→ Shows debt payment type summary with totals
```

---

## Additional App Features

### Dashboard Widgets

| Widget | Description | Size |
|--------|-------------|------|
| Spending Overview | Monthly/yearly totals | Large |
| Upcoming Payments | Next 7 days list | Medium |
| Category Breakdown | Pie/donut chart | Medium |
| Recent Activity | Last 5 changes | Small |
| Savings Progress | Goal progress bars | Medium |
| Debt Tracker | Debt payoff progress | Medium |
| Card Balances | Per-card totals | Medium |
| Quick Stats | Key numbers | Small |

**Customization:**
- Drag-and-drop layout
- Show/hide widgets
- Widget size options
- Color themes per widget

### Goals & Targets

| Feature | Description |
|---------|-------------|
| Monthly budget | Set overall spending limit |
| Category budgets | Limit per category |
| Savings goals | Target amount with deadline |
| Debt payoff | Calculate payoff timeline |
| Alerts | Notify when approaching limit |

### Price Tracking

| Feature | Description |
|---------|-------------|
| Price history | Track changes over time |
| Change alerts | Notify on price increase |
| History chart | Visual price timeline |
| Annual comparison | "20% more than last year" |

### Sharing & Collaboration

| Feature | Description |
|---------|-------------|
| Family sharing | Share dashboard with family |
| Joint view | Combined household spending |
| Split tracking | Track shared expenses |
| Roles | Viewer, Editor, Admin |
| Invite system | Email invitations |

### Mobile Features

| Feature | Description | Priority |
|---------|-------------|----------|
| PWA | Installable web app | P1 |
| Home widget | Quick balance view | P2 |
| Native app | React Native iOS/Android | P3 |
| Apple Watch | Complications and app | P4 |
| Siri shortcuts | Voice commands | P4 |
| Android widgets | Home screen widgets | P3 |

---

## Implementation Phases

### Phase 1: Foundation (Current Sprint)
**Timeline: 2 weeks**

| Task | Effort | Status |
|------|--------|--------|
| Settings page structure | 4h | TODO |
| Tab navigation component | 2h | TODO |
| Profile tab - view/edit name | 3h | TODO |
| Profile tab - change password | 4h | TODO |
| Preferences tab - display settings | 4h | TODO |
| Preferences tab - defaults | 3h | TODO |
| Backend: profile update API | 2h | TODO |
| Backend: change password API | 2h | TODO |
| Backend: preferences API | 3h | TODO |
| Settings link in header dropdown | 1h | TODO |

**Deliverable:** Basic settings page with Profile and Preferences tabs.

### Phase 2: Cards & Categories (Next Sprint)
**Timeline: 2 weeks**

| Task | Effort | Status |
|------|--------|--------|
| Payment Cards tab | 6h | TODO |
| Card management (CRUD) | 4h | EXISTS (enhance) |
| Card reordering | 3h | TODO |
| Categories tab | 5h | TODO |
| Category management (CRUD) | 4h | TODO |
| Category icons library | 4h | TODO |
| Backend: categories API | 4h | TODO |

**Deliverable:** Full card and category management in settings.

### Phase 3: Notifications & Export (Sprint +2)
**Timeline: 2 weeks**

| Task | Effort | Status |
|------|--------|--------|
| Notifications tab | 4h | TODO |
| Email notification settings | 3h | TODO |
| Reminder preferences | 3h | TODO |
| Data Export tab | 4h | TODO |
| PDF report export | 6h | TODO |
| Scheduled backups UI | 4h | TODO |
| Backend: notification preferences | 4h | TODO |
| Backend: PDF generation | 6h | TODO |

**Deliverable:** Notification settings and enhanced export options.

### Phase 4: Icons & AI Settings (Sprint +3)
**Timeline: 2 weeks**

| Task | Effort | Status |
|------|--------|--------|
| Icons & Branding tab | 5h | TODO |
| Icon library browser | 6h | TODO |
| Icon search | 3h | TODO |
| Auto icon fetching | 4h | TODO |
| AI Assistant tab | 4h | TODO |
| AI preferences | 3h | TODO |
| Backend: icon service | 6h | TODO |

**Deliverable:** Icon management and AI configuration.

### Phase 5: Smart Import (Sprint +4)
**Timeline: 3 weeks**

| Task | Effort | Status |
|------|--------|--------|
| Bank statement upload UI | 4h | TODO |
| PDF parsing service | 8h | TODO |
| AI transaction extraction | 12h | TODO |
| Recurring pattern detection | 8h | TODO |
| Review interface | 6h | TODO |
| Service matching database | 8h | TODO |

**Deliverable:** AI-powered bank statement import.

### Phase 6: Integrations (Sprint +5)
**Timeline: 3 weeks**

| Task | Effort | Status |
|------|--------|--------|
| Calendar sync (Google) | 8h | TODO |
| Calendar sync (Apple) | 6h | TODO |
| Webhook system | 8h | TODO |
| Telegram bot | 8h | TODO |
| Zapier integration | 10h | TODO |

**Deliverable:** External service integrations.

### Phase 7: Open Banking (Sprint +6)
**Timeline: 4 weeks**

| Task | Effort | Status |
|------|--------|--------|
| TrueLayer integration | 16h | TODO |
| Account connection flow | 8h | TODO |
| Transaction sync | 10h | TODO |
| Auto subscription detection | 12h | TODO |

**Deliverable:** Live bank connection and auto-detection.

---

## Technical Requirements

### Frontend Dependencies

```json
{
  "new_dependencies": {
    "@radix-ui/react-tabs": "Tab navigation",
    "@radix-ui/react-switch": "Toggle switches",
    "@radix-ui/react-select": "Dropdown selects",
    "@radix-ui/react-slider": "Range sliders",
    "@radix-ui/react-alert-dialog": "Confirmation dialogs",
    "react-dropzone": "File upload",
    "react-color": "Color picker",
    "react-beautiful-dnd": "Drag and drop",
    "date-fns": "Date formatting (already have)",
    "zod": "Form validation"
  }
}
```

### Backend Dependencies

```toml
[new_dependencies]
python-pdfplumber = "PDF parsing"
openai = "AI features (already have)"
clearbit = "Logo API"
google-auth = "Gmail integration"
icalendar = "Calendar export"
weasyprint = "PDF generation"
pillow = "Image processing"
```

### Database Changes

```sql
-- Categories table (new)
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#6366F1',
    icon VARCHAR(50),
    is_default BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    budget_amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User preferences enhancement
ALTER TABLE users
ADD COLUMN notification_preferences JSONB DEFAULT '{}';

-- Icon cache table
CREATE TABLE icon_cache (
    id UUID PRIMARY KEY,
    service_name VARCHAR(255) NOT NULL,
    icon_url TEXT,
    brand_color VARCHAR(7),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Webhook subscriptions
CREATE TABLE webhook_subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    url TEXT NOT NULL,
    events TEXT[] NOT NULL,
    secret VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints Needed

### Profile & Auth

```
PATCH /api/auth/profile
  - Update user profile (full_name, avatar_url)

POST /api/auth/change-password
  - Change password (current_password, new_password)

GET /api/auth/sessions
  - List active sessions

DELETE /api/auth/sessions/{session_id}
  - Revoke a session
```

### Preferences

```
GET /api/users/preferences
  - Get all user preferences

PUT /api/users/preferences
  - Update preferences (partial update)

GET /api/users/preferences/{key}
  - Get specific preference
```

### Categories

```
GET /api/categories
  - List all categories (default + custom)

POST /api/categories
  - Create custom category

PUT /api/categories/{id}
  - Update category

DELETE /api/categories/{id}
  - Delete category (must reassign payments first)

POST /api/categories/merge
  - Merge two categories
```

### Icons

```
GET /api/icons/search?q={query}
  - Search icon library

GET /api/icons/service/{name}
  - Get icon for known service

POST /api/icons/fetch-url
  - Fetch icon from URL (favicon)

POST /api/icons/generate
  - AI-generate icon
```

### Import

```
POST /api/import/bank-statement
  - Upload and parse bank statement

GET /api/import/bank-statement/{job_id}
  - Get parsing results

POST /api/import/bank-statement/{job_id}/confirm
  - Confirm and import detected payments
```

### Notifications

```
GET /api/notifications/preferences
  - Get notification settings

PUT /api/notifications/preferences
  - Update notification settings

POST /api/notifications/test
  - Send test notification
```

### Webhooks

```
GET /api/webhooks
  - List webhook subscriptions

POST /api/webhooks
  - Create webhook subscription

DELETE /api/webhooks/{id}
  - Delete webhook subscription

POST /api/webhooks/{id}/test
  - Test webhook with sample payload
```

### Calendar

```
GET /api/calendar/ical
  - Get iCal feed URL for user

POST /api/calendar/sync/google
  - Initiate Google Calendar sync

DELETE /api/calendar/sync/google
  - Disconnect Google Calendar
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Settings completion | 80% of users complete profile | Analytics |
| Card setup | 70% have at least 1 card | DB query |
| Import usage | 30% use import feature | Analytics |
| AI icon usage | 50% of payments have icons | DB query |
| Notification engagement | 60% enable notifications | DB query |
| Calendar sync | 20% connect calendar | Analytics |
| Retention | 40% weekly active users | Analytics |

---

## Security Considerations

1. **Password Changes**
   - Require current password
   - Enforce password strength
   - Send email notification on change
   - Invalidate other sessions option

2. **OAuth Connections**
   - Minimal scope requests
   - Token encryption at rest
   - Regular token refresh
   - Revocation on disconnect

3. **Bank Statements**
   - Process in memory only
   - No permanent storage of statements
   - Encryption in transit
   - Audit logging

4. **Webhooks**
   - HMAC signature verification
   - Retry with backoff
   - IP allowlisting option
   - Rate limiting

---

**Document Version:** 1.0
**Created:** 2024-12-15
**Author:** AI Assistant
**Review Status:** Draft - Pending Review
