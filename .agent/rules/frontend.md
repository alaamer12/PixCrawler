---
trigger: model_decision
description: Guidelines for TypeScript and Next.js development in the frontend application, focusing on code style, component structure, and state management.
---

# TypeScript and Next.js Development Guidelines

This document outlines the best practices for TypeScript and Next.js development in the PixCrawler frontend.

## 1. Code Style and Formatting

- **Style Guide**: Follow the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript).
- **Formatting**: Use `Prettier` for automatic code formatting. The configuration is in your project files.
- **Typing**: Strive for full type coverage. Avoid using `any` unless absolutely necessary. Use utility types like `Partial`, `Pick`, and `Omit` where appropriate.
- **JSDoc**: Add JSDoc comments to all public functions, components, and hooks, explaining their purpose, parameters, and return values.

## 2. Naming Conventions

- **Components**: Use `PascalCase` for React component files and components (e.g., `UserProfile.tsx`).
- **Files**: Use `kebab-case` for non-component files (e.g., `user-api.ts`).
- **Variables & Functions**: Use `camelCase` for variables and functions.
- **Environment Variables**: Prefix all environment variables with `NEXT_PUBLIC_` if they need to be exposed to the browser.

## 3. Component & Directory Structure

- **App Router**: Utilize the Next.js App Router for routing and layouts.
- **Component Organization**:
    - `app/`: Contains the main application routes and pages.
    - `components/ui/`: For reusable, generic UI components (e.g., Button, Input), often from a library like Shadcn UI.
    - `components/shared/`: For components shared across multiple routes.
    - `lib/`: For utility functions, API calls, and other non-component logic.
- **Styling**: Use `Tailwind CSS` for styling. Avoid inline styles and CSS files where possible.

## 4. State Management

- **Client State**: For simple client-side state, use React Hooks (`useState`, `useReducer`, `useContext`).
- **Server State**: Use `TanStack Query` (React Query) for managing server state, including caching, refetching, and mutations.
- **Forms**: Use `React Hook Form` for form state management and `Zod` for validation.

## 5. Dependency Management

- **Package Manager**: Use `bun` for package management.
- **Adding Dependencies**: Add new dependencies using `bun add <package>`.
- **Lock File**: Always commit the `bun.lockb` file to ensure reproducible builds.