import { useState, useCallback } from 'react';

export const useFavoriteAnimation = () => {
  const [animatingIds, setAnimatingIds] = useState<Set<number>>(new Set());

  const triggerAnimation = useCallback((id: number) => {
    setAnimatingIds(prev => new Set(prev).add(id));
    setTimeout(() => {
      setAnimatingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }, 300);
  }, []);

  const isAnimating = useCallback((id: number) => animatingIds.has(id), [animatingIds]);

  return { triggerAnimation, isAnimating };
};
