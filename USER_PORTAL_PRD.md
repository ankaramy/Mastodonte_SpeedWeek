# User Portal — PRD (IFCore)

## Overview
A secure user portal for IFCore that provides authentication, onboarding, subscription management (Stripe), profile & settings, support, and account lifecycle controls. This portal will be hosted with Cloudflare Pages (frontend) and Cloudflare Workers for API/auth logic; backend orchestration and heavy jobs continue to use the HuggingFace Space orchestrator and D1 database. Follow IFCore skill contracts for any platform-facing code.

## Primary Users & Roles
- Captains (admins): platform-wide visibility, manage subscriptions, support escalations.
- Team Leads: manage team billing seats, invite/remove team members, view usage and team settings.
- Team Members: sign up, onboard, access product features according to team subscription.
- Support Agents: view user account info and logs, raise tickets, but cannot change billing without authorization.

## Goals
- Provide secure, smooth sign-up and login flows (email + password, OAuth optional).
- Collect minimal onboarding data to provision user accounts and teams.
- Offer subscription plans with Stripe integration (create, update, cancel, refund flows).
- Allow users to manage settings, billing, and account deletion with audit trails.
- Build with Cloudflare Pages + Workers and integrate with HuggingFace and D1 per IFCore architecture.

## Scope & Feature List
1. Authentication
   - Sign up (email + password) with email verification.
   - Sign in (email + password) with optional 2FA (TOTP) in later iterations.
   - Password reset flow (email with secure token).
   - Session management via secure HTTP-only cookies or signed JWTs validated by Worker.

2. Onboarding
   - Team creation or join existing team during signup.
   - Ask essential onboarding questions (team name, role, organization type).
   - Default onboarding flow provisions minimal team record in D1.

3. Terms & Conditions / Privacy
   - Present T&Cs during signup with required checkbox acceptance.
   - Store acceptance timestamp and T&C version in user record.

4. Subscription Plans & Billing
   - Plans: Free tier (limited runs), Team (paid seats), Enterprise (custom).
   - Integrate with Stripe Billing: checkout sessions, subscriptions, invoices.
   - Stripe webhooks handled in a secure Worker endpoint: invoice.paid, invoice.payment_failed, customer.subscription.updated, customer.subscription.deleted.
   - Billing portal link (Stripe Hosted Billing Portal) for self-service updates.

5. Cancel / Pause Subscription
   - Users can cancel subscription from portal; show cancellation effective date and retention period.
   - Allow pause or downgrade (if enabled) — controlled via Stripe API.

6. Settings / Configuration
   - Profile (name, email, avatar), team settings (team name, seats), notification preferences, API keys (rotate/regenerate), and integration settings (webhooks endpoints).

7. Delete Account
   - Soft-delete with confirmation: mark account, schedule full delete after retention window (e.g., 30 days).
   - On delete: cancel active subscriptions (or transfer billing), remove secrets (API keys), and anonymize or remove user data per policy.

8. Support / Help
   - Help page with documentation links, FAQs, and a ticket form that creates a support ticket (stored in D1 or forwarded to external ticketing via webhooks).
   - Link to Captains contact and escalation paths.

9. User Profile Page
   - Shows plan status, next billing date, usage summary, recent activity, and quick links to support, billing portal, and account deletion.

## Data Model (high-level)
- users: id, email, password_hash, name, avatar_url, role, team_id, accepted_tc_version, accepted_tc_ts, status, created_at, deleted_at
- teams: id, name, owner_user_id, seats, plan_id, stripe_customer_id, created_at
- subscriptions: id, team_id, stripe_subscription_id, plan_id, status, current_period_end
- invoices/logs: event_id, team_id, type, payload (JSON), created_at
- sessions: session_id, user_id, token_hash, expires_at

Store personal/sensitive fields encrypted or hashed. Use D1 for lightweight records; delegate heavy billing state to Stripe and sync via webhooks.

## API Endpoints (Worker) — examples
- POST /api/auth/signup {email,password,teamName,accept_tc_version} -> 201 + send verification email
- POST /api/auth/login {email,password} -> 200 + Set cookie/JWT
- POST /api/auth/logout -> 200 + clear cookie
- POST /api/auth/password-reset {email} -> 200 + send reset email
- GET /api/user/profile -> 200 (auth required)
- POST /api/user/profile -> 200 (update info)
- GET /api/billing/plans -> 200 (public plan list)
- POST /api/billing/checkout-session -> 303 redirect to Stripe Checkout
- POST /api/billing/webhook -> 200 (Stripe webhook handler)
- POST /api/support/ticket -> 201 (create ticket)
- POST /api/admin/subscription/cancel -> 200 (admin only)

