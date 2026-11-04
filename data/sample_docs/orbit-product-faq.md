# Orbit Product FAQ

> Owner: Product Marketing  
> Last reviewed: 5 October 2026

## 1. What is Orbit?

Orbit is a customer-support platform that brings email, chat, voice, and API
tickets into one queue. Teams use Orbit to triage requests, automate routing,
measure response times, and close the loop on customer feedback.

## 2. Plans and pricing

| Plan | Monthly price | Included seats | Key features |
| --- | --- | --- | --- |
| Starter | INR 2,500 per agent | Up to 5 | Email and chat, shared inbox, basic reporting |
| Growth | INR 4,500 per agent | Up to 50 | Automation, SLAs, CSAT, Slack and Jira integrations |
| Enterprise | Custom | Unlimited | SAML SSO, SCIM, data residency, audit logs, premium support |

Annual plans receive a **15% discount**. Prices exclude applicable taxes. Overage
seats are billed at the plan rate and appear on the next invoice.

## 3. Is there a free trial?

Yes. New customers get a **14-day free trial** with Growth features. No credit card
is required. Trial workspaces are limited to **10 agents** and **1,000 tickets**.
At the end of the trial, the workspace becomes read-only for 30 days before data
is scheduled for deletion.

## 4. Do you support SSO and SCIM?

- **SAML 2.0 SSO** is available on Growth and Enterprise plans.
- **SCIM user provisioning** is available on Enterprise only.
- Just-in-time provisioning is supported with SAML. Domain verification is
  required before SSO can be enforced.
- Customers can test SSO in a sandbox workspace before enforcing it in production.

## 5. What integrations are available?

Orbit has native integrations with **Slack, Microsoft Teams, Jira, Salesforce,
HubSpot, Zapier, and PagerDuty**. Webhooks and a REST API are available on all
paid plans. The API uses token authentication and supports ticket, contact,
comment, and report endpoints.

## 6. Where is data stored, and for how long?

- Customers can choose **India** or **EU** data residency on Enterprise. Growth
  and Starter workspaces are hosted in India.
- The default retention period for closed tickets and attachments is **13 months**.
- Enterprise customers can configure retention from **30 days to 7 years**.
- Backups are encrypted and retained for **35 days**.
- Deleted workspaces are purged from active systems within **30 days** and from
  backups within **90 days**.

## 7. What is the uptime commitment?

Enterprise has a **99.9% monthly uptime service-level objective (SLO)** for the
core ticket and chat services. Growth has a **99.5% monthly SLO**. Planned
maintenance is announced at least **72 hours** in advance and is excluded from
downtime calculations. Service credits are available when the SLO is missed and
must be requested within **30 days** of the affected month.

## 8. Which security certifications does Orbit have?

Orbit maintains **SOC 2 Type II** and **ISO 27001** certifications. The platform
supports GDPR and India's Digital Personal Data Protection Act (DPDP). Enterprise
customers can request the latest audit reports and a completed security
questionnaire from their account manager. Penetration tests are performed at least
annually by an independent firm.

## 9. What are the API rate limits?

- Growth: **600 requests per minute** per workspace.
- Enterprise: **3,000 requests per minute** per workspace.
- When a limit is exceeded, the API returns **HTTP 429** with a `Retry-After`
  header. Clients should back off exponentially and respect the header.
- Bulk exports and reporting endpoints have separate limits documented in the
  developer portal.

## 10. Does Orbit use customer data to train AI models?

No. Orbit's AI features, including suggested replies and ticket summarization, do
not train models on customer data. AI features are **opt-in** at the workspace
level. Customers can disable them at any time. Data sent to AI features stays in
the selected residency region and is not shared with third-party model providers
for training.

## 11. How do I get support?

- **Starter:** email and in-app chat, 08:00–20:00 IST, Monday to Saturday.
- **Growth:** email, chat, and priority queue, with the SLAs in the Customer
  Support Playbook.
- **Enterprise:** 24/7 P1 phone bridge, a named technical account manager, and
  quarterly service reviews.
- Security issues should be reported to security@northstar.example, not through
  the general support queue.
