(() => {
  'use strict';
  if (window.UBCMatchUpdates) return;
  let busy = false;

  async function refreshLiveMatches() {
    const target = document.getElementById('live-matches');
    if (!target || busy || document.visibilityState === 'hidden') return;
    busy = true;
    try {
      const response = await fetch('/matches', {
        credentials: 'same-origin',
        headers: { 'Accept': 'text/html', 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!response.ok) return;
      const html = await response.text();
      const parsed = new DOMParser().parseFromString(html, 'text/html');
      const next = parsed.getElementById('live-matches');
      if (next) target.innerHTML = next.innerHTML;
    } catch (error) {
      // A transient refresh failure must never interrupt the rest of the hub.
    } finally {
      busy = false;
    }
  }

  window.setInterval(refreshLiveMatches, 15000);
  document.addEventListener('visibilitychange', refreshLiveMatches);
  window.UBCMatchUpdates = { refresh: refreshLiveMatches };
})();
