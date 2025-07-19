
// ------------------ Add Secondary Role ------------------
function initAddSecondaryRole() {
    const addButton = document.getElementById("add-secondary-role");
    if (!addButton) return;
    
    // Remove any existing event listeners by cloning and replacing the button
    const newButton = addButton.cloneNode(true);
    addButton.parentNode.replaceChild(newButton, addButton);
    
    newButton.addEventListener("click", function () {
        // Get the current number of secondary role fields
        let roleIdx = document.querySelectorAll('[name^="secondary_roles"]').length;
        
        // Parse role choices from a data attribute
        const roleChoicesElement = document.getElementById("role-choices");
        if (!roleChoicesElement) {
            console.error("Role choices element not found");
            return;
        }
        
        let roleChoices = JSON.parse(roleChoicesElement.dataset.choices);
        
        // Check for existing roles to prevent duplicates
        let existingRoles = [];
        document.querySelectorAll('[name$="-secondary_role"]').forEach(select => {
            if (select.value && select.value !== "0") {
                existingRoles.push(select.value);
            }
        });

        let newRole = `
            <div class="form-group mt-3" id="secondary-role-${roleIdx}">
                <div class="d-flex align-items-center">
                    <select id="secondary_roles-${roleIdx}-secondary_role" name="secondary_roles-${roleIdx}-secondary_role" class="form-select form-control">
                        ${roleChoices
                .map(
                    (choice) =>
                        `<option value="${choice.value}">${choice.label}</option>`
                )
                .join("")}
                    </select>
                    <img src="/static/icons/delete_icon.png" width="25" alt="Delete" class="ms-3 delete-role" style="cursor: pointer;">
                </div>
                <div class="mb-3 text-danger fw-semibold"></div>
            </div>
        `;

        document.getElementById("secondary-roles").insertAdjacentHTML("beforeend", newRole);
    });
}

// ------------------ Delete Secondary Role ------------------
function initDeleteSecondaryRole() {
    // This is a global event listener for dynamic elements
    document.addEventListener("click", function (event) {
        if (event.target.classList.contains("delete-role")) {
            let roleDiv = event.target.closest(".form-group");
            roleDiv.remove();
        }
    });
}

// ------------------ Portrait Form Dynamic Role Management ------------------
// This function is removed as it's duplicating functionality

// ------------------ Search By Range ------------------
function toggleEndDate() {
    var checkBox = document.getElementById("search_by_range");
    if (!checkBox) return;
    
    var endDateField = document.getElementById("end_date_field");
    if (!endDateField) return;
    
    var input = endDateField.querySelector("input");
    if (!input) return;
    
    if (checkBox.checked == true){
        input.disabled = false;
    } else {
        input.disabled = true;
    }
}

// ------------------ Toggle Sidebar ------------------
function toggleSidebar() {
    const body = document.body;
    body.classList.toggle('sidebar-collapsed');
    
    // Update the toggle button icon
    const toggleBtn = document.getElementById('sidebar-toggle');
    if (toggleBtn) {
        if (body.classList.contains('sidebar-collapsed')) {
            toggleBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        } else {
            toggleBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
        }
    }
    
    // Store the state in localStorage
    localStorage.setItem('sidebarCollapsed', body.classList.contains('sidebar-collapsed'));
}

// ------------------ Toggle Table Visibility ------------------
function toggleVisibility(tableId, arrowId) {
    var tableContainer = document.getElementById(tableId);
    var toggleArrow = document.getElementById(arrowId);
    if (tableContainer.style.display === "none") {
        tableContainer.style.display = "block";
        toggleArrow.innerHTML = "&#9650;"; // Up arrow
    } else {
        tableContainer.style.display = "none";
        toggleArrow.innerHTML = "&#9660;"; // Down arrow
    }
}

