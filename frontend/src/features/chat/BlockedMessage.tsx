interface BlockedMessageProps {
  content: string;
  riskCategories?: string[];
  revisionHint?: string;
}

export default function BlockedMessage({
  content,
  riskCategories,
  revisionHint,
}: BlockedMessageProps) {
  return (
    <div className="mx-4 my-2 rounded-lg border border-red-200 bg-red-50 p-4">
      <div className="flex items-start gap-2">
        <span className="text-red-500 text-lg">&#9888;</span>
        <div className="flex-1">
          <p className="text-sm font-medium text-red-800">{content}</p>
          {riskCategories && riskCategories.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {riskCategories.map((cat) => (
                <span
                  key={cat}
                  className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700"
                >
                  {cat}
                </span>
              ))}
            </div>
          )}
          {revisionHint && (
            <p className="mt-2 text-xs text-red-600">{revisionHint}</p>
          )}
        </div>
      </div>
    </div>
  );
}
