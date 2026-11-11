import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.164.1/build/three.module.js';

(() => {
    'use strict';
    const intro = document.getElementById('cinematic-intro');
    const canvas = document.getElementById('intro-3d-canvas');
    const title = document.getElementById('reveal-title');
    const auth = document.getElementById('auth-stage');
    const shell = document.getElementById('app-shell');
    const fireTransition = document.getElementById('fire-transition');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const storageKey = 'ubc-cinematic-intro-v2';
    if (!intro || !canvas || !auth || !shell) return;

    let renderer, scene, camera, envelope, flap, seal, particles, raf = 0;
    let startedAt = 0, phase = 'idle', previousFocus = null;
    const clock = new THREE.Clock();

    function makeEnvelope() {
        const group = new THREE.Group();
        const paper = new THREE.MeshStandardMaterial({ color: 0xe9dfcc, roughness: .72, metalness: .03 });
        const darkPaper = new THREE.MeshStandardMaterial({ color: 0xb7a58e, roughness: .8 });
        const body = new THREE.Mesh(new THREE.BoxGeometry(3.35, 2.15, .12), paper);
        group.add(body);
        const flapShape = new THREE.Shape();
        flapShape.moveTo(-1.675, 1.075); flapShape.lineTo(0, -.12); flapShape.lineTo(1.675, 1.075); flapShape.closePath();
        const flapGeo = new THREE.ShapeGeometry(flapShape);
        flap = new THREE.Mesh(flapGeo, darkPaper);
        flap.position.z = .075;
        group.add(flap);
        const seamMat = new THREE.LineBasicMaterial({ color: 0x7b6b5b, transparent: true, opacity: .5 });
        const seam = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(-1.62,-1.02,.08), new THREE.Vector3(0,-.08,.08), new THREE.Vector3(1.62,-1.02,.08)
        ]);
        group.add(new THREE.Line(seam, seamMat));
        const sealMat = new THREE.MeshStandardMaterial({ color: 0x9a3029, roughness: .38, metalness: .25 });
        seal = new THREE.Mesh(new THREE.CylinderGeometry(.34,.38,.12,48), sealMat);
        seal.rotation.x = Math.PI / 2;
        seal.position.set(0,-.02,.18);
        group.add(seal);
        const ring = new THREE.Mesh(new THREE.TorusGeometry(.29,.025,8,48), new THREE.MeshStandardMaterial({color:0xe5b66e,metalness:.7,roughness:.25}));
        ring.position.copy(seal.position); ring.position.z += .08; group.add(ring);
        const stamp = new THREE.Mesh(new THREE.CylinderGeometry(.105,.105,.015,6), new THREE.MeshStandardMaterial({color:0xf1c889,metalness:.5,roughness:.35}));
        stamp.rotation.x=Math.PI/2; stamp.position.set(0,-.02,.27); group.add(stamp);
        return group;
    }

    function init3D() {
        try {
            renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
            renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.outputColorSpace = THREE.SRGBColorSpace;
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(36, window.innerWidth/window.innerHeight, .1, 100);
            camera.position.set(0,0,10);
            scene.add(new THREE.AmbientLight(0xffffff, 1.25));
            const key = new THREE.DirectionalLight(0xffdfb4, 3.2); key.position.set(-3,5,7); scene.add(key);
            const rim = new THREE.PointLight(0xf05a32, 24, 18); rim.position.set(3,-2,4); scene.add(rim);
            const blue = new THREE.PointLight(0x4c75a5, 10, 15); blue.position.set(-4,1,-2); scene.add(blue);
            envelope = makeEnvelope(); envelope.scale.setScalar(.01); envelope.position.set(-5,3,-1); scene.add(envelope);
            const count=420, positions=new Float32Array(count*3), colors=new Float32Array(count*3);
            for(let i=0;i<count;i++){positions[i*3]=(Math.random()-.5)*13;positions[i*3+1]=(Math.random()-.5)*8;positions[i*3+2]=(Math.random()-.5)*4;const c=new THREE.Color().setHSL(.06+Math.random()*.06,.85,.48+Math.random()*.25);colors.set([c.r,c.g,c.b],i*3);}
            const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(positions,3));geo.setAttribute('color',new THREE.BufferAttribute(colors,3));
            particles=new THREE.Points(geo,new THREE.PointsMaterial({size:.035,vertexColors:true,transparent:true,opacity:.0,blending:THREE.AdditiveBlending,depthWrite:false}));scene.add(particles);
            window.addEventListener('resize',resize);
            return true;
        } catch (error) { console.warn('UBC 3D intro fallback:',error); return false; }
    }

    function resize(){if(!renderer||!camera)return;camera.aspect=window.innerWidth/window.innerHeight;camera.updateProjectionMatrix();renderer.setSize(window.innerWidth,window.innerHeight);}
    function animate(){
        raf=requestAnimationFrame(animate);
        if(!renderer||!scene)return;
        const elapsed=clock.getElapsedTime();
        if(envelope){
            if(phase==='arrival'){const t=Math.min((performance.now()-startedAt)/2100,1), eased=1-Math.pow(1-t,4);envelope.position.set(-5+5*eased,3-3*eased,Math.sin(t*Math.PI)*1.5);envelope.rotation.set(.25*(1-t),-.35*(1-t),-.55*(1-t));const s=.01+.99*eased;envelope.scale.setScalar(s);if(t>=1){phase='waiting';document.getElementById('intro-controls')?.classList.add('is-visible');}}
            if(phase==='waiting'){envelope.position.y=Math.sin(elapsed*1.2)*.035;envelope.rotation.y=Math.sin(elapsed*.5)*.025;seal.rotation.z=Math.sin(elapsed*.8)*.04;}
            if(phase==='impact'){const t=Math.min((performance.now()-startedAt)/700,1);envelope.scale.setScalar(1+t*.12);envelope.rotation.z*=.94;if(t>.16)particles.material.opacity=Math.min((t-.16)*1.6,.95);if(t>=1)revealTitle();}
        }
        if(particles&&phase!=='idle'){particles.rotation.y=elapsed*.025;particles.rotation.z=Math.sin(elapsed*.18)*.025;}
        renderer.render(scene,camera);
    }

    function revealTitle(){if(phase==='title')return;phase='title';title.classList.add('is-visible');intro.classList.add('is-title');}
    function startIntro(){
        previousFocus=document.activeElement;intro.classList.add('is-active');intro.setAttribute('aria-hidden','false');
        document.body.classList.add('intro-lock');phase='arrival';startedAt=performance.now();clock.start();
        document.getElementById('intro-skip')?.focus({preventScroll:true});
        if(reducedMotion.matches){intro.classList.add('is-static');revealTitle();document.getElementById('intro-controls')?.classList.add('is-visible');phase='title';return;}
        if(!renderer){revealTitle();document.getElementById('intro-controls')?.classList.add('is-visible');phase='title';return;}
        cancelAnimationFrame(raf);animate();
    }
    function impact(){if(phase!=='waiting')return;phase='impact';startedAt=performance.now();intro.classList.add('is-impact');}
    function openAuth(){
        cancelAnimationFrame(raf);intro.classList.remove('is-active','is-title','is-impact');intro.setAttribute('aria-hidden','true');
        document.body.classList.remove('intro-lock');auth.hidden=false;auth.classList.add('is-entering');
        document.getElementById('guest-entry')?.focus({preventScroll:true});
        try{sessionStorage.setItem(storageKey,'1');}catch(_){}
    }
    function closeCurtainsToHome(){
        auth.classList.add('is-leaving');fireTransition.classList.add('is-running');
        window.setTimeout(()=>{auth.hidden=true;shell.classList.add('is-unlocked');fireTransition.classList.remove('is-running');auth.classList.remove('is-leaving');if(previousFocus?.focus)previousFocus.focus({preventScroll:true});},1250);
    }
    function replay(){auth.hidden=true;shell.classList.remove('is-unlocked');startIntro();}
    document.getElementById('intro-continue')?.addEventListener('click',impact);
    document.getElementById('intro-skip')?.addEventListener('click',openAuth);
    document.getElementById('guest-entry')?.addEventListener('click',closeCurtainsToHome);
    document.getElementById('replay-intro')?.addEventListener('click',replay);
    if(init3D()) { if(!reducedMotion.matches) startIntro(); else { intro.classList.add('is-active','is-static');revealTitle();document.getElementById('intro-controls')?.classList.add('is-visible');phase='title'; } }
    else { startIntro(); }
    window.UBCTransition={revealHome:closeCurtainsToHome};
})();
