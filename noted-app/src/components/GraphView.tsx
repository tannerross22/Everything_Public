import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import type { GraphNode, GraphLink } from '../types'
import { getTopLevelFolder, DULL_COLOR } from '../hooks/useFolderColors'

interface D3Node extends GraphNode, d3.SimulationNodeDatum {
  linkCount?: number
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  source: string | D3Node
  target: string | D3Node
}

interface GraphViewProps {
  nodes: GraphNode[]
  links: GraphLink[]
  onNodeClick: (noteId: string) => void
  folderColors: Record<string, string>
  vaultDir: string
}

export default function GraphView({ nodes, links, onNodeClick, folderColors, vaultDir }: GraphViewProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const linkSelectionRef = useRef<d3.Selection<d3.BaseType, any, d3.BaseType, unknown> | null>(null)
  const originalPositionsRef = useRef<Map<string, { x: number; y: number }> | null>(null)

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || nodes.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove() // Clear previous render

    const container = containerRef.current
    const width = container.clientWidth
    const height = container.clientHeight

    svg.attr('width', width).attr('height', height)

    // Count links per node for sizing
    const linkCounts = new Map<string, number>()
    links.forEach((l) => {
      linkCounts.set(l.source, (linkCounts.get(l.source) || 0) + 1)
      linkCounts.set(l.target, (linkCounts.get(l.target) || 0) + 1)
    })

    // Create simulation data (deep copy)
    const simNodes: D3Node[] = nodes.map((n) => ({
      ...n,
      linkCount: linkCounts.get(n.id) || 0,
    }))

    // Calculate 90th percentile for initial positioning
    const sortedLinkCounts = simNodes.map(n => n.linkCount || 0).sort((a, b) => b - a)
    const threshold90 = sortedLinkCounts[Math.floor(sortedLinkCounts.length * 0.1)]

    // Calculate outer radius first - needed for initial positioning
    const maxLinks = Math.max(...simNodes.map((d) => d.linkCount || 0), 1)
    const outerRadius = Math.min(width, height) * 0.40

    // Spawn nodes with reverse initial positions: small nodes start center, large nodes start outside
    // As forces apply, large nodes are pulled inward and naturally displace small nodes outward
    const hubNodes = simNodes.filter(n => (n.linkCount || 0) >= threshold90)
    const mediumNodes = simNodes.filter(n => (n.linkCount || 0) > 5 && (n.linkCount || 0) < threshold90)
    const smallNodes = simNodes.filter(n => (n.linkCount || 0) <= 5)

    // Small nodes: start in center (they'll get pushed outward as larger nodes are pulled inward)
    smallNodes.forEach((node, idx) => {
      const angle = (idx / Math.max(smallNodes.length, 1)) * Math.PI * 2
      const centerSpread = 60
      node.x = width / 2 + Math.cos(angle) * centerSpread * Math.random()
      node.y = height / 2 + Math.sin(angle) * centerSpread * Math.random()
    })

    // Medium nodes: start at middle-outer ring
    mediumNodes.forEach((node, idx) => {
      const angle = (idx / Math.max(mediumNodes.length, 1)) * Math.PI * 2
      const radius = outerRadius * 0.6
      node.x = width / 2 + Math.cos(angle) * radius
      node.y = height / 2 + Math.sin(angle) * radius
    })

    // Hub nodes: start far outside (they'll be pulled inward by strong radial force)
    hubNodes.forEach((node, idx) => {
      const angle = (idx / Math.max(hubNodes.length, 1)) * Math.PI * 2
      const radius = outerRadius * 1.5  // Start outside, get pulled in while displacing others out
      node.x = width / 2 + Math.cos(angle) * radius
      node.y = height / 2 + Math.sin(angle) * radius
    })

    const simLinks: D3Link[] = links.map((l) => ({
      source: l.source,
      target: l.target,
    }))

    // Create zoom group
    const g = svg.append('g')

    // Zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    const nodeRadius = (d: D3Node) => {
      const linkCount = d.linkCount || 0
      if (linkCount >= threshold90) {
        // Top 10% most connected: range 8-18px for good contrast
        return Math.min(18, 8 + (linkCount - threshold90) * 1.0)
      } else {
        // Bottom 90%: much smaller, minimal variation (5-7px)
        return 5 + (linkCount / threshold90) * 2
      }
    }

    // Add randomness to radial positions to avoid void in middle
    // 0 links → outerRadius (edge), maxLinks → near center with randomness (0-50px)
    const radialTarget = (d: D3Node) => {
      const ratio = (d.linkCount || 0) / maxLinks
      // Deterministic randomness per node ID to break symmetry
      const randomness = Math.sin(d.id.charCodeAt(0) * 12.9898) * 0.5 + 0.5

      // Hub nodes (high ratio) target very close to center (0-50px) with randomness
      // Peripheral nodes (low ratio) target toward outer ring
      // Formula: hub randomness scales with ratio, outer ring scales with (1-ratio)
      const target = outerRadius * (1 - ratio) + randomness * 50 * ratio

      if (d.id === 'App Component') {
        console.log('[Graph] App Component radial:', { linkCount: d.linkCount, ratio, randomness, target, maxLinks })
      }
      return target
    }

    // Distance kept mostly constant; slight scaling to prevent tight clustering
    const linkDistance = (d: D3Link) => {
      const sourceLinks = (d.source as D3Node).linkCount || 0
      const targetLinks = (d.target as D3Node).linkCount || 0
      const avgLinks = (sourceLinks + targetLinks) / 2
      return 160 + avgLinks * 1.5  // Increased base distance for more spread
    }

    // Charge (repulsion) - reduced for hubs so they don't overwhelm the centering radial force
    const chargeStrength = (d: D3Node) => {
      const linkCount = d.linkCount || 0
      if (linkCount >= threshold90) {
        // Hub nodes: minimal repulsion so radial force can pull them to center
        return -30
      }
      // Other nodes: standard repulsion
      return -40 - linkCount * 1
    }

    // Track if any node is being dragged
    let isDraggingNode = false

    // Extract folder path from node path
    const getFolder = (path: string): string => {
      // Get everything except the filename
      const parts = path.split(/[/\\]/)
      parts.pop() // Remove filename
      return parts.join('/') // Return folder path
    }

    // Custom force to cluster nodes from the same folder (disabled during drag to prevent jumping)
    const folderClusterForce = () => {
      if (isDraggingNode) return // Skip clustering while dragging

      for (const node of simNodes) {
        const nodeFolder = getFolder(node.path)

        // Find other nodes in the same folder
        for (const other of simNodes) {
          if (node === other || !other.x || !other.y || !node.x || !node.y) continue

          const otherFolder = getFolder(other.path)
          if (nodeFolder === otherFolder) {
            // Attractive force between nodes in same folder
            const dx = other.x - node.x
            const dy = other.y - node.y
            const distance = Math.sqrt(dx * dx + dy * dy)

            if (distance > 1) {
              const strength = 0.003 // Minimal clustering to avoid jitter
              const fx = (dx / distance) * strength
              const fy = (dy / distance) * strength

              node.vx = (node.vx || 0) + fx
              node.vy = (node.vy || 0) + fy
              other.vx = (other.vx || 0) - fx
              other.vy = (other.vy || 0) - fy
            }
          }
        }
      }
    }

    const simulation = d3.forceSimulation(simNodes)
      .force('link', d3.forceLink<D3Node, D3Link>(simLinks)
        .id((d) => d.id)
        .distance(linkDistance as any)
      )
      .force('charge', d3.forceManyBody().strength(chargeStrength as any))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('radial', d3.forceRadial<D3Node>(
        (d) => {
          // Isolated/unfiled nodes (0-1 connections) pushed beyond viewport edge for clear separation
          // Medium connectivity (2-5 connections) at mid-range
          // Hub nodes (6+) gently pulled to center to prevent drift to periphery
          if (d.linkCount === 0 || d.linkCount === 1) {
            return outerRadius * 2.0  // Double distance - massive gap between hub and isolated files
          } else if (d.linkCount <= 5) {
            return outerRadius * 0.25  // Much closer to hub center
          }
          // High connectivity hub nodes: gentle pull to center (0 radius) to prevent outward drift
          return 0
        },
        width / 2,
        height / 2
      ).strength((d) => {
        // Tiered force strength: strong for outer rings, strong for hub nodes to keep them centered
        if (d.linkCount === 0 || d.linkCount === 1) {
          return 0.3  // Strong outward push for isolated files
        } else if (d.linkCount <= 5) {
          return 0.15  // Medium inward pull for weakly connected
        }
        // High connectivity: strong inward pull to overcome charge repulsion and keep centered
        return 0.4
      }))
      .force('folderCluster', folderClusterForce as any)
      .force('collision', d3.forceCollide().radius((d) => nodeRadius(d as D3Node) + 30))
      .alphaDecay(0.04)

    // Draw links — grey by default, highlighted when node is selected
    const link = g.append('g')
      .selectAll('line')
      .data(simLinks)
      .join('line')
      .attr('stroke', '#2a2a3e')
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.3)

    // Store link selection in ref so it can be updated when selectedNodeId changes
    linkSelectionRef.current = link

    // Draw nodes
    const node = g.append('g')
      .selectAll('g')
      .data(simNodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(drag(simulation, setSelectedNodeId, () => setSelectedNodeId(null), (isDragging) => {
        isDraggingNode = isDragging
      }, simNodes, originalPositionsRef) as any)

    // Resolve node color from top-level folder
    const nodeColor = (d: D3Node): string => {
      if (!d.path || !vaultDir) return DULL_COLOR
      const folder = getTopLevelFolder(d.path, vaultDir)
      if (!folder) return DULL_COLOR
      return folderColors[folder] ?? DULL_COLOR
    }

    // Hover color: slightly brighter version of the node color
    const nodeHoverColor = (d: D3Node): string => {
      const base = d3.color(nodeColor(d))
      return base ? base.brighter(0.4).formatHex() : nodeColor(d)
    }

    // Stroke: slightly darker version
    const nodeStroke = (d: D3Node): string => {
      const base = d3.color(nodeColor(d))
      return base ? base.darker(0.5).formatHex() : '#45475a'
    }

    // Node circles
    node.append('circle')
      .attr('r', nodeRadius)
      .attr('fill', nodeColor)
      .attr('stroke', nodeStroke)
      .attr('stroke-width', 2)

    // Node labels
    node.append('text')
      .text((d) => d.id)
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => nodeRadius(d) + 16)
      .attr('fill', '#cdd6f4')
      .attr('font-size', '13px')
      .attr('font-weight', '500')
      .attr('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif')

    // Hover effects
    node
      .on('mouseenter', function (_event, d) {
        d3.select(this).select('circle')
          .transition().duration(150)
          .attr('r', nodeRadius(d) * 1.2)
          .attr('fill', nodeHoverColor(d))
          .attr('stroke-width', 3)
      })
      .on('mouseleave', function (_event, d) {
        d3.select(this).select('circle')
          .transition().duration(150)
          .attr('r', nodeRadius(d))
          .attr('fill', nodeColor(d))
          .attr('stroke-width', 2)
      })

    // Track if this was a drag or a click
    let isDragging = false

    // Click handler - only navigate on click, not on drag
    node.on('click', (_event, d) => {
      if (!isDragging) {
        onNodeClick(d.id)
      }
    })

    // Tick update
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
    })

    // Cleanup
    return () => {
      simulation.stop()
    }
  }, [nodes, links, onNodeClick])

  // Update link colors when selection changes
  useEffect(() => {
    if (!linkSelectionRef.current) return

    const link = linkSelectionRef.current

    link
      .attr('stroke', (d: any) => {
        if (!selectedNodeId) return '#2a2a3e'
        const source = typeof d.source === 'string' ? d.source : (d.source as any).id
        const target = typeof d.target === 'string' ? d.target : (d.target as any).id
        if (source === selectedNodeId || target === selectedNodeId) {
          return '#cba6f7' // Bright purple accent
        }
        return '#2a2a3e' // Dark color close to background
      })
      .attr('stroke-width', (d: any) => {
        if (!selectedNodeId) return 2
        const source = typeof d.source === 'string' ? d.source : (d.source as any).id
        const target = typeof d.target === 'string' ? d.target : (d.target as any).id
        if (source === selectedNodeId || target === selectedNodeId) {
          return 3
        }
        return 2
      })
      .attr('stroke-opacity', (d: any) => {
        if (!selectedNodeId) return 0.3 // Grey by default
        const source = typeof d.source === 'string' ? d.source : (d.source as any).id
        const target = typeof d.target === 'string' ? d.target : (d.target as any).id
        if (source === selectedNodeId || target === selectedNodeId) {
          return 1 // Highlighted in purple
        }
        return 0 // Invisible when not connected
      })
  }, [selectedNodeId])

  return (
    <div ref={containerRef} className="graph-container">
      {nodes.length === 0 ? (
        <div className="graph-empty">
          <p>No notes to visualize yet.</p>
          <p>Create notes with [[wiki links]] to see the graph.</p>
        </div>
      ) : (
        <svg ref={svgRef} className="graph-svg" />
      )}
    </div>
  )
}

