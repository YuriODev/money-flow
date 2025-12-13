# TypeScript/JavaScript Coding Standards

## Overview

This document defines the TypeScript and JavaScript coding standards for the Subscription Tracker frontend (Next.js). All code must follow these guidelines.

## Table of Contents

1. [TypeScript Configuration](#typescript-configuration)
2. [Code Style](#code-style)
3. [React Best Practices](#react-best-practices)
4. [State Management](#state-management)
5. [API Integration](#api-integration)
6. [Error Handling](#error-handling)
7. [Testing](#testing)
8. [Linting and Formatting](#linting-and-formatting)

---

## TypeScript Configuration

### Strict Mode

Always use strict TypeScript configuration (`frontend/tsconfig.json`):

```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true
  }
}
```

### Type Everything

```typescript
// ✅ GOOD: Explicit types
interface Subscription {
  id: string;
  name: string;
  amount: string;
  currency: string;
  frequency: string;
  next_payment_date: string;
}

function formatCurrency(amount: number, currency: string = "GBP"): string {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency }).format(amount);
}

// ❌ BAD: No types
function formatCurrency(amount, currency = "GBP") {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency }).format(amount);
}
```

---

## Code Style

### Naming Conventions

```typescript
// Components: PascalCase
function SubscriptionList() {}
const AgentChat: React.FC = () => {};

// Functions/Variables: camelCase
const getUserSubscriptions = () => {};
const isActive = true;
const subscriptionCount = 10;

// Constants: UPPER_SNAKE_CASE
const DEFAULT_CURRENCY = "GBP";
const API_TIMEOUT = 5000;

// Types/Interfaces: PascalCase
interface SubscriptionData {}
type ApiResponse = {};

// Private properties: _leadingUnderscore (rare in TS)
class Service {
  private _cache: Map<string, any>;
}
```

### File Naming

```
components/
  SubscriptionList.tsx       # Component files: PascalCase
  AddSubscriptionModal.tsx

lib/
  api.ts                     # Utility files: camelCase
  utils.ts
  formatCurrency.ts

hooks/
  useSubscriptions.ts        # Hooks: camelCase with 'use' prefix
  useDebounce.ts
```

---

## React Best Practices

### Component Structure

```typescript
"use client";  // Only if needed for client components

import { useState, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";

// Types/Interfaces first
interface SubscriptionListProps {
  userId?: string;
  showInactive?: boolean;
}

// Component
export function SubscriptionList({ userId, showInactive = false }: SubscriptionListProps) {
  // 1. Hooks
  const [filter, setFilter] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["subscriptions", userId],
    queryFn: () => subscriptionApi.getAll(),
  });

  // 2. Effects
  useEffect(() => {
    // ...
  }, []);

  // 3. Event handlers
  const handleDelete = async (id: string) => {
    // ...
  };

  // 4. Render helpers
  const renderSubscription = (sub: Subscription) => {
    return <div key={sub.id}>{sub.name}</div>;
  };

  // 5. Early returns
  if (isLoading) return <LoadingSkeleton />;
  if (!data) return <EmptyState />;

  // 6. Main render
  return (
    <div className="subscription-list">
      {data.map(renderSubscription)}
    </div>
  );
}
```

### Props and State Types

```typescript
// ✅ GOOD: Explicit prop types
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: "primary" | "secondary";
  disabled?: boolean;
  children?: React.ReactNode;
}

export function Button({ label, onClick, variant = "primary", disabled }: ButtonProps) {
  return (
    <button onClick={onClick} disabled={disabled} className={`btn-${variant}`}>
      {label}
    </button>
  );
}

// ❌ BAD: No prop types
export function Button({ label, onClick, variant = "primary" }) {
  // ...
}
```

### Hooks

```typescript
// Custom hook example
import { useState, useEffect } from "react";

interface UseDebounceOptions {
  delay?: number;
}

export function useDebounce<T>(value: T, { delay = 500 }: UseDebounceOptions = {}): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Usage
const [searchTerm, setSearchTerm] = useState("");
const debouncedSearch = useDebounce(searchTerm, { delay: 300 });
```

---

## State Management

### React Query for Server State

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// ✅ GOOD: Use React Query for server state
export function useSubscriptions() {
  return useQuery({
    queryKey: ["subscriptions"],
    queryFn: () => subscriptionApi.getAll(),
    staleTime: 60 * 1000, // 1 minute
  });
}

export function useCreateSubscription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SubscriptionCreate) => subscriptionApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
    },
  });
}

// Usage in component
function SubscriptionList() {
  const { data, isLoading, error } = useSubscriptions();
  const createMutation = useCreateSubscription();

  const handleCreate = async (data: SubscriptionCreate) => {
    await createMutation.mutateAsync(data);
  };

  // ...
}
```

### useState for UI State

```typescript
// ✅ GOOD: useState for UI-only state
const [isModalOpen, setIsModalOpen] = useState(false);
const [selectedTab, setSelectedTab] = useState<"list" | "chat">("list");
const [filter, setFilter] = useState("");

// ❌ BAD: Don't use useState for server data
const [subscriptions, setSubscriptions] = useState([]);  // Use React Query instead!
```

---

## API Integration

### Type-Safe API Client

```typescript
// lib/api.ts
import axios, { AxiosInstance } from "axios";

const API_URL = typeof window === 'undefined'
  ? process.env.BACKEND_URL || "http://backend:8000"
  : "";

export const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Type definitions
export interface Subscription {
  id: string;
  name: string;
  amount: string;
  currency: string;
  frequency: string;
  next_payment_date: string;
}

export interface SubscriptionCreate {
  name: string;
  amount: number;
  currency?: string;
  frequency: string;
  start_date: string;
}

// API methods
export const subscriptionApi = {
  getAll: async (): Promise<Subscription[]> => {
    const { data } = await api.get<Subscription[]>("/subscriptions");
    return data;
  },

  create: async (subscription: SubscriptionCreate): Promise<Subscription> => {
    const { data } = await api.post<Subscription>("/subscriptions", subscription);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/subscriptions/${id}`);
  },
};
```

---

## Error Handling

### Try-Catch with Proper Types

```typescript
// ✅ GOOD: Proper error handling
async function handleSubmit(data: SubscriptionCreate) {
  try {
    const result = await subscriptionApi.create(data);
    toast.success(`Created ${result.name}`);
    return result;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || "Failed to create subscription";
      toast.error(message);
    } else {
      toast.error("An unexpected error occurred");
      console.error(error);
    }
    throw error;
  }
}

// ❌ BAD: Generic catch
async function handleSubmit(data: any) {
  try {
    const result = await subscriptionApi.create(data);
  } catch (e) {
    alert("Error!");  // Don't use alert()
  }
}
```

### Error Boundaries

```typescript
// components/ErrorBoundary.tsx
"use client";

import React, { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-container">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## Testing

### Component Testing

```typescript
// SubscriptionList.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { SubscriptionList } from "./SubscriptionList";
import * as api from "@/lib/api";

// Mock API
jest.mock("@/lib/api");

describe("SubscriptionList", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("displays subscriptions when loaded", async () => {
    // Arrange
    const mockSubscriptions = [
      { id: "1", name: "Netflix", amount: "15.99", currency: "GBP" },
      { id: "2", name: "Spotify", amount: "9.99", currency: "GBP" },
    ];

    (api.subscriptionApi.getAll as jest.Mock).mockResolvedValue(mockSubscriptions);

    // Act
    render(<SubscriptionList />, { wrapper });

    // Assert
    await waitFor(() => {
      expect(screen.getByText("Netflix")).toBeInTheDocument();
      expect(screen.getByText("Spotify")).toBeInTheDocument();
    });
  });

  it("handles delete action", async () => {
    // Test implementation...
  });
});
```

---

## Linting and Formatting

### ESLint Configuration

Create `frontend/.eslintrc.json`:

```json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn",
    "@typescript-eslint/explicit-function-return-type": "off",
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn",
    "no-console": ["warn", { "allow": ["error", "warn"] }]
  }
}
```

### Prettier Configuration

Create `frontend/.prettierrc`:

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": false,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always"
}
```

### Running Linters

```bash
# Lint code
cd frontend
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix

# Format with Prettier
npx prettier --write "src/**/*.{ts,tsx,js,jsx}"
```

---

## Quick Checklist

Before committing:

- [ ] All components have proper TypeScript types
- [ ] Props interfaces are defined
- [ ] No `any` types (or minimal, with justification)
- [ ] Error handling is implemented
- [ ] Code passes ESLint
- [ ] Code is formatted with Prettier
- [ ] Tests are written
- [ ] No console.log() in production code
- [ ] Accessibility considered (aria labels, etc.)

---

**Last Updated**: 2025-11-28
**Maintained By**: Frontend Team
