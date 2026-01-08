/**
 * AuthorDisplay Component
 * Displays author information with "et al." abbreviation for 3+ authors
 * SPEC-CROSSREF-001: REQ-STA-001
 */

interface AuthorDisplayProps {
  /** First author name (full name) */
  firstAuthor: string | null;
  /** Array of co-author names */
  coAuthors: string[] | null;
  /** Type of display: 'first' for B column (first author), 'co' for C column (co-authors) */
  type: 'first' | 'co';
}

/**
 * Format author name to "Family, G." format
 * @param fullName - Full author name (e.g., "John Doe" or "Doe, John")
 * @returns Formatted name (e.g., "Doe, J.")
 */
function formatAuthorName(fullName: string): string {
  if (!fullName || fullName.trim() === '') return '';

  const trimmed = fullName.trim();

  // Handle "Family, Given" format
  if (trimmed.includes(',')) {
    const [family, given] = trimmed.split(',').map(s => s.trim());
    if (given && given.length > 0) {
      return `${family}, ${given.charAt(0).toUpperCase()}.`;
    }
    return family;
  }

  // Handle "Given Family" format
  const parts = trimmed.split(/\s+/);
  if (parts.length === 1) {
    return parts[0];
  }

  const family = parts[parts.length - 1];
  const given = parts[0];
  return `${family}, ${given.charAt(0).toUpperCase()}.`;
}

/**
 * Get full author list for tooltip display
 */
function getFullAuthorList(firstAuthor: string | null, coAuthors: string[] | null): string {
  const authors: string[] = [];

  if (firstAuthor) {
    authors.push(firstAuthor);
  }

  if (coAuthors && coAuthors.length > 0) {
    authors.push(...coAuthors);
  }

  if (authors.length === 0) {
    return '';
  }

  return authors.join(', ');
}

export function AuthorDisplay({ firstAuthor, coAuthors, type }: AuthorDisplayProps) {
  const totalAuthors = (firstAuthor ? 1 : 0) + (coAuthors?.length || 0);

  // Handle null/empty authors gracefully
  if (type === 'first') {
    // B column: First Author
    if (!firstAuthor) {
      return <span className="text-text-secondary">-</span>;
    }

    const formattedFirst = formatAuthorName(firstAuthor);
    const fullList = getFullAuthorList(firstAuthor, coAuthors);

    return (
      <span
        className="cursor-default"
        title={fullList || undefined}
      >
        {formattedFirst}
      </span>
    );
  }

  // C column: Co-authors
  // Total 1 author (single author): C column empty or "-"
  if (totalAuthors <= 1) {
    return <span className="text-text-secondary">-</span>;
  }

  // Total 2 authors: C column shows 2nd author only
  if (totalAuthors === 2 && coAuthors && coAuthors.length > 0) {
    const formattedSecond = formatAuthorName(coAuthors[0]);
    const fullList = getFullAuthorList(firstAuthor, coAuthors);

    return (
      <span
        className="cursor-default"
        title={fullList || undefined}
      >
        {formattedSecond}
      </span>
    );
  }

  // Total 3+ authors: C column shows "Second Author et al."
  if (totalAuthors >= 3 && coAuthors && coAuthors.length > 0) {
    const formattedSecond = formatAuthorName(coAuthors[0]);
    const fullList = getFullAuthorList(firstAuthor, coAuthors);

    return (
      <span
        className="cursor-help"
        title={fullList || undefined}
      >
        {formattedSecond} <span className="italic text-text-secondary">et al.</span>
      </span>
    );
  }

  return <span className="text-text-secondary">-</span>;
}
