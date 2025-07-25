/**
 * Documentation page JavaScript for Kale Email API Platform
 * Production-ready documentation functionality
 */

'use strict';

const DocsAPI = {
    // Initialize documentation page
    init: function() {
        this.setupNavigation();
        this.setupCodeExamples();
        this.setupCopyButtons();
        this.setupTryItNow();
        this.highlightCurrentSection();
    },

    // Setup sidebar navigation
    setupNavigation: function() {
        const navLinks = document.querySelectorAll('.docs-nav a');
        const sections = document.querySelectorAll('.docs-section');

        // Highlight active section on scroll
        let ticking = false;
        
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    this.updateActiveNavItem();
                    ticking = false;
                });
                ticking = true;
            }
        });

        // Smooth scroll to sections
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    },

    // Update active navigation item based on scroll position
    updateActiveNavItem: function() {
        const sections = document.querySelectorAll('.docs-section');
        const navLinks = document.querySelectorAll('.docs-nav a');
        
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            
            if (window.pageYOffset >= sectionTop - 100) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active', 'bg-blue-50', 'text-blue-600', 'border-blue-300');
            link.classList.add('text-gray-600', 'hover:text-gray-900');
            
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.remove('text-gray-600', 'hover:text-gray-900');
                link.classList.add('active', 'bg-blue-50', 'text-blue-600', 'border-blue-300');
            }
        });
    },

    // Highlight current section based on URL hash
    highlightCurrentSection: function() {
        const hash = window.location.hash;
        if (hash) {
            const targetElement = document.querySelector(hash);
            if (targetElement) {
                setTimeout(() => {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }, 100);
            }
        }
    },

    // Setup code example highlighting and copy functionality
    setupCodeExamples: function() {
        const codeBlocks = document.querySelectorAll('pre code');
        
        codeBlocks.forEach(block => {
            // Add copy button to each code block
            const pre = block.parentElement;
            const copyButton = document.createElement('button');
            copyButton.className = 'absolute top-2 right-2 px-2 py-1 bg-gray-700 text-white text-xs rounded hover:bg-gray-600 transition-colors';
            copyButton.textContent = 'Copy';
            copyButton.addEventListener('click', () => {
                this.copyCodeToClipboard(block.textContent, copyButton);
            });

            pre.style.position = 'relative';
            pre.appendChild(copyButton);
        });
    },

    // Setup copy buttons for API keys and URLs
    setupCopyButtons: function() {
        const copyButtons = document.querySelectorAll('[data-copy]');
        
        copyButtons.forEach(button => {
            button.addEventListener('click', () => {
                const textToCopy = button.getAttribute('data-copy');
                this.copyToClipboard(textToCopy);
            });
        });
    },

    // Setup "Try It Now" interactive examples
    setupTryItNow: function() {
        const tryButtons = document.querySelectorAll('.try-it-btn');
        
        tryButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const exampleType = button.getAttribute('data-example');
                this.showInteractiveExample(exampleType, button);
            });
        });
    },

    // Show interactive API example
    showInteractiveExample: function(exampleType, button) {
        const container = button.nextElementSibling;
        if (!container || !container.classList.contains('interactive-example')) {
            return;
        }

        // Toggle visibility
        if (container.style.display === 'none' || !container.style.display) {
            container.style.display = 'block';
            button.textContent = 'Hide Example';
            this.loadInteractiveExample(exampleType, container);
        } else {
            container.style.display = 'none';
            button.textContent = 'Try It Now';
        }
    },

    // Load interactive example content
    loadInteractiveExample: function(exampleType, container) {
        switch (exampleType) {
            case 'send-email':
                this.createSendEmailExample(container);
                break;
            case 'create-template':
                this.createTemplateExample(container);
                break;
            case 'list-templates':
                this.createListTemplatesExample(container);
                break;
            default:
                container.innerHTML = '<p class="text-gray-600">Example not available</p>';
        }
    },

    // Create send email interactive example
    createSendEmailExample: function(container) {
        container.innerHTML = `
            <div class="bg-gray-50 p-6 rounded-lg border">
                <h4 class="font-semibold text-lg mb-4 text-gray-800">Try Send Email API</h4>
                <form id="send-email-example" class="space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">API Key</label>
                            <input type="password" id="api-key-input" placeholder="Enter your API key" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                            <p class="text-xs text-gray-500 mt-1">Get your API key from the Dashboard</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Username</label>
                            <input type="text" id="username-input" placeholder="Your username" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                        </div>
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Template ID</label>
                            <input type="text" id="template-id-input" placeholder="template-123" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">To Email</label>
                            <input type="email" id="to-email-input" placeholder="recipient@example.com" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                        </div>
                    </div>
                    <div class="flex flex-col sm:flex-row gap-3">
                        <button type="submit" class="flex-1 bg-gradient-to-r from-blue-500 to-blue-600 text-white py-2 px-4 rounded-md hover:from-blue-600 hover:to-blue-700 transition-all duration-200 font-medium">
                            Send Test Email
                        </button>
                        <button type="button" onclick="this.closest('.interactive-example').style.display='none'; this.closest('.interactive-example').previousElementSibling.textContent='Try It Now';" 
                                class="flex-1 bg-gray-100 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-200 transition-all duration-200 font-medium">
                            Close
                        </button>
                    </div>
                </form>
                <div id="send-email-result" class="mt-4 hidden"></div>
            </div>
        `;

        const form = container.querySelector('#send-email-example');
        form.addEventListener('submit', this.handleSendEmailExample.bind(this));
    },

    // Handle send email example submission
    handleSendEmailExample: async function(e) {
        e.preventDefault();
        
        const form = e.target;
        const resultDiv = document.getElementById('send-email-result');
        const submitBtn = form.querySelector('button[type="submit"]');
        
        const apiKey = form.querySelector('#api-key-input').value.trim();
        const username = form.querySelector('#username-input').value.trim();
        const templateId = form.querySelector('#template-id-input').value.trim();
        const toEmail = form.querySelector('#to-email-input').value.trim();

        if (!apiKey || !username || !templateId || !toEmail) {
            this.showExampleResult(resultDiv, 'Please fill in all fields', 'error');
            return;
        }

        this.setButtonLoading(submitBtn, true);

        try {
            const response = await fetch(`/${username}/${templateId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': apiKey
                },
                body: JSON.stringify({
                    to_email: toEmail,
                    variables: {
                        name: 'Test User',
                        message: 'This is a test email from the documentation'
                    }
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showExampleResult(resultDiv, 'Email sent successfully!', 'success');
            } else {
                this.showExampleResult(resultDiv, data.detail || 'Failed to send email', 'error');
            }
        } catch (error) {
            this.showExampleResult(resultDiv, 'Network error: ' + error.message, 'error');
        } finally {
            this.setButtonLoading(submitBtn, false);
        }
    },

    // Show example result with improved styling
    showExampleResult: function(container, message, type) {
        const icons = {
            success: '<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>',
            error: '<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>',
            info: '<svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>'
        };

        container.className = `mt-4 p-4 rounded-lg flex items-start ${
            type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
            type === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
            'bg-blue-50 text-blue-800 border border-blue-200'
        }`;
        
        container.innerHTML = `
            <div class="flex">
                ${icons[type] || icons.info}
                <div>
                    <p class="font-medium">${type === 'success' ? 'Success' : type === 'error' ? 'Error' : 'Info'}</p>
                    <p class="text-sm mt-1">${message}</p>
                </div>
            </div>
        `;
        container.classList.remove('hidden');
        
        // Auto-hide after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                container.classList.add('hidden');
            }, 5000);
        }
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

    // Copy code to clipboard
    copyCodeToClipboard: function(text, button) {
        navigator.clipboard.writeText(text).then(() => {
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            button.classList.add('bg-green-600');
            
            setTimeout(() => {
                button.textContent = originalText;
                button.classList.remove('bg-green-600');
            }, 2000);
        }).catch(() => {
            button.textContent = 'Failed';
            setTimeout(() => {
                button.textContent = 'Copy';
            }, 2000);
        });
    },

    // Copy text to clipboard
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(() => {
            // Could use a toast notification here
            const notification = document.createElement('div');
            notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded shadow-lg z-50';
            notification.textContent = 'Copied to clipboard!';
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
        }).catch(() => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
        });
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    DocsAPI.init();
});

// Export for global access
window.DocsAPI = DocsAPI;
