'use strict';

// Globe.GL 2.46.2 is vendored locally. world.json is the supplied Natural Earth
// 1:110m map. Coordinates below are representative display points, not borders.
async function initializeGlobe() {
  const container = document.getElementById('export-globe');
  if (!container) return;

  const wrapper = container.closest('.globe-wrap');
  const status = document.getElementById('globe-status');
  const coordinates = {
    eac: [56, 62], eu: [50, 12], uae: [25.2, 55.3], us: [38, -98],
    jp: [36, 140], cn: [33, 104], asean: [9, 106],
  };
  const origin = { code: 'kr', name: '대한민국', lat: 36.5, lng: 127.5 };
  const destinations = Array.from(document.querySelectorAll('.country-card[data-country]'), link => {
    const code = link.dataset.country;
    const [lat, lng] = coordinates[code];
    return { code, lat, lng, name: link.querySelector('strong').textContent, href: link.href };
  });
  let globe;

  function showFallback() {
    globe?.pauseAnimation();
    wrapper.classList.remove('is-ready');
    container.replaceChildren();
    status.textContent = '지구본을 불러오지 못했습니다. 지도 또는 아래 국가 카드를 눌러 선택하세요.';
  }

  try {
    if (!window.Globe) throw new Error('Globe library unavailable');
    status.textContent = '회전 가능한 지구본을 불러오는 중입니다…';
    const response = await fetch(container.dataset.mapUrl, { signal: AbortSignal.timeout(15000) });
    if (!response.ok) throw new Error('World map unavailable');
    const world = await response.json();
    if (world.type !== 'FeatureCollection' || !world.features?.length) {
      throw new Error('Invalid world map');
    }

    const goToCountry = location => {
      if (location.href) window.location.assign(location.href);
    };
    globe = new Globe(container, { animateIn: false, waitForGlobeReady: false })
      .width(container.clientWidth)
      .height(container.clientHeight)
      .backgroundColor('rgba(0,0,0,0)')
      .atmosphereColor('#b8a9e5')
      .atmosphereAltitude(0.12)
      .polygonsData(world.features)
      .polygonCapColor(() => '#ddd7ed')
      .polygonSideColor(() => '#c6bedf')
      .polygonStrokeColor(() => '#bfb4d9')
      .polygonAltitude(0.006)
      .polygonLabel(() => '')
      .polygonsTransitionDuration(0)
      .pointsData([origin, ...destinations])
      .pointColor(location => location.code === 'kr' ? '#6546c6' : '#9277dc')
      .pointRadius(location => location.code === 'kr' ? 0.65 : 0.5)
      .pointAltitude(0.018)
      .pointLabel(() => '')
      .pointsTransitionDuration(0)
      .onPointClick(goToCountry)
      .arcsData(destinations)
      .arcStartLat(origin.lat)
      .arcStartLng(origin.lng)
      .arcStartAltitude(0.012)
      .arcEndLat('lat')
      .arcEndLng('lng')
      .arcEndAltitude(0.012)
      .arcColor(() => '#9270ce')
      .arcAltitudeAutoScale(0.28)
      .arcStroke(0.28)
      .arcDashLength(0.025)
      .arcDashGap(0.018)
      .arcDashAnimateTime(0)
      .arcsTransitionDuration(0)
      .htmlElementsData([origin, ...destinations])
      .htmlAltitude(0.025)
      .htmlTransitionDuration(0)
      .htmlElement(location => {
        const anchor = document.createElement('div');
        anchor.className = 'globe-marker-anchor';
        anchor.dataset.country = location.code;
        const label = document.createElement(location.href ? 'a' : 'span');
        label.className = `globe-marker globe-marker--${location.code}`;
        label.textContent = location.name;
        if (location.href) {
          label.href = location.href;
          label.setAttribute('aria-label', `${location.name} 선택`);
          // A name click navigates; dragging the globe itself only rotates it.
          label.addEventListener('pointerdown', event => event.stopPropagation());
        }
        anchor.append(label);
        return anchor;
      });

    const material = globe.globeMaterial();
    material.color.set('#fbfaff');
    material.emissive.set('#eee9f7');
    material.emissiveIntensity = 0.3;
    material.specular.set('#d8cfef');
    material.shininess = 12;
    const controls = globe.controls();
    const radius = globe.getGlobeRadius();
    controls.autoRotate = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    controls.autoRotateSpeed = 0.35;
    controls.enableRotate = !container.closest('.home-intro');
    controls.enableZoom = !container.closest('.home-intro');
    controls.enablePan = false;
    const updateControls = () => {
      const interactive = Boolean(container.closest('.home-globe-dock'));
      controls.enableRotate = interactive;
      controls.enableZoom = interactive;
      controls.autoRotate = !interactive && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      status.textContent = interactive
        ? '드래그하여 회전 · 휠로 확대/축소 · 국가 이름을 눌러 선택'
        : '스크롤하여 국가 선택 지도로 이동하세요';
    };
    document.addEventListener('globe-dock-change', updateControls);
    updateControls();
    controls.zoomSpeed = 0.7;
    controls.minPolarAngle = 0.06;
    controls.maxPolarAngle = Math.PI - 0.06;

    const fitGlobe = (resetView = false) => {
      const vertical = globe.camera().fov * Math.PI / 360;
      const horizontal = Math.atan(Math.tan(vertical) * container.clientWidth / Math.max(1, container.clientHeight));
      const distance = radius / Math.sin(Math.min(vertical, horizontal)) * 1.08;
      controls.minDistance = distance;
      controls.maxDistance = Math.max(radius * 5, distance * 2);
      globe.pointOfView({ altitude: distance / radius - 1, ...(resetView ? { lat: 26, lng: 104 } : {}) });
    };
    const reset = () => fitGlobe(true);
    const zoom = factor => {
      const { altitude } = globe.pointOfView();
      globe.pointOfView({ altitude: Math.max(controls.minDistance / radius - 1,
        Math.min(controls.maxDistance / radius - 1, (altitude + 1) * factor - 1)) });
    };
    reset();
    const canvas = container.querySelector('canvas');
    canvas.tabIndex = 0;
    canvas.setAttribute('role', 'group');
    canvas.setAttribute('aria-label', '지구본: 방향키로 회전, 더하기·빼기로 확대·축소, Home으로 처음 위치');
    canvas.addEventListener('keydown', event => {
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      const shifts = { ArrowLeft: [0, -12], ArrowRight: [0, 12], ArrowUp: [10, 0], ArrowDown: [-10, 0] };
      if (shifts[event.key]) {
        const [latDelta, lngDelta] = shifts[event.key];
        const view = globe.pointOfView();
        globe.pointOfView({ lat: Math.max(-80, Math.min(80, view.lat + latDelta)), lng: view.lng + lngDelta });
      } else if (event.key === '+' || event.key === '=') zoom(0.8);
      else if (event.key === '-') zoom(1.25);
      else if (event.key === 'Home') reset();
      else return;
      event.preventDefault();
    });
    canvas.addEventListener('webglcontextlost', showFallback, { once: true });
    new ResizeObserver(() => {
      if (container.clientWidth && container.clientHeight) {
        globe.width(container.clientWidth).height(container.clientHeight);
        fitGlobe();
      }
    }).observe(container);

    // Avoid spending GPU time on a globe outside the viewport or in a hidden tab.
    let inView = true;
    const updateAnimation = () => {
      if (!document.hidden && inView && wrapper.classList.contains('is-ready')) globe.resumeAnimation();
      else globe.pauseAnimation();
    };
    new IntersectionObserver(([entry]) => {
      inView = entry.isIntersecting;
      updateAnimation();
    }).observe(container);
    document.addEventListener('visibilitychange', updateAnimation);
    wrapper.classList.add('is-ready');
    status.textContent = container.closest('.home-intro')
      ? '국가 이름 또는 아래 국가 카드를 눌러 선택'
      : '드래그하여 회전 · 휠로 확대/축소 · 국가 이름을 눌러 선택';
  } catch (error) {
    showFallback();
    console.warn('지구본 대신 기존 지도와 국가 카드를 표시합니다.', error);
  }
}

