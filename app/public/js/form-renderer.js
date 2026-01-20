/**
 * Fieldman Form Renderer
 * Dynamically renders forms from JSONSchema with conditional logic support
 */

class FormRenderer {
    constructor() {
        this.currentSchema = null;
        this.currentUISchema = null;
        this.formData = {};
        this.currentTemplateId = null;
        // Use global CONFIG if available, or fallback
        this.CONFIG = window.CONFIG || {
            API_BASE: 'http://127.0.0.1:8080/api/v1'
        };
    }

    /**
     * Initialize the form renderer with event listeners
     */
    init() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });

        // Bank selection
        document.getElementById('bank-select')?.addEventListener('change', (e) => {
            this.loadTemplatesForBank(e.target.value);
        });

        // Template selection
        document.getElementById('template-select')?.addEventListener('change', (e) => {
            this.showTemplateInfo(e.target.value);
        });

        // Start form button
        document.getElementById('start-form-btn')?.addEventListener('click', () => {
            this.startForm();
        });

        // Demo form button
        document.getElementById('demo-form-btn')?.addEventListener('click', () => {
            this.loadDemoForm();
        });

        // Form actions
        document.getElementById('validate-btn')?.addEventListener('click', () => {
            this.validateForm();
        });

        document.getElementById('save-draft-btn')?.addEventListener('click', () => {
            this.saveDraft();
        });

        document.getElementById('submit-btn')?.addEventListener('click', () => {
            this.submitForm();
        });

        // Load banks on page load
        this.loadBanks();
    }

    /**
     * Switch between tabs
     */
    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(tabName).classList.add('active');
    }

    /**
     * Load banks from API
     */
    async loadBanks() {
        try {
            // Use apiRequest from app.js which handles tokens
            const result = await apiRequest(`${this.CONFIG.API_BASE}/banks`);
            const data = result.data || result; // Handle pagination wrapper or direct list

            const select = document.getElementById('bank-select');

            data.forEach(bank => {
                const option = document.createElement('option');
                option.value = bank.id;
                option.textContent = bank.name;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading banks:', error);
            this.showError('Failed to load banks. Using demo mode.');
        }
    }

    /**
     * Load templates for selected bank
     */
    async loadTemplatesForBank(bankId) {
        const templateSelect = document.getElementById('template-select');
        templateSelect.innerHTML = '<option value="">-- Loading... --</option>';
        templateSelect.disabled = true;

        if (!bankId) {
            templateSelect.innerHTML = '<option value="">-- First select a bank --</option>';
            return;
        }

        try {
            const result = await apiRequest(`${this.CONFIG.API_BASE}/templates/bank/${bankId}`);
            const data = result.data || result;

            templateSelect.innerHTML = '<option value="">-- Select a Form Type --</option>';

            data.forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = `${template.title || template.form_type} (v${template.version})`;
                option.dataset.template = JSON.stringify(template);
                templateSelect.appendChild(option);
            });

            templateSelect.disabled = false;
        } catch (error) {
            console.error('Error loading templates:', error);
            templateSelect.innerHTML = '<option value="">-- Error loading templates --</option>';
        }
    }

    /**
     * Show template information
     */
    showTemplateInfo(templateId) {
        const select = document.getElementById('template-select');
        const option = select.options[select.selectedIndex];
        const startBtn = document.getElementById('start-form-btn');
        const infoBox = document.getElementById('template-info');

        if (!templateId || !option.dataset.template) {
            startBtn.disabled = true;
            infoBox.style.display = 'none';
            return;
        }

        const template = JSON.parse(option.dataset.template);
        document.getElementById('template-title').textContent = `Title: ${template.title || 'N/A'}`;
        document.getElementById('template-description').textContent = `Description: ${template.description || 'N/A'}`;
        document.getElementById('template-version').textContent = `Version: ${template.version}`;

        infoBox.style.display = 'block';
        startBtn.disabled = false;
        this.currentTemplateId = templateId;
    }

    /**
     * Start filling the selected form
     */
    startForm() {
        const select = document.getElementById('template-select');
        const option = select.options[select.selectedIndex];

        if (!option.dataset.template) return;

        const template = JSON.parse(option.dataset.template);
        this.currentSchema = template.json_schema;
        this.currentUISchema = template.ui_schema || {};
        this.currentTemplateId = template.id;
        this.formData = {};

        this.renderForm();
        this.switchTab('fill-form');

        document.getElementById('current-form-title').textContent = template.title || template.form_type;
        document.getElementById('current-form-description').textContent = template.description || '';
    }

    /**
     * Load a demo form for testing
     */
    loadDemoForm() {
        this.currentSchema = {
            "type": "object",
            "title": "Customer Survey Demo",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "minLength": 3,
                    "title": "Customer Name"
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "title": "Email Address"
                },
                "phone": {
                    "type": "string",
                    "pattern": "^\\d{10}$",
                    "title": "Phone Number",
                    "description": "10-digit phone number"
                },
                "satisfaction_rating": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "title": "Satisfaction Rating"
                },
                "has_complaints": {
                    "type": "boolean",
                    "title": "Do you have any complaints?"
                },
                "complaint_details": {
                    "type": "string",
                    "title": "Complaint Details"
                },
                "products": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["Savings Account", "Checking Account", "Loan", "Credit Card"]
                    },
                    "title": "Products Owned"
                }
            },
            "required": ["customer_name", "email", "satisfaction_rating", "has_complaints"],
            "if": {
                "properties": {
                    "has_complaints": { "const": true }
                }
            },
            "then": {
                "required": ["complaint_details"]
            }
        };

        this.currentUISchema = {};
        this.currentTemplateId = null;
        this.formData = {};

        this.renderForm();
        this.switchTab('fill-form');

        document.getElementById('current-form-title').textContent = 'Demo Customer Survey';
        document.getElementById('current-form-description').textContent = 'Test form with conditional logic';
    }

    /**
     * Render the form from JSONSchema
     */
    renderForm() {
        const container = document.getElementById('form-container');
        container.innerHTML = '';

        if (!this.currentSchema) {
            container.innerHTML = '<div class="empty-state"><p>No schema loaded</p></div>';
            return;
        }

        const formElement = this.createFormElement(this.currentSchema, '', this.formData);
        container.appendChild(formElement);

        document.getElementById('form-actions').style.display = 'flex';
        document.getElementById('validation-errors').style.display = 'none';
    }

    /**
     * Create form elements recursively
     */
    createFormElement(schema, path, data) {
        const container = document.createElement('div');

        if (schema.type === 'object') {
            return this.renderObject(schema, path, data);
        } else if (schema.type === 'array') {
            return this.renderArray(schema, path, data);
        } else {
            return this.renderField(schema, path, data);
        }
    }

    /**
     * Render a simple field (wrapper for createInput)
     */
    renderField(schema, path, data) {
        return this.createInput(schema, path, data);
    }

    /**
     * Create an item for an array
     */
    createArrayItem(itemSchema, path, data, index) {
        const wrapper = document.createElement('div');
        wrapper.className = 'array-item';

        const header = document.createElement('div');
        header.className = 'array-item-header';
        header.innerHTML = `<span class="array-item-title">Item ${index + 1}</span>`;

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'remove-item-btn';
        removeBtn.textContent = 'Remove';
        removeBtn.onclick = () => this.removeArrayItem(path, index);
        header.appendChild(removeBtn);

        wrapper.appendChild(header);

        const content = this.createFormElement(itemSchema, path, data);
        wrapper.appendChild(content);

        return wrapper;
    }

    /**
     * Remove item from array
     */
    removeArrayItem(path, index) {
        // Parse path to find parent array and splice
        // Simple implementation: read current data, modify, set back
        const arrayPath = path.substring(0, path.lastIndexOf('['));
        const currentArray = this.getNestedValue(this.formData, arrayPath) || [];

        currentArray.splice(index, 1);
        this.setNestedValue(this.formData, arrayPath, currentArray);
        this.renderForm();
    }

    /**
     * Render an object (nested fields)
     */
    renderObject(schema, path, data) {
        const container = document.createElement('div');
        container.className = path ? 'object-container' : '';

        const properties = schema.properties || {};
        const required = schema.required || [];

        Object.keys(properties).forEach(key => {
            const fieldPath = path ? `${path}.${key}` : key;
            const fieldSchema = properties[key];
            const isRequired = required.includes(key);

            // Check if field should be visible based on conditionals
            if (!this.shouldShowField(schema, key, data)) {
                return;
            }

            const fieldGroup = document.createElement('div');
            fieldGroup.className = 'form-group';
            fieldGroup.dataset.field = key;

            // Create label
            if (fieldSchema.type !== 'boolean') {
                const label = document.createElement('label');
                label.textContent = fieldSchema.title || key;
                if (isRequired) {
                    const req = document.createElement('span');
                    req.className = 'required';
                    req.textContent = '*';
                    label.appendChild(req);
                }
                fieldGroup.appendChild(label);

                // Add description if present
                if (fieldSchema.description) {
                    const desc = document.createElement('small');
                    desc.className = 'field-description';
                    desc.textContent = fieldSchema.description;
                    fieldGroup.appendChild(desc);
                }
            }

            // Create input/element (recursive)
            // Initialize data if undefined for nested types
            let fieldData = data[key];
            if (fieldData === undefined) {
                if (fieldSchema.type === 'object') fieldData = {};
                if (fieldSchema.type === 'array') fieldData = [];
            }

            const input = this.createFormElement(fieldSchema, fieldPath, fieldData);
            fieldGroup.appendChild(input);

            container.appendChild(fieldGroup);
        });

        return container;
    }

    /**
     * Render an array field
     */
    renderArray(schema, path, data) {
        const container = document.createElement('div');
        container.className = 'array-container';

        const items = Array.isArray(data) ? data : [];

        items.forEach((item, index) => {
            const itemDiv = this.createArrayItem(schema.items, `${path}[${index}]`, item, index);
            container.appendChild(itemDiv);
        });

        const addBtn = document.createElement('button');
        addBtn.type = 'button';
        addBtn.className = 'add-item-btn';
        addBtn.textContent = '+ Add Item';
        addBtn.onclick = () => this.addArrayItem(path);
        container.appendChild(addBtn);

        return container;
    }

    /**
     * Create input field based on schema type
     */
    createInput(schema, path, value) {
        const type = schema.type;
        let input;

        if (schema.enum) {
            // Dropdown for enum
            input = document.createElement('select');
            input.className = 'form-control';

            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = '-- Select --';
            input.appendChild(emptyOption);

            schema.enum.forEach(option => {
                const opt = document.createElement('option');
                opt.value = option;
                opt.textContent = option;
                input.appendChild(opt);
            });

            if (value) input.value = value;
        } else if (type === 'boolean') {
            const wrapper = document.createElement('div');
            input = document.createElement('input');
            input.type = 'checkbox';
            input.id = `field-${path}`;
            input.checked = value || false;

            const label = document.createElement('label');
            label.htmlFor = input.id;
            label.textContent = schema.title || path.split('.').pop();

            wrapper.appendChild(input);
            wrapper.appendChild(label);
            return wrapper;
        } else if (type === 'integer' || type === 'number') {
            input = document.createElement('input');
            input.type = 'number';
            input.className = 'form-control';
            if (schema.minimum !== undefined) input.min = schema.minimum;
            if (schema.maximum !== undefined) input.max = schema.maximum;
            if (value !== undefined) input.value = value;
        } else if (schema.format === 'date') {
            input = document.createElement('input');
            input.type = 'date';
            input.className = 'form-control';
            if (value) input.value = value;
        } else if (schema.format === 'email') {
            input = document.createElement('input');
            input.type = 'email';
            input.className = 'form-control';
            if (value) input.value = value;
        } else if (schema.maxLength && schema.maxLength > 100) {
            input = document.createElement('textarea');
            input.className = 'form-control';
            if (value) input.value = value;
        } else {
            // Default text input
            input = document.createElement('input');
            input.type = 'text';
            input.className = 'form-control';
            if (value) input.value = value;
        }

        input.dataset.path = path;
        input.addEventListener('change', (e) => this.updateFormData(e));
        input.addEventListener('input', (e) => this.updateFormData(e));

        return input;
    }

    /**
     * Update form data when field changes
     */
    updateFormData(event) {
        const path = event.target.dataset.path;
        let value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;

        // Convert to number if needed
        if (event.target.type === 'number' && value !== '') {
            value = parseFloat(value);
        }

        this.setNestedValue(this.formData, path, value);

        // Re-render to handle conditional logic
        this.renderForm();
    }

    /**
     * Check if field should be shown based on conditional logic
     */
    shouldShowField(schema, fieldName, data) {
        if (!schema.if) return true;

        // Simple conditional check
        const condition = schema.if;
        if (condition.properties) {
            for (const [key, value] of Object.entries(condition.properties)) {
                if (value.const !== undefined) {
                    if (data[key] !== value.const) {
                        // Check if field is in 'else' block
                        if (schema.else && schema.else.properties && schema.else.properties[fieldName]) {
                            return true;
                        }
                        if (schema.then && schema.then.properties && schema.then.properties[fieldName]) {
                            return false;
                        }
                    } else {
                        // Condition is true, show 'then' fields
                        if (schema.then && schema.then.properties && schema.then.properties[fieldName]) {
                            return true;
                        }
                    }
                }
            }
        }

        return true;
    }

    /**
     * Validate form
     */
    async validateForm() {
        const errorsDiv = document.getElementById('validation-errors');
        errorsDiv.innerHTML = '';
        errorsDiv.style.display = 'none';

        // Clear previous errors
        document.querySelectorAll('.has-error').forEach(el => el.classList.remove('has-error'));
        document.querySelectorAll('.field-error').forEach(el => el.remove());

        try {
            const result = await apiRequest(`${this.CONFIG.API_BASE}/submissions/validate`, {
                method: 'POST',
                body: JSON.stringify({
                    template_id: this.currentTemplateId,
                    submission_data: this.formData
                })
            });

            if (result.is_valid) {
                this.showSuccess('✅ Form is valid!');
            } else {
                this.showValidationErrors(result.errors);
            }
        } catch (error) {
            console.error('Validation error:', error);
            this.showError('Failed to validate form');
        }
    }

    /**
     * Show validation errors
     */
    showValidationErrors(errors) {
        const errorsDiv = document.getElementById('validation-errors');
        errorsDiv.innerHTML = '<h4>Validation Errors:</h4>';

        errors.forEach(error => {
            const errorItem = document.createElement('div');
            errorItem.className = 'error-item';
            errorItem.innerHTML = `<span class="error-field">${error.field}:</span> ${error.message}`;
            errorsDiv.appendChild(errorItem);

            // Highlight field with error
            const input = document.querySelector(`[data-path="${error.field}"]`);
            if (input) {
                input.classList.add('has-error');
                const errorMsg = document.createElement('span');
                errorMsg.className = 'field-error';
                errorMsg.textContent = error.message;
                input.parentElement.appendChild(errorMsg);
            }
        });

        errorsDiv.style.display = 'block';
    }

    /**
     * Helper to set nested value in object
     */
    setNestedValue(obj, path, value) {
        const keys = path.split(/[\.\[\]]/).filter(k => k);
        let current = obj;

        for (let i = 0; i < keys.length - 1; i++) {
            if (!current[keys[i]]) {
                current[keys[i]] = isNaN(keys[i + 1]) ? {} : [];
            }
            current = current[keys[i]];
        }

        current[keys[keys.length - 1]] = value;
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        const container = document.getElementById('form-container');
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.textContent = message;
        container.insertBefore(successDiv, container.firstChild);

        setTimeout(() => successDiv.remove(), 3000);
    }

    /**
     * Show error message
     */
    showError(message) {
        alert(message);
    }

    /**
     * Save draft
     */
    async saveDraft() {
        console.log('Saving draft:', this.formData);
        this.showSuccess('Draft saved! (Not yet implemented)');
    }

    /**
     * Submit form
     */
    async submitForm() {
        console.log('Submitting form:', this.formData);
        this.showSuccess('Form submitted! (Not yet implemented)');
    }

    /**
     * Add array item
     */
    addArrayItem(path) {
        const current = this.getNestedValue(this.formData, path) || [];
        current.push({});
        this.setNestedValue(this.formData, path, current);
        this.renderForm();
    }

    /**
     * Get nested value from object
     */
    getNestedValue(obj, path) {
        const keys = path.split(/[\.\[\]]/).filter(k => k);
        let current = obj;

        for (const key of keys) {
            if (current === undefined || current === null) return undefined;
            current = current[key];
        }

        return current;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const renderer = new FormRenderer();
    renderer.init();
});