// ------------------ Column Panel Controls ------------------
function toggleColumnPanel() {
    var panel = document.getElementById('columnPanel');
    var icon = document.getElementById('columnToggleIcon');
    
    if (panel.classList.contains('d-none')) {
        panel.classList.remove('d-none');
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        panel.classList.add('d-none');
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

function toggleColumn(column) {
    var elements = document.getElementsByClassName('column-' + column);
    for (var i = 0; i < elements.length; i++) {
        if (elements[i].style.display === 'none') {
            elements[i].style.display = '';
        } else {
            elements[i].style.display = 'none';
        }
    }
}

// ---------------------- MODAL FUNCTIONS ----------------------

// ------------------ Modal Backdrop Fix ------------------
function fixModalBackdrop() {
    // Listen for when any modal is hidden
    document.addEventListener('hidden.bs.modal', function() {
        // Remove any lingering backdrop
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
        // Ensure body doesn't have modal-open class
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    });
}

// ------------------ Delete Confirmation Buttons ------------------
function setupDeleteButtons() {
    const deleteButtons = document.querySelectorAll('.delete-button');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-portrait-id') || 
                      this.getAttribute('data-role-id') || 
                      this.getAttribute('data-pir-id');
            
            const modalId = `deleteModal${id}`;
            const modal = document.getElementById(modalId);
            
            if (modal) {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            }
        });
    });
}

// ------------------ Flash Message Auto-dismiss ------------------
function setupFlashMessages() {
    // Target both .flash-message class (used in main app) and .alert class (used in login/signup)
    const flashMessages = document.querySelectorAll('.flash-message, .alert');
    if (flashMessages.length > 0) {
        flashMessages.forEach(function(message) {
            // For bootstrap alerts
            if (message.classList.contains('alert')) {
                setTimeout(function() {
                    try {
                        const bsAlert = new bootstrap.Alert(message);
                        bsAlert.close();
                    } catch (e) {
                        // Fallback if bootstrap object isn't available
                        message.style.opacity = '0';
                        setTimeout(function() {
                            message.style.display = 'none';
                        }, 500);
                    }
                }, 5000);
            } 
            // For custom flash messages
            else {
                setTimeout(function() {
                    message.style.opacity = '0';
                    setTimeout(function() {
                        message.style.display = 'none';
                    }, 500);
                }, 4000);
            }
        });
    }
}

// ------------------ Wikipedia Import Date Controls ------------------
function initWikipediaImportControls() {
    // DOM Elements
    const useDateRangeCheckbox = document.getElementById('useRangeSwitch');
    const singleDateInput = document.getElementById('singleDateContainer');
    const dateRangeInputs = document.getElementById('dateRangeContainer');
    const wikiForm = document.getElementById('wikiImportForm');
    const importBirths = document.getElementById('importBirths');
    const importDeaths = document.getElementById('importDeaths');
    
    if (!useDateRangeCheckbox || !singleDateInput || !dateRangeInputs) return;
    
    // Function to clear error messages
    function clearErrors() {
        document.querySelectorAll('.errors').forEach(alert => {
            alert.remove();
        });
    }
    
    // Function to add error message
    function addError(container, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'errors mt-2';
        errorDiv.textContent = message;
        container.appendChild(errorDiv);
        return errorDiv;
    }
    
    // Function to validate date inputs
    function validateDateInputs() {
        let isValid = true;
        let errors = {};
        
        clearErrors();
        
        // Validate based on which date input is visible
        if (useDateRangeCheckbox.checked) {
            // Date range validation
            const startMonth = document.getElementById('startMonth').value;
            const startDay = document.getElementById('startDay').value;
            const endMonth = document.getElementById('endMonth').value;
            const endDay = document.getElementById('endDay').value;
            
            // Validate start date
            if (!startMonth || !startDay) {
                addError(document.getElementById('startMonth').parentElement.parentElement.parentElement, 
                         "Please select both month and day for the start date.");
                isValid = false;
                errors.start_date = true;
            }
            
            // Validate end date
            if (!endMonth || !endDay) {
                addError(document.getElementById('endMonth').parentElement.parentElement.parentElement,
                         "Please select both month and day for the end date.");
                isValid = false;
                errors.end_date = true;
            }
            
            // Compare dates if both are complete
            if (startMonth && startDay && endMonth && endDay) {
                const startDate = new Date(2000, parseInt(startMonth) - 1, parseInt(startDay));
                const endDate = new Date(2000, parseInt(endMonth) - 1, parseInt(endDay));
                
                if (startDate > endDate) {
                    addError(dateRangeInputs, "Start date cannot be after end date.");
                    isValid = false;
                    errors.date_range = true;
                }
            }
        } else {
            // Single date validation
            const singleMonth = document.getElementById('singleMonth').value;
            const singleDay = document.getElementById('singleDay').value;
            
            if (!singleMonth || !singleDay) {
                addError(singleDateInput, "Please select both month and day.");
                isValid = false;
                errors.single_date = true;
            }
        }
        
        // Validate checkboxes
        if (!importBirths.checked && !importDeaths.checked) {
            addError(importBirths.parentElement.parentElement, "Please select at least one option (Births or Deaths).");
            isValid = false;
            errors.checkbox = true;
        }
        
        return { isValid, errors };
    }
    
    // Add form submission validation
    if (wikiForm) {
        wikiForm.addEventListener('submit', function(e) {
            const { isValid } = validateDateInputs();
            if (!isValid) {
                e.preventDefault();
                return false;
            }
            return true;
        });
    }
    
    // Toggle between single date and date range
    useDateRangeCheckbox.addEventListener('change', function() {
        clearErrors(); // Clear errors when switching between date inputs
        
        if (this.checked) {
            singleDateInput.style.display = 'none';
            dateRangeInputs.style.display = 'block';
        } else {
            singleDateInput.style.display = 'block';
            dateRangeInputs.style.display = 'none';
        }
    });
    
    // Initialize days in dropdowns
    function populateDays(monthSelect, daySelect) {
        if (!monthSelect || !daySelect) return;
        
        const month = monthSelect.value;
        if (!month) return;
        
        const daysInMonth = new Date(2000, month, 0).getDate();
        const currentDay = daySelect.value;
        
        // Clear existing options
        daySelect.innerHTML = '<option value="" selected disabled>Day</option>';
        
        // Add day options
        for (let i = 1; i <= daysInMonth; i++) {
            const day = i.toString().padStart(2, '0');
            const option = document.createElement('option');
            option.value = day;
            option.textContent = day;
            
            // Restore selected day if valid
            if (currentDay === day) {
                option.selected = true;
            }
            
            daySelect.appendChild(option);
        }
    }
    
    // Initialize all date dropdowns
    const monthSelects = [
        document.getElementById('singleMonth'),
        document.getElementById('startMonth'),
        document.getElementById('endMonth')
    ];
    
    const daySelects = [
        document.getElementById('singleDay'),
        document.getElementById('startDay'),
        document.getElementById('endDay')
    ];
    
    // Set up event listeners for month changes
    for (let i = 0; i < monthSelects.length; i++) {
        if (monthSelects[i]) {
            // Initial population
            populateDays(monthSelects[i], daySelects[i]);
            
            // Update when month changes
            monthSelects[i].addEventListener('change', function() {
                populateDays(monthSelects[i], daySelects[i]);
            });
        }
    }
}

