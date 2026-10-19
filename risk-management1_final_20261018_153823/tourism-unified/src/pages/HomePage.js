//home page
import React, { useEffect, useRef, useState, useCallback } from 'react';

// ── ASSET CONFIGURATION ──
const ASSETS = {
  heroVideo: '/videos/sl-hero.mp4',
  destinations: {
    sigiriya: '/images/sigiriya.jpg',
    galle: '/images/galle-fort.jpg',
    ella: '/images/ella-train.jpg',
    mirissa: '/images/mirissa-beach.jpg',
  },
  components: {
    risk: '/images/sigiriya-crowd.jpg',
    sos: '/images/coast-guard.jpg',
    itinerary: '/images/train-journey.jpg',
    hotel: '/images/beach-resort.jpg',
  },
};

// ── GRADIENT FALLBACKS ──
const GRADIENTS = {
  hero: 'linear-gradient(135deg, #0c1a1a 0%, #1a2e2e 50%, #0f2027 100%)',
  sigiriya: 'linear-gradient(180deg, #1a2a1c 0%, #0d1a0f 100%)',
  galle: 'linear-gradient(180deg, #1c2a3a 0%, #0d1a2a 100%)',
  ella: 'linear-gradient(180deg, #1a2a1a 0%, #0d1a0d 100%)',
  mirissa: 'linear-gradient(180deg, #1a2a3c 0%, #0d1a2e 100%)',
  risk: 'linear-gradient(180deg, #1a2a2a 0%, #0d1a1a 100%)',
  sos: 'linear-gradient(180deg, #2a1a1a 0%, #1a0d0d 100%)',
  itinerary: 'linear-gradient(180deg, #1a2a1a 0%, #0d1a0d 100%)',
  hotel: 'linear-gradient(180deg, #1a1a2a 0%, #0d0d1a 100%)',
};

const MEMBERS = [
  {
    name: 'Abinaya R',
    id: 'IT22090058',
    nav: 'risk',
    title: 'Tourism Risk & Context Intelligence',
    desc: 'Predicts crowd levels and risk conditions at 50 Sri Lankan tourist sites using Random Forest ML. 93.39% accuracy across 36,550 training records.',
    tech: ['Random Forest', 'Flask', '16 Features', '36.5K Records'],
    status: 'live',
    accent: '#14B8A6',
    metric: { val: '93.39%', label: 'Accuracy' },
    image: ASSETS.components.risk,
    fallback: GRADIENTS.risk,
  },
  {
    name: 'De Silva D.S.K',
    id: 'IT22108654',
    nav: 'sos',
    title: 'SOS Emergency Safety System',
    desc: 'Voice-activated distress detection using Whisper STT and NER across 10 languages. GPS dispatch to police in under 90 seconds.',
    tech: ['Whisper STT', 'NER Pipeline', 'Random Forest', '100K Posts'],
    status: 'demo',
    accent: '#F87171',
    metric: { val: '<90s', label: 'Response' },
    image: ASSETS.components.sos,
    fallback: GRADIENTS.sos,
  },
  {
    name: 'Wanniarachchi P.M.R',
    id: 'IT22225092',
    nav: 'itinerary',
    title: 'AI Itinerary + Emotion Chatbot',
    desc: 'A* safety-aware routing with facial emotion detection to recommend activities matching the tourist\'s current mood state.',
    tech: ['A* Routing', 'Emotion AI', 'ARCore', '10K Hotels'],
    status: 'demo',
    accent: '#34D399',
    metric: { val: '70%', label: 'Time Saved' },
    image: ASSETS.components.itinerary,
    fallback: GRADIENTS.itinerary,
  },
  {
    name: 'De Silva D.C.M',
    id: 'IT22108586',
    nav: 'hotel',
    title: 'Hotel, Flight & Driver Matcher',
    desc: 'Matches CMB flight arrivals to SLTDA-verified hotels and licensed drivers. Real-time bundle booking with safety filters.',
    tech: ['Flask', 'CMB Flights', 'SLTDA Drivers', 'Budget Match'],
    status: 'live',
    accent: '#60A5FA',
    metric: { val: '100%', label: 'Verified' },
    image: ASSETS.components.hotel,
    fallback: GRADIENTS.hotel,
  },
];

