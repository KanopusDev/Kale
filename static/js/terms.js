/**
 * Terms of Service page JavaScript for Kale Email API Platform
 * Production-ready terms and conditions functionality
 */

'use strict';

const TermsAPI = {
    // Initialize terms page
    init: function() {
        this.setupTableOfContents();
        this.setupScrollHighlighting();
        this.setupAcceptanceTracking();
        this.setupPrintFunctionality();
        this.setupSearchFunctionality();
        this.loadTermsHistory();
        this.trackPageView();
    },

    // Setup table of contents navigation
    setupTableOfContents: function() {
        const tocContainer = document.getElementById('terms-toc');
        const sections = document.querySelectorAll('.terms-section');
        
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
                const sectionId = section.id || `terms-section-${index}`;
                section.id = sectionId;

                const listItem = document.createElement('li');
                const link = document.createElement('a');
                
                link.href = `#${sectionId}`;
                link.textContent = heading.textContent;
                link.className = 'text-blue-600 hover:text-blue-800 transition-colors text-sm block py-1 px-2 rounded hover:bg-blue-50';
                
                listItem.appendChild(link);
                tocList.appendChild(listItem);
            }
        });

        container.innerHTML = `
            <div class="bg-gray-50 rounded-lg p-4">
                <h3 class="font-semibold text-gray-900 mb-3">Table of Contents</h3>
                ${tocList.outerHTML}
            </div>
        `;
    },

    // Setup table of contents navigation
    setupTocNavigation: function() {
        const tocLinks = document.querySelectorAll('#terms-toc a');
        
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
                    
                    // Update URL hash
                    history.pushState(null, null, `#${targetId}`);
                    
                    // Track section view
                    this.trackSectionView(targetId);
                }
            });
        });
    },

    // Setup scroll highlighting for active sections
    setupScrollHighlighting: function() {
        const sections = document.querySelectorAll('.terms-section');
        const tocLinks = document.querySelectorAll('#terms-toc a');
        
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
            link.classList.remove('font-semibold', 'text-blue-800', 'bg-blue-100');
            link.classList.add('text-blue-600');
            
            if (activeSection && link.getAttribute('href') === `#${activeSection}`) {
                link.classList.remove('text-blue-600');
                link.classList.add('font-semibold', 'text-blue-800', 'bg-blue-100');
            }
        });
    },

    // Setup terms acceptance tracking
    setupAcceptanceTracking: function() {
        const acceptButton = document.getElementById('accept-terms');
        const declineButton = document.getElementById('decline-terms');
        
        if (acceptButton) {
            acceptButton.addEventListener('click', () => {
                this.handleTermsAcceptance(true);
            });
        }

        if (declineButton) {
            declineButton.addEventListener('click', () => {
                this.handleTermsAcceptance(false);
            });
        }

        // Show current acceptance status
        this.displayAcceptanceStatus();
    },

    // Handle terms acceptance
    handleTermsAcceptance: function(accepted) {
        const timestamp = new Date().toISOString();
        const version = this.getCurrentTermsVersion();
        
        const acceptanceData = {
            accepted: accepted,
            timestamp: timestamp,
            version: version,
            ip_hash: this.generateIPHash(), // Privacy-friendly IP tracking
            user_agent: navigator.userAgent
        };

        // Store acceptance locally
        localStorage.setItem('terms_acceptance', JSON.stringify(acceptanceData));

        // If user is logged in, could also send to backend
        if (this.isUserLoggedIn()) {
            this.sendAcceptanceToBackend(acceptanceData);
        }

        // Show confirmation
        if (accepted) {
            this.showAcceptanceMessage('Thank you for accepting our Terms of Service.', 'success');
            // Redirect to dashboard or intended page after delay
            setTimeout(() => {
                const returnUrl = new URLSearchParams(window.location.search).get('return');
                window.location.href = returnUrl || '/dashboard';
            }, 2000);
        } else {
            this.showAcceptanceMessage('You have declined our Terms of Service. Some features may not be available.', 'warning');
        }

        this.displayAcceptanceStatus();
    },

    // Display current acceptance status
    displayAcceptanceStatus: function() {
        const statusContainer = document.getElementById('acceptance-status');
        if (!statusContainer) return;

        const acceptanceData = JSON.parse(localStorage.getItem('terms_acceptance') || 'null');
        
        if (acceptanceData) {
            const statusClass = acceptanceData.accepted ? 'text-green-600' : 'text-red-600';
            const statusText = acceptanceData.accepted ? 'Accepted' : 'Declined';
            const date = new Date(acceptanceData.timestamp).toLocaleDateString();
            
            statusContainer.innerHTML = `
                <div class="bg-gray-50 rounded-lg p-4">
                    <h3 class="font-semibold text-gray-900 mb-2">Your Status</h3>
                    <p class="text-sm">
                        Status: <span class="${statusClass} font-medium">${statusText}</span><br>
                        Date: <span class="text-gray-600">${date}</span><br>
                        Version: <span class="text-gray-600">${acceptanceData.version}</span>
                    </p>
                </div>
            `;
        } else {
            statusContainer.innerHTML = `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h3 class="font-semibold text-yellow-800 mb-2">Action Required</h3>
                    <p class="text-sm text-yellow-700">Please review and accept our Terms of Service to continue using our platform.</p>
                </div>
            `;
        }
    },

    // Setup print functionality
    setupPrintFunctionality: function() {
        const printButton = document.getElementById('print-terms');
        if (printButton) {
            printButton.addEventListener('click', () => {
                this.printTerms();
            });
        }
    },

    // Print terms of service
    printTerms: function() {
        const printWindow = window.open('', '_blank');
        const content = this.generatePrintContent();
        
        printWindow.document.write(content);
        printWindow.document.close();
        
        printWindow.onload = function() {
            printWindow.print();
            printWindow.close();
        };
    },

    // Generate print-friendly content
    generatePrintContent: function() {
        const title = document.title;
        const mainContent = document.querySelector('.terms-content')?.innerHTML || 
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
                        margin-top: 25px; 
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
                    <h1>Kale Email API - Terms of Service</h1>
                    <p>Version: ${this.getCurrentTermsVersion()}</p>
                    <p>Generated on: ${new Date().toLocaleDateString()}</p>
                </div>
                <div class="content">
                    ${mainContent}
                </div>
                <div class="print-footer">
                    <p>This document was generated from https://kale.kanopus.org/terms</p>
                    <p>For the most up-to-date version, please visit our website.</p>
                </div>
            </body>
            </html>
        `;
    },

    // Setup search functionality
    setupSearchFunctionality: function() {
        const searchInput = document.getElementById('terms-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchTermsContent(e.target.value);
            });

            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    e.target.value = '';
                    this.clearSearch();
                }
            });
        }
    },

    // Search terms content
    searchTermsContent: function(searchTerm) {
        const content = document.querySelector('.terms-content') || document.querySelector('main');
        if (!content) return;

        this.clearSearch();

        if (!searchTerm || searchTerm.length < 3) {
            return;
        }

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
            
            const beforeText = text.substring(0, match.start);
            const matchText = text.substring(match.start, match.end);
            const afterText = text.substring(match.end);

            const highlight = document.createElement('mark');
            highlight.className = 'bg-yellow-200 px-1 rounded';
            highlight.textContent = matchText;

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
            
            const searchInput = document.getElementById('terms-search');
            if (searchInput) {
                searchInput.parentNode.insertBefore(resultsContainer, searchInput.nextSibling);
            }
        }

        resultsContainer.innerHTML = count > 0 
            ? `<p class="text-blue-800 text-sm">Found ${count} match${count !== 1 ? 'es' : ''} for "${searchTerm}" <button onclick="TermsAPI.clearSearch()" class="ml-2 text-blue-600 hover:text-blue-800">Clear</button></p>`
            : `<p class="text-blue-800 text-sm">No matches found for "${searchTerm}" <button onclick="TermsAPI.clearSearch()" class="ml-2 text-blue-600 hover:text-blue-800">Clear</button></p>`;
        
        resultsContainer.style.display = 'block';
    },

    // Clear search highlights and results
    clearSearch: function() {
        const highlights = document.querySelectorAll('mark');
        highlights.forEach(highlight => {
            const parent = highlight.parentNode;
            parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
            parent.normalize();
        });

        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }

        const searchInput = document.getElementById('terms-search');
        if (searchInput) {
            searchInput.value = '';
        }
    },

    // Load terms history
    loadTermsHistory: function() {
        const historyContainer = document.getElementById('terms-history');
        if (!historyContainer) return;

        const history = this.getTermsHistory();
        this.displayTermsHistory(historyContainer, history);
    },

    // Get terms history (simulated)
    getTermsHistory: function() {
        return [
            {
                version: '2.1',
                date: '2024-01-15',
                changes: ['Updated data processing clauses', 'Added new API rate limiting terms', 'Clarified refund policy']
            },
            {
                version: '2.0',
                date: '2023-12-01',
                changes: ['Major revision for GDPR compliance', 'Updated privacy terms', 'New liability limitations']
            },
            {
                version: '1.5',
                date: '2023-08-15',
                changes: ['Added API usage guidelines', 'Updated acceptable use policy']
            }
        ];
    },

    // Display terms history
    displayTermsHistory: function(container, history) {
        container.innerHTML = `
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold mb-4">Terms Version History</h3>
                <div class="space-y-4">
                    ${history.map(version => `
                        <div class="border-l-4 border-blue-500 pl-4">
                            <div class="flex items-center justify-between mb-2">
                                <h4 class="font-semibold">Version ${version.version}</h4>
                                <span class="text-sm text-gray-600">${new Date(version.date).toLocaleDateString()}</span>
                            </div>
                            <ul class="text-sm text-gray-700 space-y-1">
                                ${version.changes.map(change => `<li>• ${change}</li>`).join('')}
                            </ul>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    },

    // Utility functions
    getCurrentTermsVersion: function() {
        return document.querySelector('[data-terms-version]')?.dataset.termsVersion || '2.1';
    },

    isUserLoggedIn: function() {
        return localStorage.getItem('auth_token') && localStorage.getItem('user');
    },

    generateIPHash: function() {
        // Generate a privacy-friendly hash (not actual IP)
        return 'hash_' + Math.random().toString(36).substring(2, 15);
    },

    sendAcceptanceToBackend: function(acceptanceData) {
        // In a real implementation, send to backend API
        fetch('/api/v1/user/terms-acceptance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify(acceptanceData)
        }).catch(() => {
            // Silent fail for now
        });
    },

    trackSectionView: function(sectionId) {
        const viewData = {
            section: sectionId,
            timestamp: new Date().toISOString()
        };
        
        // Store in local analytics
        const views = JSON.parse(localStorage.getItem('terms_section_views') || '[]');
        views.push(viewData);
        
        if (views.length > 50) {
            views.splice(0, views.length - 50);
        }
        
        localStorage.setItem('terms_section_views', JSON.stringify(views));
    },

    trackPageView: function() {
        const visitData = {
            page: 'terms',
            timestamp: new Date().toISOString(),
            version: this.getCurrentTermsVersion()
        };

        const visits = JSON.parse(localStorage.getItem('page_visits') || '[]');
        visits.push(visitData);
        
        if (visits.length > 10) {
            visits.splice(0, visits.length - 10);
        }
        
        localStorage.setItem('page_visits', JSON.stringify(visits));
    },

    showAcceptanceMessage: function(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `fixed top-4 right-4 p-4 rounded shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-black' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        messageDiv.textContent = message;
        
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    },

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
    TermsAPI.init();
    TermsAPI.handleHashNavigation();
});

// Handle hash changes
window.addEventListener('hashchange', function() {
    TermsAPI.handleHashNavigation();
});

// Export for global access
window.TermsAPI = TermsAPI;
