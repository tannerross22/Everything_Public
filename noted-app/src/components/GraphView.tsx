import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import type { GraphNode, GraphLink } from '../types'

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
}

export default function GraphView({ nodes, links, onNodeClick }: GraphViewProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

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

    // Force simulation
    const simulation = d3.forceSimulation(simNodes)
      .force('link', d3.forceLink<D3Node, D3Link>(simLinks)
        .id((d) => d.id)
        .distance(120)
      )
      .force('charge', d3.forceManyBody().strength(-250))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(35))

    // Draw links
    const link = g.append('g')
      .selectAll('line')
      .data(simLinks)
      .join('line')
      .attr('stroke', '#585b70')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.6)

    // Draw nodes
    const node = g.append('g')
      .selectAll('g')
      .data(simNodes)
      .join('g')
      .attr('cursor', 'pointer')
      .call(drag(simulation) as any)

    // Node circles
    node.append('circle')
      .attr('r', (d) => Math.min(6 + (d.linkCount || 0) * 3, 20))
      .attr('fill', (d) => d.path ? '#cba6f7' : '#585b70')
      .attr('stroke', (d) => d.path ? '#9370db' : '#45475a')
      .attr('stroke-width', 2)

    // Node labels
    node.append('text')
      .text((d) => d.id)
      .attr('text-anchor', 'middle')
      .attr('dy', (d) => Math.min(6 + (d.linkCount || 0) * 3, 20) + 14)
      .attr('fill', (d) => d.path ? '#cdd6f4' : '#6c7086')
      .attr('font-size', '11px')
      .attr('font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif')

    // Hover effects
    node
      .on('mouseenter', function () {
        d3.select(this).select('circle')
          .transition().duration(200)
          .attr('fill', '#d4b8ff')
          .attr('stroke-width', 3)
      })
      .on('mouseleave', function (_event, d) {
        d3.select(this).select('circle')
          .transition().duration(200)
          .attr('fill', d.path ? '#cba6f7' : '#585b70')
          .attr('stroke-width', 2)
      })

    // Click handler
    node.on('click', (_event, d) => {
      onNodeClick(d.id)
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

// Drag behavior
function drag(simulation: d3.Simulation<D3Node, D3Link>) {
  function dragstarted(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
  }

  function dragged(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
    event.subject.fx = event.x
    event.subject.fy = event.y
  }

  function dragended(event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>) {
    if (!event.active) simulation.alphaTarget(0)
    event.subject.fx = null
    event.subject.fy = null
  }

  return d3.drag<SVGGElement, D3Node>()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended)
}
