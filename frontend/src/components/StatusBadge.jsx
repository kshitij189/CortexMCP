/**
 * Reusable status badge component with color mapping per workflow stage.
 */
import { getStatusConfig } from '../utils/formatters';

export default function StatusBadge({ status }) {
  const { label, color } = getStatusConfig(status);

  return (
    <span className={`badge ${color}`}>
      {label}
    </span>
  );
}