All admin or billing-changing endpoints must require strong RBAC and be protected by Worker-authenticated tokens.

## UX Flows (condensed)
1. Signup → verify email → create team or join → accept T&C → go to onboarding → land on `Profile` page.
2. Login → session cookie set → Dashboard → Billing card shows current plan and `Manage subscription` button → opens Stripe Billing Portal.
3. Cancel subscription → confirm modal → show effective date and consequences → cancel via Worker -> Stripe API -> webhook updates subscription state.
4. Delete account → two-step flow (confirm via email or password) -> mark soft-delete -> start retention timer -> final deletion after window.

## Stripe Integration Details
- Use Stripe Checkout for new subscriptions; store `stripe_customer_id` on `teams` record.
- Use Stripe Billing Portal for self-service updates: Worker creates a portal session and returns redirect.
- Implement webhook endpoint `/api/billing/webhook` to handle invoice.payment_failed, invoice.paid, customer.subscription.updated, customer.subscription.deleted to keep D1 synced.
- Webhook security: verify signatures using Stripe signing secret; retry/exponential backoff for transient failures.

## Security & Compliance
- Passwords: strong hashing (bcrypt/argon2) and enforce strong passwords at signup.
- Sessions: use HTTP-only, Secure cookies with SameSite=strict; or signed JWTs with short TTL and refresh tokens stored server-side.
- CSRF: protect write endpoints accordingly (SameSite cookies + CSRF token where applicable).
- Data privacy: follow retention rules; support account deletion and data export on request.
- PCI: do not store card numbers; use Stripe-hosted forms and tokens. Ensure webhooks and server calls use server-side secrets.

## Monitoring & Alerts
- Monitor login failure spikes, password-reset abuse, webhook failures, and billing failures via logs and alerts.
- Track metrics: new signups/day, active users, subscription churn, failed payments, support ticket volume.
- Expose admin endpoints to read those metrics (integrate with Admin Panel previously created).

## Edge Cases & Error Handling
- Stale Stripe webhook events: idempotency checks via event id.
- Partial provisioning failure: if team creation fails after signup, rollback or mark user for manual remediation.
- Billing disputes and refunds: provide admin tools (Captains) to issue refunds via Stripe Dashboard or Worker API (if permitted).

## MVP (v1) — Minimal, shippable set
- Email/password sign up + email verification
- Login + session management (cookie-based)
- Onboarding: create team, basic profile
- T&C acceptance recorded
- Subscription: Stripe Checkout for Team plan, webhook processing for invoice.payment_failed and customer.subscription.created
- Billing portal redirect
- Profile page and settings (name, email)
- Support ticket form creating entries in D1
- Account deletion (soft-delete with 30-day retention)

## Implementation Plan (4-week suggested split)
Week 1 — Auth & Onboarding
- Implement Worker endpoints for signup/login/logout
- Email verification and password reset flows (use transactional email provider)
- Basic profile and team creation in D1

Week 2 — Billing (Stripe)
- Configure Stripe products/prices
- Implement checkout session creation and return redirect
- Implement webhook handler and subscription record sync
- Add Billing Portal redirect

Week 3 — Settings & Support
- Settings UI + API (profile, notifications)
- Support ticket endpoint and basic UI
- Account deletion flow

Week 4 — Testing, RBAC, Hardening
- Add RBAC checks (Captains/Team Leads), audits, logging
- E2E tests for auth, billing, webhook handling
- Deploy to staging on Cloudflare Pages + Worker, test HuggingFace interactions

## Acceptance Criteria
- Users can sign up, verify email, log in, and create a team.
- Users can purchase a subscription via Stripe Checkout and see subscription state in portal.
- Stripe webhooks update subscription records in D1 reliably (idempotent handling).
- Users can request account deletion and data is scheduled for removal.
- RBAC prevents unauthorized billing or admin actions.

## Next Steps / Deliverables
- Review and approve MVP scope and timeline.
- Add environment secrets to the Worker (Stripe secret, email provider creds) and document deployment steps.
- I can scaffold the Worker auth endpoints and the basic frontend pages (`/auth/login`, `/auth/signup`, `/billing`) next.

---

*Built to align with IFCore skill guidance: use Cloudflare Workers for auth and API, Cloudflare Pages for static UI, HuggingFace Space remains the orchestrator for checks, and D1 is the lightweight DB. I followed the contracts in the IFCore skill for API naming and logging where relevant.*
