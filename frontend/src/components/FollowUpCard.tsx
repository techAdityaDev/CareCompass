interface FollowUpCardProps {
  question: string;
  language: string;
  t: (key: string) => string;
  textSize: number;
}

export function FollowUpCard({ question, textSize }: FollowUpCardProps) {
  return (
    <div className="flex justify-start">
      <p className="max-w-[85%] rounded-2xl rounded-bl-sm border border-teal-100 bg-teal-50 px-4 py-3 text-gray-800" style={{ fontSize: `${16 * textSize}px` }}>
        {question}
      </p>
    </div>
  );
}