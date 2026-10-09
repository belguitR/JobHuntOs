chrome.runtime.onMessage.addListener((message, sender) => {
  if (message.type !== 'submission-hint' || !sender.tab?.id || !sender.url) return;
  const host = new URL(sender.url).hostname;
  if (!(host.endsWith('.greenhouse.io') || host === 'jobs.lever.co')) return;
  const hint = {
    title: String(message.title || '').slice(0, 300),
    url: sender.url,
    time: Date.now(),
  };
  chrome.storage.local.set({ [`pending-${sender.tab.id}`]: hint });
  chrome.action.setBadgeText({ tabId: sender.tab.id, text: '!' });
  chrome.action.setBadgeBackgroundColor({ tabId: sender.tab.id, color: '#73506d' });
});

chrome.tabs.onRemoved.addListener((id) => chrome.storage.local.remove(`pending-${id}`));