initializeGlobe();

// Move the existing globe as the dashboard map heading enters view.
function initializeHomeIntro() {
  const intro = document.querySelector('.home-intro');
  if (!intro) return;
  const scene = intro.querySelector('.intro-scene');
  const wrapper = intro.querySelector('.globe-wrap');
  const dock = document.querySelector('.home-globe-dock');
  const mapHeading = dock?.querySelector('.map-topline');
  if (!scene || !wrapper || !dock || !mapHeading) return;
  let pending = false;
  const update = () => {
    pending = false;
    const pastIntro = intro.getBoundingClientRect().bottom <= 0;
    const progress = Math.max(0, Math.min(1, window.scrollY / Math.max(1, intro.offsetHeight - window.innerHeight)));
    intro.style.setProperty('--intro-progress', progress);
    intro.classList.toggle('is-past-intro', pastIntro);
    const destination = mapHeading.getBoundingClientRect().top <= window.innerHeight / 2 ? dock : scene;
    if (wrapper.parentElement !== destination) {
      destination.append(wrapper);
      document.dispatchEvent(new Event('globe-dock-change'));
    }
  };
  const schedule = () => {
    if (!pending) {
      pending = true;
      requestAnimationFrame(update);
    }
  };
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule);
  update();
}
initializeHomeIntro();
