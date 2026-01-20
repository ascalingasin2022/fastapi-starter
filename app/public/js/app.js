// Configuration
const CONFIG = {
    API_BASE: 'http://127.0.0.1:8080/api/v1',
    TIMEOUT: 30000, // 30 seconds
    RETRY_ATTEMPTS: 1
};

// Utility functions
function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
    updateAuthStatus();
}

function clearToken() {
    localStorage.removeItem('token');
    updateAuthStatus();
}

function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '1000';
    alertDiv.style.maxWidth = '300px';

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

function updateAuthStatus() {
    const token = getToken();
    const tokenDisplay = document.getElementById('token-display');
    const logoutBtn = document.getElementById('logout-btn');

    if (token) {
        tokenDisplay.textContent = 'Logged in';
        logoutBtn.style.display = 'inline';
    } else {
        tokenDisplay.textContent = 'Not logged in';
        logoutBtn.style.display = 'none';
    }
}

// Enhanced API request with timeout and better error handling
async function apiRequest(url, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CONFIG.TIMEOUT);

    try {
        const response = await fetch(url, {
            ...options,
            headers,
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        // Handle different response statuses
        if (!response.ok) {
            let errorMessage;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}`;
            } catch {
                errorMessage = await response.text() || `HTTP ${response.status}`;
            }

            // Handle specific status codes
            if (response.status === 401) {
                clearToken();
                throw new Error('Authentication required. Please log in again.');
            } else if (response.status === 403) {
                throw new Error('Access denied. You do not have permission for this action.');
            } else if (response.status === 404) {
                throw new Error('Resource not found.');
            } else if (response.status >= 500) {
                throw new Error(`Server error: ${errorMessage}`);
            } else {
                throw new Error(errorMessage);
            }
        }

        // Handle empty responses
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return { success: true };
        }
    } catch (error) {
        clearTimeout(timeoutId);

        // Handle network errors
        if (error.name === 'AbortError') {
            throw new Error('Request timeout. Please check your connection and try again.');
        } else if (error instanceof TypeError && error.message.includes('fetch')) {
            throw new Error('Network error. Unable to connect to server. Please ensure the backend is running.');
        } else {
            throw error;
        }
    }
}

// Button state management helper
function setButtonLoading(button, loading) {
    if (loading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.textContent = 'Loading...';
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || button.textContent;
    }
}

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        btn.classList.add('active');
        document.getElementById(btn.dataset.tab).classList.add('active');
    });
});

// Logout
document.getElementById('logout-btn').addEventListener('click', clearToken);

// Auth functions
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        username: document.getElementById('reg-username').value,
        email: document.getElementById('reg-email').value,
        password: document.getElementById('reg-password').value,
        first_name: document.getElementById('reg-first-name').value || null,
        last_name: document.getElementById('reg-last-name').value || null,
        department: document.getElementById('reg-department').value || null,
        level: parseInt(document.getElementById('reg-level').value) || 1,
        location: document.getElementById('reg-location').value || null
    };

    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/auth/register`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        showAlert('Registration successful!');
        console.log(result);
    } catch (error) {
        showAlert('Registration failed: ' + error.message, 'error');
    }
});

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('username', document.getElementById('login-username').value);
    formData.append('password', document.getElementById('login-password').value);

    try {
        const result = await fetch(`${CONFIG.API_BASE}/auth/login`, {
            method: 'POST',
            body: formData
        });

        if (!result.ok) {
            throw new Error(`HTTP ${result.status}: ${await result.text()}`);
        }

        const data = await result.json();
        setToken(data.access_token);
        showAlert('Login successful!');
    } catch (error) {
        showAlert('Login failed: ' + error.message, 'error');
    }
});

