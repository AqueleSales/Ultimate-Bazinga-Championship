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
  let sealMesh = null;
  let openingTimer = 0;
  let explosionShards = [];
  let explosionStartedAt = 0;
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
    sealMesh = seal;
    seal.rotation.x = Math.PI / 2;
    seal.position.set(0, -.08, .2);
    group.add(seal);

    const stamp = new THREE.Mesh(
      new THREE.CylinderGeometry(.11, .11, .02, 6),
      new THREE.MeshStandardMaterial({ color: 0xf1c889, metalness: .45, roughness: .35 })
    );
    stamp.rotation.x = Math.PI / 2;
    stamp.position.set(0, -.08, .31);
    group.add(stamp);
    return group;
  }

  function createExplosion() {
    if (!THREE || !scene || !envelope) return;
    explosionShards.forEach((shard) => scene.remove(shard.mesh));
    explosionShards = [];
    const palette = [0xe9dfcc, 0xd8c4a8, 0xb7a58e, 0x9a3029, 0xe5a94f, 0xf2c57f];
    const center = envelope.position.clone();
    const count = 42;
    for (let i = 0; i < count; i += 1) {
      const width = .12 + Math.random() * .42;
      const height = .12 + Math.random() * .38;
      const shape = new THREE.Shape();
      shape.moveTo(-width * .5, -height * .35);
      shape.lineTo(width * (.25 + Math.random() * .5), -height * .5);
      shape.lineTo((Math.random() - .5) * width, height * .6);
      shape.closePath();
      const geometry = new THREE.ShapeGeometry(shape);
      const material = new THREE.MeshBasicMaterial({
        color: palette[i % palette.length],
        side: THREE.DoubleSide,
        transparent: false
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(
        center.x + (Math.random() - .5) * 2.4,
        center.y + (Math.random() - .5) * 1.5,
        center.z + .2 + Math.random() * .45
      );
      scene.add(mesh);
      const direction = new THREE.Vector3(
        (Math.random() - .5) * 2.2,
        (Math.random() - .15) * 2.4,
        (Math.random() - .5) * 1.2
      ).normalize();
      explosionShards.push({
        mesh,
        velocity: direction.multiplyScalar(2.2 + Math.random() * 5.2),
        spin: new THREE.Vector3(
          (Math.random() - .5) * 13,
          (Math.random() - .5) * 13,
          (Math.random() - .5) * 13
        )
      });
    }
    envelope.visible = false;
    explosionStartedAt = performance.now();
  }

  function updateExplosion(delta) {
    if (!explosionShards.length) return;
    explosionShards.forEach((shard) => {
      shard.velocity.y -= 3.8 * delta;
      shard.mesh.position.addScaledVector(shard.velocity, delta);
      shard.mesh.rotation.x += shard.spin.x * delta;
      shard.mesh.rotation.y += shard.spin.y * delta;
      shard.mesh.rotation.z += shard.spin.z * delta;
    });
  }

  function clearExplosion() {
    explosionShards.forEach((shard) => {
      scene?.remove(shard.mesh);
      shard.mesh.geometry.dispose();
      shard.mesh.material.dispose();
    });
    explosionShards = [];
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
    authTimer = window.setTimeout(openAuth, reducedMotion.matches ? 0 : 6500);
  }

  function animate() {
    raf = requestAnimationFrame(animate);
    if (!renderer || !scene || !clock) return;
    const delta = Math.min(clock.getDelta(), .04);
    const elapsed = clock.elapsedTime;

    if (phase === 'arrival') {
      const raw = Math.min((performance.now() - startedAt) / 4800, 1);
      const t = raw * raw * (3 - 2 * raw);
      const drift = (1 - raw);
      let vertical;
      if (raw < .22) {
        const fall = raw / .22;
        vertical = 3 - 4.2 * (1 - Math.pow(1 - fall, 3));
      } else if (raw < .62) {
        const rise = (raw - .22) / .4;
        vertical = -1.2 + 1.85 * (rise * rise * (3 - 2 * rise));
      } else if (raw < .86) {
        vertical = .65 + Math.sin((raw - .62) / .24 * Math.PI) * .28;
      } else {
        const slam = (raw - .86) / .14;
        vertical = .65 * Math.pow(1 - slam, 3);
      }
      envelope.position.set(
        -5 + 5 * t + Math.sin(raw * Math.PI * 4) * 1.15 * drift,
        vertical,
        -1 + Math.sin(raw * Math.PI * 5) * 1.1 * drift
      );
      envelope.rotation.set(
        Math.sin(raw * Math.PI * 4) * .48 * drift,
        Math.cos(raw * Math.PI * 3) * .62 * drift,
        -.9 * drift + Math.sin(raw * Math.PI * 5) * .75 * drift
      );
      envelope.scale.setScalar(.025 + .975 * t);
      if (raw >= 1) {
        phase = 'landing';
        startedAt = performance.now();
        intro.classList.add('is-impact');
      }
    } else if (phase === 'landing') {
      const t = Math.min((performance.now() - startedAt) / 720, 1);
      const bounce = Math.exp(-5 * t) * Math.cos(t * 17);
      envelope.position.y = -.12 + bounce * .34;
      envelope.rotation.z = bounce * .13;
      envelope.scale.setScalar(1 - Math.abs(bounce) * .035);
      if (t >= 1) {
        phase = 'waiting';
        envelope.position.set(0, 0, 0);
        envelope.rotation.set(0, 0, 0);
        envelope.scale.setScalar(1);
        showControls();
      }
    } else if (phase === 'waiting') {
      const pulse = Math.sin(elapsed * 5.2);
      const tremor = Math.sin(elapsed * 37) * .006;
      envelope.position.set(Math.sin(elapsed * 1.7) * .025 + tremor, Math.sin(elapsed * 2.3) * .035, 0);
      envelope.rotation.set(Math.sin(elapsed * 3.1) * .012, Math.sin(elapsed * 2.4) * .018, tremor * 1.5);
      envelope.scale.setScalar(1 + Math.max(0, pulse) * .018);
      if (sealMesh) sealMesh.scale.setScalar(1 + Math.max(0, pulse) * .055);
    } else if (phase === 'opening') {
      const t = Math.min((performance.now() - startedAt) / 1550, 1);
      updateExplosion(delta);
      if (particles) particles.material.opacity = Math.max(0, 1 - t * .7);
      if (t >= 1) {
        clearExplosion();
        revealTitle();
      }
    }

    if (particles && phase !== 'idle') {
      particles.rotation.y = elapsed * .035;
      particles.rotation.z = Math.sin(elapsed * .22) * .04;
      if (phase === 'opening') {
        const p = particles.geometry.attributes.position;
        for (let i = 0; i < p.count; i += 1) {
          p.array[i * 3 + 1] += .012 + (i % 7) * .001;
          if (p.array[i * 3 + 1] > 4) p.array[i * 3 + 1] = -4;
        }
        p.needsUpdate = true;
      }
    }
    renderer.render(scene, camera);
  }

  function startIntro() {
    window.clearTimeout(authTimer);
    auth.hidden = true;
    shell.classList.remove('is-unlocked');
    intro.classList.remove('is-title', 'is-impact', 'is-static', 'is-card-ready', 'is-opening');
    title?.classList.remove('is-visible');
    controls?.classList.remove('is-visible');
    intro.classList.add('is-active');
    intro.setAttribute('aria-hidden', 'false');
    document.body.classList.add('intro-lock');
    phase = 'arrival';
    startedAt = performance.now();

    if (reducedMotion.matches) {
      intro.classList.add('is-static', 'is-fallback', 'is-card-ready');
      phase = 'waiting';
      showControls();
      return;
    }
    if (!renderer || !envelope) {
      intro.classList.add('is-fallback');
      window.setTimeout(() => {
        if (phase !== 'arrival') return;
        phase = 'waiting';
        intro.classList.add('is-card-ready');
        showControls();
      }, 4800);
      return;
    }
    envelope.position.set(-5, 3, -1);
    envelope.rotation.set(.25, -.35, -.55);
    envelope.scale.setScalar(.01);
    if (flapPivot) flapPivot.rotation.x = 0;
    if (sealMesh) sealMesh.scale.setScalar(1);
    if (envelope) envelope.visible = true;
    clearExplosion();
    if (particles) particles.material.opacity = 0;
    clock.start();
    cancelAnimationFrame(raf);
    animate();
  }

  function impact() {
    if (phase !== 'waiting') return;
    window.clearTimeout(openingTimer);
    if (!renderer || !envelope) {
      phase = 'opening';
      intro.classList.add('is-opening');
      document.getElementById('intro-fallback-card')?.classList.add('is-exploding');
      openingTimer = window.setTimeout(revealTitle, reducedMotion.matches ? 0 : 1450);
      return;
    }
    phase = 'opening';
    startedAt = performance.now();
    intro.classList.remove('is-impact');
    intro.classList.add('is-opening');
    createExplosion();
    if (particles) particles.material.opacity = 1;
  }

  function clickEnvelope(event) {
    if (phase !== 'waiting') return;
    if (!renderer || !camera || !envelope || !THREE) { impact(); return; }
    const rect = canvas.getBoundingClientRect();
    const pointer = new THREE.Vector2(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      -((event.clientY - rect.top) / rect.height) * 2 + 1
    );
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(pointer, camera);
    if (raycaster.intersectObject(envelope, true).length) impact();
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
    if (auth.dataset.authenticated === 'true') { enterHub(); return; }
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
    }, reducedMotion.matches ? 0 : 1550);
  }

  canvas.addEventListener('click', clickEnvelope);
  canvas.addEventListener('keydown', (event) => {
    if ((event.key === 'Enter' || event.key === ' ') && phase === 'waiting') {
      event.preventDefault();
      impact();
    }
  });
  document.getElementById('intro-fallback-card')?.addEventListener('click', impact);
  document.getElementById('intro-skip')?.addEventListener('click', openAuth);
  document.getElementById('guest-entry')?.addEventListener('click', enterHub);
  document.getElementById('replay-intro')?.addEventListener('click', startIntro);

  (async () => {
    let entered = false;
    try { entered = sessionStorage.getItem('ubc-hub-entered-v1') === '1'; } catch (_) {}
    if (entered && auth.dataset.authenticated !== 'true') {
      shell.classList.add('is-unlocked');
      auth.hidden = true;
      return;
    }
    if (auth.dataset.authenticated === 'true') {
      phase = 'auth';
      intro.classList.remove('is-active');
      intro.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('intro-lock');
      auth.hidden = false;
      auth.classList.add('is-entering');
      document.getElementById('guest-entry')?.focus({ preventScroll: true });
      return;
    }
    await init3D();
    startIntro();
  })();

  window.UBCTransition = { revealHome: enterHub, replay: startIntro };
})();
