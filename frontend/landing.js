class MintyLanding {
  constructor() {
    this.init();
  }

  init() {
    this.setupMobileNavigation();
    this.setupScrollAnimations();
    this.setupSmoothScroll();
    this.setupParallax();
    this.setupInteractiveElements();
    this.setupTypingEffect();
  }

  // Mobile Navigation
  setupMobileNavigation() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');

    if (hamburger && navMenu) {
      hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
      });

      // Close menu when clicking nav links
      document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
          hamburger.classList.remove('active');
          navMenu.classList.remove('active');
        });
      });

      // Close menu when clicking outside
      document.addEventListener('click', (e) => {
        if (!hamburger.contains(e.target) && !navMenu.contains(e.target)) {
          hamburger.classList.remove('active');
          navMenu.classList.remove('active');
        }
      });
    }
  }

  // Scroll Animations
  setupScrollAnimations() {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate');
        }
      });
    }, observerOptions);

    // Add animation class to feature cards
    document.querySelectorAll('.feature-card').forEach((card, index) => {
      card.classList.add('animate-on-scroll');
      card.style.animationDelay = `${index * 0.2}s`;
      observer.observe(card);
    });

    // Add animation to other elements
    document.querySelectorAll('.team-member, .project-link, .about-story').forEach(element => {
      element.classList.add('animate-on-scroll');
      observer.observe(element);
    });
  }

  // Smooth Scroll
  setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        
        if (target) {
          const offsetTop = target.offsetTop - 80; // Account for fixed nav
          
          window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
          });
        }
      });
    });
  }

  // Parallax Effects
  setupParallax() {
    let ticking = false;

    const updateParallax = () => {
      const scrolled = window.pageYOffset;
      const rate = scrolled * -0.5;

      // Parallax for hero background
      const hero = document.querySelector('.hero');
      if (hero) {
        hero.style.transform = `translateY(${rate}px)`;
      }

      // Parallax for dashboard preview
      const dashboard = document.querySelector('.dashboard-preview');
      if (dashboard) {
        const parallaxRate = scrolled * -0.3;
        dashboard.style.transform = `perspective(1000px) rotateY(-5deg) translateY(${parallaxRate}px)`;
      }

      ticking = false;
    };

    const requestParallaxUpdate = () => {
      if (!ticking) {
        requestAnimationFrame(updateParallax);
        ticking = true;
      }
    };

    window.addEventListener('scroll', requestParallaxUpdate);
  }

  // Interactive Elements
  setupInteractiveElements() {
    // Navbar background on scroll
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', () => {
      if (window.scrollY > 100) {
        navbar.style.background = 'rgba(251, 251, 253, 0.95)';
        navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
      } else {
        navbar.style.background = 'rgba(251, 251, 253, 0.8)';
        navbar.style.boxShadow = 'none';
      }
    });

    // Button hover effects with ripple
    document.querySelectorAll('.btn').forEach(button => {
      button.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');

        this.appendChild(ripple);

        setTimeout(() => {
          ripple.remove();
        }, 600);
      });
    });

    // Feature card interactions
    document.querySelectorAll('.feature-card').forEach(card => {
      card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-8px) scale(1.02)';
      });

      card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0) scale(1)';
      });
    });

    // Dashboard preview interaction
    const dashboard = document.querySelector('.dashboard-preview');
    if (dashboard) {
      dashboard.addEventListener('mouseenter', function() {
        this.style.transform = 'perspective(1000px) rotateY(0deg) scale(1.05)';
      });

      dashboard.addEventListener('mouseleave', function() {
        this.style.transform = 'perspective(1000px) rotateY(-5deg) scale(1)';
      });
    }
  }

  // Typing Effect for Hero Title
  setupTypingEffect() {
    const heroTitle = document.querySelector('.hero-title .gradient-text');
    if (!heroTitle) return;

    const text = 'Minty';
    heroTitle.innerHTML = '';
    
    let index = 0;
    const typeEffect = () => {
      if (index < text.length) {
        heroTitle.innerHTML += text.charAt(index);
        index++;
        setTimeout(typeEffect, 200);
      } else {
        // Add cursor blink effect briefly
        heroTitle.innerHTML += '<span class="cursor">|</span>';
        setTimeout(() => {
          const cursor = heroTitle.querySelector('.cursor');
          if (cursor) cursor.remove();
        }, 1000);
      }
    };

    // Start typing effect after page load
    setTimeout(typeEffect, 1000);
  }

  // Dynamic Stats Counter
  setupStatsCounter() {
    const stats = document.querySelectorAll('.stat-value');
    
    const countUp = (element, target) => {
      const increment = target / 100;
      let current = 0;
      
      const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
          element.textContent = target;
          clearInterval(timer);
        } else {
          element.textContent = Math.floor(current);
        }
      }, 20);
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const text = entry.target.textContent;
          const number = parseFloat(text.replace(/[^\d.-]/g, ''));
          if (number) {
            countUp(entry.target, number);
          }
          observer.unobserve(entry.target);
        }
      });
    });

    stats.forEach(stat => observer.observe(stat));
  }

  // Progressive Enhancement
  setupProgressiveEnhancement() {
    // Add CSS classes for JavaScript-enhanced features
    document.documentElement.classList.add('js-enabled');

    // Preload images for better performance
    const images = [
      'assets/minty-logo-primary.svg',
      'assets/minty-logo-icon.svg'
    ];

    images.forEach(src => {
      const img = new Image();
      img.src = src;
    });

    // Service Worker for offline capability (optional)
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
          .then(() => console.log('SW registered'))
          .catch(() => console.log('SW registration failed'));
      });
    }
  }

  // Chart Animation
  animateChart() {
    const chartLine = document.querySelector('.chart-line');
    if (chartLine) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.style.animation = 'drawLine 2s ease-out forwards';
            observer.unobserve(entry.target);
          }
        });
      });

      observer.observe(chartLine);
    }
  }

  // Mouse cursor effect
  setupCursorEffect() {
    const cursor = document.createElement('div');
    cursor.classList.add('cursor-dot');
    cursor.style.cssText = `
      position: fixed;
      width: 8px;
      height: 8px;
      background: #007AFF;
      border-radius: 50%;
      pointer-events: none;
      z-index: 9999;
      transition: transform 0.1s ease;
      transform: translate(-50%, -50%);
    `;
    
    document.body.appendChild(cursor);

    document.addEventListener('mousemove', (e) => {
      cursor.style.left = e.clientX + 'px';
      cursor.style.top = e.clientY + 'px';
    });

    // Hide cursor on mobile
    if (window.innerWidth <= 768) {
      cursor.style.display = 'none';
    }
  }
}

// Add ripple effect styles
const rippleStyles = `
  .btn {
    position: relative;
    overflow: hidden;
  }
  
  .ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.6);
    transform: scale(0);
    animation: ripple-animation 0.6s linear;
    pointer-events: none;
  }
  
  @keyframes ripple-animation {
    to {
      transform: scale(4);
      opacity: 0;
    }
  }
  
  .cursor {
    animation: blink 1s infinite;
  }
  
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
  
  .js-enabled .hero-content {
    animation-delay: 0.5s;
  }
  
  .js-enabled .hero-image {
    animation-delay: 0.8s;
  }
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = rippleStyles;
document.head.appendChild(styleSheet);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new MintyLanding();
});

// Performance optimization
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    // Recalculate positions after resize
    location.reload();
  }, 250);
});

// Lazy loading for images
if ('IntersectionObserver' in window) {
  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.classList.remove('lazy');
        imageObserver.unobserve(img);
      }
    });
  });

  document.querySelectorAll('img[data-src]').forEach(img => {
    imageObserver.observe(img);
  });
}