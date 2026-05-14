import { useState, useCallback, useRef } from 'react'

export interface ModalConfig {
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  isDangerous?: boolean
}

export function useModal() {
  const [isOpen, setIsOpen] = useState(false)
  const [config, setConfig] = useState<ModalConfig | null>(null)
  const resolveRef = useRef<((value: boolean) => void) | null>(null)

  const confirm = useCallback(
    async (modalConfig: ModalConfig): Promise<boolean> => {
      setConfig(modalConfig)
      setIsOpen(true)

      return new Promise((resolve) => {
        resolveRef.current = resolve
      })
    },
    []
  )

  const handleConfirm = useCallback(() => {
    if (resolveRef.current) {
      resolveRef.current(true)
    }
    setIsOpen(false)
    setConfig(null)
    resolveRef.current = null
  }, [])

  const handleCancel = useCallback(() => {
    if (resolveRef.current) {
      resolveRef.current(false)
    }
    setIsOpen(false)
    setConfig(null)
    resolveRef.current = null
  }, [])

  return {
    isOpen,
    config,
    confirm,
    handleConfirm,
    handleCancel,
  }
}
