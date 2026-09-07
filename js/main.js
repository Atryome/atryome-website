/**
 * AURORA WEB — MAIN SCRIPT
 * Hero v1.0, Section 02 Aurora, Section 03 Experience, Section 04 Technology, Section 05 Vision, Section 06 Contact & Footer
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Trigger initial dark emergence sequence
  requestAnimationFrame(() => {
    document.body.classList.remove('is-loading');
    document.body.classList.add('is-loaded');
  });

  // 2. Handle scroll indication and Header ambient backdrop
  const header = document.getElementById('site-header');
  const scrollIndicator = document.getElementById('scroll-indicator');

  const handleScroll = () => {
    const currentScrollY = window.scrollY;

    // Fade scroll indicator gently on initial scroll
    if (scrollIndicator) {
      if (currentScrollY > 50) {
        scrollIndicator.style.opacity = '0';
        scrollIndicator.style.pointerEvents = 'none';
      } else {
        scrollIndicator.style.opacity = '1';
        scrollIndicator.style.pointerEvents = 'auto';
      }
    }

    // Header ambient backdrop activation when scrolling past initial Hero area
    if (header) {
      if (currentScrollY > 80) {
        header.style.background = 'rgba(0, 0, 0, 0.85)';
        header.style.backdropFilter = 'blur(16px)';
        header.style.webkitBackdropFilter = 'blur(16px)';
        header.style.borderBottom = '1px solid rgba(255, 255, 255, 0.07)';
      } else {
        header.style.background = 'transparent';
        header.style.backdropFilter = 'none';
        header.style.webkitBackdropFilter = 'none';
        header.style.borderBottom = 'none';
      }
    }
  };

  window.addEventListener('scroll', handleScroll, { passive: true });

  // 3. Section Reveal Intersection Observer (Fail-Safe for #aurora, #experience, #technology, #vision, and #contact)
  const revealSections = document.querySelectorAll('.section-aurora, .section-experience, .section-technology, .section-vision, .section-contact, .development-section');

  if ('IntersectionObserver' in window && revealSections.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in-view');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    });

    revealSections.forEach(section => {
      // Check if already in viewport or accessed via hash anchor
      const rect = section.getBoundingClientRect();
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        section.classList.add('is-in-view');
      } else {
        observer.observe(section);
      }
    });
  } else {
    // Fallback: If IntersectionObserver is unsupported, reveal all sections immediately
    revealSections.forEach(section => section.classList.add('is-in-view'));
  }

  // 4. Handle direct anchor jump on page load (e.g., #experience)
  if (window.location.hash) {
    const targetEl = document.querySelector(window.location.hash);
    if (targetEl) {
      targetEl.classList.add('is-in-view');
    }
  }

  // 5. Ambient Atmosphere Audio Controller (Native HTML5 Audio + Ambient Autoplay + Mute/Unmute Toggle)
  const atmosphereBtn = document.getElementById('atmosphere-toggle');
  const auroraAudio = document.getElementById('aurora-audio-player');

  if (atmosphereBtn && auroraAudio) {
    const TARGET_VOLUME = 0.30;
    const FADE_IN_DURATION = 3000; // ~3.0s fade in
    const FADE_OUT_DURATION = 1800; // ~1.8s fade out
    let fadeInterval = null;
    let fallbackAttempted = false;

    const stopFade = () => {
      if (fadeInterval) {
        clearInterval(fadeInterval);
        fadeInterval = null;
      }
    };

    const fadeIn = (onComplete) => {
      stopFade();
      const startTime = performance.now();
      const startVol = auroraAudio.volume;

      fadeInterval = setInterval(() => {
        const elapsed = performance.now() - startTime;
        const progress = Math.min(elapsed / FADE_IN_DURATION, 1);
        auroraAudio.volume = startVol + (TARGET_VOLUME - startVol) * progress;

        if (progress >= 1) {
          stopFade();
          auroraAudio.volume = TARGET_VOLUME;
          if (onComplete) onComplete();
        }
      }, 30);
    };

    const fadeOut = (onComplete) => {
      stopFade();
      const startTime = performance.now();
      const startVol = auroraAudio.volume;

      fadeInterval = setInterval(() => {
        const elapsed = performance.now() - startTime;
        const progress = Math.min(elapsed / FADE_OUT_DURATION, 1);
        auroraAudio.volume = Math.max(0, startVol * (1 - progress));

        if (progress >= 1) {
          stopFade();
          auroraAudio.volume = 0;
          auroraAudio.pause();
          if (onComplete) onComplete();
        }
      }, 30);
    };

    const setControlState = (active) => {
      atmosphereBtn.setAttribute('aria-pressed', active ? 'true' : 'false');
      document.body.classList.toggle('atmosphere-active', active);
    };

    const removeFallbackListeners = () => {
      window.removeEventListener('pointerdown', handleFirstInteraction, { capture: true });
      window.removeEventListener('touchstart', handleFirstInteraction, { capture: true });
      window.removeEventListener('keydown', handleFirstInteraction, { capture: true });
    };

    const handleFirstInteraction = (e) => {
      if (fallbackAttempted) return;

      if (e && e.target && atmosphereBtn.contains(e.target)) {
        fallbackAttempted = true;
        removeFallbackListeners();
        return;
      }

      fallbackAttempted = true;
      removeFallbackListeners();

      auroraAudio.volume = 0;
      const playPromise = auroraAudio.play();
      if (playPromise !== undefined) {
        playPromise.then(() => {
          setControlState(true);
          fadeIn();
        }).catch(() => {
          stopFade();
          auroraAudio.volume = 0;
          auroraAudio.pause();
          setControlState(false);
        });
      }
    };

    const registerFallback = () => {
      if (fallbackAttempted) return;
      window.addEventListener('pointerdown', handleFirstInteraction, { capture: true });
      window.addEventListener('touchstart', handleFirstInteraction, { capture: true });
      window.addEventListener('keydown', handleFirstInteraction, { capture: true });
    };

    // Manual Sound Toggle (SOUND ON / SOUND OFF)
    atmosphereBtn.addEventListener('click', () => {
      fallbackAttempted = true;
      removeFallbackListeners();

      const isCurrentlyActive = atmosphereBtn.getAttribute('aria-pressed') === 'true';

      if (!isCurrentlyActive) {
        // Activate Sound
        auroraAudio.volume = 0;
        const playPromise = auroraAudio.play();

        if (playPromise !== undefined) {
          playPromise.then(() => {
            setControlState(true);
            fadeIn();
          }).catch(() => {
            stopFade();
            auroraAudio.volume = 0;
            auroraAudio.pause();
            setControlState(false);
          });
        } else {
          setControlState(true);
          fadeIn();
        }
      } else {
        // Mute / Deactivate Sound
        setControlState(false);
        fadeOut();
      }
    });

    // Initial Autoplay Attempt (Page Load)
    auroraAudio.volume = 0;
    const initialPlay = auroraAudio.play();

    if (initialPlay !== undefined) {
      initialPlay.then(() => {
        fallbackAttempted = true;
        setControlState(true);
        fadeIn();
      }).catch(() => {
        // Autoplay blocked by browser policy — remain silent and await first user interaction
        stopFade();
        auroraAudio.volume = 0;
        auroraAudio.pause();
        setControlState(false);
        registerFallback();
      });
    } else {
      fallbackAttempted = true;
      setControlState(true);
      fadeIn();
    }
  }
});