// Users functions
document.getElementById('get-users-btn').addEventListener('click', async () => {
    const btn = document.getElementById('get-users-btn');
    setButtonLoading(btn, true);
    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/users/`);
        const users = result.data || [];
        const container = document.getElementById('users-list');
        if (users.length === 0) {
            container.innerHTML = '<p>No users found.</p>';
            return;
        }

        let tableHtml = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Full Name</th>
                        <th>Department</th>
                        <th>Level</th>
                        <th>Active</th>
                        <th>Superuser</th>
                    </tr>
                </thead>
                <tbody>
        `;

        users.forEach(user => {
            tableHtml += `
                <tr>
                    <td>${user.id}</td>
                    <td>${user.username}</td>
                    <td>${user.email}</td>
                    <td>${user.full_name || ''}</td>
                    <td>${user.department || ''}</td>
                    <td>${user.level || ''}</td>
                    <td><span class="status-${user.is_active ? 'success' : 'error'}">${user.is_active ? 'Yes' : 'No'}</span></td>
                    <td><span class="status-${user.is_superuser ? 'success' : 'error'}">${user.is_superuser ? 'Yes' : 'No'}</span></td>
                </tr>
            `;
        });

        tableHtml += '</tbody></table>';
        container.innerHTML = tableHtml;
    } catch (error) {
        document.getElementById('users-list').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    } finally {
        setButtonLoading(btn, false);
    }
});

document.getElementById('get-user-by-email-btn').addEventListener('click', async () => {
    const email = document.getElementById('user-email').value;
    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/users/by-email?email=${encodeURIComponent(email)}`);
        const user = result.data;
        const container = document.getElementById('user-by-email');

        if (!user) {
            container.innerHTML = '<p>User not found.</p>';
            return;
        }

        container.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Full Name</th>
                        <th>Department</th>
                        <th>Level</th>
                        <th>Location</th>
                        <th>Active</th>
                        <th>Superuser</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>${user.id}</td>
                        <td>${user.username}</td>
                        <td>${user.email}</td>
                        <td>${user.full_name || ''}</td>
                        <td>${user.department || ''}</td>
                        <td>${user.level || ''}</td>
                        <td>${user.location || ''}</td>
                        <td><span class="status-${user.is_active ? 'success' : 'error'}">${user.is_active ? 'Yes' : 'No'}</span></td>
                        <td><span class="status-${user.is_superuser ? 'success' : 'error'}">${user.is_superuser ? 'Yes' : 'No'}</span></td>
                    </tr>
                </tbody>
            </table>
        `;
    } catch (error) {
        document.getElementById('user-by-email').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
});

document.getElementById('get-user-by-id-btn').addEventListener('click', async () => {
    const id = document.getElementById('user-id').value;
    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/users/${id}`);
        const user = result.data;
        const container = document.getElementById('user-by-id');

        if (!user) {
            container.innerHTML = '<p>User not found.</p>';
            return;
        }

        container.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Full Name</th>
                        <th>Department</th>
                        <th>Level</th>
                        <th>Location</th>
                        <th>Active</th>
                        <th>Superuser</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>${user.id}</td>
                        <td>${user.username}</td>
                        <td>${user.email}</td>
                        <td>${user.full_name || ''}</td>
                        <td>${user.department || ''}</td>
                        <td>${user.level || ''}</td>
                        <td>${user.location || ''}</td>
                        <td><span class="status-${user.is_active ? 'success' : 'error'}">${user.is_active ? 'Yes' : 'No'}</span></td>
                        <td><span class="status-${user.is_superuser ? 'success' : 'error'}">${user.is_superuser ? 'Yes' : 'No'}</span></td>
                    </tr>
                </tbody>
            </table>
        `;
    } catch (error) {
        document.getElementById('user-by-id').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
});

document.getElementById('delete-user-btn').addEventListener('click', async () => {
    const id = document.getElementById('delete-user-id').value;
    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/users/${id}`, { method: 'DELETE' });
        document.getElementById('delete-result').innerHTML = '<pre>' + JSON.stringify(result.data, null, 2) + '</pre>';
    } catch (error) {
        document.getElementById('delete-result').textContent = 'Error: ' + error.message;
    }
});

// RBAC functions
document.getElementById('assign-role-btn').addEventListener('click', async () => {
    const data = {
        username: document.getElementById('assign-username').value,
        role: document.getElementById('assign-role').value
    };
    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/rbac/roles/assign`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        showAlert(result.message);
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
});