// Call the function when the DOM is loaded
document.addEventListener("DOMContentLoaded", function () {
    // Initialize all components
    initAddSecondaryRole();
    initDeleteSecondaryRole();
    toggleEndDate();
    
    // Initialize sidebar state
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (sidebarCollapsed) {
        document.body.classList.add('sidebar-collapsed');
        const toggleBtn = document.getElementById('sidebar-toggle');
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        }
    }
    
    // Add event listener to sidebar toggle button
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    // Initialize other functions
    setupDeleteButtons();
    setupFlashMessages();
    fixModalBackdrop();
    initSidebarToggle();
    setupResponsiveBehavior();
    initWikipediaImportControls();
});

// ------------------ Responsive Sidebar ------------------
function setupResponsiveBehavior() {
    // Initialize responsive behavior
    if (window.innerWidth > 768) {
        document.body.classList.add('sidebar-open');
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            document.body.classList.add('sidebar-open');
        } else {
            document.body.classList.remove('sidebar-open');
        }
    });
}

// ------------------ Sidebar Toggle Initialization ------------------
function initSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebar-toggle');
    if (sidebarToggle) {
        // Remove any existing listeners first
        const newToggle = sidebarToggle.cloneNode(true);
        sidebarToggle.parentNode.replaceChild(newToggle, sidebarToggle);
        
        // Add click event to toggle button
        newToggle.addEventListener('click', toggleSidebar);
        
        // Check if sidebar was collapsed previously
        if (localStorage.getItem('sidebarCollapsed') === 'true') {
            document.body.classList.add('sidebar-collapsed');
            newToggle.innerHTML = '<i class="fas fa-chevron-right"></i>';
        }
    }
    
    // Mobile sidebar toggle
    const mobileSidebarToggle = document.getElementById('mobile-sidebar-toggle');
    if (mobileSidebarToggle) {
        mobileSidebarToggle.addEventListener('click', toggleSidebar);
    }
}