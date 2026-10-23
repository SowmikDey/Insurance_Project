import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { api } from '../services/api';

const GlossaryContext = createContext(null);

export const GlossaryProvider = ({ children }) => {
  const [terms, setTerms] = useState([]);
  const [termsMap, setTermsMap] = useState({});
  const [activeTerm, setActiveTerm] = useState(null);
  const [modalTerm, setModalTerm] = useState(null);
  const [popoverPos, setPopoverPos] = useState({ top: '0px', bottom: 'auto', left: '0px', placement: 'bottom' });
  const [isLoading, setIsLoading] = useState(true);
  
  const hoverTimeoutRef = useRef(null);
  const closeTimeoutRef = useRef(null);

  // Auto-dismiss floating popover on scroll or window resize
  useEffect(() => {
    if (!activeTerm) return;
    const dismiss = () => {
      clearTimeout(hoverTimeoutRef.current);
      clearTimeout(closeTimeoutRef.current);
      setActiveTerm(null);
    };
    window.addEventListener('scroll', dismiss, { passive: true });
    window.addEventListener('resize', dismiss, { passive: true });
    return () => {
      window.removeEventListener('scroll', dismiss);
      window.removeEventListener('resize', dismiss);
    };
  }, [activeTerm]);

  useEffect(() => {
    const fetchTerms = async () => {
      try {
        const data = await api.getGlossaryTerms();
        setTerms(data);
        
        const map = {};
        data.forEach(t => {
          map[t.slug.toLowerCase()] = t;
          map[t.term.toLowerCase()] = t;
          
          // Clean base term
          const clean = t.term.replace(/\(.*?\)/g, '').trim().toLowerCase();
          map[clean] = t;
          
          if (t.aliases && Array.isArray(t.aliases)) {
            t.aliases.forEach(a => {
              if (a) map[a.toLowerCase()] = t;
            });
          }
        });
        setTermsMap(map);
      } catch (err) {
        console.error('Failed to load glossary terms:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchTerms();
  }, []);

  const findTerm = (identifier) => {
    if (!identifier) return null;
    const key = identifier.toLowerCase().trim();
    if (termsMap[key]) return termsMap[key];
    
    // Check clean version without punctuation
    const cleanKey = key.replace(/[-_()]/g, ' ').replace(/\s+/g, ' ').trim();
    if (termsMap[cleanKey]) return termsMap[cleanKey];

    // Substring fallback
    const matched = terms.find(t => 
      t.slug.toLowerCase() === key || 
      t.term.toLowerCase().includes(key) || 
      key.includes(t.term.toLowerCase().replace(/\(.*?\)/g, '').trim())
    );
    return matched || null;
  };

  const handleMouseEnter = (termIdentifier, event) => {
    clearTimeout(closeTimeoutRef.current);
    const term = findTerm(termIdentifier);
    if (!term) return;

    // Capture bounding client rect synchronously in viewport coordinates
    const target = event?.currentTarget;
    if (!target || typeof target.getBoundingClientRect !== 'function') return;
    const rect = target.getBoundingClientRect();

    hoverTimeoutRef.current = setTimeout(() => {
      const popoverWidth = 352; // matches w-88 (22rem)
      const estimatedHeight = 280;

      // Viewport-relative horizontal positioning with safe margins
      let left = rect.left;
      if (left + popoverWidth > window.innerWidth - 16) {
        left = Math.max(16, window.innerWidth - popoverWidth - 16);
      }
      if (left < 16) left = 16;

      // Smart vertical positioning:
      // If there's not enough room below AND more room above, position ABOVE the term
      const spaceBelow = window.innerHeight - rect.bottom;
      const spaceAbove = rect.top;
      const showAbove = spaceBelow < estimatedHeight && spaceAbove > spaceBelow;

      let pos;
      if (showAbove) {
        pos = {
          top: 'auto',
          bottom: `${Math.max(12, window.innerHeight - rect.top + 8)}px`,
          left: `${left}px`,
          placement: 'top'
        };
      } else {
        pos = {
          top: `${Math.min(window.innerHeight - 60, Math.max(12, rect.bottom + 8))}px`,
          bottom: 'auto',
          left: `${left}px`,
          placement: 'bottom'
        };
      }

      setPopoverPos(pos);
      setActiveTerm(term);
    }, 150);
  };

  const cancelClose = () => {
    clearTimeout(closeTimeoutRef.current);
  };

  const handleMouseLeave = () => {
    clearTimeout(hoverTimeoutRef.current);
    closeTimeoutRef.current = setTimeout(() => {
      setActiveTerm(null);
    }, 200);
  };

  const handleClick = (termIdentifier, e) => {
    if (e) e.stopPropagation();
    const term = findTerm(termIdentifier);
    if (term) {
      setActiveTerm(null);
      setModalTerm(term);
    }
  };

  const closeModal = () => {
    setModalTerm(null);
  };

  return (
    <GlossaryContext.Provider value={{
      terms,
      termsMap,
      activeTerm,
      modalTerm,
      popoverPos,
      isLoading,
      findTerm,
      handleMouseEnter,
      handleMouseLeave,
      cancelClose,
      handleClick,
      closeModal,
      openFullModal: (term) => {
        setActiveTerm(null);
        setModalTerm(term);
      }
    }}>
      {children}
    </GlossaryContext.Provider>
  );
};

export const useGlossary = () => {
  const context = useContext(GlossaryContext);
  if (!context) {
    throw new Error('useGlossary must be used within a GlossaryProvider');
  }
  return context;
};
