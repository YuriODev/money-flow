# Popular Subscription Templates Feature Plan

## Overview

Add a feature that allows users to quickly add popular subscriptions from pre-defined templates, reducing manual data entry and ensuring accurate default values.

## User Stories

1. **As a user**, I want to quickly add common subscriptions like Netflix, Spotify, etc., without typing all the details manually.
2. **As a user**, I want templates to pre-fill common UK pricing when available.
3. **As a user**, I want to be able to customize template values before adding.

## Implementation

### Phase 1: Template Data Structure

Create a templates configuration file with popular services:

```typescript
// frontend/src/lib/subscription-templates.ts
interface SubscriptionTemplate {
  name: string;
  category: string;
  paymentType: PaymentType;
  defaultAmount?: number;
  defaultCurrency?: string;
  defaultFrequency?: Frequency;
  iconUrl?: string;
  description?: string;
  tags?: string[];
}

const SUBSCRIPTION_TEMPLATES: Record<string, SubscriptionTemplate[]> = {
  streaming: [
    { name: "Netflix", category: "Entertainment", paymentType: "subscription", defaultAmount: 10.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "Disney+", category: "Entertainment", paymentType: "subscription", defaultAmount: 7.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "Amazon Prime Video", category: "Entertainment", paymentType: "subscription", defaultAmount: 8.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "Apple TV+", category: "Entertainment", paymentType: "subscription", defaultAmount: 8.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "NOW TV", category: "Entertainment", paymentType: "subscription", defaultAmount: 9.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "Sky", category: "Entertainment", paymentType: "subscription" },
    { name: "BT Sport", category: "Entertainment", paymentType: "subscription" },
  ],
  music: [
    { name: "Spotify", category: "Entertainment", paymentType: "subscription", defaultAmount: 10.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "Apple Music", category: "Entertainment", paymentType: "subscription", defaultAmount: 10.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "YouTube Music", category: "Entertainment", paymentType: "subscription", defaultAmount: 10.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "Tidal", category: "Entertainment", paymentType: "subscription", defaultAmount: 10.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "Deezer", category: "Entertainment", paymentType: "subscription", defaultAmount: 10.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
  ],
  productivity: [
    { name: "Microsoft 365", category: "Productivity", paymentType: "subscription", defaultAmount: 5.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "Adobe Creative Cloud", category: "Productivity", paymentType: "subscription", defaultAmount: 54.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "Notion", category: "Productivity", paymentType: "subscription", defaultAmount: 8, defaultCurrency: "USD", defaultFrequency: "MONTHLY" },
    { name: "Slack", category: "Productivity", paymentType: "subscription" },
    { name: "Figma", category: "Productivity", paymentType: "subscription", defaultAmount: 12, defaultCurrency: "USD", defaultFrequency: "MONTHLY" },
    { name: "1Password", category: "Productivity", paymentType: "subscription", defaultAmount: 2.99, defaultCurrency: "USD", defaultFrequency: "MONTHLY" },
  ],
  gaming: [
    { name: "Xbox Game Pass", category: "Gaming", paymentType: "subscription", defaultAmount: 10.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "PlayStation Plus", category: "Gaming", paymentType: "subscription", defaultAmount: 8.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "Nintendo Switch Online", category: "Gaming", paymentType: "subscription", defaultAmount: 3.49, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "EA Play", category: "Gaming", paymentType: "subscription", defaultAmount: 3.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
  ],
  fitness: [
    { name: "Gym Membership", category: "Health", paymentType: "subscription" },
    { name: "Peloton", category: "Health", paymentType: "subscription", defaultAmount: 12.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "Strava", category: "Health", paymentType: "subscription", defaultAmount: 7.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
    { name: "MyFitnessPal", category: "Health", paymentType: "subscription", defaultAmount: 9.99, defaultCurrency: "GBP", defaultFrequency: "MONTHLY" },
  ],
  utilities_uk: [
    { name: "Council Tax", category: "Utilities", paymentType: "utility", defaultFrequency: "MONTHLY" },
    { name: "Electricity", category: "Utilities", paymentType: "utility", defaultFrequency: "MONTHLY" },
    { name: "Gas", category: "Utilities", paymentType: "utility", defaultFrequency: "MONTHLY" },
    { name: "Water", category: "Utilities", paymentType: "utility", defaultFrequency: "MONTHLY" },
    { name: "Broadband", category: "Utilities", paymentType: "utility", defaultFrequency: "MONTHLY" },
    { name: "Mobile Phone", category: "Utilities", paymentType: "utility", defaultFrequency: "MONTHLY" },
    { name: "TV Licence", category: "Utilities", paymentType: "utility", defaultAmount: 169.50, defaultCurrency: "GBP", defaultFrequency: "YEARLY" },
  ],
  insurance_uk: [
    { name: "Car Insurance", category: "Insurance", paymentType: "insurance", defaultFrequency: "YEARLY" },
    { name: "Home Insurance", category: "Insurance", paymentType: "insurance", defaultFrequency: "YEARLY" },
    { name: "Life Insurance", category: "Insurance", paymentType: "insurance", defaultFrequency: "MONTHLY" },
    { name: "Health Insurance", category: "Insurance", paymentType: "insurance", defaultFrequency: "MONTHLY" },
    { name: "Pet Insurance", category: "Insurance", paymentType: "insurance", defaultFrequency: "MONTHLY" },
    { name: "Travel Insurance", category: "Insurance", paymentType: "insurance", defaultFrequency: "YEARLY" },
  ],
};
```

### Phase 2: UI Components

1. **Template Browser Modal** - Categorized list of templates with search
2. **Template Card** - Shows service name, icon, default price, "Add" button
3. **Quick Add from Template** - Pre-fills AddSubscriptionModal with template values

### Phase 3: Integration Points

1. Add "Browse Templates" button next to "Add Payment" in SubscriptionList
2. Template selection opens AddSubscriptionModal with pre-filled values
3. User can customize any field before saving

## Files to Create/Modify

### New Files
- `frontend/src/lib/subscription-templates.ts` - Template data
- `frontend/src/components/TemplatesBrowser.tsx` - Template browser modal

### Modified Files
- `frontend/src/components/SubscriptionList.tsx` - Add "Browse Templates" button
- `frontend/src/components/AddSubscriptionModal.tsx` - Accept initial values prop

## Estimated Effort

- Phase 1 (Data): 1-2 hours
- Phase 2 (UI): 2-3 hours
- Phase 3 (Integration): 1-2 hours

Total: ~5-7 hours

## Future Enhancements

1. User-created templates (save custom subscriptions as templates)
2. Regional pricing (US, EU, UK variants)
3. Template suggestions based on existing subscriptions
4. Auto-fetch current pricing from APIs

---

Created: 2025-12-03
Status: Planned