// Drag behavior — highlights connections while dragging, remembers original positions to revert on release
function drag(
  simulation: d3.Simulation<D3Node, D3Link>,
  onDragStart: (id: string) => void,
  onDragEnd: () => void,
  setDraggingNode: (isDragging: boolean) => void,
  simNodes: D3Node[],
  originalPositionsRef: React.MutableRefObject<Map<string, { x: number; y: number }> | null>
) {
  function dragstarted(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
    // Save original positions of all nodes before dragging
    const positions = new Map<string, { x: number; y: number }>()
    for (const node of simNodes) {
      if (node.x !== undefined && node.y !== undefined) {
        positions.set(node.id, { x: node.x, y: node.y })
      }
    }
    originalPositionsRef.current = positions

    if (!event.active) simulation.alphaTarget(0.02).restart()  // Very low alpha during drag - only local movement
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
    // Show connections and disable clustering while dragging
    onDragStart(event.subject.id)
    setDraggingNode(true)
  }

  function dragged(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
    event.subject.fx = event.x
    event.subject.fy = event.y
  }

  function dragended(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
    // Release the node and let it settle where it is
    event.subject.fx = null
    event.subject.fy = null

    // Clear selection immediately so connections turn grey
    onDragEnd()
    setDraggingNode(false)

    // Restart simulation at normal alpha to let graph settle naturally
    if (!event.active) simulation.alphaTarget(0).restart()
  }

  return d3.drag<SVGGElement, D3Node>()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended)
}
