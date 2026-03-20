/**
 * Floating Label JavaScript Support
 * Handles edge cases and enhanced functionality for floating labels
 */

document.addEventListener('DOMContentLoaded', function() {
    // Select all floating groups
    const floatingGroups = document.querySelectorAll('.floating-group');
    
    floatingGroups.forEach(group => {
        const input = group.querySelector('.input-field');
        if (!input) return;
        
        // Initialize state on load
        checkAndUpdateLabel(input);
        
        // Update on input event
        input.addEventListener('input', function() {
            checkAndUpdateLabel(this);
        });
        
        // Update on change (for selects)
        input.addEventListener('change', function() {
            checkAndUpdateLabel(this);
        });
        
        // Update on focus
        input.addEventListener('focus', function() {
            checkAndUpdateLabel(this);
        });
        
        // Update on blur
        input.addEventListener('blur', function() {
            checkAndUpdateLabel(this);
        });
    });
    
    /**
     * Check if input has value and update label accordingly
     */
    function checkAndUpdateLabel(input) {
        const group = input.closest('.floating-group');
        if (!group) return;
        
        const hasValue = input.value.trim() !== '';
        const label = group.querySelector('label');
        
        if (hasValue) {
            input.style.paddingTop = '14px';
            input.style.paddingBottom = '10px';
        } else if (!input.matches(':focus')) {
            input.style.paddingTop = '12px';
            input.style.paddingBottom = '12px';
        }
    }
    
    /**
     * Form validation with error states
     */
    window.updateFloatingLabelState = function(inputId, state = null) {
        const input = document.getElementById(inputId);
        if (!input) return;
        
        const group = input.closest('.floating-group');
        if (!group) return;
        
        // Remove existing state classes
        group.classList.remove('has-error', 'has-success');
        
        if (state === 'error') {
            group.classList.add('has-error');
        } else if (state === 'success') {
            group.classList.add('has-success');
        }
    };
    
    /**
     * Validate required fields
     */
    window.validateFloatingLabels = function(formId) {
        const form = document.getElementById(formId);
        if (!form) return true;
        
        let isValid = true;
        const inputs = form.querySelectorAll('.floating-group .input-field[required]');
        
        inputs.forEach(input => {
            const group = input.closest('.floating-group');
            if (!group) return;
            
            const isEmpty = input.value.trim() === '';
            const isInvalid = input.invalid;
            
            if (isEmpty || isInvalid) {
                group.classList.add('has-error');
                isValid = false;
            } else {
                group.classList.remove('has-error');
            }
        });
        
        return isValid;
    };
});

/**
 * Initialize floating labels on dynamically added content
 */
window.initFloatingLabels = function(container = document) {
    const floatingGroups = container.querySelectorAll('.floating-group');
    
    floatingGroups.forEach(group => {
        const input = group.querySelector('.input-field');
        if (!input || input.dataset.initialized) return;
        
        input.dataset.initialized = 'true';
        
        input.addEventListener('input', function() {
            checkAndUpdateLabel(this);
        });
        
        input.addEventListener('change', function() {
            checkAndUpdateLabel(this);
        });
    });
    
    function checkAndUpdateLabel(input) {
        const group = input.closest('.floating-group');
        if (!group) return;
        
        const hasValue = input.value.trim() !== '';
        if (hasValue) {
            input.style.paddingTop = '14px';
            input.style.paddingBottom = '10px';
        } else if (!input.matches(':focus')) {
            input.style.paddingTop = '12px';
            input.style.paddingBottom = '12px';
        }
    }
};
