"use client";

import React from "react";
import { ExternalLink, Mail } from "lucide-react";

interface FormattedDraftProps {
  content: string;
  className?: string;
}

export function FormattedDraft({ content, className = "" }: FormattedDraftProps) {
  if (!content) return null;

  // Split into lines
  const lines = content.split("\n");

  // Check for Subject line
  let subject = "";
  let bodyLines: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (i === 0 && line.toLowerCase().startsWith("subject:")) {
      subject = line.replace(/^subject:\s*/i, "").trim();
    } else {
      bodyLines.push(line);
    }
  }

  // Helper to parse inline markdown (bold, links, urls)
  const renderInline = (text: string) => {
    // Regex for markdown links [text](url), raw urls, and bold **text**
    const parts: React.ReactNode[] = [];
    const regex = /(\[.*?\]\(https?:\/\/[^\s)]+\)|https?:\/\/[^\s]+|\*\*.*?\*\*)/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }

      const token = match[0];
      if (token.startsWith("[") && token.includes("](")) {
        // [link](url)
        const label = token.substring(1, token.indexOf("]("));
        const url = token.substring(token.indexOf("](") + 2, token.length - 1);
        parts.push(
          <a
            key={match.index}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-semibold text-blue-400 underline decoration-blue-400/50 hover:text-blue-300 hover:decoration-blue-300 transition-colors"
          >
            {label}
            <ExternalLink className="h-3 w-3 inline" />
          </a>
        );
      } else if (token.startsWith("http")) {
        // Raw URL
        parts.push(
          <a
            key={match.index}
            href={token}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 font-semibold text-blue-400 underline decoration-blue-400/50 hover:text-blue-300 hover:decoration-blue-300 transition-colors font-mono text-[11px] bg-blue-950/40 px-1.5 py-0.5 rounded border border-blue-800/40"
          >
            {token}
            <ExternalLink className="h-3 w-3 inline" />
          </a>
        );
      } else if (token.startsWith("**") && token.endsWith("**")) {
        // Bold
        parts.push(
          <strong key={match.index} className="font-semibold text-white">
            {token.substring(2, token.length - 2)}
          </strong>
        );
      }

      lastIndex = regex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts;
  };

  return (
    <div className={`space-y-3 font-sans text-xs leading-relaxed text-zinc-200 ${className}`}>
      {/* Subject Header if present */}
      {subject && (
        <div className="flex items-center gap-2 rounded-lg bg-zinc-900 border border-zinc-800 px-3 py-2 text-zinc-200">
          <Mail className="h-3.5 w-3.5 text-blue-400 shrink-0" />
          <span className="text-[11px] font-semibold text-zinc-400">Subject:</span>
          <span className="font-medium text-white select-all">{subject}</span>
        </div>
      )}

      {/* Body Lines */}
      <div className="space-y-2">
        {bodyLines.map((line, idx) => {
          const trimmed = line.trim();

          if (!trimmed) {
            return <div key={idx} className="h-1.5" />;
          }

          // Bullet list item
          if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
            return (
              <div key={idx} className="flex items-start gap-2 pl-3">
                <span className="text-blue-400 font-bold select-none leading-5">•</span>
                <div className="flex-1 text-zinc-300 leading-5">
                  {renderInline(trimmed.substring(2))}
                </div>
              </div>
            );
          }

          // Numbered list item
          const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
          if (numMatch) {
            return (
              <div key={idx} className="flex items-start gap-2 pl-3">
                <span className="text-blue-400 font-mono text-[11px] font-bold select-none shrink-0 leading-5">
                  {numMatch[1]}.
                </span>
                <div className="flex-1 text-zinc-300 leading-5">
                  {renderInline(numMatch[2])}
                </div>
              </div>
            );
          }

          // Section header (e.g. **What Happens Next** on its own line)
          if (trimmed.startsWith("**") && trimmed.endsWith("**") && trimmed.length > 4) {
            return (
              <div key={idx} className="font-bold text-white text-[13px] pt-2 pb-0.5 border-b border-zinc-800/60">
                {trimmed.substring(2, trimmed.length - 2)}
              </div>
            );
          }

          // Standard paragraph
          return (
            <p key={idx} className="text-zinc-200 leading-relaxed">
              {renderInline(line)}
            </p>
          );
        })}
      </div>
    </div>
  );
}