document.getElementById('revoke-role-btn').addEventListener('click', async () => {
    const data = {
        username: document.getElementById('revoke-username').value,
        role: document.getElementById('revoke-role').value
    };
    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/rbac/roles/revoke`, {
            method: 'DELETE',
            body: JSON.stringify(data)
        });
        showAlert(result.message);
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
});

document.getElementById('get-user-roles-btn').addEventListener('click', async () => {
    const username = document.getElementById('user-roles-username').value;
    try {
        const roles = await apiRequest(`${CONFIG.API_BASE}/rbac/roles/user/${username}`);
        const container = document.getElementById('user-roles-list');

        if (roles.length === 0) {
            container.innerHTML = '<p>No roles assigned.</p>';
            return;
        }

        let tableHtml = `
            <table>
                <thead>
                    <tr>
                        <th>Role</th>
                    </tr>
                </thead>
                <tbody>
        `;

        roles.forEach(role => {
            tableHtml += `<tr><td>${role}</td></tr>`;
        });

        tableHtml += '</tbody></table>';
        container.innerHTML = tableHtml;
    } catch (error) {
        document.getElementById('user-roles-list').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
});

document.getElementById('get-role-users-btn').addEventListener('click', async () => {
    const role = document.getElementById('role-users-role').value;
    try {
        const users = await apiRequest(`${CONFIG.API_BASE}/rbac/roles/${role}/users`);
        const container = document.getElementById('role-users-list');

        if (users.length === 0) {
            container.innerHTML = '<p>No users have this role.</p>';
            return;
        }

        let tableHtml = `
            <table>
                <thead>
                    <tr>
                        <th>Username</th>
                    </tr>
                </thead>
                <tbody>
        `;

        users.forEach(username => {
            tableHtml += `<tr><td>${username}</td></tr>`;
        });

        tableHtml += '</tbody></table>';
        container.innerHTML = tableHtml;
    } catch (error) {
        document.getElementById('role-users-list').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
});

document.getElementById('assign-perm-btn').addEventListener('click', async () => {
    const data = {
        role: document.getElementById('perm-role').value,
        resource: document.getElementById('perm-resource').value,
        action: document.getElementById('perm-action').value
    };
    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/rbac/permissions/assign`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        showAlert(result.message);
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
});

document.getElementById('revoke-perm-btn').addEventListener('click', async () => {
    const data = {
        role: document.getElementById('revoke-perm-role').value,
        resource: document.getElementById('revoke-perm-resource').value,
        action: document.getElementById('revoke-perm-action').value
    };
    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/rbac/permissions/revoke`, {
            method: 'DELETE',
            body: JSON.stringify(data)
        });
        showAlert(result.message);
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
});

document.getElementById('get-role-perm-btn').addEventListener('click', async () => {
    const role = document.getElementById('role-perm-role').value;
    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/rbac/permissions/role/${role}`);
        const permissions = result.permissions || [];
        const container = document.getElementById('role-perm-list');

        if (permissions.length === 0) {
            container.innerHTML = '<p>No permissions assigned to this role.</p>';
            return;
        }

        let tableHtml = `
            <table>
                <thead>
                    <tr>
                        <th>Role</th>
                        <th>Resource</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
        `;

        permissions.forEach(perm => {
            tableHtml += `
                <tr>
                    <td>${perm[0]}</td>
                    <td>${perm[1]}</td>
                    <td>${perm[2]}</td>
                </tr>
            `;
        });

        tableHtml += '</tbody></table>';
        container.innerHTML = tableHtml;
    } catch (error) {
        document.getElementById('role-perm-list').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
});

document.getElementById('check-perm-btn').addEventListener('click', async () => {
    const data = {
        username: document.getElementById('check-username').value,
        resource: document.getElementById('check-resource').value,
        action: document.getElementById('check-action').value
    };
    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/rbac/check-permission`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        const container = document.getElementById('check-result');
        container.innerHTML = `
            <table>
                <tbody>
                    <tr>
                        <td><strong>Username:</strong></td>
                        <td>${result.username}</td>
                    </tr>
                    <tr>
                        <td><strong>Resource:</strong></td>
                        <td>${result.resource}</td>
                    </tr>
                    <tr>
                        <td><strong>Action:</strong></td>
                        <td>${result.action}</td>
                    </tr>
                    <tr>
                        <td><strong>Has Permission:</strong></td>
                        <td><span class="status-${result.has_permission ? 'success' : 'error'}">${result.has_permission ? 'Yes' : 'No'}</span></td>
                    </tr>
                </tbody>
            </table>
        `;
    } catch (error) {
        document.getElementById('check-result').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
});

// ABAC functions
document.getElementById('list-policies-btn').addEventListener('click', async () => {
    try {
        const policies = await apiRequest(`${CONFIG.API_BASE}/abac/policies`);
        const container = document.getElementById('policies-list');

        if (policies.length === 0) {
            container.innerHTML = '<p>No ABAC policies found.</p>';
            return;
        }

        let tableHtml = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Description</th>
                        <th>Active</th>
                    </tr>
                </thead>
                <tbody>
        `;

        policies.forEach(policy => {
            tableHtml += `
                <tr>
                    <td>${policy.id}</td>
                    <td>${policy.name}</td>
                    <td>${policy.description || ''}</td>
                    <td><span class="status-${policy.is_active ? 'success' : 'error'}">${policy.is_active ? 'Yes' : 'No'}</span></td>
                </tr>
            `;
        });

        tableHtml += '</tbody></table>';
        container.innerHTML = tableHtml;
    } catch (error) {
        document.getElementById('policies-list').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
});

