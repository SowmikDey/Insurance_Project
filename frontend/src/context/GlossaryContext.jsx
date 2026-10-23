import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { api } from '../services/api';

const GlossaryContext = createContext(null);

export const GlossaryProvider = ({ children }) => {
  const [terms, setTerms] = useState([]);
  const [termsMap, setTermsMap] = useState({});
  const [activeTerm, setActiveTerm] = useState(null);
  const [modalTerm, setModalTerm] = useState(null);
  const [popoverPos, setPopoverPos] = useState({ top: 0, left: 0 });
  const [isLoading, setIsLoading] = useState(true);
  
  const hoverTimeoutRef = useRef(null);
  const closeTimeoutRef = useRef(null);

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

    const rect = event.currentTarget.getBoundingClientRect();
    const scrollY = window.scrollY || window.pageYOffset;
    const scrollX = window.scrollX || window.pageXOffset;

    hoverTimeoutRef.current = setTimeout(() => {
      // Calculate responsive popover position
      const popoverWidth = 360;
      let left = rect.left + scrollX;
      if (left + popoverWidth > window.innerWidth - 20) {
        left = window.innerWidth - popoverWidth - 20;
      }
      if (left < 10) left = 10;

      const top = rect.bottom + scrollY + 8;
      setPopoverPos({ top, left });
      setActiveTerm(term);
    }, 180);
  };

  const handleMouseLeave = () => {
    clearTimeout(hoverTimeoutRef.current);
    closeTimeoutRef.current = setTimeout(() => {
      setActiveTerm(null);
    }, 220);
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
      handleClick,
      closeModal,
      openFullModal: (term) => setModalTerm(term)
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
