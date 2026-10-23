import React, { useMemo } from 'react';
import { useGlossary } from '../context/GlossaryContext';

export const HighlightedText = ({ text, className = "" }) => {
  const { terms, handleMouseEnter, handleMouseLeave, handleClick } = useGlossary();

  const renderedElements = useMemo(() => {
    if (text === null || text === undefined) return null;
    if (typeof text !== 'string') return text;
    if (!text.trim()) return text;

    // 1. Build regex search for all terms and their aliases
    const termMap = new Map();
    const allKeywords = [];

    if (terms && Array.isArray(terms)) {
      terms.forEach(t => {
        if (!t || !t.term) return;
        const cleanTerm = t.term.replace(/\(.*?\)/g, '').trim();
        termMap.set(cleanTerm.toLowerCase(), t);
        allKeywords.push(cleanTerm);

        if (cleanTerm.includes('-')) {
          const spaceVer = cleanTerm.replace(/-/g, ' ');
          termMap.set(spaceVer.toLowerCase(), t);
          allKeywords.push(spaceVer);
        }

        if (t.aliases && Array.isArray(t.aliases)) {
          t.aliases.forEach(a => {
            if (a) {
              termMap.set(a.toLowerCase().trim(), t);
              allKeywords.push(a.trim());
            }
          });
        }
      });
    }

    // Sort longest first to avoid partial matching
    const uniqueKeywords = Array.from(new Set(allKeywords))
      .filter(k => k.length >= 3)
      .sort((a, b) => b.length - a.length);

    let regexPattern = null;
    if (uniqueKeywords.length > 0) {
      regexPattern = new RegExp(
        `\\b(${uniqueKeywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})\\b`,
        'gi'
      );
    }

    // Helper: highlight glossary terms in a leaf string
    const highlightGlossary = (rawStr, keyPrefix) => {
      if (!regexPattern || !rawStr || typeof rawStr !== 'string') return rawStr;
      const parts = [];
      let lastIndex = 0;
      let match;
      regexPattern.lastIndex = 0;

      while ((match = regexPattern.exec(rawStr)) !== null) {
        const matchedText = match[0];
        const matchStart = match.index;
        const matchEnd = regexPattern.lastIndex;

        // Add preceding plain text
        if (matchStart > lastIndex) {
          parts.push(rawStr.substring(lastIndex, matchStart));
        }

        const lookupKey = matchedText.toLowerCase();
        const termObj = termMap.get(lookupKey) || (terms && terms.find(t => t.slug === lookupKey));

        if (termObj) {
          parts.push(
            <span
              key={`${keyPrefix}-hl-${matchStart}-${termObj.slug}`}
              className="glossary-term-highlight"
              tabIndex={0}
              role="button"
              aria-haspopup="dialog"
              aria-label={`Insurance term: ${termObj.term}. Click or hover for definition.`}
              onMouseEnter={(e) => handleMouseEnter(termObj.slug, e)}
              onMouseLeave={handleMouseLeave}
              onClick={(e) => handleClick(termObj.slug, e)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleClick(termObj.slug, e);
                }
              }}
            >
              {matchedText}
            </span>
          );
        } else {
          parts.push(matchedText);
        }

        lastIndex = matchEnd;
      }

      if (lastIndex < rawStr.length) {
        parts.push(rawStr.substring(lastIndex));
      }

      return parts.length > 0 ? parts : rawStr;
    };

    // Helper: process italics within a substring
    const processItalics = (str, prefix) => {
      if (!str || typeof str !== 'string') return str;
      const italicRegex = /(\*(?!\*)[^*]+?\*(?!\*))/g;
      const italicParts = str.split(italicRegex);

      if (italicParts.length === 1) {
        return highlightGlossary(str, prefix);
      }

      return italicParts.map((part, idx) => {
        if (part.startsWith('*') && part.endsWith('*') && part.length >= 3 && !part.startsWith('**')) {
          const inner = part.slice(1, -1);
          return (
            <em key={`${prefix}-em-${idx}`} className="italic">
              {highlightGlossary(inner, `${prefix}-em-${idx}`)}
            </em>
          );
        }
        return highlightGlossary(part, `${prefix}-p-${idx}`);
      });
    };

    // Helper: process inline code `code`
    const processCode = (str, prefix) => {
      if (!str || typeof str !== 'string') return str;
      const codeRegex = /(`[^`]+?`)/g;
      const codeParts = str.split(codeRegex);

      if (codeParts.length === 1) {
        return processItalics(str, prefix);
      }

      return codeParts.map((part, idx) => {
        if (part.startsWith('`') && part.endsWith('`') && part.length >= 3) {
          const inner = part.slice(1, -1);
          return (
            <code key={`${prefix}-code-${idx}`} className="px-1.5 py-0.5 rounded bg-slate-100 font-mono text-xs text-slate-800">
              {inner}
            </code>
          );
        }
        return processItalics(part, `${prefix}-c-${idx}`);
      });
    };

    // Main: split on **bold**
    const boldRegex = /(\*\*[^*]+?\*\*)/g;
    const boldParts = text.split(boldRegex);

    if (boldParts.length === 1) {
      return processCode(text, 'root');
    }

    return boldParts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
        const inner = part.slice(2, -2);
        return (
          <strong key={`b-${idx}`} className="font-semibold text-inherit">
            {processCode(inner, `b-${idx}`)}
          </strong>
        );
      }
      return processCode(part, `nb-${idx}`);
    });
  }, [text, terms, handleMouseEnter, handleMouseLeave, handleClick]);

  return <span className={className}>{renderedElements}</span>;
};