document.getElementById('create-policy-btn').addEventListener('click', async () => {
    let rules;
    try {
        rules = JSON.parse(document.getElementById('policy-rules').value);
    } catch (e) {
        showAlert('Invalid JSON in rules', 'error');
        return;
    }

    const data = {
        name: document.getElementById('policy-name').value,
        description: document.getElementById('policy-description').value,
        rules: rules,
        is_active: true
    };

    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/abac/policies`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        showAlert('Policy created!');
        console.log(result);
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
});

document.getElementById('set-user-attr-btn').addEventListener('click', async () => {
    const data = {
        user_id: parseInt(document.getElementById('user-attr-user-id').value),
        attribute_key: document.getElementById('user-attr-key').value,
        attribute_value: document.getElementById('user-attr-value').value
    };

    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/abac/attributes/user`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        showAlert('Attribute set!');
        console.log(result);
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
});

document.getElementById('get-user-attr-btn').addEventListener('click', async () => {
    const userId = document.getElementById('get-user-attr-id').value;
    try {
        const attributes = await apiRequest(`${CONFIG.API_BASE}/abac/attributes/user/${userId}`);
        const container = document.getElementById('user-attr-list');

        if (attributes.length === 0) {
            container.innerHTML = '<p>No attributes found for this user.</p>';
            return;
        }

        let tableHtml = `
            <table>
                <thead>
                    <tr>
                        <th>Attribute Key</th>
                        <th>Attribute Value</th>
                    </tr>
                </thead>
                <tbody>
        `;

        attributes.forEach(attr => {
            tableHtml += `
                <tr>
                    <td>${attr.attribute_key}</td>
                    <td>${attr.attribute_value}</td>
                </tr>
            `;
        });

        tableHtml += '</tbody></table>';
        container.innerHTML = tableHtml;
    } catch (error) {
        document.getElementById('user-attr-list').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
});

document.getElementById('check-abac-btn').addEventListener('click', async () => {
    const data = {
        username: document.getElementById('abac-check-username').value,
        resource: document.getElementById('abac-check-resource').value,
        action: document.getElementById('abac-check-action').value,
        resource_type: document.getElementById('abac-resource-type').value || null,
        resource_id: document.getElementById('abac-resource-id').value || null
    };

    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/abac/check`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        const container = document.getElementById('abac-check-result');
        container.innerHTML = `
            <table>
                <tbody>
                    <tr>
                        <td><strong>Username:</strong></td>
                        <td>${result.username}</td>
                    </tr>
                    <tr>
                        <td><strong>Resource:</strong></td>
                        <td>${result.resource}</td>
                    </tr>
                    <tr>
                        <td><strong>Action:</strong></td>
                        <td>${result.action}</td>
                    </tr>
                    <tr>
                        <td><strong>Has Permission:</strong></td>
                        <td><span class="status-${result.has_permission ? 'success' : 'error'}">${result.has_permission ? 'Yes' : 'No'}</span></td>
                    </tr>
                    <tr>
                        <td><strong>Matched Policies:</strong></td>
                        <td>${result.matched_policies.join(', ') || 'None'}</td>
                    </tr>
                    <tr>
                        <td><strong>Reason:</strong></td>
                        <td>${result.reason}</td>
                    </tr>
                </tbody>
            </table>
        `;
    } catch (error) {
        document.getElementById('abac-check-result').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
});

// ReBAC functions
document.getElementById('list-relationships-btn').addEventListener('click', async () => {
    try {
        const relationships = await apiRequest(`${CONFIG.API_BASE}/rebac/relationships`);
        const container = document.getElementById('relationships-list');

        if (relationships.length === 0) {
            container.innerHTML = '<p>No relationships found.</p>';
            return;
        }

        let tableHtml = `
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Subject Type</th>
                        <th>Subject ID</th>
                        <th>Resource Type</th>
                        <th>Resource ID</th>
                        <th>Relationship Type</th>
                    </tr>
                </thead>
                <tbody>
        `;

        relationships.forEach(rel => {
            tableHtml += `
                <tr>
                    <td>${rel.id}</td>
                    <td>${rel.subject_type}</td>
                    <td>${rel.subject_id}</td>
                    <td>${rel.resource_type}</td>
                    <td>${rel.resource_id}</td>
                    <td>${rel.relationship_type}</td>
                </tr>
            `;
        });

        tableHtml += '</tbody></table>';
        container.innerHTML = tableHtml;
    } catch (error) {
        document.getElementById('relationships-list').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
});

document.getElementById('create-rel-btn').addEventListener('click', async () => {
    const data = {
        subject_type: document.getElementById('rel-subject-type').value,
        subject_id: document.getElementById('rel-subject-id').value,
        resource_type: document.getElementById('rel-resource-type').value,
        resource_id: document.getElementById('rel-resource-id').value,
        parent_resource_type: document.getElementById('rel-parent-type').value || null,
        parent_resource_id: document.getElementById('rel-parent-id').value || null,
        relationship_type: document.getElementById('rel-type').value
    };

    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/rebac/relationships`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        showAlert('Relationship created!');
        console.log(result);
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
    }
});

