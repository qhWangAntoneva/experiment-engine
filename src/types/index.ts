export interface SimulationParams {
  name: string
  description: string
  parameters: Record<string, number | string | boolean>
}

export interface SimulationResult {
  id: string
  timestamp: string
  params: SimulationParams
  outputs: Record<string, number | string>
  status: 'success' | 'failed' | 'running'
  duration: number
}

export interface MetricCardData {
  label: string
  value: string | number
  unit?: string
  trend?: 'up' | 'down' | 'stable'
  change?: number
  status?: 'normal' | 'warning' | 'critical'
}

export interface NavItem {
  label: string
  path: string
  icon: string
}