const PLATFORM_STATS = [
  { val: '2.36M', label: 'Annual Arrivals', sub: 'Sri Lanka 2025' },
  { val: '50', label: 'Sites Covered', sub: 'Real-time predictions' },
  { val: '93.4%', label: 'ML Accuracy', sub: 'Production model' },
  { val: '4', label: 'AI Systems', sub: 'Integrated platform' },
];

const DESTINATIONS = [
  { name: 'Sigiriya', region: 'Cultural Triangle', image: ASSETS.destinations.sigiriya, fallback: GRADIENTS.sigiriya, offset: 0 },
  { name: 'Galle Fort', region: 'Southern Coast', image: ASSETS.destinations.galle, fallback: GRADIENTS.galle, offset: 20 },
  { name: 'Ella', region: 'Hill Country', image: ASSETS.destinations.ella, fallback: GRADIENTS.ella, offset: 0 },
  { name: 'Mirissa', region: 'Whale Coast', image: ASSETS.destinations.mirissa, fallback: GRADIENTS.mirissa, offset: 20 },
];

// ── MAGNETIC TEXT COMPONENT ──
// Text that subtly follows the cursor when nearby
function MagneticText({ children, className = '', style = {}, intensity = 0.3 }) {
  const ref = useRef(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  const handleMouseMove = useCallback((e) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const distX = e.clientX - centerX;
    const distY = e.clientY - centerY;
    const distance = Math.sqrt(distX * distX + distY * distY);
    const maxDist = 150;

    if (distance < maxDist) {
      const force = (1 - distance / maxDist) * intensity;
      setOffset({ x: distX * force, y: distY * force });
    } else {
      setOffset({ x: 0, y: 0 });
    }
  }, [intensity]);

  const handleMouseLeave = useCallback(() => {
    setOffset({ x: 0, y: 0 });
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [handleMouseMove]);

  return (
    <span
      ref={ref}
      className={className}
      style={{
        display: 'inline-block',
        transform: `translate(${offset.x}px, ${offset.y}px)`,
        transition: 'transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)',
        ...style,
      }}
      onMouseLeave={handleMouseLeave}
    >
      {children}
    </span>
  );
}

// ── GLITCH TEXT ON HOVER ──
function GlitchText({ text, className = '', style = {} }) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <span
      className={className}
      style={{
        position: 'relative',
        display: 'inline-block',
        ...style,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <span style={{ position: 'relative', zIndex: 3 }}>{text}</span>
      {isHovered && (
        <>
          <span
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              color: '#ef4444',
              zIndex: 1,
              clipPath: 'inset(0 0 50% 0)',
              animation: 'glitchTop 0.3s infinite',
              opacity: 0.8,
            }}
          >
            {text}
          </span>
          <span
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              color: '#22d3ee',
              zIndex: 2,
              clipPath: 'inset(50% 0 0 0)',
              animation: 'glitchBottom 0.3s infinite reverse',
              opacity: 0.8,
            }}
          >
            {text}
          </span>
        </>
      )}
    </span>
  );
}

// ── INTERSECTION OBSERVER HOOK ──
function useInView(threshold = 0.1) {
  const ref = useRef(null);
  const [isInView, setIsInView] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { threshold }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [threshold]);

  return [ref, isInView];
}

// ── ANIMATED SECTION ──
function AnimatedSection({ children, delay = 0, direction = 'up' }) {
  const [ref, isInView] = useInView(0.1);
  const transforms = {
    up: 'translateY(40px)',
    down: 'translateY(-40px)',
    left: 'translateX(-40px)',
    right: 'translateX(40px)',
    scale: 'scale(0.95)',
  };

  return (
    <div
      ref={ref}
      style={{
        opacity: isInView ? 1 : 0,
        transform: isInView ? 'translate(0) scale(1)' : transforms[direction],
        transition: `all 0.8s cubic-bezier(0.16, 1, 0.3, 1) ${delay}s`,
        willChange: 'transform, opacity',
      }}
    >
      {children}
    </div>
  );
}

