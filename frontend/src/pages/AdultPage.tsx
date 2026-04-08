import { useDashboardLayout } from '../context/DashboardLayoutContext'
import { DashboardWorkspace } from '../features/dashboard/DashboardWorkspace'

export function AdultPage() {
  const { selectedPlateWells } = useDashboardLayout()
  return <DashboardWorkspace variant="adult" plateWells={selectedPlateWells} />
}
