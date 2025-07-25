/**
 * Privacy page JavaScript for Kale Email API Platform
 * Production-ready privacy policy functionality
 */

'use strict';

const PrivacyAPI = {
    // Initialize privacy page
    init: function() {
        this.setupTableOfContents();
        this.setupScrollHighlighting();
        this.setupPrintFunctionality();
        this.setupSearchFunctionality();
        this.trackPageViews();
    },

    // Setup table of contents navigation
    setupTableOfContents: function() {
        const tocContainer = document.getElementById('table-of-contents');
        const sections = document.querySelectorAll('.privacy-section');
        
        if (tocContainer && sections.length > 0) {
            this.generateTableOfContents(tocContainer, sections);
            this.setupTocNavigation();
        }
    },

    // Generate table of contents
    generateTableOfContents: function(container, sections) {
        const tocList = document.createElement('ul');
        tocList.className = 'space-y-2';

        sections.forEach((section, index) => {
            const heading = section.querySelector('h2, h3');
            if (heading) {
                const sectionId = section.id || `section-${index}`;
                section.id = sectionId;

                const listItem = document.createElement('li');
                const link = document.createElement('a');
                
                link.href = `#${sectionId}`;
                link.textContent = heading.textContent;
                link.className = 'text-blue-600 hover:text-blue-800 transition-colors text-sm block py-1';
                
                listItem.appendChild(link);
                tocList.appendChild(listItem);
            }
        });

        container.appendChild(tocList);
    },

    // Setup table of contents navigation
    setupTocNavigation: function() {
        const tocLinks = document.querySelectorAll('#table-of-contents a');
        
        tocLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    
                    // Update URL without triggering page reload
                    history.pushState(null, null, `#${targetId}`);
                }
            });
        });
    },

    // Setup scroll highlighting for active sections
    setupScrollHighlighting: function() {
        const sections = document.querySelectorAll('.privacy-section');
        const tocLinks = document.querySelectorAll('#table-of-contents a');
        
        if (sections.length === 0 || tocLinks.length === 0) return;

        let ticking = false;
        
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    this.updateActiveSection(sections, tocLinks);
                    ticking = false;
                });
                ticking = true;
            }
        });
    },

    // Update active section highlighting
    updateActiveSection: function(sections, tocLinks) {
        const scrollPosition = window.pageYOffset + 100;
        let activeSection = null;

        // Find the current active section
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionBottom = sectionTop + section.offsetHeight;
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionBottom) {
                activeSection = section.id;
            }
        });

        // Update TOC highlighting
        tocLinks.forEach(link => {
            link.classList.remove('font-semibold', 'text-blue-800');
            link.classList.add('text-blue-600');
            
            if (activeSection && link.getAttribute('href') === `#${activeSection}`) {
                link.classList.remove('text-blue-600');
                link.classList.add('font-semibold', 'text-blue-800');
            }
        });
    },

    // Setup print functionality
    setupPrintFunctionality: function() {
        const printButton = document.getElementById('print-privacy');
        if (printButton) {
            printButton.addEventListener('click', () => {
                this.printPrivacyPolicy();
            });
        }
    },

    // Print privacy policy
    printPrivacyPolicy: function() {
        // Create a print-friendly version
        const printWindow = window.open('', '_blank');
        const content = this.generatePrintContent();
        
        printWindow.document.write(content);
        printWindow.document.close();
        
        // Wait for content to load, then print
        printWindow.onload = function() {
            printWindow.print();
            printWindow.close();
        };
    },

    // Generate print-friendly content
    generatePrintContent: function() {
        const title = document.title;
        const mainContent = document.querySelector('.privacy-content')?.innerHTML || 
                           document.querySelector('main')?.innerHTML || 
                           document.body.innerHTML;

        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>${title}</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        line-height: 1.6; 
                        margin: 40px; 
                        color: #333;
                    }
                    h1, h2, h3 { 
                        color: #2563eb; 
                        margin-top: 30px; 
                        margin-bottom: 15px;
                    }
                    h1 { font-size: 24px; }
                    h2 { font-size: 20px; }
                    h3 { font-size: 16px; }
                    p { margin-bottom: 12px; }
                    ul, ol { margin-bottom: 12px; padding-left: 25px; }
                    .print-header {
                        border-bottom: 2px solid #2563eb;
                        padding-bottom: 20px;
                        margin-bottom: 30px;
                    }
                    .print-footer {
                        margin-top: 40px;
                        padding-top: 20px;
                        border-top: 1px solid #ccc;
                        font-size: 12px;
                        color: #666;
                    }
                    @media print {
                        body { margin: 20px; }
                        .no-print { display: none; }
                    }
                </style>
            </head>
            <body>
                <div class="print-header">
                    <h1>Kale Email API - Privacy Policy</h1>
                    <p>Generated on: ${new Date().toLocaleDateString()}</p>
                </div>
                <div class="content">
                    ${mainContent}
                </div>
                <div class="print-footer">
                    <p>This document was generated from https://kale.kanopus.org/privacy</p>
                    <p>For the most up-to-date version, please visit our website.</p>
                </div>
            </body>
            </html>
        `;
    },

    // Setup search functionality
    setupSearchFunctionality: function() {
        const searchInput = document.getElementById('privacy-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchPrivacyContent(e.target.value);
            });

            // Clear search on escape key
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    e.target.value = '';
                    this.clearSearch();
                }
            });
        }
    },

    // Search privacy policy content
    searchPrivacyContent: function(searchTerm) {
        const content = document.querySelector('.privacy-content') || document.querySelector('main');
        if (!content) return;

        // Clear previous highlights
        this.clearSearch();

        if (!searchTerm || searchTerm.length < 3) {
            return;
        }

        // Find and highlight matches
        const matches = this.findTextMatches(content, searchTerm);
        this.highlightMatches(matches);
        this.showSearchResults(matches.length, searchTerm);
    },

    // Find text matches in content
    findTextMatches: function(container, searchTerm) {
        const matches = [];
        const walker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let node;
        while (node = walker.nextNode()) {
            const text = node.textContent;
            const regex = new RegExp(searchTerm, 'gi');
            let match;

            while ((match = regex.exec(text)) !== null) {
                matches.push({
                    node: node,
                    start: match.index,
                    end: match.index + searchTerm.length,
                    text: match[0]
                });
            }
        }

        return matches;
    },

    // Highlight search matches
    highlightMatches: function(matches) {
        matches.forEach(match => {
            const parent = match.node.parentNode;
            const text = match.node.textContent;
            
            // Create highlighted version
            const beforeText = text.substring(0, match.start);
            const matchText = text.substring(match.start, match.end);
            const afterText = text.substring(match.end);

            // Create new elements
            const highlight = document.createElement('mark');
            highlight.className = 'bg-yellow-200 px-1';
            highlight.textContent = matchText;

            // Replace original text node
            const beforeNode = document.createTextNode(beforeText);
            const afterNode = document.createTextNode(afterText);

            parent.insertBefore(beforeNode, match.node);
            parent.insertBefore(highlight, match.node);
            parent.insertBefore(afterNode, match.node);
            parent.removeChild(match.node);
        });
    },

    // Show search results
    showSearchResults: function(count, searchTerm) {
        let resultsContainer = document.getElementById('search-results');
        
        if (!resultsContainer) {
            resultsContainer = document.createElement('div');
            resultsContainer.id = 'search-results';
            resultsContainer.className = 'bg-blue-50 border border-blue-200 rounded p-3 mb-4';
            
            const searchInput = document.getElementById('privacy-search');
            if (searchInput) {
                searchInput.parentNode.insertBefore(resultsContainer, searchInput.nextSibling);
            }
        }

        if (count > 0) {
            resultsContainer.innerHTML = `
                <p class="text-blue-800 text-sm">
                    Found ${count} match${count !== 1 ? 'es' : ''} for "${searchTerm}"
                    <button onclick="PrivacyAPI.clearSearch()" class="ml-2 text-blue-600 hover:text-blue-800">
                        Clear
                    </button>
                </p>
            `;
            resultsContainer.style.display = 'block';
        } else {
            resultsContainer.innerHTML = `
                <p class="text-blue-800 text-sm">
                    No matches found for "${searchTerm}"
                    <button onclick="PrivacyAPI.clearSearch()" class="ml-2 text-blue-600 hover:text-blue-800">
                        Clear
                    </button>
                </p>
            `;
            resultsContainer.style.display = 'block';
        }
    },

    // Clear search highlights and results
    clearSearch: function() {
        // Remove highlights
        const highlights = document.querySelectorAll('mark');
        highlights.forEach(highlight => {
            const parent = highlight.parentNode;
            parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
            parent.normalize();
        });

        // Hide search results
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }

        // Clear search input
        const searchInput = document.getElementById('privacy-search');
        if (searchInput) {
            searchInput.value = '';
        }
    },

    // Track page views (privacy-compliant)
    trackPageViews: function() {
        // Only track if user hasn't opted out
        const hasOptedOut = localStorage.getItem('privacy_opt_out') === 'true';
        
        if (!hasOptedOut) {
            // Simple, privacy-friendly analytics
            const visitData = {
                page: 'privacy',
                timestamp: new Date().toISOString(),
                referrer: document.referrer ? new URL(document.referrer).hostname : 'direct'
            };

            // Store locally (could be sent to analytics service)
            const visits = JSON.parse(localStorage.getItem('page_visits') || '[]');
            visits.push(visitData);
            
            // Keep only last 10 visits to respect privacy
            if (visits.length > 10) {
                visits.splice(0, visits.length - 10);
            }
            
            localStorage.setItem('page_visits', JSON.stringify(visits));
        }
    },

    // Setup privacy preferences
    setupPrivacyPreferences: function() {
        const optOutButton = document.getElementById('opt-out-tracking');
        const optInButton = document.getElementById('opt-in-tracking');
        
        if (optOutButton) {
            optOutButton.addEventListener('click', () => {
                localStorage.setItem('privacy_opt_out', 'true');
                this.showPrivacyMessage('You have opted out of analytics tracking.', 'success');
                this.updatePrivacyStatus();
            });
        }

        if (optInButton) {
            optInButton.addEventListener('click', () => {
                localStorage.removeItem('privacy_opt_out');
                this.showPrivacyMessage('You have opted in to analytics tracking.', 'success');
                this.updatePrivacyStatus();
            });
        }

        // Initialize privacy status
        this.updatePrivacyStatus();
    },

    // Update privacy tracking status display
    updatePrivacyStatus: function() {
        const statusElement = document.getElementById('tracking-status');
        const hasOptedOut = localStorage.getItem('privacy_opt_out') === 'true';
        
        if (statusElement) {
            statusElement.textContent = hasOptedOut ? 'Disabled' : 'Enabled';
            statusElement.className = hasOptedOut ? 'text-red-600' : 'text-green-600';
        }
    },

    // Show privacy-related messages
    showPrivacyMessage: function(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `fixed top-4 right-4 p-4 rounded shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        messageDiv.textContent = message;
        
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    },

    // Handle URL hash navigation
    handleHashNavigation: function() {
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
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    PrivacyAPI.init();
    PrivacyAPI.setupPrivacyPreferences();
    PrivacyAPI.handleHashNavigation();
});

// Handle hash changes
window.addEventListener('hashchange', function() {
    PrivacyAPI.handleHashNavigation();
});

// Export for global access
window.PrivacyAPI = PrivacyAPI;
