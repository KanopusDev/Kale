/**
 * Index Page JavaScript for Kale Email API Platform
 * Production-ready landing page functionality
 */

'use strict';

// Initialize index page
document.addEventListener('DOMContentLoaded', function() {
    initializeIndexPage();
});

function initializeIndexPage() {
    initializeNavigation();
    initializeScrollEffects();
    initializeFeatureInteractions();
    initializeCTAButtons();
    initializeAuthModals();
    setupEventListeners();
}

function setupEventListeners() {
    // Event delegation for data-action attributes
    document.addEventListener('click', function(e) {
        const target = e.target.closest('[data-action]');
        if (!target) return;
        
        const action = target.dataset.action;
        e.preventDefault();
        
        switch (action) {
            case 'scroll-to-demo':
                scrollToDemo();
                break;
            case 'show-register':
                showRegister();
                break;
            case 'show-login':
                showLogin();
                break;
            case 'hide-auth':
                hideAuth();
                break;
        }
    });
    
    // Form submissions
    const indexLoginForm = document.getElementById('index-login-form');
    const indexRegisterForm = document.getElementById('index-register-form');
    
    if (indexLoginForm) {
        indexLoginForm.addEventListener('submit', handleLogin);
    }
    
    if (indexRegisterForm) {
        indexRegisterForm.addEventListener('submit', handleRegister);
    }
}

function initializeAuthModals() {
    // Initialize auth modal functionality
    const authOverlay = document.getElementById('auth-overlay');
    if (authOverlay) {
        // Close modal when clicking overlay
        authOverlay.addEventListener('click', function(e) {
            if (e.target === authOverlay) {
                hideAuth();
            }
        });
    }
    
    // Close modal on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideAuth();
        }
    });
}

function initializeNavigation() {
    // Mobile menu toggle
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            const isOpen = !mobileMenu.classList.contains('hidden');
            
            if (isOpen) {
                mobileMenu.classList.add('hidden');
                mobileMenuButton.setAttribute('aria-expanded', 'false');
            } else {
                mobileMenu.classList.remove('hidden');
                mobileMenuButton.setAttribute('aria-expanded', 'true');
            }
        });
    }
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function initializeScrollEffects() {
    // Header background on scroll
    const header = document.querySelector('header');
    if (header) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                header.classList.add('bg-white', 'shadow-lg');
                header.classList.remove('bg-transparent');
            } else {
                header.classList.remove('bg-white', 'shadow-lg');
                header.classList.add('bg-transparent');
            }
        });
    }
    
    // Intersection Observer for fade-in animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                entry.target.classList.remove('opacity-0');
            }
        });
    }, observerOptions);
    
    // Observe elements with fade-in class
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach(element => {
        element.classList.add('opacity-0');
        observer.observe(element);
    });
}

function initializeFeatureInteractions() {
    // Feature cards hover effects
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('transform', 'scale-105', 'shadow-xl');
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('transform', 'scale-105', 'shadow-xl');
        });
    });
    
    // Statistics counter animation
    const stats = document.querySelectorAll('[data-count]');
    const statsObserver = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                statsObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    stats.forEach(stat => {
        statsObserver.observe(stat);
    });
}

function initializeCTAButtons() {
    // CTA button interactions
    const ctaButtons = document.querySelectorAll('.cta-button');
    ctaButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Add ripple effect
            const ripple = document.createElement('span');
            ripple.className = 'ripple';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Get started button
    const getStartedButton = document.getElementById('get-started');
    if (getStartedButton) {
        getStartedButton.addEventListener('click', function() {
            // Check if user is logged in
            if (localStorage.getItem('auth_token')) {
                window.location.href = '/dashboard';
            } else {
                window.location.href = '/register';
            }
        });
    }
    
    // Try demo button
    const tryDemoButton = document.getElementById('try-demo');
    if (tryDemoButton) {
        tryDemoButton.addEventListener('click', function() {
            window.location.href = '/docs#getting-started';
        });
    }
}

function animateCounter(element) {
    const target = parseInt(element.dataset.count);
    const duration = 2000; // 2 seconds
    const step = target / (duration / 16); // 60fps
    let current = 0;
    
    const timer = setInterval(function() {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        
        element.textContent = Math.floor(current).toLocaleString();
    }, 16);
}

