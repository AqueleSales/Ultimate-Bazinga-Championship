(() => {
  'use strict';

  const main = document.getElementById('main-content');
  if (!main || window.UBCNavigation) return;

  let activeController = null;
  let navigationId = 0;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  function isInternalPageUrl(url) {
    return url.origin === window.location.origin &&
      !url.pathname.startsWith('/auth/') &&
      !url.searchParams.has('screen') &&
      !url.pathname.startsWith('/static/');
  }

  function shouldIgnoreLink(event, link, url) {
    return event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey || event.ctrlKey || event.shiftKey || event.altKey ||
      link.target && link.target !== '_self' ||
      link.hasAttribute('download') ||
      link.relList.contains('external') ||
      link.hasAttribute('data-no-spa') ||
      !isInternalPageUrl(url);
  }

  function parsePage(html) {
    const parsed = new DOMParser().parseFromString(html, 'text/html');
    const nextMain = parsed.getElementById('main-content');
    if (!nextMain) return null;
    return { main: nextMain, title: parsed.title };
  }

  function setBusy(value) {
    main.setAttribute('aria-busy', value ? 'true' : 'false');
  }

  function updatePage(page) {
    const apply = () => {
      main.innerHTML = page.main.innerHTML;
      document.title = page.title || document.title;
      main.focus({ preventScroll: true });
    };

    if (!reducedMotion.matches && typeof document.startViewTransition === 'function') {
      document.startViewTransition(apply);
    } else {
      main.classList.add('is-page-transitioning');
      requestAnimationFrame(() => {
        apply();
        requestAnimationFrame(() => main.classList.remove('is-page-transitioning'));
      });
    }
  }

  async function requestPage(url, options = {}) {
    const { push = true, restoreScroll = null, fallback = true, formData = null, method = 'GET' } = options;
    const id = ++navigationId;
    if (activeController) activeController.abort();
    activeController = new AbortController();
    setBusy(true);

    try {
      const response = await fetch(url.href, {
        method,
        body: formData,
        credentials: 'same-origin',
        signal: activeController.signal,
        headers: {
          'Accept': 'text/html',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (id !== navigationId) return false;
      const finalUrl = new URL(response.url || url.href, window.location.href);

      // OAuth, logout and explicit login screens must run through a full document load.
      if (!isInternalPageUrl(finalUrl) || !response.headers.get('content-type')?.includes('text/html')) {
        if (fallback) window.location.assign(finalUrl.href);
        return false;
      }

      const page = parsePage(await response.text());
      if (!response.ok || !page) {
        if (fallback) window.location.assign(finalUrl.href);
        return false;
      }

      if (push) {
        history.replaceState({ ...(history.state || {}), ubcScrollY: window.scrollY }, '', window.location.href);
        history.pushState({ ubcScrollY: 0 }, '', finalUrl.href);
      } else if (finalUrl.href !== window.location.href) {
        history.replaceState(history.state || {}, '', finalUrl.href);
      }

      updatePage(page);
      if (finalUrl.hash) {
        requestAnimationFrame(() => document.getElementById(decodeURIComponent(finalUrl.hash.slice(1)))?.scrollIntoView());
      } else if (restoreScroll !== null) {
        window.scrollTo({ top: restoreScroll, behavior: 'auto' });
      } else if (push) {
        window.scrollTo({ top: 0, behavior: 'auto' });
      }
      return true;
    } catch (error) {
      if (error.name === 'AbortError') return false;
      if (fallback) window.location.assign(url.href);
      return false;
    } finally {
      if (id === navigationId) {
        activeController = null;
        setBusy(false);
      }
    }
  }

  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[href]');
    if (!link) return;
    const url = new URL(link.href, window.location.href);
    if (shouldIgnoreLink(event, link, url)) return;

    if (url.pathname === window.location.pathname && url.search === window.location.search) {
      if (url.hash) return;
      event.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    event.preventDefault();
    requestPage(url);
  });

  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.hasAttribute('data-no-spa') || form.target && form.target !== '_self') return;

    const method = (form.method || 'GET').toUpperCase();
    if (!['GET', 'POST'].includes(method)) return;

    const url = new URL(form.action || window.location.href, window.location.href);
    if (!isInternalPageUrl(url) || form.enctype === 'multipart/form-data') return;

    event.preventDefault();
    const formData = new FormData(form);
    if (method === 'GET') {
      for (const [key, value] of formData.entries()) {
        if (typeof value === 'string') url.searchParams.append(key, value);
      }
      requestPage(url, { method: 'GET' });
      return;
    }
    requestPage(url, { method, formData });
  });

  window.addEventListener('popstate', (event) => {
    const url = new URL(window.location.href);
    requestPage(url, { push: false, restoreScroll: event.state?.ubcScrollY ?? 0, fallback: true });
  });

  window.UBCNavigation = {
    navigate(url) {
      const target = new URL(url, window.location.href);
      if (!isInternalPageUrl(target)) {
        window.location.assign(target.href);
        return;
      }
      requestPage(target);
    }
  };
})();
