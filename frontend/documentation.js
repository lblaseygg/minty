class MintyDocumentation {
    constructor() {
        this.init();
    }

    init() {
        this.setupMobileNavigation();
        this.setupScrollAnimations();
        this.setupSmoothScroll();
        this.setupSidebarNavigation();
        this.setupCopyButtons();
        this.setupCodeBlockHighlight();
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

            document.querySelectorAll('.nav-link').forEach(link => {
                link.addEventListener('click', () => {
                    hamburger.classList.remove('active');
                    navMenu.classList.remove('active');
                });
            });

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

        document.querySelectorAll('.toc-card, .doc-section, .step, .feature-item, .portfolio-card, .endpoint, .example-card, .deployment-card').forEach((element, index) => {
            element.classList.add('animate-on-scroll');
            element.style.transitionDelay = `${index * 0.05}s`;
            observer.observe(element);
        });
    }

    // Smooth Scroll
    setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));

                if (target) {
                    const offsetTop = target.offsetTop - 80;
                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }

    // Sidebar Navigation Highlighting
    setupSidebarNavigation() {
        const sections = document.querySelectorAll('.doc-section');
        const navLinks = document.querySelectorAll('.sidebar-nav a');

        const observerOptions = {
            threshold: 0.3,
            rootMargin: '0px 0px -60% 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    navLinks.forEach(link => {
                        link.classList.remove('active');
                        if (link.getAttribute('href') === `#${entry.target.id}`) {
                            link.classList.add('active');
                            // Scroll sidebar to keep active link in view
                            link.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
                        }
                    });
                }
            });
        }, observerOptions);

        sections.forEach(section => observer.observe(section));
    }

    // Copy to Clipboard
    setupCopyButtons() {
        window.copyCode = (id) => {
            const codeElement = document.getElementById(id);
            const text = codeElement.textContent;
            navigator.clipboard.writeText(text).then(() => {
                const button = codeElement.parentElement.querySelector('.copy-btn');
                button.classList.add('copied');
                button.innerHTML = '<i class="fas fa-check"></i> Copied';
                setTimeout(() => {
                    button.classList.remove('copied');
                    button.innerHTML = '<i class="fas fa-copy"></i> Copy';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy: ', err);
            });
        };
    }

    // Code Block Highlight Animation
    setupCodeBlockHighlight() {
        document.querySelectorAll('.code-block').forEach(block => {
            block.addEventListener('click', () => {
                block.style.animation = 'highlightCode 0.3s ease';
                setTimeout(() => {
                    block.style.animation = 'none';
                }, 300);
            });
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MintyDocumentation();
});

// Inject styles for dynamic effects
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    .copy-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 13px;
        font-family: 'SF Pro Text', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .copy-btn.copied {
        color: var(--success-color);
    }

    .copy-btn.copied i::before {
        content: "\\f00c"; /* Checkmark icon */
    }
`;
document.head.appendChild(styleSheet);