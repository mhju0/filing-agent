try {
  const saved = localStorage.getItem('filing-theme');
  document.documentElement.dataset.theme = saved === 'dark' || saved === 'light' ? saved : matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
} catch { /* Storage can be disabled; the page keeps its readable light default. */ }
