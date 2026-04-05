/* =====================================================
   Smart Agricultural Loan System - Custom JavaScript
   Animations, Interactions & Utilities
   ===================================================== */

document.addEventListener('DOMContentLoaded', function() {
    initAnimations();
    initNavbar();
    initFileUpload();
    initFormValidation();
    initTooltips();
    initToast();
    initDarkMode();
});

/* --------------------------------------------------
   Animations on Scroll (AOS-like)
   -------------------------------------------------- */
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('[data-animate]').forEach(el => {
        observer.observe(el);
    });
}

/* Add animation classes */
document.querySelectorAll('.feature-card, .stat-card, .card-custom').forEach(el => {
    el.setAttribute('data-animate', 'fade-in-up');
});

/* --------------------------------------------------
   Navbar Effects
   -------------------------------------------------- */
function initNavbar() {
    const navbar = document.querySelector('.navbar-custom');
    if (!navbar) return;

    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.classList.add('navbar-scrolled');
            navbar.style.padding = '10px 0';
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.15)';
        } else {
            navbar.classList.remove('navbar-scrolled');
            navbar.style.padding = '16px 0';
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.12)';
        }
        
        lastScroll = currentScroll;
    });

    // Active link highlighting
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

/* --------------------------------------------------
   File Upload Enhancement
   -------------------------------------------------- */
function initFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const wrapper = input.closest('.file-upload-wrapper');
        if (wrapper) {
            setupFileUpload(wrapper, input);
        }
    });
}

function setupFileUpload(wrapper, input) {
    const fileName = wrapper.querySelector('.file-name');
    const fileSize = wrapper.querySelector('.file-size');
    const preview = wrapper.querySelector('.preview-area');
    
    input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        // Update file info
        if (fileName) {
            fileName.textContent = file.name;
        }
        if (fileSize) {
            fileSize.textContent = formatFileSize(file.size);
        }
        
        // Show preview for images
        if (file.type.startsWith('image/') && preview) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.innerHTML = `<img src="${e.target.result}" alt="Preview" class="img-thumbnail" style="max-width: 200px; max-height: 200px;">`;
            };
            reader.readAsDataURL(file);
        }
        
        // Add success class
        wrapper.classList.add('file-selected');
        wrapper.querySelector('.upload-icon').innerHTML = '<i class="bi bi-check-circle-fill text-success"></i>';
    });
    
    // Drag and drop
    wrapper.addEventListener('dragover', function(e) {
        e.preventDefault();
        wrapper.classList.add('drag-over');
    });
    
    wrapper.addEventListener('dragleave', function() {
        wrapper.classList.remove('drag-over');
    });
    
    wrapper.addEventListener('drop', function(e) {
        e.preventDefault();
        wrapper.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            input.dispatchEvent(new Event('change'));
        }
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/* --------------------------------------------------
   Form Validation
   -------------------------------------------------- */
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Real-time validation
    document.querySelectorAll('.form-control-custom').forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    
    // Required check
    if (field.hasAttribute('required') && !value) {
        isValid = false;
    }
    
    // Email validation
    if (field.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        isValid = emailRegex.test(value);
    }
    
    // Number validation
    if (field.type === 'number') {
        const min = field.getAttribute('min');
        const max = field.getAttribute('max');
        
        if (min && parseFloat(value) < parseFloat(min)) isValid = false;
        if (max && parseFloat(value) > parseFloat(max)) isValid = false;
    }
    
    // Password validation
    if (field.name === 'password1' && value) {
        isValid = value.length >= 8;
    }
    
    // Update UI
    if (isValid && value) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else if (!isValid) {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
    } else {
        field.classList.remove('is-invalid', 'is-valid');
    }
    
    return isValid;
}

/* --------------------------------------------------
   Password Strength
   -------------------------------------------------- */
function checkPasswordStrength(password) {
    let strength = 0;
    let feedback = '';
    
    if (password.length >= 8) strength += 1;
    if (password.match(/[a-z]/)) strength += 1;
    if (password.match(/[A-Z]/)) strength += 1;
    if (password.match(/[0-9]/)) strength += 1;
    if (password.match(/[^a-zA-Z0-9]/)) strength += 1;
    
    switch(strength) {
        case 0:
        case 1:
            feedback = 'Weak';
            break;
        case 2:
            feedback = 'Fair';
            break;
        case 3:
        case 4:
            feedback = 'Good';
            break;
        case 5:
            feedback = 'Strong';
            break;
    }
    
    return { strength, feedback };
}

/* --------------------------------------------------
   Tooltips
   -------------------------------------------------- */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/* --------------------------------------------------
   Toast Notifications
   -------------------------------------------------- */
function initToast() {
    window.showToast = function(message, type = 'info') {
        const wrapper = document.querySelector('.toast-wrapper');
        if (!wrapper) return;
        
        const icons = {
            success: 'bi-check-circle-fill',
            error: 'bi-x-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast-custom toast-${type}`;
        toast.innerHTML = `
            <i class="toast-icon bi ${icons[type]}"></i>
            <div class="toast-content">${message}</div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="bi bi-x"></i>
            </button>
        `;
        
        wrapper.appendChild(toast);
        
        // Auto remove
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    };
}

/* --------------------------------------------------
   Loading Spinner
   -------------------------------------------------- */
function showLoader() {
    const wrapper = document.querySelector('.spinner-wrapper');
    if (wrapper) {
        wrapper.classList.add('active');
    }
}

function hideLoader() {
    const wrapper = document.querySelector('.spinner-wrapper');
    if (wrapper) {
        wrapper.classList.remove('active');
    }
}

// Auto-show loader on form submit
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        }
        showLoader();
    });
});

