/**
 * Date and status formatting utilities.
 */

export function formatDate(dateString) {
  if (!dateString) return '—';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(dateString) {
  if (!dateString) return '—';
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return formatDate(dateString);
}

export function getStatusConfig(status) {
  const configs = {
    JOB_CREATED:               { label: 'Created',    color: 'badge-created',   group: 'created' },
    SEARCH_STARTED:            { label: 'Searching',  color: 'badge-running',   group: 'running' },
    SEARCH_COMPLETED:          { label: 'Searching',  color: 'badge-running',   group: 'running' },
    SEARCHING:                 { label: 'Searching',  color: 'badge-running',   group: 'running' },
    SCRAPING_STARTED:          { label: 'Scraping',   color: 'badge-running',   group: 'running' },
    SCRAPING_COMPLETED:        { label: 'Scraping',   color: 'badge-running',   group: 'running' },
    SCRAPING:                  { label: 'Scraping',   color: 'badge-running',   group: 'running' },
    SUMMARIZATION_STARTED:     { label: 'Summarizing', color: 'badge-running',  group: 'running' },
    SUMMARIZATION_COMPLETED:   { label: 'Summarizing', color: 'badge-running',  group: 'running' },
    SUMMARIZING:               { label: 'Summarizing', color: 'badge-running',  group: 'running' },
    DEDUPLICATION_STARTED:     { label: 'Deduplicating', color: 'badge-running', group: 'running' },
    DEDUPLICATION_COMPLETED:   { label: 'Deduplicating', color: 'badge-running', group: 'running' },
    REPORT_GENERATION_STARTED: { label: 'Generating Report', color: 'badge-running', group: 'running' },
    REPORT_GENERATION_COMPLETED: { label: 'Generating Report', color: 'badge-running', group: 'running' },
    JOB_FINISHED:              { label: 'Completed',  color: 'badge-completed', group: 'completed' },
    JOB_FAILED:                { label: 'Failed',     color: 'badge-failed',    group: 'failed' },
    FAILED:                    { label: 'Failed',     color: 'badge-failed',    group: 'failed' },
  };
  return configs[status] || { label: status, color: 'badge-created', group: 'unknown' };
}
