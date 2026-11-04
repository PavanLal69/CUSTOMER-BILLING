// Local copies of the Stageshow kit parts used by this frontend.
// Source: benjitaylor/skills — stageshow (MIT). See NOTICE.md.

import './stage.css'
import { LookContext } from './looks'
import type { ReactNode } from 'react'
import { Avatar } from './Avatar'
import { Badge } from './Badge'

export { LookContext, Avatar, Badge }

export function StageshowRoot({ children }: { children: ReactNode }) {
  return (
    <LookContext.Provider value={{ theme: 'light', palette: 'accent', fidelity: 'standard', layout: 'wide' }}>
      <div className="ss-stage cx-app">{children}</div>
    </LookContext.Provider>
  )
}
