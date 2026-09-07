try {
  const choice = localStorage.getItem("filing-design-theme");
  document.documentElement.dataset.theme =
    choice ||
    (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
} catch {
  document.documentElement.dataset.theme = "light";
}
