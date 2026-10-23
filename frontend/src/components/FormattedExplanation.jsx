import React, { useMemo } from 'react';
import { HighlightedText } from './HighlightedText';

/**
 * FormattedExplanation parses multi-paragraph markdown content into structured blocks:
 * - Tables (| Header | Header |)
 * - Numbered lists (1. Item)
 * - Bullet lists (- Item, * Item)
 * - Checklists (✅ Item, ❌ Item)
 * - Subheadings (### Subtitle or standalone **Heading:**)
 * - Paragraphs with vertical rhythm and spacing
 * 
 * Every text leaf is routed through <HighlightedText> to maintain interactive glossary popovers.
 */
export const FormattedExplanation = ({ content, className = "", textColor = "text-slate-700" }) => {
  const blocks = useMemo(() => {
    if (!content || typeof content !== 'string') return [];

    const lines = content.split('\n');
    const result = [];
    let currentBlock = null;

    for (let i = 0; i < lines.length; i++) {
      const rawLine = lines[i];
      const trimmed = rawLine.trim();

      // Empty line closes the active block
      if (!trimmed) {
        if (currentBlock) {
          result.push(currentBlock);
          currentBlock = null;
        }
        continue;
      }

      // 1. Table row check: starts and ends with '|'
      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        if (currentBlock && currentBlock.type === 'table') {
          currentBlock.lines.push(trimmed);
        } else {
          if (currentBlock) result.push(currentBlock);
          currentBlock = { type: 'table', lines: [trimmed] };
        }
        continue;
      }

      // 2. Ordered list item check: "1. ", "2. ", etc.
      const olMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
      if (olMatch) {
        if (currentBlock && currentBlock.type === 'ol') {
          currentBlock.items.push({ num: olMatch[1], content: olMatch[2] });
        } else {
          if (currentBlock) result.push(currentBlock);
          currentBlock = {
            type: 'ol',
            items: [{ num: olMatch[1], content: olMatch[2] }]
          };
        }
        continue;
      }

      // 3. Checklist item check: "✅ ", "❌ "
      const checkMatch = trimmed.match(/^([✅❌])\s*(.*)$/);
      if (checkMatch) {
        if (currentBlock && currentBlock.type === 'checklist') {
          currentBlock.items.push({ icon: checkMatch[1], text: checkMatch[2] });
        } else {
          if (currentBlock) result.push(currentBlock);
          currentBlock = {
            type: 'checklist',
            items: [{ icon: checkMatch[1], text: checkMatch[2] }]
          };
        }
        continue;
      }

      // 4. Unordered list item check: "- ", "* ", "• "
      const ulMatch = trimmed.match(/^[-*•]\s+(.*)$/);
      if (ulMatch) {
        if (currentBlock && currentBlock.type === 'ul') {
          currentBlock.items.push(ulMatch[1]);
        } else {
          if (currentBlock) result.push(currentBlock);
          currentBlock = {
            type: 'ul',
            items: [ulMatch[1]]
          };
        }
        continue;
      }

      // 5. Heading check: starts with ### or is standalone **Title:** / **Title**
      const headingMatch = trimmed.match(/^#{1,4}\s+(.*)$/);
      const boldTitleMatch = trimmed.match(/^\*\*([^*]+?)\*\*:?$/);
      if (headingMatch || boldTitleMatch) {
        if (currentBlock) result.push(currentBlock);
        const title = headingMatch ? headingMatch[1] : boldTitleMatch[1];
        result.push({ type: 'heading', title });
        currentBlock = null;
        continue;
      }

      // 6. Continuation of list or paragraph
      if (currentBlock) {
        if (currentBlock.type === 'ol') {
          currentBlock.items[currentBlock.items.length - 1].content += ' ' + trimmed;
        } else if (currentBlock.type === 'ul') {
          currentBlock.items[currentBlock.items.length - 1] += ' ' + trimmed;
        } else if (currentBlock.type === 'checklist') {
          currentBlock.items[currentBlock.items.length - 1].text += ' ' + trimmed;
        } else if (currentBlock.type === 'paragraph') {
          currentBlock.text += ' ' + trimmed;
        } else {
          result.push(currentBlock);
          currentBlock = { type: 'paragraph', text: trimmed };
        }
      } else {
        currentBlock = { type: 'paragraph', text: trimmed };
      }
    }

    if (currentBlock) {
      result.push(currentBlock);
    }

    return result;
  }, [content]);

  if (!blocks || blocks.length === 0) return null;

  return (
    <div className={`space-y-4 ${className}`}>
      {blocks.map((block, idx) => {
        switch (block.type) {
          case 'heading':
            return (
              <h4 key={idx} className="font-bold text-slate-900 text-sm sm:text-base pt-3 first:pt-0 pb-1 flex items-center gap-2 border-b border-slate-100">
                <HighlightedText text={block.title} />
              </h4>
            );

          case 'table': {
            // Process markdown table
            const cleanRows = block.lines
              .map(line => 
                line.split('|')
                  .map(cell => cell.trim())
                  .filter((_, cIdx, arr) => cIdx > 0 && cIdx < arr.length - 1)
              )
              .filter(cells => cells.length > 0 && !cells.every(c => /^[-:\s]+$/.test(c)));

            if (cleanRows.length === 0) return null;

            const headerRow = cleanRows[0];
            const bodyRows = cleanRows.slice(1);

            return (
              <div key={idx} className="overflow-x-auto my-3 rounded-xl border border-slate-200 bg-white shadow-xs">
                <table className="min-w-full text-left text-xs sm:text-sm divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      {headerRow.map((headerCell, hIdx) => (
                        <th key={hIdx} className="px-4 py-3 font-semibold text-slate-800 tracking-wide">
                          <HighlightedText text={headerCell} />
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {bodyRows.map((row, rIdx) => (
                      <tr key={rIdx} className={rIdx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} className="px-4 py-2.5 text-slate-700">
                            <HighlightedText text={cell} />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          }

          case 'ol':
            return (
              <ol key={idx} className="space-y-2.5 my-3">
                {block.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="flex items-start gap-3 text-sm leading-relaxed">
                    <span className="flex items-center justify-center w-5 h-5 rounded-full bg-teal-100 text-teal-800 text-xs font-bold shrink-0 mt-0.5 shadow-xs">
                      {item.num}
                    </span>
                    <div className={`flex-1 ${textColor}`}>
                      <HighlightedText text={item.content} />
                    </div>
                  </li>
                ))}
              </ol>
            );

          case 'ul':
            return (
              <ul key={idx} className="space-y-2 my-3 pl-1">
                {block.items.map((item, itemIdx) => (
                  <li key={itemIdx} className="flex items-start gap-2.5 text-sm leading-relaxed">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-600 mt-2 shrink-0" />
                    <div className={`flex-1 ${textColor}`}>
                      <HighlightedText text={item} />
                    </div>
                  </li>
                ))}
              </ul>
            );

          case 'checklist':
            return (
              <div key={idx} className="space-y-2 my-3">
                {block.items.map((item, itemIdx) => {
                  const isSuccess = item.icon === '✅';
                  return (
                    <div
                      key={itemIdx}
                      className={`flex items-start gap-2.5 px-3 py-2 rounded-xl border text-xs sm:text-sm leading-relaxed ${
                        isSuccess
                          ? 'bg-emerald-50/70 border-emerald-200/80 text-emerald-950'
                          : 'bg-rose-50/70 border-rose-200/80 text-rose-950'
                      }`}
                    >
                      <span className="text-sm shrink-0 mt-0.5">{item.icon}</span>
                      <div className="flex-1 font-medium">
                        <HighlightedText text={item.text} />
                      </div>
                    </div>
                  );
                })}
              </div>
            );

          case 'paragraph':
          default:
            return (
              <p key={idx} className={`leading-relaxed text-sm ${textColor}`}>
                <HighlightedText text={block.text} />
              </p>
            );
        }
      })}
    </div>
  );
};
