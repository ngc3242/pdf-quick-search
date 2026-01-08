interface HighlightedSnippetProps {
  text: string;
  query: string;
}

export function HighlightedSnippet({ text, query }: HighlightedSnippetProps) {
  if (!query) {
    return <span>{text}</span>;
  }

  const parts = text.split(new RegExp(`(${escapeRegex(query)})`, 'gi'));

  return (
    <span>
      {parts.map((part, index) => {
        const isMatch = part.toLowerCase() === query.toLowerCase();
        return isMatch ? (
          <mark
            key={index}
            className="bg-yellow-200 text-gray-900 px-0.5 rounded"
          >
            {part}
          </mark>
        ) : (
          <span key={index}>{part}</span>
        );
      })}
    </span>
  );
}

function escapeRegex(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
