"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { agentApi, ChatMessage } from "@/lib/api";
import { RotateCcw, Send, Sparkles, Zap, TrendingUp, CreditCard } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  data?: unknown;
}

const CHAT_STORAGE_KEY = "subscription-tracker-chat-history";

// Function to highlight text - only "X payments/subscriptions" gets a violet pill
// Currency amounts use bold markdown from the LLM, not automatic highlighting
function highlightText(text: string): React.ReactNode[] {
  const segments: React.ReactNode[] = [];
  let keyIndex = 0;

  // Pattern for "X payments/subscriptions" - violet pill
  const paymentPattern = /(\d+)\s+(payments?|subscriptions?)/gi;

  // Process the text
  let lastIndex = 0;
  let match;

  // Clone regex to avoid state issues
  const regex = new RegExp(paymentPattern.source, paymentPattern.flags);

  while ((match = regex.exec(text)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      segments.push(text.slice(lastIndex, match.index));
    }
    // Add highlighted match
    segments.push(
      <span key={keyIndex++} className="inline-flex items-center px-1.5 py-0.5 rounded-md bg-violet-100 dark:bg-violet-900/50 text-violet-700 dark:text-violet-300 font-semibold">
        {match[0]}
      </span>
    );
    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    segments.push(text.slice(lastIndex));
  }

  return segments.length > 0 ? segments : [text];
}

// Custom component to render text with highlights
function HighlightedText({ children }: { children: React.ReactNode }) {
  if (typeof children === 'string') {
    return <>{highlightText(children)}</>;
  }

  if (Array.isArray(children)) {
    return (
      <>
        {children.map((child, i) => (
          <HighlightedText key={i}>{child}</HighlightedText>
        ))}
      </>
    );
  }

  return <>{children}</>;
}

// Process inline formatting (bold, italic) and return React nodes
function processInlineFormatting(text: string, keyPrefix: string = ''): React.ReactNode[] {
  // Replace **bold** with markers
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);

  return parts.map((part, i) => {
    const key = `${keyPrefix}-${i}`;

    // Bold text: **text**
    if (part.startsWith('**') && part.endsWith('**')) {
      const content = part.slice(2, -2);
      return (
        <strong key={key} className="font-semibold text-gray-900 dark:text-gray-100 bg-gradient-to-r from-violet-500/10 to-purple-500/10 dark:from-violet-500/20 dark:to-purple-500/20 px-1 py-0.5 rounded">
          <HighlightedText>{content}</HighlightedText>
        </strong>
      );
    }

    // Italic text: *text*
    if (part.startsWith('*') && part.endsWith('*') && !part.startsWith('**')) {
      const content = part.slice(1, -1);
      return <em key={key} className="italic"><HighlightedText>{content}</HighlightedText></em>;
    }

    // Regular text - skip empty parts
    if (!part) return null;
    return <HighlightedText key={key}>{part}</HighlightedText>;
  }).filter(Boolean);
}