// Newsletter subscription
function handleNewsletterSubscription(event) {
    event.preventDefault();
    
    const form = event.target;
    const emailInput = form.querySelector('input[type="email"]');
    const submitButton = form.querySelector('button[type="submit"]');
    
    if (!emailInput || !emailInput.value.trim()) {
        KaleAPI.showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    if (!KaleAPI.validateEmail(emailInput.value.trim())) {
        KaleAPI.showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    // Show loading state
    KaleAPI.showLoading(submitButton);
    
    // Simulate API call (replace with actual endpoint when available)
    setTimeout(() => {
        KaleAPI.hideLoading(submitButton);
        KaleAPI.showNotification('Thank you for subscribing to our newsletter!', 'success');
        emailInput.value = '';
    }, 1000);
}

// Contact form
function handleContactForm(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Basic validation
    const name = formData.get('name');
    const email = formData.get('email');
    const message = formData.get('message');
    
    if (!name || !email || !message) {
        KaleAPI.showNotification('Please fill in all required fields', 'error');
        return;
    }

    // Simulate form submission
    KaleAPI.showNotification('Message sent successfully!', 'success');
    form.reset();
}

// Auth modal functions
function scrollToDemo() {
    const demoSection = document.getElementById('demo') || document.getElementById('features');
    if (demoSection) {
        demoSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

function showLogin() {
    const authOverlay = document.getElementById('auth-overlay');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (authOverlay && loginForm && registerForm) {
        loginForm.classList.remove('hidden');
        registerForm.classList.add('hidden');
        authOverlay.classList.remove('hidden');
        
        // Focus on email field
        const emailField = loginForm.querySelector('input[type="email"]');
        if (emailField) {
            setTimeout(() => emailField.focus(), 100);
        }
    }
}

function showRegister() {
    const authOverlay = document.getElementById('auth-overlay');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    if (authOverlay && loginForm && registerForm) {
        loginForm.classList.add('hidden');
        registerForm.classList.remove('hidden');
        authOverlay.classList.remove('hidden');
        
        // Focus on username field
        const usernameField = registerForm.querySelector('input[type="text"]');
        if (usernameField) {
            setTimeout(() => usernameField.focus(), 100);
        }
    }
}

function hideAuth() {
    const authOverlay = document.getElementById('auth-overlay');
    if (authOverlay) {
        authOverlay.classList.add('hidden');
    }
}

async function handleLogin(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = KaleAPI.getFormData(form);
    
    // Basic validation
    if (!formData.email || !formData.password) {
        KaleAPI.showNotification('Please fill in all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: formData.email,
                password: formData.password
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }
        
        // Store authentication data
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        KaleAPI.showNotification('Login successful! Redirecting...', 'success');
        
        setTimeout(() => {
            if (data.user.is_admin) {
                window.location.href = '/admin';
            } else {
                window.location.href = '/dashboard';
            }
        }, 1000);
        
    } catch (error) {
        KaleAPI.showNotification(error.message, 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = KaleAPI.getFormData(form);
    
    // Basic validation
    if (!formData.username || !formData.email || !formData.password) {
        KaleAPI.showNotification('Please fill in all fields', 'error');
        return;
    }
    
    if (formData.password !== formData.confirmPassword) {
        KaleAPI.showNotification('Passwords do not match', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/v1/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: formData.username,
                email: formData.email,
                password: formData.password
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Registration failed');
        }
        
        KaleAPI.showNotification('Registration successful! Please log in.', 'success');
        
        // Switch to login form
        setTimeout(() => {
            showLogin();
        }, 1000);
        
    } catch (error) {
        KaleAPI.showNotification(error.message, 'error');
    }
    
    if (!KaleAPI.validateEmail(email)) {
        KaleAPI.showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    // Show loading state
    KaleAPI.showLoading(submitButton);
    
    // Simulate API call (replace with actual endpoint when available)
    setTimeout(() => {
        KaleAPI.hideLoading(submitButton);
        KaleAPI.showNotification('Thank you for your message! We\'ll get back to you soon.', 'success');
        form.reset();
    }, 1000);
}

// FAQ interactions
function initializeFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');
        const icon = item.querySelector('.faq-icon');
        
        if (question && answer) {
            question.addEventListener('click', function() {
                const isOpen = !answer.classList.contains('hidden');
                
                // Close all other FAQ items
                faqItems.forEach(otherItem => {
                    if (otherItem !== item) {
                        const otherAnswer = otherItem.querySelector('.faq-answer');
                        const otherIcon = otherItem.querySelector('.faq-icon');
                        if (otherAnswer) otherAnswer.classList.add('hidden');
                        if (otherIcon) otherIcon.style.transform = 'rotate(0deg)';
                    }
                });
                
                // Toggle current item
                if (isOpen) {
                    answer.classList.add('hidden');
                    if (icon) icon.style.transform = 'rotate(0deg)';
                } else {
                    answer.classList.remove('hidden');
                    if (icon) icon.style.transform = 'rotate(180deg)';
                }
            });
        }
    });
}

// Initialize FAQ when DOM is ready
document.addEventListener('DOMContentLoaded', initializeFAQ);

// Expose functions for HTML onclick handlers
window.handleNewsletterSubscription = handleNewsletterSubscription;
window.handleContactForm = handleContactForm;