// ── SAFE IMAGE WITH SHIMMER ──
function SafeImage({ src, fallback, alt, style, className }) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  if (error || !src) {
    return <div style={{ ...style, background: fallback }} aria-label={alt} />;
  }

  return (
    <>
      {!loaded && (
        <div
          style={{
            ...style,
            background: 'linear-gradient(90deg, #1a1a1a 25%, #2a2a2a 50%, #1a1a1a 75%)',
            backgroundSize: '200% 100%',
            animation: 'shimmer 1.5s infinite',
            position: style.position || 'absolute',
            inset: 0,
          }}
        />
      )}
      <img
        src={src}
        alt={alt}
        style={{ ...style, opacity: loaded ? 1 : 0, transition: 'opacity 0.6s ease' }}
        className={className}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
      />
    </>
  );
}

// ── VIDEO HERO ──
function VideoHero({ videoSrc, fallback }) {
  const [videoError, setVideoError] = useState(false);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const videoRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (video) video.play().catch(() => setVideoError(true));
  }, []);

  if (videoError || !videoSrc) {
    return (
      <div
        style={{
          position: 'absolute',
          inset: '-20px',
          background: fallback,
          filter: 'brightness(0.4) saturate(1.2)',
        }}
      />
    );
  }

  return (
    <>
      {!videoLoaded && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: fallback,
            filter: 'brightness(0.4) saturate(1.2)',
            zIndex: 1,
          }}
        />
      )}
      <video
        ref={videoRef}
        autoPlay
        muted
        loop
        playsInline
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          filter: 'brightness(0.4) saturate(1.2)',
          opacity: videoLoaded ? 1 : 0,
          transition: 'opacity 1s ease',
        }}
        onLoadedData={() => setVideoLoaded(true)}
        onError={() => setVideoError(true)}
      >
        <source src={videoSrc} type="video/mp4" />
      </video>
    </>
  );
}