document.getElementById('check-rebac-btn').addEventListener('click', async () => {
    const data = {
        username: document.getElementById('rebac-check-username').value,
        resource: document.getElementById('rebac-check-resource').value,
        action: document.getElementById('rebac-check-action').value
    };

    try {
        const result = await apiRequest(`${CONFIG.API_BASE}/rebac/check`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        const container = document.getElementById('rebac-check-result');
        container.innerHTML = `
            <table>
                <tbody>
                    <tr>
                        <td><strong>Username:</strong></td>
                        <td>${result.username}</td>
                    </tr>
                    <tr>
                        <td><strong>Resource:</strong></td>
                        <td>${result.resource}</td>
                    </tr>
                    <tr>
                        <td><strong>Action:</strong></td>
                        <td>${result.action}</td>
                    </tr>
                    <tr>
                        <td><strong>Has Permission:</strong></td>
                        <td><span class="status-${result.has_permission ? 'success' : 'error'}">${result.has_permission ? 'Yes' : 'No'}</span></td>
                    </tr>
                    <tr>
                        <td><strong>Relationship Path:</strong></td>
                        <td>${result.relationship_path.join(' → ') || 'None'}</td>
                    </tr>
                    <tr>
                        <td><strong>Reason:</strong></td>
                        <td>${result.reason}</td>
                    </tr>
                </tbody>
            </table>
        `;
    } catch (error) {
        document.getElementById('rebac-check-result').innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
    }
});

// Health function
document.getElementById('health-check-btn').addEventListener('click', async () => {
    const btn = document.getElementById('health-check-btn');
    const container = document.getElementById('health-status');

    setButtonLoading(btn, true);
    container.innerHTML = '<p>Checking backend health...</p>';

    try {
        // Health endpoint is at root /health, not under /api/v1
        const response = await fetch('http://localhost:8000/health', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Backend returned status ${response.status}`);
        }

        const result = await response.json();

        container.innerHTML = `
            <table>
                <tbody>
                    <tr>
                        <td><strong>Status:</strong></td>
                        <td><span class="status-success">✅ ${result.status || 'healthy'}</span></td>
                    </tr>
                    <tr>
                        <td><strong>Backend:</strong></td>
                        <td><span class="status-success">Connected</span></td>
                    </tr>
                </tbody>
            </table>
        `;
    } catch (error) {
        console.error('Health check failed:', error);
        container.innerHTML = `
            <table>
                <tbody>
                    <tr>
                        <td><strong>Status:</strong></td>
                        <td><span class="status-error">❌ Unhealthy</span></td>
                    </tr>
                    <tr>
                        <td><strong>Error:</strong></td>
                        <td>${error.message}</td>
                    </tr>
                    <tr>
                        <td><strong>Suggestion:</strong></td>
                        <td>Ensure the FastAPI backend is running on http://localhost:8000</td>
                    </tr>
                </tbody>
            </table>
        `;
    } finally {
        setButtonLoading(btn, false);
    }
});

// Initialize
updateAuthStatus();