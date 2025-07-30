// Check if user is logged in
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
    }
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 3000);
}

// Show success message
function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 3000);
}

// Fetch profile data
async function fetchProfile() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5001/profile', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 404) {
            // Profile doesn't exist yet, show empty form
            setEditing(true);
            return;
        }

        if (!response.ok) {
            throw new Error('Failed to fetch profile');
        }

        const data = await response.json();
        populateForm(data);
        setEditing(false);
    } catch (error) {
        showError(error.message);
    }
}

// Populate form with profile data
function populateForm(data) {
    document.getElementById('risk-tolerance').value = data.risk_tolerance || 'medium';
    document.getElementById('investment-goals').value = data.investment_goals || '';
    
    const sectorsSelect = document.getElementById('preferred-sectors');
    if (data.preferred_sectors) {
        Array.from(sectorsSelect.options).forEach(option => {
            option.selected = data.preferred_sectors.includes(option.value);
        });
    }
}

// Save profile data
async function saveProfile(formData) {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5001/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Failed to save profile');
        }

        showSuccess('Profile saved successfully');
        setEditing(false);
    } catch (error) {
        showError(error.message);
    }
}

// Update profile data
async function updateProfile(formData) {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('http://localhost:5001/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Failed to update profile');
        }

        showSuccess('Profile updated successfully');
        setEditing(false);
    } catch (error) {
        showError(error.message);
    }
}

// Toggle editing mode
function setEditing(editing) {
    const form = document.getElementById('profile-form');
    const editButton = form.querySelector('.btn-secondary');
    const saveButton = form.querySelector('.btn-primary');
    const inputs = form.querySelectorAll('select, textarea');

    inputs.forEach(input => {
        input.disabled = !editing;
    });

    editButton.style.display = editing ? 'none' : 'block';
    saveButton.style.display = editing ? 'block' : 'none';
}

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    fetchProfile();

    const form = document.getElementById('profile-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            risk_tolerance: document.getElementById('risk-tolerance').value,
            investment_goals: document.getElementById('investment-goals').value,
            preferred_sectors: Array.from(document.getElementById('preferred-sectors').selectedOptions)
                .map(option => option.value)
        };

        try {
            const response = await fetch('http://localhost:5001/profile', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.status === 404) {
                await saveProfile(formData);
            } else {
                await updateProfile(formData);
            }
        } catch (error) {
            showError(error.message);
        }
    });
}); 