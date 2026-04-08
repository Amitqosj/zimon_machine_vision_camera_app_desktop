import { useDashboardLayout } from '../context/DashboardLayoutContext'
import { DashboardWorkspace } from '../features/dashboard/DashboardWorkspace'

export function LarvalPage() {
  const { selectedPlateWells } = useDashboardLayout()
  return <DashboardWorkspace variant="larval" plateWells={selectedPlateWells} />
}
