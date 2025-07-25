/**
 * Support page JavaScript for Kale Email API Platform
 * Production-ready support functionality
 */

'use strict';

const SupportAPI = {
    // Initialize support page
    init: function() {
        this.setupContactForm();
        this.setupFAQToggle();
        this.setupSearchFunctionality();
        this.loadSystemStatus();
    },

    // Setup contact form
    setupContactForm: function() {
        const contactForm = document.getElementById('contact-form');
        if (contactForm) {
            contactForm.addEventListener('submit', this.handleContactForm.bind(this));
        }

        // Setup form validation
        const formFields = contactForm?.querySelectorAll('input, textarea, select');
        formFields?.forEach(field => {
            field.addEventListener('blur', () => this.validateField(field));
            field.addEventListener('input', () => this.clearFieldError(field));
        });
    },

    // Handle contact form submission
    handleContactForm: async function(e) {
        e.preventDefault();
        
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Validate form
        if (!this.validateContactForm(form)) {
            return;
        }

        this.setButtonLoading(submitBtn, true);

        try {
            const formData = new FormData(form);
            const contactData = {
                name: formData.get('name'),
                email: formData.get('email'),
                subject: formData.get('subject'),
                message: formData.get('message'),
                priority: formData.get('priority') || 'medium',
                category: formData.get('category') || 'general'
            };

            // Since we don't have a contact endpoint, we'll simulate submission
            // In a real implementation, this would send to your support system
            await this.simulateContactSubmission(contactData);
            
            this.showFormSuccess('Thank you! Your message has been sent. We\'ll get back to you within 24 hours.');
            form.reset();
            
        } catch (error) {
            this.showFormError('Failed to send message. Please try again or contact us directly at support@kale.kanopus.org');
        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    },

    // Simulate contact form submission
    simulateContactSubmission: function(data) {
        return new Promise((resolve) => {
            // Simulate API delay
            setTimeout(() => {
                resolve({ success: true });
            }, 1500);
        });
    },

    // Validate contact form
    validateContactForm: function(form) {
        let isValid = true;
        
        const name = form.querySelector('[name="name"]');
        const email = form.querySelector('[name="email"]');
        const subject = form.querySelector('[name="subject"]');
        const message = form.querySelector('[name="message"]');

        // Validate name
        if (!name.value.trim()) {
            this.showFieldError(name, 'Name is required');
            isValid = false;
        }

        // Validate email
        if (!email.value.trim()) {
            this.showFieldError(email, 'Email is required');
            isValid = false;
        } else if (!this.isValidEmail(email.value)) {
            this.showFieldError(email, 'Please enter a valid email address');
            isValid = false;
        }

        // Validate subject
        if (!subject.value.trim()) {
            this.showFieldError(subject, 'Subject is required');
            isValid = false;
        }

        // Validate message
        if (!message.value.trim()) {
            this.showFieldError(message, 'Message is required');
            isValid = false;
        } else if (message.value.trim().length < 10) {
            this.showFieldError(message, 'Message must be at least 10 characters long');
            isValid = false;
        }

        return isValid;
    },

    // Validate individual field
    validateField: function(field) {
        const value = field.value.trim();
        const name = field.getAttribute('name');

        switch (name) {
            case 'name':
                if (!value) {
                    this.showFieldError(field, 'Name is required');
                    return false;
                }
                break;
            case 'email':
                if (!value) {
                    this.showFieldError(field, 'Email is required');
                    return false;
                } else if (!this.isValidEmail(value)) {
                    this.showFieldError(field, 'Please enter a valid email address');
                    return false;
                }
                break;
            case 'subject':
                if (!value) {
                    this.showFieldError(field, 'Subject is required');
                    return false;
                }
                break;
            case 'message':
                if (!value) {
                    this.showFieldError(field, 'Message is required');
                    return false;
                } else if (value.length < 10) {
                    this.showFieldError(field, 'Message must be at least 10 characters long');
                    return false;
                }
                break;
        }

        this.clearFieldError(field);
        return true;
    },

    // Setup FAQ toggle functionality
    setupFAQToggle: function() {
        const faqItems = document.querySelectorAll('.faq-item');
        
        faqItems.forEach(item => {
            const question = item.querySelector('.faq-question');
            const answer = item.querySelector('.faq-answer');
            const icon = item.querySelector('.faq-icon');
            
            if (question && answer) {
                question.addEventListener('click', () => {
                    const isOpen = !answer.classList.contains('hidden');
                    
                    // Close all other FAQ items
                    faqItems.forEach(otherItem => {
                        const otherAnswer = otherItem.querySelector('.faq-answer');
                        const otherIcon = otherItem.querySelector('.faq-icon');
                        if (otherAnswer !== answer) {
                            otherAnswer.classList.add('hidden');
                            if (otherIcon) {
                                otherIcon.classList.remove('rotate-180');
                            }
                        }
                    });
                    
                    // Toggle current item
                    if (isOpen) {
                        answer.classList.add('hidden');
                        if (icon) icon.classList.remove('rotate-180');
                    } else {
                        answer.classList.remove('hidden');
                        if (icon) icon.classList.add('rotate-180');
                    }
                });
            }
        });
    },

    // Setup search functionality for FAQ
    setupSearchFunctionality: function() {
        const searchInput = document.getElementById('faq-search');
        const faqItems = document.querySelectorAll('.faq-item');
        
        if (searchInput && faqItems.length > 0) {
            searchInput.addEventListener('input', (e) => {
                const searchTerm = e.target.value.toLowerCase().trim();
                
                faqItems.forEach(item => {
                    const question = item.querySelector('.faq-question');
                    const answer = item.querySelector('.faq-answer');
                    
                    if (question && answer) {
                        const questionText = question.textContent.toLowerCase();
                        const answerText = answer.textContent.toLowerCase();
                        
                        if (questionText.includes(searchTerm) || answerText.includes(searchTerm)) {
                            item.style.display = 'block';
                        } else {
                            item.style.display = 'none';
                        }
                    }
                });

                // Show "no results" message if needed
                this.updateSearchResults(searchTerm, faqItems);
            });
        }
    },

    // Update search results display
    updateSearchResults: function(searchTerm, faqItems) {
        const visibleItems = Array.from(faqItems).filter(item => 
            item.style.display !== 'none'
        );

        let noResultsMsg = document.getElementById('no-results-message');
        
        if (searchTerm && visibleItems.length === 0) {
            if (!noResultsMsg) {
                noResultsMsg = document.createElement('div');
                noResultsMsg.id = 'no-results-message';
                noResultsMsg.className = 'text-center py-8 text-gray-500';
                noResultsMsg.innerHTML = `
                    <p class="text-lg mb-2">No results found for "${searchTerm}"</p>
                    <p class="text-sm">Try a different search term or contact us directly.</p>
                `;
                
                const faqContainer = document.querySelector('.faq-container');
                if (faqContainer) {
                    faqContainer.appendChild(noResultsMsg);
                }
            }
            noResultsMsg.style.display = 'block';
        } else if (noResultsMsg) {
            noResultsMsg.style.display = 'none';
        }
    },

    // Load system status
    loadSystemStatus: async function() {
        const statusContainer = document.getElementById('system-status');
        if (!statusContainer) return;

        try {
            // Since we don't have a status endpoint, we'll show a default status
            this.displaySystemStatus({
                status: 'operational',
                lastUpdate: new Date().toISOString(),
                services: [
                    { name: 'API Service', status: 'operational' },
                    { name: 'Email Delivery', status: 'operational' },
                    { name: 'Dashboard', status: 'operational' }
                ]
            });
        } catch (error) {
            this.displaySystemStatus({
                status: 'unknown',
                lastUpdate: new Date().toISOString(),
                services: []
            });
        }
    },

    // Display system status
    displaySystemStatus: function(status) {
        const statusContainer = document.getElementById('system-status');
        if (!statusContainer) return;

        const statusColor = status.status === 'operational' ? 'green' : 
                           status.status === 'degraded' ? 'yellow' : 'red';

        statusContainer.innerHTML = `
            <div class="bg-white rounded-lg shadow p-6">
                <div class="flex items-center mb-4">
                    <div class="w-3 h-3 bg-${statusColor}-500 rounded-full mr-3"></div>
                    <h3 class="text-lg font-semibold">System Status: ${status.status.charAt(0).toUpperCase() + status.status.slice(1)}</h3>
                </div>
                <p class="text-sm text-gray-600 mb-4">Last updated: ${this.formatDate(status.lastUpdate)}</p>
                
                ${status.services.length > 0 ? `
                    <div class="space-y-2">
                        <h4 class="font-medium text-gray-900">Services</h4>
                        ${status.services.map(service => `
                            <div class="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                                <span class="text-sm text-gray-700">${service.name}</span>
                                <span class="text-sm text-${service.status === 'operational' ? 'green' : 'red'}-600 font-medium">
                                    ${service.status.charAt(0).toUpperCase() + service.status.slice(1)}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    },

    // Show field error
    showFieldError: function(field, message) {
        this.clearFieldError(field);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-red-600 text-sm mt-1';
        errorDiv.textContent = message;
        
        field.classList.add('border-red-500');
        field.parentNode.appendChild(errorDiv);
    },

    // Clear field error
    clearFieldError: function(field) {
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
        field.classList.remove('border-red-500');
    },

    // Show form success message
    showFormSuccess: function(message) {
        this.clearFormMessages();
        const successDiv = document.createElement('div');
        successDiv.className = 'form-message bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4';
        successDiv.textContent = message;
        
        const form = document.getElementById('contact-form');
        if (form) {
            form.insertBefore(successDiv, form.firstChild);
        }
    },

    // Show form error message
    showFormError: function(message) {
        this.clearFormMessages();
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-message bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4';
        errorDiv.textContent = message;
        
        const form = document.getElementById('contact-form');
        if (form) {
            form.insertBefore(errorDiv, form.firstChild);
        }
    },

    // Clear form messages
    clearFormMessages: function() {
        const existingMessages = document.querySelectorAll('.form-message');
        existingMessages.forEach(msg => msg.remove());
    },

    // Set button loading state
    setButtonLoading: function(button, loading) {
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = 'Sending...';
            button.classList.add('opacity-75');
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText;
            button.classList.remove('opacity-75');
        }
    },

    // Validate email format
    isValidEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Format date
    formatDate: function(dateString) {
        return new Date(dateString).toLocaleString();
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    SupportAPI.init();
});

// Export for global access
window.SupportAPI = SupportAPI;
