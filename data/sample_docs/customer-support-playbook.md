# Northstar Labs Customer Support Playbook

> Owner: Customer Experience  
> Last reviewed: 10 October 2026

## 1. Purpose

This playbook defines how the Orbit support team triages tickets, communicates
with customers, escalates incidents, handles refunds, and closes the feedback
loop. It applies to support engineers, team leads, and incident commanders.

## 2. Support channels and hours

- **Email and in-app chat:** 08:00 to 20:00 IST, Monday to Saturday.
- **P1 phone bridge:** 24/7 for customers on the Enterprise plan.
- **Status page:** updated for any customer-visible incident within **30 minutes**
  of confirmation.
- **Security reports:** route to security@northstar.example and do not discuss
  details in the customer ticket.

## 3. Ticket priority matrix

| Priority | Definition | First response | Update cadence | Target resolution |
| --- | --- | --- | --- | --- |
| P1 Critical | Production is down or severely degraded; no workaround; multiple users or a business-critical workflow is blocked | 15 minutes | Every 30 minutes | 4 hours |
| P2 High | A major feature is impaired or a single business-critical workflow is blocked; workaround is limited | 1 hour | Every 4 hours | 1 business day |
| P3 Normal | A non-critical feature is broken or a question has a reasonable workaround | 8 business hours | Every 2 business days | 3 business days |
| P4 Low | Cosmetic issue, documentation request, or feature suggestion | 2 business days | As needed | 10 business days |

Priority is based on **customer impact**, not on who reported the ticket or how
upset they are. When impact is unclear, start at P2 and reassess after triage.

## 4. Ticket lifecycle

1. **New** — ticket is created by email, chat, the API, or the customer portal.
2. **Triaged** — priority, category, and owner are set. This must happen within
   **30 minutes** for P1/P2 and **4 business hours** for P3/P4.
3. **In progress** — the owner is actively working and has posted an internal
   note describing the current hypothesis.
4. **Waiting on customer** — the team needs information or confirmation. The
   customer is told exactly what is needed.
5. **Resolved** — the fix or answer is confirmed. The resolution note must be
   customer-safe and must not contain internal hostnames, credentials, or stack
   traces.
6. **Closed** — automatically closes **5 days** after resolution unless the
   customer replies.

Every customer-visible reply must include the next step and the next update time.
Internal notes must never be pasted into the customer reply.

## 5. Escalation

- **P1:** page the on-call support engineer through PagerDuty immediately, open
  the **#incident** channel, and assign an incident commander. Notify the
  Director of Customer Experience within 30 minutes.
- **P2:** escalate to the support team lead after 30 minutes without progress.
  Engage engineering on-call if the issue is reproducible in production.
- **P3/P4:** escalate to the team lead if the target resolution date is at risk.
- Escalation is not blame. Include the ticket ID, impact, steps tried, and the
  specific help needed.
- Do not promise a fix date until engineering has confirmed it. Say what is known
  and when the next update will come.

## 6. Refunds and service credits

- Refund requests are eligible within **30 days of the charge**.
- Duplicate charges are refunded in full regardless of the 30-day window.
- Service-level credits follow the customer's contract. Enterprise credits are
  calculated against the monthly fee for the affected service.
- Refunds above **INR 50,000** require manager approval. Credits above
  **INR 100,000** require Finance approval.
- Never promise a refund or credit in chat before the approval is recorded in the
  ticket. Tell the customer it is under review and give a decision date.
- Refunds are returned to the original payment method within **7 to 10 business
  days** after approval.

## 7. Customer feedback and closed-loop process

- A **CSAT survey** is sent when a ticket is resolved. Customers rate the support
  experience from **1 to 5**.
- A score of **1 or 2 is a detractor**. The ticket owner must contact the customer
  within **one business day**, acknowledge the experience, and document the root
  cause.
- Feedback is tagged with product area, journey stage, and theme in the
  **Voice of Customer** dashboard.
- The support lead reviews feedback weekly. Product and Engineering review
  aggregated themes on the **first Tuesday of each month**.
- Customers who ask not to be contacted again are excluded from follow-up but
  their score still counts in aggregate reporting.
- Do not edit or delete a negative survey response. Add context as an internal
  note instead.

## 8. Data privacy and account security

- Verify the requester's identity before changing account settings, billing
  details, SSO configuration, or data-retention settings.
- Acceptable verification: a signed-in session plus confirmation of the account
  owner's email, or a callback to the phone number on file.
- Never ask for a password, one-time code, full payment-card number, or government
  ID in a support ticket.
- Do not attach raw production logs that contain personal data. Redact names,
  email addresses, tokens, and IP addresses before sharing.
- A suspected data breach is a **P1 security incident**. Follow the Information
  Security Policy immediately.

## 9. Writing style

- Lead with the answer or the next step, then explain.
- Use plain language. Avoid internal jargon and unexpanded acronyms.
- Acknowledge impact without over-apologizing. Be specific about what happens next.
- Use bullet points for steps and include links to public documentation.
- Match the customer's language when the team has coverage; otherwise use English
  and offer a translated follow-up when possible.

## 10. Quality assurance

- Team leads sample **10% of closed tickets** each week.
- The quality score covers accuracy, tone, ownership, timeliness, and privacy.
- The team target is a **90% quality score**. Scores below 80% trigger a coaching
  plan, not automatic disciplinary action.
- Recurring quality issues are added to the weekly support enablement session.
