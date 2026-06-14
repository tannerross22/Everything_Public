import '../styles/SettingsPage.css'

interface SettingsPageProps {
  onClose: () => void
}

export default function SettingsPage({ onClose }: SettingsPageProps) {
  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-panel" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h1 className="settings-title">Settings</h1>
          <button className="settings-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="settings-content">
          <p className="settings-placeholder">Settings coming soon...</p>
        </div>
      </div>
    </div>
  )
}