// ── MAIN COMPONENT ──
export default function HomePage({ onNavigate }) {
  const [scrollY, setScrollY] = useState(0);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [navVisible, setNavVisible] = useState(false);
  const heroRef = useRef(null);
  const lastScrollY = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentY = window.scrollY;
      setScrollY(currentY);
      // Show nav when scrolling up or past hero
      setNavVisible(currentY < lastScrollY.current || currentY > 100);
      lastScrollY.current = currentY;
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const el = heroRef.current;
    if (!el) return;
    const handleMouseMove = (e) => {
      const rect = el.getBoundingClientRect();
      setMousePosition({
        x: ((e.clientX - rect.left) / rect.width - 0.5) * 20,
        y: ((e.clientY - rect.top) / rect.height - 0.5) * 10,
      });
    };
    el.addEventListener('mousemove', handleMouseMove);
    return () => el.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const scrollProgress = Math.min(scrollY / window.innerHeight, 1);

  return (
    <div
      style={{
        backgroundColor: '#0a0a0a',
        minHeight: '100vh',
        color: '#fafaf9',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
        overflowX: 'hidden',
      }}
    >
      {/* ── SCROLL PROGRESS ── */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          height: '2px',
          background: 'transparent',
          zIndex: 200,
        }}
      >
        <div
          style={{
            width: `${scrollProgress * 100}%`,
            height: '100%',
            background: 'linear-gradient(90deg, #14B8A6, #2DD4BF)',
            transition: 'width 0.1s linear',
          }}
        />
      </div>

      {/* ── NAVIGATION ── */}
      <nav
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 100,
          backgroundColor: navVisible ? 'rgba(10, 10, 10, 0.9)' : 'transparent',
          backdropFilter: navVisible ? 'blur(20px) saturate(180%)' : 'none',
          borderBottom: navVisible ? '1px solid rgba(255,255,255,0.06)' : '1px solid transparent',
          transform: navVisible ? 'translateY(0)' : 'translateY(-100%)',
          transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        <div
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            padding: '0 32px',
            height: '64px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <MagneticText intensity={0.2}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                cursor: 'pointer',
              }}
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            >
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  border: '1px solid #14B8A6',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '12px',
                  fontWeight: 700,
                  color: '#14B8A6',
                  letterSpacing: '1px',
                }}
              >
                SJ
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span
                  style={{
                    fontSize: '14px',
                    fontWeight: 600,
                    letterSpacing: '-0.01em',
                    color: '#fafaf9',
                    lineHeight: 1.2,
                  }}
                >
                  SafeJourney
                </span>
                <span
                  style={{
                    fontSize: '10px',
                    fontWeight: 500,
                    color: '#57534e',
                    letterSpacing: '0.05em',
                    textTransform: 'uppercase',
                    lineHeight: 1.2,
                  }}
                >
                  AI Platform
                </span>
              </div>
            </div>
          </MagneticText>

          <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
            {['Research', 'Architecture', 'Team'].map((item) => (
              <MagneticText key={item} intensity={0.15}>
                <a
                  href={`#${item.toLowerCase()}`}
                  style={{
                    fontSize: '13px',
                    fontWeight: 500,
                    color: '#78716c',
                    textDecoration: 'none',
                    letterSpacing: '0.02em',
                    position: 'relative',
                    paddingBottom: '2px',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = '#14B8A6';
                    e.currentTarget.querySelector('.underline').style.transform = 'scaleX(1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = '#78716c';
                    e.currentTarget.querySelector('.underline').style.transform = 'scaleX(0)';
                  }}
                >
                  {item}
                  <span
                    className="underline"
                    style={{
                      position: 'absolute',
                      bottom: 0,
                      left: 0,
                      right: 0,
                      height: '1px',
                      backgroundColor: '#14B8A6',
                      transform: 'scaleX(0)',
                      transformOrigin: 'left',
                      transition: 'transform 0.3s ease',
                    }}
                  />
                </a>
              </MagneticText>
            ))}
            <div
              style={{
                width: '1px',
                height: '16px',
                backgroundColor: 'rgba(255,255,255,0.08)',
              }}
            />
            <span
              style={{
                fontSize: '11px',
                color: '#44403c',
                fontFamily: 'ui-monospace, monospace',
                fontWeight: 500,
                letterSpacing: '0.05em',
              }}
            >
              R26-IT-152
            </span>
          </div>
        </div>
      </nav>

      {/* ── HERO ── */}
      <div
        ref={heroRef}
        style={{
          position: 'relative',
          height: '100vh',
          minHeight: '700px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            zIndex: 0,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              position: 'absolute',
              inset: '-40px',
              transform: `scale(1.1) translate(${mousePosition.x * -0.3}px, ${mousePosition.y * -0.3}px)`,
              transition: 'transform 0.3s ease-out',
            }}
          >
            <VideoHero videoSrc={ASSETS.heroVideo} fallback={GRADIENTS.hero} />
          </div>
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background:
                'linear-gradient(to bottom, rgba(10,10,10,0.5) 0%, rgba(10,10,10,0.2) 40%, rgba(10,10,10,0.7) 80%, rgba(10,10,10,1) 100%)',
              zIndex: 2,
            }}
          />
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'radial-gradient(ellipse at center, transparent 30%, rgba(10,10,10,0.6) 100%)',
              zIndex: 2,
            }}
          />
        </div>

        <div
          style={{
            position: 'relative',
            zIndex: 3,
            maxWidth: '900px',
            padding: '0 24px',
            transform: `translateY(${scrollY * 0.15}px)`,
            opacity: Math.max(0, 1 - scrollY / 800),
          }}
        >
          <AnimatedSection>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '12px',
                marginBottom: '48px',
                padding: '10px 20px',
                border: '1px solid rgba(20, 184, 166, 0.2)',
                backgroundColor: 'rgba(20, 184, 166, 0.05)',
              }}
            >
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  backgroundColor: '#14B8A6',
                  animation: 'pulse 2s ease-in-out infinite',
                }}
              />
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  letterSpacing: '0.15em',
                  textTransform: 'uppercase',
                  color: '#14B8A6',
                }}
              >
                SLIIT Research Project — May 2026
              </span>
            </div>
          </AnimatedSection>

          <AnimatedSection delay={0.1}>
            <h1
              style={{
                fontSize: 'clamp(42px, 8vw, 84px)',
                fontWeight: 700,
                lineHeight: 1.0,
                letterSpacing: '-0.04em',
                marginBottom: '24px',
                color: '#ffffff',
              }}
            >
              <MagneticText intensity={0.1}>
                <span style={{ display: 'block' }}>Intelligent Safety</span>
              </MagneticText>
              <MagneticText intensity={0.15}>
                <span
                  style={{
                    display: 'block',
                    background: 'linear-gradient(135deg, #14B8A6 0%, #2DD4BF 50%, #5EEAD4 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundSize: '200% auto',
                  }}
                >
                  for Sri Lanka
                </span>
              </MagneticText>
            </h1>
          </AnimatedSection>

          <AnimatedSection delay={0.2}>
            <p
              style={{
                fontSize: 'clamp(16px, 2vw, 20px)',
                lineHeight: 1.7,
                color: 'rgba(255,255,255,0.55)',
                maxWidth: '560px',
                margin: '0 auto 40px',
                fontWeight: 400,
              }}
            >
              Four integrated AI systems protecting 2.36 million annual visitors across 50
              destinations — from predictive risk analytics to emergency response.
            </p>
          </AnimatedSection>

          <AnimatedSection delay={0.3}>
            <div
              style={{
                display: 'flex',
                gap: '16px',
                justifyContent: 'center',
                flexWrap: 'wrap',
              }}
            >
              <MagneticText intensity={0.25}>
                <button
                  onClick={() => onNavigate('risk')}
                  style={{
                    padding: '14px 32px',
                    backgroundColor: '#14B8A6',
                    color: '#0a0a0a',
                    border: 'none',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    letterSpacing: '0.01em',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#2DD4BF';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#14B8A6';
                    e.currentTarget.style.transform = 'translateY(0)';
                  }}
                >
                  Explore Live System
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M3 8h10M9 4l4 4-4 4"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
              </MagneticText>

              <MagneticText intensity={0.25}>
                <button
                  onClick={() => onNavigate('hotel')}
                  style={{
                    padding: '14px 32px',
                    backgroundColor: 'transparent',
                    color: '#d6d3d1',
                    border: '1px solid rgba(255,255,255,0.15)',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    letterSpacing: '0.01em',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(255,255,255,0.3)';
                    e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)';
                    e.currentTarget.style.color = '#ffffff';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)';
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = '#d6d3d1';
                  }}
                >
                  Book Hotels & Flights
                </button>
              </MagneticText>
            </div>
          </AnimatedSection>

          <div
            style={{
              position: 'absolute',
              bottom: '40px',
              left: '50%',
              transform: 'translateX(-50%)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px',
              opacity: Math.max(0, 1 - scrollY / 400),
            }}
          >
            <span
              style={{
                fontSize: '10px',
                color: 'rgba(255,255,255,0.3)',
                letterSpacing: '0.15em',
                textTransform: 'uppercase',
              }}
            >
              Scroll
            </span>
            <div
              style={{
                width: '1px',
                height: '40px',
                background: 'linear-gradient(to bottom, rgba(20, 184, 166, 0.5), transparent)',
                animation: 'scrollPulse 2s ease-in-out infinite',
              }}
            />
          </div>
        </div>
      </div>

      {/* ── STATS BAND ── */}
      <div
        id="research"
        style={{
          borderTop: '1px solid rgba(255,255,255,0.06)',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          backgroundColor: 'rgba(255,255,255,0.01)',
        }}
      >
        <div
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          }}
        >
          {PLATFORM_STATS.map((s, i) => (
            <AnimatedSection key={s.label} delay={i * 0.1}>
              <div
                style={{
                  padding: '48px 32px',
                  textAlign: 'center',
                  borderRight: i < 3 ? '1px solid rgba(255,255,255,0.06)' : 'none',
                }}
              >
                <MagneticText intensity={0.2}>
                  <div
                    style={{
                      fontSize: 'clamp(28px, 4vw, 40px)',
                      fontWeight: 700,
                      color: '#ffffff',
                      lineHeight: 1,
                      marginBottom: '8px',
                      letterSpacing: '-0.03em',
                      fontVariantNumeric: 'tabular-nums',
                    }}
                  >
                    {s.val}
                  </div>
                </MagneticText>
                <div
                  style={{
                    fontSize: '13px',
                    color: '#a8a29e',
                    fontWeight: 500,
                    marginBottom: '4px',
                  }}
                >
                  {s.label}
                </div>
                <div style={{ fontSize: '11px', color: '#44403c' }}>{s.sub}</div>
              </div>
            </AnimatedSection>
          ))}
        </div>
      </div>

      {/* ── DESTINATIONS ── */}
      <div style={{ position: 'relative', padding: '120px 0', overflow: 'hidden' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 32px' }}>
          <AnimatedSection>
            <div style={{ marginBottom: '72px' }}>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  letterSpacing: '0.2em',
                  textTransform: 'uppercase',
                  color: '#14B8A6',
                  display: 'block',
                  marginBottom: '16px',
                }}
              >
                Protected Destinations
              </span>
              <h2
                style={{
                  fontSize: 'clamp(32px, 5vw, 56px)',
                  fontWeight: 700,
                  color: '#fafaf9',
                  letterSpacing: '-0.03em',
                  lineHeight: 1.1,
                  maxWidth: '600px',
                }}
              >
                <MagneticText intensity={0.08}>
                  <GlitchText text="Where Intelligence" />
                </MagneticText>
                <br />
                <span style={{ color: '#57534e' }}>Meets Island Beauty</span>
              </h2>
            </div>
          </AnimatedSection>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '16px',
            }}
          >
            {DESTINATIONS.map((dest, i) => (
              <AnimatedSection key={dest.name} delay={i * 0.12} direction="scale">
                <div
                  style={{
                    position: 'relative',
                    height: '480px',
                    overflow: 'hidden',
                    cursor: 'pointer',
                    transform: `translateY(${dest.offset}px)`,
                    border: '1px solid rgba(255,255,255,0.06)',
                  }}
                  onMouseEnter={(e) => {
                    const img = e.currentTarget.querySelector('.dest-img');
                    const overlay = e.currentTarget.querySelector('.dest-overlay');
                    const content = e.currentTarget.querySelector('.dest-content');
                    if (img) img.style.transform = 'scale(1.05)';
                    if (overlay) overlay.style.opacity = '0.8';
                    if (content) content.style.transform = 'translateY(-8px)';
                  }}
                  onMouseLeave={(e) => {
                    const img = e.currentTarget.querySelector('.dest-img');
                    const overlay = e.currentTarget.querySelector('.dest-overlay');
                    const content = e.currentTarget.querySelector('.dest-content');
                    if (img) img.style.transform = 'scale(1)';
                    if (overlay) overlay.style.opacity = '0.5';
                    if (content) content.style.transform = 'translateY(0)';
                  }}
                >
                  <SafeImage
                    src={dest.image}
                    fallback={dest.fallback}
                    alt={dest.name}
                    className="dest-img"
                    style={{
                      position: 'absolute',
                      inset: 0,
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      transition: 'transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
                    }}
                  />
                  <div
                    className="dest-overlay"
                    style={{
                      position: 'absolute',
                      inset: 0,
                      background:
                        'linear-gradient(to top, rgba(10,10,10,0.95) 0%, rgba(10,10,10,0.4) 50%, transparent 100%)',
                      opacity: 0.5,
                      transition: 'opacity 0.4s ease',
                    }}
                  />
                  <div
                    className="dest-content"
                    style={{
                      position: 'absolute',
                      bottom: 0,
                      left: 0,
                      right: 0,
                      padding: '32px',
                      transition: 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 600,
                        color: '#14B8A6',
                        letterSpacing: '0.1em',
                        textTransform: 'uppercase',
                        display: 'block',
                        marginBottom: '8px',
                      }}
                    >
                      {dest.region}
                    </span>
                    <h3
                      style={{
                        fontSize: '28px',
                        fontWeight: 600,
                        color: '#ffffff',
                        letterSpacing: '-0.02em',
                      }}
                    >
                      {dest.name}
                    </h3>
                  </div>
                </div>
              </AnimatedSection>
            ))}
          </div>
        </div>
      </div>

      {/* ── COMPONENTS ── */}
      <div id="architecture" style={{ maxWidth: '1280px', margin: '0 auto', padding: '80px 32px 120px' }}>
        <AnimatedSection>
          <div style={{ marginBottom: '80px' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 600,
                letterSpacing: '0.2em',
                textTransform: 'uppercase',
                color: '#14B8A6',
                display: 'block',
                marginBottom: '16px',
              }}
            >
              Platform Architecture
            </span>
            <h2
              style={{
                fontSize: 'clamp(32px, 5vw, 48px)',
                fontWeight: 700,
                color: '#fafaf9',
                letterSpacing: '-0.03em',
                marginBottom: '16px',
                lineHeight: 1.1,
              }}
            >
              <MagneticText intensity={0.08}>
                <GlitchText text="Four Integrated" />
              </MagneticText>
              <br />
              <span style={{ color: '#57534e' }}>Systems</span>
            </h2>
            <p
              style={{
                fontSize: '17px',
                color: '#78716c',
                lineHeight: 1.6,
                maxWidth: '480px',
              }}
            >
              Each module operates independently with fault isolation. One component failure never
              compromises the platform.
            </p>
          </div>
        </AnimatedSection>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
            gap: '16px',
          }}
        >
          {MEMBERS.map((m, i) => (
            <AnimatedSection key={m.id} delay={i * 0.1} direction="up">
              <div
                onClick={() => onNavigate(m.nav)}
                style={{
                  position: 'relative',
                  backgroundColor: 'rgba(255,255,255,0.01)',
                  border: '1px solid rgba(255,255,255,0.06)',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  transition: 'all 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
                  display: 'flex',
                  flexDirection: 'column',
                  height: '100%',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = `${m.accent}40`;
                  e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.02)';
                  e.currentTarget.style.transform = 'translateY(-6px)';
                  const img = e.currentTarget.querySelector('.card-img');
                  if (img) img.style.transform = 'scale(1.08)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)';
                  e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.01)';
                  e.currentTarget.style.transform = 'translateY(0)';
                  const img = e.currentTarget.querySelector('.card-img');
                  if (img) img.style.transform = 'scale(1)';
                }}
              >
                <div
                  style={{
                    height: '220px',
                    position: 'relative',
                    overflow: 'hidden',
                    borderBottom: `1px solid ${m.accent}20`,
                  }}
                >
                  <SafeImage
                    src={m.image}
                    fallback={m.fallback}
                    alt={m.title}
                    className="card-img"
                    style={{
                      position: 'absolute',
                      inset: 0,
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      filter: 'saturate(0.7) brightness(0.6)',
                      transition: 'transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      background: `linear-gradient(to bottom, transparent 0%, ${m.accent}15 100%)`,
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      top: '20px',
                      right: '20px',
                      textAlign: 'right',
                    }}
                  >
                    <MagneticText intensity={0.3}>
                      <div
                        style={{
                          fontSize: '36px',
                          fontWeight: 700,
                          color: '#ffffff',
                          lineHeight: 1,
                          textShadow: '0 2px 20px rgba(0,0,0,0.5)',
                          fontVariantNumeric: 'tabular-nums',
                        }}
                      >
                        {m.metric.val}
                      </div>
                    </MagneticText>
                    <div
                      style={{
                        fontSize: '11px',
                        color: 'rgba(255,255,255,0.6)',
                        fontWeight: 500,
                        marginTop: '4px',
                        letterSpacing: '0.05em',
                      }}
                    >
                      {m.metric.label}
                    </div>
                  </div>
                </div>

                <div style={{ padding: '28px', flex: 1, display: 'flex', flexDirection: 'column' }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      marginBottom: '12px',
                    }}
                  >
                    <span
                      style={{
                        fontSize: '10px',
                        fontWeight: 700,
                        letterSpacing: '0.1em',
                        textTransform: 'uppercase',
                        color: m.accent,
                        padding: '4px 8px',
                        border: `1px solid ${m.accent}30`,
                        backgroundColor: `${m.accent}10`,
                      }}
                    >
                      {m.id}
                    </span>
                    <span style={{ color: 'rgba(255,255,255,0.15)' }}>/</span>
                    <span style={{ fontSize: '12px', fontWeight: 500, color: '#57534e' }}>
                      {m.name}
                    </span>
                  </div>

                  <h3
                    style={{
                      fontSize: '20px',
                      fontWeight: 600,
                      color: '#fafaf9',
                      lineHeight: 1.3,
                      marginBottom: '12px',
                      letterSpacing: '-0.01em',
                    }}
                  >
                    <MagneticText intensity={0.1}>{m.title}</MagneticText>
                  </h3>

                  <p
                    style={{
                      color: '#78716c',
                      fontSize: '14px',
                      lineHeight: 1.7,
                      marginBottom: '20px',
                      flex: 1,
                    }}
                  >
                    {m.desc}
                  </p>

                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '6px',
                      marginBottom: '24px',
                    }}
                  >
                    {m.tech.map((t) => (
                      <span
                        key={t}
                        style={{
                          padding: '4px 10px',
                          fontSize: '11px',
                          color: '#78716c',
                          fontWeight: 500,
                          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                          border: '1px solid rgba(255,255,255,0.06)',
                          backgroundColor: 'rgba(255,255,255,0.02)',
                          letterSpacing: '0.02em',
                        }}
                      >
                        {t}
                      </span>
                    ))}
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      paddingTop: '20px',
                      borderTop: '1px solid rgba(255,255,255,0.06)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: m.status === 'live' ? '#34D399' : '#FBBF24',
                          boxShadow:
                            m.status === 'live'
                              ? '0 0 10px rgba(52, 211, 153, 0.4)'
                              : '0 0 10px rgba(251, 191, 36, 0.3)',
                        }}
                      />
                      <span
                        style={{
                          fontSize: '11px',
                          fontWeight: 600,
                          color: m.status === 'live' ? '#34D399' : '#FBBF24',
                          textTransform: 'uppercase',
                          letterSpacing: '0.08em',
                        }}
                      >
                        {m.status === 'live' ? 'Live System' : 'In Development'}
                      </span>
                    </div>
                    <MagneticText intensity={0.2}>
                      <span
                        style={{
                          fontSize: '13px',
                          color: m.accent,
                          fontWeight: 600,
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        Explore
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                          <path
                            d="M3 8h10M9 4l4 4-4 4"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </span>
                    </MagneticText>
                  </div>
                </div>
              </div>
            </AnimatedSection>
          ))}
        </div>
      </div>



      {/* ── FOOTER ── */}
      <footer
        style={{
          borderTop: '1px solid rgba(255,255,255,0.06)',
          backgroundColor: '#050505',
        }}
      >
        <div
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            padding: '48px 32px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '24px',
          }}
        >
          <div>
            <div
              style={{
                fontSize: '14px',
                fontWeight: 600,
                color: '#fafaf9',
                marginBottom: '6px',
                letterSpacing: '-0.01em',
              }}
            >
              SafeJourney AI
            </div>
            <div
              style={{
                fontSize: '12px',
                color: '#44403c',
                lineHeight: 1.6,
                letterSpacing: '0.02em',
              }}
            >
              AI-Based Tourism Safety & Itinerary Platform · R26-IT-152
              <br />
              SLIIT Sri Lanka · 2026
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            <span
              style={{
                fontSize: '11px',
                color: '#333',
                fontFamily: 'ui-monospace, monospace',
                fontWeight: 500,
                letterSpacing: '0.05em',
              }}
            >

            </span>
          </div>
        </div>
      </footer>

      <style>{`
        @keyframes scrollPulse {
          0%, 100% { transform: translateY(0); opacity: 1; }
          50% { transform: translateY(8px); opacity: 0.3; }
        }
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes glitchTop {
          0%, 100% { transform: translate(0); }
          20% { transform: translate(-2px, -1px); }
          40% { transform: translate(2px, 1px); }
          60% { transform: translate(-1px, 1px); }
          80% { transform: translate(1px, -1px); }
        }
        @keyframes glitchBottom {
          0%, 100% { transform: translate(0); }
          20% { transform: translate(2px, 1px); }
          40% { transform: translate(-2px, -1px); }
          60% { transform: translate(1px, -1px); }
          80% { transform: translate(-1px, 1px); }
        }
        @media (max-width: 768px) {
          .divider { display: none !important; }
        }
      `}</style>
    </div>
  );
}
