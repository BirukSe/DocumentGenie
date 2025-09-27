// Theme utility functions
export const getInitialTheme = () => {
  if (typeof window !== 'undefined') {
    const savedTheme = localStorage.getItem('documentgenie-theme');
    return savedTheme ? JSON.parse(savedTheme) : true; // Default to dark mode
  }
  return true; // Default to dark mode
};

export const saveTheme = (isDark) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('documentgenie-theme', JSON.stringify(isDark));
  }
};
