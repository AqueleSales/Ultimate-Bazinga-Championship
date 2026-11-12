(() => {
  'use strict';

  const intro = document.getElementById('cinematic-intro');
  const canvas = document.getElementById('intro-3d-canvas');
  const title = document.getElementById('reveal-title');
  const auth = document.getElementById('auth-stage');
  const shell = document.getElementById('app-shell');
  const fireTransition = document.getElementById('fire-transition');
  const controls = document.getElementById('intro-controls');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const storageKey = 'ubc-cinematic-intro-v3';

  if (!intro || !canvas || !auth || !shell) return;

  let THREE = null;
  let renderer = null;
  let scene = null;
  let camera = null;
  let envelope = null;
  let flapPivot = null;
  let particles = null;
  let raf = 0;
  let clock = null;
  let startedAt = 0;
  let phase = 'idle';
  let authTimer = 0;

  function makeEnvelope() {
    const group = new THREE.Group();
    const paper = new THREE.MeshStandardMaterial({ color: 0xe9dfcc, roughness: .72 });
    const inner = new THREE.MeshStandardMaterial({ color: 0xb7a58e, roughness: .8 });
    const body = new THREE.Mesh(new THREE.BoxGeometry(3.45, 2.25, .13), paper);
    group.add(body);

    const pocket = new THREE.Mesh(new THREE.BoxGeometry(3.38, 1.15, .035), inner);
    pocket.position.set(0, -.52, .09);
    group.add(pocket);

    flapPivot = new THREE.Group();
    flapPivot.position.set(0, 1.12, .12);
    const shape = new THREE.Shape();
    shape.moveTo(-1.69, 0);
    shape.lineTo(1.69, 0);
    shape.lineTo(0, -1.22);
    shape.closePath();
    const flap = new THREE.Mesh(new THREE.ShapeGeometry(shape), paper);
    flap.position.y = 0;
    flapPivot.add(flap);
    group.add(flapPivot);

    const seal = new THREE.Mesh(
      new THREE.CylinderGeometry(.34, .38, .13, 48),
      new THREE.MeshStandardMaterial({ color: 0x9a3029, roughness: .35, metalness: .28 })
    );
    seal.rotation.x = Math.PI / 2;
    seal.position.set(0, -.08, .2);
    group.add(seal);

    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(.29, .025, 8, 48),
      new THREE.MeshStandardMaterial({ color: 0xe5b66e, metalness: .65, roughness: .28 })
    );
    ring.position.set(0, -.08, .29);
    group.add(ring);

    const stamp = new THREE.Mesh(
      new THREE.CylinderGeometry(.11, .11, .02, 6),
      new THREE.MeshStandardMaterial({ color: 0xf1c889, metalness: .45, roughness: .35 })
    );
    stamp.rotation.x = Math.PI / 2;
    stamp.position.set(0, -.08, .31);
    group.add(stamp);
    return group;
  }

  async function init3D() {
    try {
      THREE = await import('https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js');
      renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.outputColorSpace = THREE.SRGBColorSpace;

      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(36, window.innerWidth / window.innerHeight, .1, 100);
      camera.position.set(0, 0, 10);
      scene.add(new THREE.AmbientLight(0xffffff, 1.15));
      const key = new THREE.DirectionalLight(0xffdfb4, 3.1);
      key.position.set(-3, 5, 7);
      scene.add(key);
      const rim = new THREE.PointLight(0xf05a32, 22, 18);
      rim.position.set(3, -2, 4);
      scene.add(rim);
      const cool = new THREE.PointLight(0x5579b4, 9, 15);
      cool.position.set(-4, 1, -2);
      scene.add(cool);

      envelope = makeEnvelope();
      envelope.scale.setScalar(.01);
      envelope.position.set(-5, 3, -1);
      scene.add(envelope);

      const count = 520;
      const positions = new Float32Array(count * 3);
      const colors = new Float32Array(count * 3);
      for (let i = 0; i < count; i += 1) {
        positions[i * 3] = (Math.random() - .5) * 13;
        positions[i * 3 + 1] = (Math.random() - .5) * 8;
        positions[i * 3 + 2] = (Math.random() - .5) * 4;
        const color = new THREE.Color().setHSL(.055 + Math.random() * .07, .85, .5 + Math.random() * .2);
        colors.set([color.r, color.g, color.b], i * 3);
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      particles = new THREE.Points(
        geometry,
        new THREE.PointsMaterial({
          size: .035, vertexColors: true, transparent: true, opacity: 0,
          blending: THREE.AdditiveBlending, depthWrite: false
        })
      );
      scene.add(particles);
      clock = new THREE.Clock();
      window.addEventListener('resize', resize);
      return true;
    } catch (error) {
      console.warn('Three.js indisponível; usando abertura 2D de reserva.', error);
      if (renderer) renderer.dispose();
      renderer = null;
      return false;
    }
  }

  function resize() {
    if (!renderer || !camera) return;
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  function showControls() {
    controls?.classList.add('is-visible');
  }

  function revealTitle() {
    if (phase === 'title' || phase === 'auth') return;
    phase = 'title';
    title?.classList.add('is-visible');
    intro.classList.add('is-title');
    showControls();
    window.clearTimeout(authTimer);
    authTimer = window.setTimeout(openAuth, 5200);
  }

  function animate() {
    raf = requestAnimationFrame(animate);
    if (!renderer || !scene || !clock) return;
    const elapsed = clock.getElapsedTime();

    if (phase === 'arrival') {
      const t = Math.min((performance.now() - startedAt) / 2200, 1);
      const eased = 1 - Math.pow(1 - t, 4);
      envelope.position.set(-5 + 5 * eased, 3 - 3 * eased, Math.sin(t * Math.PI) * 1.25);
      envelope.rotation.set(.22 * (1 - eased), -.32 * (1 - eased), -.52 * (1 - eased));
      envelope.scale.setScalar(.01 + .99 * eased);
      if (t >= 1) {
        phase = 'waiting';
        showControls();
      }
    } else if (phase === 'waiting') {
      envelope.position.y = Math.sin(elapsed * 1.15) * .045;
      envelope.rotation.y = Math.sin(elapsed * .5) * .025;
    } else if (phase === 'impact') {
      const t = Math.min((performance.now() - startedAt) / 950, 1);
      envelope.scale.setScalar(1 + Math.sin(t * Math.PI) * .13);
      if (flapPivot) flapPivot.rotation.x = -Math.min(t * 1.8, 1.35);
      if (particles) particles.material.opacity = Math.min(t * 1.15, .95);
      if (t >= 1) revealTitle();
    }

    if (particles && phase !== 'idle') {
      particles.rotation.y = elapsed * .025;
      particles.rotation.z = Math.sin(elapsed * .18) * .025;
    }
    renderer.render(scene, camera);
  }

  function startIntro() {
    window.clearTimeout(authTimer);
    auth.hidden = true;
    shell.classList.remove('is-unlocked');
    intro.classList.remove('is-title', 'is-impact', 'is-static');
    title?.classList.remove('is-visible');
    controls?.classList.remove('is-visible');
    intro.classList.add('is-active');
    intro.setAttribute('aria-hidden', 'false');
    document.body.classList.add('intro-lock');
    phase = 'arrival';
    startedAt = performance.now();

    if (reducedMotion.matches) {
      intro.classList.add('is-static');
      revealTitle();
      return;
    }
    if (!renderer || !envelope) {
      intro.classList.add('is-fallback');
      window.setTimeout(revealTitle, 1600);
      return;
    }
    envelope.position.set(-5, 3, -1);
    envelope.rotation.set(.25, -.35, -.55);
    envelope.scale.setScalar(.01);
    if (flapPivot) flapPivot.rotation.x = 0;
    if (particles) particles.material.opacity = 0;
    clock.start();
    cancelAnimationFrame(raf);
    animate();
  }

  function impact() {
    if (phase !== 'waiting') return;
    phase = 'impact';
    startedAt = performance.now();
    intro.classList.add('is-impact');
  }

  function openAuth() {
    if (phase === 'auth') return;
    phase = 'auth';
    window.clearTimeout(authTimer);
    cancelAnimationFrame(raf);
    intro.classList.remove('is-active', 'is-title', 'is-impact', 'is-fallback');
    intro.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('intro-lock');
    auth.hidden = false;
    auth.classList.remove('is-leaving');
    auth.classList.add('is-entering');
    document.getElementById('guest-entry')?.focus({ preventScroll: true });
    try { sessionStorage.setItem(storageKey, '1'); } catch (_) {}
  }

  function enterHub() {
    auth.classList.add('is-leaving');
    fireTransition?.classList.add('is-running');
    window.setTimeout(() => {
      auth.hidden = true;
      shell.classList.add('is-unlocked');
      fireTransition?.classList.remove('is-running');
      auth.classList.remove('is-leaving');
      document.getElementById('main-content')?.focus({ preventScroll: true });
      try { sessionStorage.setItem('ubc-hub-entered-v1', '1'); } catch (_) {}
    }, reducedMotion.matches ? 0 : 1050);
  }

  document.getElementById('intro-continue')?.addEventListener('click', impact);
  document.getElementById('intro-skip')?.addEventListener('click', openAuth);
  document.getElementById('guest-entry')?.addEventListener('click', enterHub);
  document.getElementById('replay-intro')?.addEventListener('click', startIntro);

  (async () => {
    let entered = false;
    try { entered = sessionStorage.getItem('ubc-hub-entered-v1') === '1'; } catch (_) {}
    if (entered) {
      shell.classList.add('is-unlocked');
      auth.hidden = true;
      return;
    }
    await init3D();
    startIntro();
  })();

  window.UBCTransition = { revealHome: enterHub, replay: startIntro };
})();
