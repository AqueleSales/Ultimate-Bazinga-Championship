(() => {
    'use strict';

    const overlay = document.getElementById('cinematic-intro');
    const enterButton = document.getElementById('intro-enter');
    const skipButton = document.getElementById('intro-skip');
    const replayButton = document.getElementById('replay-intro');
    const sparks = document.getElementById('intro-sparks');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const storageKey = 'ubc-intro-seen-v1';
    const backgroundRegions = [
        document.querySelector('.site-header'),
        document.getElementById('main-content'),
        document.querySelector('.site-footer')
    ].filter(Boolean);
    let revealTimer = null;
    let hideTimer = null;
    let previouslyFocused = null;

    if (!overlay || !enterButton || !skipButton || !replayButton) return;

    function setBackgroundInert(isInert) {
        backgroundRegions.forEach((region) => {
            region.inert = isInert;
        });
    }

    function createSparks() {
        if (!sparks || reducedMotion.matches) return;
        const fragment = document.createDocumentFragment();
        for (let index = 0; index < 24; index += 1) {
            const spark = document.createElement('span');
            spark.style.left = `${Math.random() * 100}%`;
            spark.style.setProperty('--spark-duration', `${1.8 + Math.random() * 2.2}s`);
            spark.style.setProperty('--spark-delay', `${Math.random() * 2.5}s`);
            spark.style.setProperty('--spark-drift', `${Math.round(Math.random() * 100 - 50)}px`);
            fragment.appendChild(spark);
        }
        sparks.replaceChildren(fragment);
    }

    function closeIntro() {
        window.clearTimeout(revealTimer);
        window.clearTimeout(hideTimer);
        overlay.classList.remove('is-revealing');
        overlay.classList.add('is-done');
        overlay.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('intro-enabled');
        document.body.classList.add('intro-complete');
        setBackgroundInert(false);
        try { window.sessionStorage.setItem(storageKey, '1'); } catch (_) { /* Storage can be unavailable. */ }
        hideTimer = window.setTimeout(() => {
            overlay.classList.remove('is-done');
            overlay.hidden = true;
            if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
                previouslyFocused.focus({ preventScroll: true });
            }
        }, 700);
    }

    function revealIntro() {
        if (reducedMotion.matches) {
            closeIntro();
            return;
        }
        enterButton.disabled = true;
        overlay.classList.add('is-revealing');
        revealTimer = window.setTimeout(closeIntro, 1550);
    }

    function openIntro() {
        window.clearTimeout(revealTimer);
        window.clearTimeout(hideTimer);
        previouslyFocused = document.activeElement;
        overlay.hidden = false;
        overlay.classList.remove('is-done', 'is-revealing');
        overlay.setAttribute('aria-hidden', 'false');
        enterButton.disabled = false;
        setBackgroundInert(true);
        document.body.classList.add('intro-enabled');
        document.body.classList.remove('intro-complete');
        createSparks();
        enterButton.focus({ preventScroll: true });
        if (reducedMotion.matches) {
            revealTimer = window.setTimeout(closeIntro, 1000);
        }
    }

    function shouldShowIntro() {
        if (reducedMotion.matches) return false;
        try { return window.sessionStorage.getItem(storageKey) !== '1'; }
        catch (_) { return true; }
    }

    enterButton.addEventListener('click', revealIntro);
    skipButton.addEventListener('click', closeIntro);
    replayButton.addEventListener('click', openIntro);

    if (shouldShowIntro()) openIntro();
})();
