# Northstar Labs Information Security Policy

> Owner: Security Office  
> Last reviewed: 1 October 2026

## 1. Scope

This policy applies to all employees, contractors, interns, and vendors who access
Northstar Labs systems or customer data. It covers company-owned and personally
owned devices used for company work.

## 2. Passwords and multi-factor authentication

- Passwords must be at least **14 characters** and unique to each service.
- Use the company-approved password manager. Do not store passwords in browsers,
  spreadsheets, notes, or chat messages.
- **Multi-factor authentication (MFA)** is mandatory for email, code hosting,
  the cloud console, the People Portal, and all production systems.
- Passwords are rotated only when compromise is suspected. Repeated rotation is
  not required and often leads to weaker passwords.
- Never share MFA codes or approve an MFA prompt you did not initiate.

## 3. Devices and endpoint security

- Company laptops must have **full-disk encryption** enabled. BitLocker is the
  standard on Windows and FileVault on macOS.
- Screen lock must activate after **5 minutes** of inactivity.
- Security patches must be installed within **7 days** of release. Critical
  patches must be installed within **48 hours**.
- Personally owned devices may access email and chat only after enrolment in the
  company mobile-device management (MDM) profile.
- Only approved software may be installed on company laptops. Requests go to the
  IT Service Desk.

## 4. Network and VPN

- Connect to the company VPN before accessing internal admin tools, production
  dashboards, or customer records from outside a Northstar office.
- Do not use public Wi-Fi for company work without the VPN active.
- Split tunnelling is disabled on managed devices.
- Do not connect unauthorized network devices, routers, or Wi-Fi extenders to
  office networks.

## 5. Data classification

| Class | Examples | Handling |
| --- | --- | --- |
| Public | Marketing site, published docs | May be shared externally |
| Internal | Policies, roadmaps, internal chat | Company staff only |
| Confidential | Customer tickets, contracts, logs | Need-to-know; encrypted at rest |
| Restricted | PII, credentials, payment data, health data | Explicit approval; never in public tools |

Customer ticket content and attachments are **Confidential**. Personal data such
as names, email addresses, phone numbers, and government identifiers is
**Restricted**. Do not copy Restricted data into email, chat, personal cloud
storage, or unapproved AI tools.

## 6. Access management

- Access follows **least privilege** and is granted only for a documented business
  need.
- Request access through the **Access Portal**. The request requires manager
  approval and, for production or Restricted data, Security Office approval.
- The standard provisioning SLA is **one business day** after all approvals.
- Access is reviewed **quarterly**. Managers must remove access that is no longer
  required.
- Shared accounts are prohibited. Service accounts must be owned by a named team
  and stored in the approved secrets manager.

## 7. Phishing and security incidents

- Report suspected phishing to **security@northstar.example** or post in
  **#security-incidents** within **15 minutes** of noticing it.
- Do not click links, open attachments, or reply to a suspected phishing message.
  Use the "Report phishing" button in the mail client.
- If you entered credentials on a suspicious site, report it immediately and
  change the password from a known-good device.
- Security incidents are classified as **P1 (critical), P2 (high), P3 (medium),
  or P4 (low)**. The Security Office assigns severity and leads the response.
- A P1 incident requires the on-call security engineer to acknowledge the page
  within **15 minutes**. The incident commander opens a dedicated incident
  channel and starts a timeline.

## 8. Lost or stolen devices

- Report a lost or stolen device to the Security Office within **one hour** of
  discovery.
- The IT team will remotely revoke sessions and wipe the device where possible.
- File a police report when local law requires it. Do not attempt to recover a
  stolen device yourself.
- Any device that stored Restricted data must be treated as a potential data
  breach until the Security Office completes an assessment.

## 9. Clean desk and clear screen

- Lock your screen whenever you leave your desk, even at home.
- Do not leave notebooks, printed customer data, or removable media visible in
  shared spaces.
- Shred paper containing Confidential or Restricted information.
- Whiteboards used for incident response must be erased at the end of the
  incident.

## 10. Artificial intelligence tools

- Only AI tools approved by the Security Office may be used for company work. The
  current approved list is maintained in the **AI Tools Register**.
- Do not paste customer data, source code, credentials, or Restricted data into
  public or consumer AI tools.
- When using an approved AI assistant, redact names, email addresses, account
  numbers, and other identifiers first.
- AI-generated output must be reviewed by a human before it is sent to a customer
  or used in a production change.
- Suspected data leakage through an AI tool is a **P1 security incident**.
