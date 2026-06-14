const SIDEBAR_WIDTH_KEY = 'noted_sidebar_width'
const SIDEBAR_COLLAPSED_KEY = 'noted_sidebar_collapsed'

const DEFAULT_WIDTH = 260
const DEFAULT_COLLAPSED = false

export interface SidebarState {
  width: number
  collapsed: boolean
}

export function loadSidebarState(): SidebarState {
  try {
    const widthRaw = localStorage.getItem(SIDEBAR_WIDTH_KEY)
    const collapsedRaw = localStorage.getItem(SIDEBAR_COLLAPSED_KEY)

    return {
      width: widthRaw ? parseInt(widthRaw, 10) : DEFAULT_WIDTH,
      collapsed: collapsedRaw ? JSON.parse(collapsedRaw) : DEFAULT_COLLAPSED,
    }
  } catch {
    return { width: DEFAULT_WIDTH, collapsed: DEFAULT_COLLAPSED }
  }
}

export function saveSidebarState(width: number, collapsed: boolean): void {
  try {
    localStorage.setItem(SIDEBAR_WIDTH_KEY, String(width))
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, JSON.stringify(collapsed))
  } catch {
    // silently fail if localStorage is unavailable
  }
}
