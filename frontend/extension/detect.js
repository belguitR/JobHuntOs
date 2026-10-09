(() => {
  if (window.__jobHuntObserver) return;
  let lastUrl = '';
  let timer;
  const check = () => {
    const visibleText = document.body?.innerText || '';
    if (
      lastUrl === location.href ||
      !/application (has been |was )?(submitted|received)|thank you for applying|thanks for applying/i.test(
        visibleText,
      )
    )
      return;
    lastUrl = location.href;
    chrome.runtime.sendMessage({
      type: 'submission-hint',
      title: document.title,
      url: location.href,
    });
  };
  window.__jobHuntObserver = new MutationObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(check, 600);
  });
  window.__jobHuntObserver.observe(document.documentElement, { subtree: true, childList: true });
  check();
})();
