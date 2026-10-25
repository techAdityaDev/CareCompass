interface MessageBubbleProps {
  message: { role: 'user' | 'assistant'; content: string };
  textSize: number;
}

export function MessageBubble({ message, textSize }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <p
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 ${
          isUser ? 'rounded-br-sm bg-teal-600 text-white' : 'rounded-bl-sm bg-gray-100 text-gray-800'
        }`}
        style={{ fontSize: `${16 * textSize}px` }}
      >
        {message.content}
      </p>
    </div>
  );
}