import { useState, useEffect, useCallback } from 'react'
import type { NoteFile, GraphNode, GraphLink } from '../types'

interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

/**
 * Hook that parses all notes for [[wiki links]] and builds graph data
 */
export function useGraph(notes: NoteFile[], vaultDir: string) {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] })

  const buildGraph = useCallback(async () => {
    if (!vaultDir || notes.length === 0) {
      setGraphData({ nodes: [], links: [] })
      return
    }

    const nodesMap = new Map<string, GraphNode>()
    const links: GraphLink[] = []

    // Add all existing notes as nodes
    for (const note of notes) {
      nodesMap.set(note.name.toLowerCase(), {
        id: note.name,
        path: note.path,
      })
    }

    // Parse each note for [[links]]
    for (const note of notes) {
      try {
        const content = await window.api.readNote(note.path)
        const regex = /\\?\[\\?\[([^\]]+)\]\]/g
        let match

        while ((match = regex.exec(content)) !== null) {
          const targetName = match[1].trim()
          const targetKey = targetName.toLowerCase()

          // Only draw links to notes that actually exist; skip phantom nodes
          if (!nodesMap.has(targetKey)) continue

          links.push({
            source: note.name,
            target: nodesMap.get(targetKey)!.id,
          })
        }
      } catch {
        // Skip notes that can't be read
      }
    }

    setGraphData({
      nodes: Array.from(nodesMap.values()),
      links,
    })
  }, [notes, vaultDir])

  useEffect(() => {
    buildGraph()
  }, [buildGraph])

  return { ...graphData, refresh: buildGraph }
}
