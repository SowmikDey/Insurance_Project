import React, { useMemo } from 'react';
import { useGlossary } from '../context/GlossaryContext';

export const HighlightedText = ({ text, className = "" }) => {
  const { terms, handleMouseEnter, handleMouseLeave, handleClick } = useGlossary();

  const renderedElements = useMemo(() => {
    if (!text || !terms || terms.length === 0) return text;

    // Build regex search for all terms and their aliases
    const termMap = new Map();
    const allKeywords = [];

    terms.forEach(t => {
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

    // Sort longest first to avoid partial matching
    const uniqueKeywords = Array.from(new Set(allKeywords))
      .filter(k => k.length >= 3)
      .sort((a, b) => b.length - a.length);

    if (uniqueKeywords.length === 0) return text;

    const regexPattern = new RegExp(
      `\\b(${uniqueKeywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})\\b`,
      'gi'
    );

    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = regexPattern.exec(text)) !== null) {
      const matchedText = match[0];
      const matchStart = match.index;
      const matchEnd = regexPattern.lastIndex;

      // Add preceding plain text
      if (matchStart > lastIndex) {
        parts.push(text.substring(lastIndex, matchStart));
      }

      const lookupKey = matchedText.toLowerCase();
      const termObj = termMap.get(lookupKey) || terms.find(t => t.slug === lookupKey);

      if (termObj) {
        parts.push(
          <span
            key={`highlight-${matchStart}-${termObj.slug}`}
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

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts;
  }, [text, terms, handleMouseEnter, handleMouseLeave, handleClick]);

  return <span className={className}>{renderedElements}</span>;
};