// Simple markdown parser that preserves highlights
function parseMarkdown(text: string): React.ReactNode[] {
  const lines = text.split('\n');
  const result: React.ReactNode[] = [];
  let listItems: string[] = [];

  const flushList = () => {
    if (listItems.length > 0) {
      result.push(
        <ul key={`list-${result.length}`} className="space-y-1.5 my-2">
          {listItems.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-[15px] leading-relaxed text-gray-700 dark:text-gray-300">
              <span className="mt-2 w-1.5 h-1.5 rounded-full bg-violet-400 flex-shrink-0" />
              <span>{processInlineFormatting(item, `li-${i}`)}</span>
            </li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  lines.forEach((line, lineIndex) => {
    const trimmed = line.trim();

    // Headers
    if (trimmed.startsWith('### ')) {
      flushList();
      result.push(
        <h3 key={lineIndex} className="text-[15px] font-semibold text-gray-900 dark:text-gray-100 mt-3 mb-1.5 first:mt-0">
          {processInlineFormatting(trimmed.slice(4), `h3-${lineIndex}`)}
        </h3>
      );
    } else if (trimmed.startsWith('## ')) {
      flushList();
      result.push(
        <h2 key={lineIndex} className="text-base font-semibold text-gray-900 dark:text-gray-100 mt-3 mb-1.5 first:mt-0">
          {processInlineFormatting(trimmed.slice(3), `h2-${lineIndex}`)}
        </h2>
      );
    } else if (trimmed.startsWith('# ')) {
      flushList();
      result.push(
        <h1 key={lineIndex} className="text-lg font-semibold text-gray-900 dark:text-gray-100 mt-3 mb-1.5 first:mt-0">
          {processInlineFormatting(trimmed.slice(2), `h1-${lineIndex}`)}
        </h1>
      );
    }
    // List items (handle bullet points - but not ** which is bold)
    else if (trimmed.startsWith('• ') || trimmed.startsWith('- ') || (trimmed.startsWith('* ') && !trimmed.startsWith('**'))) {
      listItems.push(trimmed.slice(2));
    }
    // Regular text
    else if (trimmed) {
      flushList();
      result.push(
        <p key={lineIndex} className="text-[15px] leading-relaxed text-gray-700 dark:text-gray-300 mb-2 last:mb-0">
          {processInlineFormatting(trimmed, `p-${lineIndex}`)}
        </p>
      );
    }
  });

  flushList();
  return result;
}

export function AgentChat() {
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(CHAT_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          setMessages(parsed);
        }
      }
    } catch (e) {
      console.error("Failed to load chat history:", e);
    }
    setIsInitialized(true);
  }, []);

  useEffect(() => {
    if (isInitialized) {
      try {
        localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
      } catch (e) {
        console.error("Failed to save chat history:", e);
      }
    }
  }, [messages, isInitialized]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 200) + "px";
    }
  }, [input]);

  const getHistory = (): ChatMessage[] => {
    return messages.map((msg) => ({
      role: msg.role,
      content: msg.content,
    }));
  };

  const executeMutation = useMutation({
    mutationFn: (command: string) => agentApi.execute(command, getHistory()),
    onSuccess: (response) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.message,
          data: response.data,
        },
      ]);
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message}`,
        },
      ]);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || executeMutation.isPending) return;

    const userMessage = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setInput("");
    executeMutation.mutate(userMessage);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem(CHAT_STORAGE_KEY);
  };

  const suggestions = [
    { text: "Add subscription", full: "Add Netflix for $15.99 monthly", icon: CreditCard, color: "bg-violet-500" },
    { text: "View all", full: "Show all my subscriptions", icon: Sparkles, color: "bg-blue-500" },
    { text: "Spending report", full: "How much am I spending per month?", icon: TrendingUp, color: "bg-emerald-500" },
    { text: "Next payments", full: "What payments are due this week?", icon: Zap, color: "bg-amber-500" },
  ];

  return (
    <div
      className="flex flex-col w-full bg-white dark:bg-gray-900 rounded-xl sm:rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
      style={{
        height: 'calc(100vh - 280px)',
        minHeight: '400px',
      }}
      role="region"
      aria-label="AI Assistant Chat"
    >
      {/* Messages Area */}
      <div
        className="flex-1 overflow-y-auto"
        role="log"
        aria-live="polite"
        aria-label="Chat messages"
      >
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center px-4 sm:px-6 py-6 sm:py-8">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="w-12 h-12 sm:w-14 sm:h-14 rounded-xl sm:rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mb-4 sm:mb-6 shadow-lg shadow-violet-500/20"
            >
              <Sparkles className="w-6 h-6 sm:w-7 sm:h-7 text-white" />
            </motion.div>

            <motion.h2
              initial={{ y: 10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-1 sm:mb-2"
            >
              What can I help with?
            </motion.h2>
            <motion.p
              initial={{ y: 10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.15 }}
              className="text-gray-500 dark:text-gray-400 text-center max-w-sm mb-6 sm:mb-8 text-sm sm:text-[15px]"
            >
              Manage subscriptions, track spending, and get insights.
            </motion.p>

            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="grid grid-cols-2 gap-2 sm:gap-2.5 w-full max-w-md"
            >
              {suggestions.map((suggestion, i) => {
                const Icon = suggestion.icon;
                return (
                  <motion.button
                    key={i}
                    onClick={() => setInput(suggestion.full)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex items-center gap-2 sm:gap-3 text-left p-2.5 sm:p-3 rounded-lg sm:rounded-xl bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700 transition-colors"
                  >
                    <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-md sm:rounded-lg ${suggestion.color} flex items-center justify-center shrink-0`}>
                      <Icon className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
                    </div>
                    <span className="text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-300">
                      {suggestion.text}
                    </span>
                  </motion.button>
                );
              })}
            </motion.div>
          </div>
        ) : (
          <div className="px-3 sm:px-4 py-4 sm:py-5 space-y-4 sm:space-y-5">
            <AnimatePresence mode="popLayout">
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className={message.role === "user" ? "flex justify-end" : ""}
                >
                  {message.role === "assistant" ? (
                    <div className="flex gap-2 sm:gap-3 max-w-[98%] sm:max-w-[95%]">
                      <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shrink-0 shadow-sm">
                        <Sparkles className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
                      </div>
                      <div className="flex-1 min-w-0 pt-0.5 text-sm sm:text-base">
                        {parseMarkdown(message.content)}
                      </div>
                    </div>
                  ) : (
                    <div className="max-w-[85%] sm:max-w-[80%]">
                      <div className="inline-block bg-violet-600 text-white rounded-2xl rounded-br-sm px-3 sm:px-4 py-2 sm:py-2.5">
                        <p className="text-sm sm:text-[15px] leading-relaxed whitespace-pre-wrap">
                          {message.content}
                        </p>
                      </div>
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            <AnimatePresence>
              {executeMutation.isPending && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex gap-2 sm:gap-3"
                >
                  <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                    <Sparkles className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
                  </div>
                  <div className="flex items-center gap-1 pt-2">
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        className="w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full bg-violet-400"
                        animate={{ opacity: [0.4, 1, 0.4] }}
                        transition={{
                          duration: 1,
                          repeat: Infinity,
                          delay: i * 0.2,
                        }}
                      />
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-3 sm:p-4 bg-gray-50 dark:bg-gray-800/50">
        <div className="max-w-3xl mx-auto">
          {messages.length > 0 && (
            <div className="flex justify-center mb-2 sm:mb-3">
              <button
                onClick={clearChat}
                className="flex items-center gap-1.5 text-[10px] sm:text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                <RotateCcw className="w-2.5 h-2.5 sm:w-3 sm:h-3" />
                New conversation
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit} aria-label="Chat message form">
            <label htmlFor="chat-input" className="sr-only">Message</label>
            <div className="relative flex items-end bg-white dark:bg-gray-800 rounded-lg sm:rounded-xl border border-gray-300 dark:border-gray-600 focus-within:border-violet-500 dark:focus-within:border-violet-400 focus-within:ring-2 focus-within:ring-violet-500/20 transition-all">
              <textarea
                id="chat-input"
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything..."
                rows={1}
                className="flex-1 resize-none bg-transparent px-3 sm:px-4 py-2.5 sm:py-3 text-sm sm:text-[15px] text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none max-h-[150px] sm:max-h-[200px] leading-relaxed"
                disabled={executeMutation.isPending}
                aria-describedby="chat-hint"
              />
              <button
                type="submit"
                disabled={executeMutation.isPending || !input.trim()}
                className="m-1 sm:m-1.5 p-1.5 sm:p-2 bg-violet-600 text-white rounded-md sm:rounded-lg hover:bg-violet-700 transition-colors disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed"
                aria-label="Send message"
              >
                <Send className="w-3.5 h-3.5 sm:w-4 sm:h-4" aria-hidden="true" />
              </button>
            </div>
            <span id="chat-hint" className="sr-only">Press Enter to send, Shift+Enter for new line</span>
          </form>
        </div>
      </div>
    </div>
  );
}