/* --------------------------------------------------
   Dark Mode Toggle
   -------------------------------------------------- */
function initDarkMode() {
    const toggle = document.querySelector('.dark-mode-toggle');
    if (!toggle) return;
    
    // Check for saved preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        toggle.checked = true;
    }
    
    toggle.addEventListener('change', function() {
        if (this.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('theme', 'light');
        }
    });
}

/* --------------------------------------------------
   Smooth Scroll
   -------------------------------------------------- */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            e.preventDefault();
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

/* --------------------------------------------------
   Number Counter Animation
   -------------------------------------------------- */
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Ease out
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(start + (target - start) * easeOut);
        
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Trigger counter animation when visible
const counters = document.querySelectorAll('[data-counter]');
if (counters.length > 0) {
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = parseInt(entry.target.getAttribute('data-counter'));
                animateCounter(entry.target, target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    counters.forEach(counter => counterObserver.observe(counter));
}

/* --------------------------------------------------
   EMI Calculator
   -------------------------------------------------- */
function calculateEMI(amount, rate, months) {
    if (amount <= 0 || months <= 0) return 0;
    
    if (rate === 0) {
        return amount / months;
    }
    
    const monthlyRate = rate / 100 / 12;
    const emi = amount * monthlyRate * Math.pow(1 + monthlyRate, months) / (Math.pow(1 + monthlyRate, months) - 1);
    return emi;
}

/* --------------------------------------------------
   Dynamic NID Status Alert
   -------------------------------------------------- */
function updateNIDStatusAlert(elementId, status) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const statusConfig = {
        verified: {
            class: 'alert-success',
            icon: 'bi-check-circle',
            text: 'Verified'
        },
        pending: {
            class: 'alert-warning',
            icon: 'bi-clock-history',
            text: 'Pending Verification'
        },
        not_uploaded: {
            class: 'alert-danger',
            icon: 'bi-exclamation-triangle',
            text: 'Not Uploaded'
        }
    };
    
    const config = statusConfig[status] || statusConfig.not_uploaded;
    element.className = `alert ${config.class} alert-custom`;
    element.innerHTML = `
        <i class="bi ${config.icon} me-2"></i>
        ${config.text}
    `;
}

/* --------------------------------------------------
   Search Highlight
   -------------------------------------------------- */
function highlightSearchTerms(terms) {
    if (!terms) return;
    
    const regex = new RegExp(terms, 'gi');
    document.querySelectorAll('.searchable').forEach(element => {
        element.innerHTML = element.textContent.replace(regex, match => 
            `<mark class="bg-warning">${match}</mark>`
        );
    });
}

/* --------------------------------------------------
   Table Sort
   -------------------------------------------------- */
function initTableSort() {
    document.querySelectorAll('.table-sortable thead th').forEach(th => {
        th.addEventListener('click', function() {
            const table = this.closest('table');
            const index = Array.from(this.parentNode.children).indexOf(this);
            const isAsc = this.classList.contains('asc');
            
            // Toggle sort classes
            table.querySelectorAll('th').forEach(h => {
                h.classList.remove('asc', 'desc');
            });
            this.classList.add(isAsc ? 'desc' : 'asc');
            
            // Sort rows
            const rows = Array.from(table.tBodies[0].rows);
            rows.sort((a, b) => {
                const aVal = a.cells[index].textContent.trim();
                const bVal = b.cells[index].textContent.trim();
                
                if (isAsc) {
                    return aVal.localeCompare(bVal, undefined, { numeric: true });
                } else {
                    return bVal.localeCompare(aVal, undefined, { numeric: true });
                }
            });
            
            rows.forEach(row => table.tBodies[0].appendChild(row));
        });
    });
}

/* --------------------------------------------------
   Mobile Menu Toggle
   -------------------------------------------------- */
function initMobileMenu() {
    const toggler = document.querySelector('.navbar-toggler');
    const menu = document.querySelector('.navbar-collapse');
    
    if (toggler && menu) {
        toggler.addEventListener('click', function() {
            menu.classList.toggle('show');
        });
        
        // Close on click outside
        document.addEventListener('click', function(e) {
            if (!toggler.contains(e.target) && !menu.contains(e.target)) {
                menu.classList.remove('show');
            }
        });
    }
}

/* --------------------------------------------------
   Responsive Image Handling
   -------------------------------------------------- */
function initResponsiveImages() {
    document.querySelectorAll('img[data-src]').forEach(img => {
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
    });
    
    // Lazy load
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    imageObserver.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

/* --------------------------------------------------
   Keyboard Navigation
   -------------------------------------------------- */
document.addEventListener('keydown', function(e) {
    // ESC to close modals
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.show').forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        });
    }
    
    // Ctrl+/ to focus search
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        const search = document.querySelector('input[type="search"], input[name="q"], input[name="search"]');
        if (search) search.focus();
    }
});

/* --------------------------------------------------
   Print Styles
   -------------------------------------------------- */
window.addEventListener('beforeprint', function() {
    document.body.classList.add('printing');
});

window.addEventListener('afterprint', function() {
    document.body.classList.remove('printing');
});

/* --------------------------------------------------
   Utility Functions
   -------------------------------------------------- */
window.utils = {
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    throttle: function(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    formatCurrency: function(amount, currency = 'BDT') {
        return new Intl.NumberFormat('en-BD', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        }).format(amount);
    },
    
    formatDate: function(date, format = 'medium') {
        const d = new Date(date);
        const options = {
            short: { year: 'numeric', month: 'short', day: 'numeric' },
            medium: { year: 'numeric', month: 'long', day: 'numeric' },
            long: { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
        };
        return d.toLocaleDateString('en-BD', options[format] || options.medium);
    }
};
