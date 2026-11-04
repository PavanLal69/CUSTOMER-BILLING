export type Priority = 'P1' | 'P2' | 'P3' | 'P4'
export type Status = 'New' | 'In progress' | 'Waiting on customer' | 'Resolved'
export type Channel = 'Email' | 'Chat' | 'Portal' | 'API'
export type MessageRole = 'customer' | 'agent' | 'note'

export interface Message {
  id: string
  role: MessageRole
  author: string
  time: string
  body: string
}

export interface Ticket {
  id: string
  subject: string
  customer: string
  contact: string
  email: string
  plan: 'Starter' | 'Growth' | 'Enterprise'
  seats: number
  channel: Channel
  priority: Priority
  status: Status
  assignee: string
  updated: string
  age: string
  firstResponse: string
  target: string
  tags: string[]
  csat: 1 | 2 | 3 | 4 | 5
  feedback: string
  theme: string
  sentiment: 'Detractor' | 'Passive' | 'Promoter'
  acknowledged: boolean
  messages: Message[]
}

export const currentUser = {
  name: 'Maya Chen',
  role: 'Support lead',
}

export const tickets: Ticket[] = [
  {
    id: 'T-1042',
    subject: 'Checkout fails for UK postcodes',
    customer: 'Lumen Studio',
    contact: 'Priya Raman',
    email: 'priya@lumen.studio',
    plan: 'Growth',
    seats: 24,
    channel: 'Email',
    priority: 'P1',
    status: 'In progress',
    assignee: 'Maya Chen',
    updated: '12m',
    age: '48m',
    firstResponse: '4m',
    target: '4h',
    tags: ['Checkout', 'Billing'],
    csat: 2,
    feedback:
      "Support was fast, but the first answer was about card declines. Our issue is the postcode field. We lost a day of UK orders.",
    theme: 'Wrong first answer',
    sentiment: 'Detractor',
    acknowledged: false,
    messages: [
      {
        id: 'm1',
        role: 'customer',
        author: 'Priya Raman',
        time: '09:12',
        body:
          "Our UK customers can't get through checkout. The postcode field rejects every postcode with a space. It started after Tuesday's release and we're losing orders.",
      },
      {
        id: 'm2',
        role: 'agent',
        author: 'Maya Chen',
        time: '09:16',
        body:
          "Hi Priya — thanks for flagging this. I've reproduced it on mobile Safari and sent it to the checkout on-call. Could you share one example postcode and the browser version?",
      },
      {
        id: 'm3',
        role: 'customer',
        author: 'Priya Raman',
        time: '09:21',
        body: 'SW1A 1AA on Safari 18.2, and Chrome 131. Both fail. The field accepts it without the space.',
      },
      {
        id: 'm4',
        role: 'note',
        author: 'Maya Chen',
        time: '09:24',
        body:
          'Reproduced. Address step deployed Tue 09:14; the postcode regex appears to strip spaces. Eng #checkout is rolling back the validation change. Next update to Priya by 10:00.',
      },
    ],
  },
  {
    id: 'T-1041',
    subject: 'SSO login loop for Enterprise workspace',
    customer: 'Halvorsen & Co',
    contact: 'Jonas Halvorsen',
    email: 'jonas@halvorsen.co',
    plan: 'Enterprise',
    seats: 180,
    channel: 'Chat',
    priority: 'P2',
    status: 'Waiting on customer',
    assignee: 'Dev Patel',
    updated: '38m',
    age: '3h',
    firstResponse: '22m',
    target: '1d',
    tags: ['SSO', 'Access'],
    csat: 3,
    feedback: "Dev has been clear, but we're still waiting on our IdP team to rotate the metadata.",
    theme: 'Waiting on customer',
    sentiment: 'Passive',
    acknowledged: false,
    messages: [
      {
        id: 'm1',
        role: 'customer',
        author: 'Jonas Halvorsen',
        time: '06:40',
        body:
          'Our users are stuck in a redirect loop after enforcing SSO. We followed the setup guide and re-uploaded the metadata this morning.',
      },
      {
        id: 'm2',
        role: 'agent',
        author: 'Dev Patel',
        time: '07:02',
        body:
          'I can see the assertion is missing the workspace claim. Before we change anything on our side, can your IdP team regenerate the metadata with the updated attribute mapping?',
      },
      {
        id: 'm3',
        role: 'note',
        author: 'Dev Patel',
        time: '07:20',
        body:
          'Waiting on Halvorsen IdP team. If metadata is not updated by 12:00, offer a temporary bypass for the three admin accounts only.',
      },
    ],
  },
  {
    id: 'T-1039',
    subject: 'Duplicate charge on August invoice',
    customer: 'Pine & Co',
    contact: 'Elena Park',
    email: 'elena@pineandco.com',
    plan: 'Growth',
    seats: 12,
    channel: 'Email',
    priority: 'P2',
    status: 'New',
    assignee: 'Maya Chen',
    updated: '1h',
    age: '1h',
    firstResponse: '—',
    target: '1d',
    tags: ['Billing', 'Refund'],
    csat: 1,
    feedback: 'Charged twice and nobody has replied. This is blocking our renewal.',
    theme: 'Billing error',
    sentiment: 'Detractor',
    acknowledged: false,
    messages: [
      {
        id: 'm1',
        role: 'customer',
        author: 'Elena Park',
        time: '08:05',
        body:
          'We were charged twice for August. Invoice INV-2081 and INV-2082 both hit our card. I need this reversed today — our finance team is holding the renewal.',
      },
    ],
  },
  {
    id: 'T-1036',
    subject: 'Data retention request for closed workspace',
    customer: 'Brightline Health',
    contact: 'Dr. Anika Rao',
    email: 'anika@brightline.health',
    plan: 'Enterprise',
    seats: 65,
    channel: 'Portal',
    priority: 'P3',
    status: 'In progress',
    assignee: 'Ari Nwosu',
    updated: '2h',
    age: '5h',
    firstResponse: '41m',
    target: '3d',
    tags: ['Privacy', 'Retention'],
    csat: 5,
    feedback: 'Ari explained the 90-day backup window clearly and gave us a date.',
    theme: 'Privacy request',
    sentiment: 'Promoter',
    acknowledged: true,
    messages: [
      {
        id: 'm1',
        role: 'customer',
        author: 'Dr. Anika Rao',
        time: '05:32',
        body:
          'We closed our sandbox workspace last month. Can you confirm when everything is removed, including backups? We need this for our DPIA record.',
      },
      {
        id: 'm2',
        role: 'agent',
        author: 'Ari Nwosu',
        time: '06:13',
        body:
          'Confirmed: active data was purged within 30 days, and the 35-day backup cycle completes on 12 November. I will send a written confirmation for your DPIA once that window closes.',
      },
    ],
  },
  {
    id: 'T-1033',
    subject: 'Feedback: handoff lost conversation context',
    customer: 'Northwind Labs',
    contact: 'Sam Okafor',
    email: 'sam@northwindlabs.com',
    plan: 'Growth',
    seats: 31,
    channel: 'Chat',
    priority: 'P3',
    status: 'Resolved',
    assignee: 'Maya Chen',
    updated: '1d',
    age: '2d',
    firstResponse: '8m',
    target: '3d',
    tags: ['Feedback', 'Quality'],
    csat: 4,
    feedback: 'The first handoff dropped the earlier context, but Maya picked it up and fixed it quickly.',
    theme: 'Handoff quality',
    sentiment: 'Promoter',
    acknowledged: true,
    messages: [
      {
        id: 'm1',
        role: 'customer',
        author: 'Sam Okafor',
        time: 'Tue 14:08',
        body:
          'The second agent asked me to re-explain everything from the first chat. The fix was quick after that, but the handoff lost all the context.',
      },
      {
        id: 'm2',
        role: 'agent',
        author: 'Maya Chen',
        time: 'Tue 14:16',
        body:
          'That should not have happened. I have the full transcript and previous internal notes now. I will take over and send the summary to your team by 3pm.',
      },
    ],
  },
  {
    id: 'T-1029',
    subject: 'API 429 on bulk export',
    customer: 'Atlas Health',
    contact: 'Noah Williams',
    email: 'noah@atlas.health',
    plan: 'Enterprise',
    seats: 420,
    channel: 'API',
    priority: 'P2',
    status: 'Resolved',
    assignee: 'Dev Patel',
    updated: '2d',
    age: '2d',
    firstResponse: '11m',
    target: '1d',
    tags: ['API', 'Rate limits'],
    csat: 5,
    feedback: 'Clear guidance on Retry-After and a burst limit increase. Great.',
    theme: 'API limits',
    sentiment: 'Promoter',
    acknowledged: true,
    messages: [
      {
        id: 'm1',
        role: 'customer',
        author: 'Noah Williams',
        time: 'Mon 11:40',
        body:
          'Our nightly export is hitting 429s at about 700 requests per minute. We are on Enterprise and expected 3,000. Can you check the workspace limit?',
      },
      {
        id: 'm2',
        role: 'agent',
        author: 'Dev Patel',
        time: 'Mon 11:51',
        body:
          'Your workspace was still on the Growth rate limit after the plan change. I have corrected it and confirmed the 3,000/min limit. Please back off exponentially and respect Retry-After for the next run.',
      },
    ],
  },
  {
    id: 'T-1024',
    subject: 'Feature request: CSAT follow-up automation',
    customer: 'Juniper Design',
    contact: 'Mina Shah',
    email: 'mina@juniper.design',
    plan: 'Starter',
    seats: 5,
    channel: 'Email',
    priority: 'P4',
    status: 'New',
    assignee: 'Maya Chen',
    updated: '2d',
    age: '3d',
    firstResponse: '1d',
    target: '10d',
    tags: ['Feedback', 'Automation'],
    csat: 5,
    feedback: "We'd love a rule that opens a follow-up when a detractor survey lands.",
    theme: 'Product request',
    sentiment: 'Promoter',
    acknowledged: true,
    messages: [
      {
        id: 'm1',
        role: 'customer',
        author: 'Mina Shah',
        time: 'Mon 09:20',
        body:
          'Could Orbit automatically create a follow-up task when a customer gives a 1 or 2 CSAT score? We do it manually today and sometimes miss the one-day follow-up.',
      },
    ],
  },
]

export const assistantSuggestions = [
  'What is our P1 first-response target?',
  'When is a customer eligible for a refund?',
  'What should happen after a detractor CSAT?',
  'How long until a resolved ticket closes?',
]

export const csatBars = [46, 58, 52, 64, 71, 62, 78]
