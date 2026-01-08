/**
 * DOILink Component
 * Displays DOI as a clickable link with external link icon
 * SPEC-CROSSREF-001: REQ-EVT-004
 */

interface DOILinkProps {
  /** DOI string (e.g., "10.1234/example") */
  doi: string | null;
  /** Pre-formatted DOI URL (e.g., "https://doi.org/10.1234/example") */
  doiUrl?: string | null;
  /** Optional className for custom styling */
  className?: string;
}

/**
 * External link icon SVG component
 */
function ExternalLinkIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  );
}

export function DOILink({ doi, doiUrl, className = '' }: DOILinkProps) {
  // Handle null/empty DOI gracefully
  if (!doi && !doiUrl) {
    return <span className="text-text-secondary">-</span>;
  }

  // Construct the URL
  // Priority: use doiUrl if provided, otherwise construct from doi
  const url = doiUrl || (doi ? `https://doi.org/${doi}` : null);

  if (!url) {
    return <span className="text-text-secondary">-</span>;
  }

  // Extract display DOI from URL if doi is not provided
  const displayDoi = doi || url.replace('https://doi.org/', '');

  // Truncate long DOIs for display
  const truncatedDoi = displayDoi.length > 30
    ? `${displayDoi.substring(0, 27)}...`
    : displayDoi;

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-flex items-center gap-1.5 text-primary hover:text-blue-700 hover:underline transition-colors ${className}`}
      title={displayDoi}
    >
      <span className="truncate max-w-[150px]">{truncatedDoi}</span>
      <ExternalLinkIcon className="flex-shrink-0 opacity-70" />
    </a>
  );
}
