// Ficheiro: app/static/js/eventos_carrossel.js

document.addEventListener('DOMContentLoaded', function() {

    // ==================== CARROSSEL DE EVENTOS ====================
    const carousel = document.querySelector('.events-carousel');
    const prevBtn = document.querySelector('.carousel-prev');
    const nextBtn = document.querySelector('.carousel-next');
    const cards = document.querySelectorAll('.event-card');

    if (carousel && prevBtn && nextBtn) {
        let currentIndex = 0;
        const cardWidth = 260 + 16; // largura do card + gap
        const visibleCards = Math.floor(carousel.offsetWidth / cardWidth);
        const maxIndex = Math.max(0, cards.length - visibleCards);

        // Função para atualizar posição do carrossel
        function updateCarousel() {
            const translateX = currentIndex * cardWidth;
            carousel.style.transform = `translateX(-${translateX}px)`;

            // Atualizar estado dos botões
            prevBtn.style.opacity = currentIndex === 0 ? '0.5' : '1';
            nextBtn.style.opacity = currentIndex >= maxIndex ? '0.5' : '1';
            prevBtn.style.pointerEvents = currentIndex === 0 ? 'none' : 'auto';
            nextBtn.style.pointerEvents = currentIndex >= maxIndex ? 'none' : 'auto';
        }

        // Event listeners para os botões
        prevBtn.addEventListener('click', () => {
            if (currentIndex > 0) {
                currentIndex--;
                updateCarousel();
            }
        });

        nextBtn.addEventListener('click', () => {
            if (currentIndex < maxIndex) {
                currentIndex++;
                updateCarousel();
            }
        });

        // Navegação por teclado
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' && currentIndex > 0) {
                currentIndex--;
                updateCarousel();
            } else if (e.key === 'ArrowRight' && currentIndex < maxIndex) {
                currentIndex++;
                updateCarousel();
            }
        });

        // Atualizar ao redimensionar
        window.addEventListener('resize', () => {
            const newVisibleCards = Math.floor(carousel.offsetWidth / cardWidth);
            const newMaxIndex = Math.max(0, cards.length - newVisibleCards);

            if (currentIndex > newMaxIndex) {
                currentIndex = newMaxIndex;
            }
            updateCarousel();
        });

        // Inicializar
        updateCarousel();

        // Auto-scroll opcional (descomente para ativar)
        /*
        setInterval(() => {
            if (currentIndex < maxIndex) {
                currentIndex++;
            } else {
                currentIndex = 0;
            }
            updateCarousel();
        }, 5000); // 5 segundos
        */
    }

    // ==================== TOGGLE ENTRE VISUALIZAÇÕES ====================
    const toggleBtns = document.querySelectorAll('.toggle-btn');
    const compactView = document.querySelector('.events-carousel-container');
    const fullView = document.querySelector('.events-grid-full');

    toggleBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const viewType = btn.dataset.view;

            // Atualizar botões ativos
            toggleBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Mostrar/esconder visualizações
            if (viewType === 'compact') {
                compactView?.classList.remove('hidden');
                fullView?.classList.add('hidden');
            } else {
                compactView?.classList.add('hidden');
                fullView?.classList.remove('hidden');
            }

            // Salvar preferência
            localStorage.setItem('eventViewType', viewType);
        });
    });

    // Restaurar preferência salva
    const savedView = localStorage.getItem('eventViewType') || 'compact';
    const savedBtn = document.querySelector(`[data-view="${savedView}"]`);
    if (savedBtn) {
        savedBtn.click();
    }

    // ==================== LAZY LOADING DE IMAGENS ====================
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.classList.remove('loading-skeleton');
                    observer.unobserve(img);
                }
            }
        });
    });

    document.querySelectorAll('img[data-src]').forEach(img => {
        img.classList.add('loading-skeleton');
        imageObserver.observe(img);
    });

    // ==================== ANIMAÇÕES DE ENTRADA ====================
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.event-card, .about-section, .hero-section').forEach(el => {
        animationObserver.observe(el);
    });

    // ==================== TOUCH/SWIPE PARA MOBILE ====================
    let touchStartX = 0;
    let touchEndX = 0;

    if (carousel) {
        carousel.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });

        carousel.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        });

        function handleSwipe() {
            const swipeThreshold = 50;
            const diff = touchStartX - touchEndX;

            if (Math.abs(diff) > swipeThreshold) {
                if (diff > 0 && currentIndex < maxIndex) {
                    // Swipe left - próximo
                    currentIndex++;
                    updateCarousel();
                } else if (diff < 0 && currentIndex > 0) {
                    // Swipe right - anterior
                    currentIndex--;
                    updateCarousel();
                }
            }
        }
    }

    // ==================== FILTROS E BUSCA ====================
    const searchInput = document.querySelector('#event-search');
    const filterBtns = document.querySelectorAll('.filter-btn');

    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterEvents, 300));
    }

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = btn.dataset.filter;
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterEvents();
        });
    });

    function filterEvents() {
        const searchTerm = searchInput?.value.toLowerCase() || '';
        const activeFilter = document.querySelector('.filter-btn.active')?.dataset.filter || 'all';

        cards.forEach(card => {
            const title = card.querySelector('.event-title')?.textContent.toLowerCase() || '';
            const speaker = card.querySelector('.event-speaker')?.textContent.toLowerCase() || '';
            const category = card.dataset.category || '';

            const matchesSearch = title.includes(searchTerm) || speaker.includes(searchTerm);
            const matchesFilter = activeFilter === 'all' || category === activeFilter;

            if (matchesSearch && matchesFilter) {
                card.style.display = 'flex';
                card.classList.add('slide-in');
            } else {
                card.style.display = 'none';
                card.classList.remove('slide-in');
            }
        });

        // Atualizar carrossel após filtro
        updateCarousel();
    }

    // ==================== LOADING STATES ====================
    function showLoading() {
        const container = document.querySelector('.events-grid') || document.querySelector('.events-carousel');
        if (container) {
            container.innerHTML = Array(6).fill().map(() =>
                '<div class="card-skeleton loading-skeleton"></div>'
            ).join('');
        }
    }

    function hideLoading() {
        const skeletons = document.querySelectorAll('.card-skeleton');
        skeletons.forEach(skeleton => skeleton.remove());
    }

    // ==================== UTILITÁRIOS ====================
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // ==================== ANALYTICS / TRACKING ====================
    function trackEvent(action, category, label) {
        if (typeof gtag !== 'undefined') {
            gtag('event', action, {
                event_category: category,
                event_label: label
            });
        }
    }

    // Tracking de cliques nos cards
    cards.forEach((card, index) => {
        card.addEventListener('click', () => {
            const eventTitle = card.querySelector('.event-title')?.textContent || `Evento ${index + 1}`;
            trackEvent('click', 'event_card', eventTitle);
        });
    });

    // Tracking de navegação do carrossel
    prevBtn?.addEventListener('click', () => {
        trackEvent('click', 'carousel', 'previous');
    });

    nextBtn?.addEventListener('click', () => {
        trackEvent('click', 'carousel', 'next');
    });

    // ==================== PERFORMANCE MONITORING ====================
    const performanceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            if (entry.entryType === 'measure') {
                console.log(`${entry.name}: ${entry.duration}ms`);
            }
        }
    });

    performanceObserver.observe({ entryTypes: ['measure'] });

    // Medir tempo de carregamento dos cards
    performance.mark('cards-start');

    // Quando todos os cards estiverem carregados
    Promise.all(Array.from(document.images).map(img => {
        if (img.complete) return Promise.resolve();
        return new Promise(resolve => {
            img.onload = resolve;
            img.onerror = resolve;
        });
    })).then(() => {
        performance.mark('cards-end');
        performance.measure('cards-load-time', 'cards-start', 'cards-end');
    });

    // ==================== ACESSIBILIDADE ====================
    // Anunciar mudanças do carrossel para leitores de tela
    const announcer = document.createElement('div');
    announcer.setAttribute('aria-live', 'polite');
    announcer.setAttribute('aria-atomic', 'true');
    announcer.className = 'sr-only';
    document.body.appendChild(announcer);

    function announce(message) {
        announcer.textContent = message;
        setTimeout(() => announcer.textContent = '', 1000);
    }

    // Anunciar navegação do carrossel
    if (prevBtn && nextBtn) {
        prevBtn.addEventListener('click', () => {
            announce(`Mostrando eventos ${currentIndex * visibleCards + 1} a ${Math.min((currentIndex + 1) * visibleCards, cards.length)} de ${cards.length}`);
        });

        nextBtn.addEventListener('click', () => {
            announce(`Mostrando eventos ${currentIndex * visibleCards + 1} a ${Math.min((currentIndex + 1) * visibleCards, cards.length)} de ${cards.length}`);
        });
    }

    console.log('🎉 Carrossel de eventos carregado com sucesso!');
});