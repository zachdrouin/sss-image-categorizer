// Common functionality for the Image Categorizer application
$(document).ready(function() {
    // Toggle API key visibility
    $('#toggle_key_btn').click(function() {
        var apiKeyInput = $('#api_key');
        var showEye = $('#show_eye');
        var hideEye = $('#hide_eye');
        
        if (apiKeyInput.attr('type') === 'password') {
            apiKeyInput.attr('type', 'text');
            showEye.hide();
            hideEye.show();
        } else {
            apiKeyInput.attr('type', 'password');
            showEye.show();
            hideEye.hide();
        }
    });
    
    // Category selection functionality
    $('.category-badge').click(function() {
        $(this).toggleClass('selected');
        updateSelectedCategories();
    });
    
    // Select/Deselect all categories in a group
    $('.select-all-btn').click(function() {
        var group = $(this).data('group');
        var selecting = $(this).hasClass('select-all');
        
        if (selecting) {
            $('.category-badge[data-group="' + group + '"]').addClass('selected');
            $(this).removeClass('select-all').addClass('deselect-all');
            $(this).html('<i class="fas fa-times-circle me-1"></i>Deselect All');
        } else {
            $('.category-badge[data-group="' + group + '"]').removeClass('selected');
            $(this).removeClass('deselect-all').addClass('select-all');
            $(this).html('<i class="fas fa-check-circle me-1"></i>Select All');
        }
        
        updateSelectedCategories();
    });
    
    function updateSelectedCategories() {
        var selected = [];
        $('.category-badge.selected').each(function() {
            selected.push($(this).data('category'));
        });
        $('#selected_categories').val(JSON.stringify(selected));
        $('#selected_count').text(selected.length);
    }
    
    // File browser functionality
    $('#browse_input_btn').click(function() {
        $.get('/browse?type=input', function(data) {
            if (data.path) {
                $('#input_file').val(data.path);
            }
        });
    });
    
    $('#browse_output_btn').click(function() {
        $.get('/browse?type=output', function(data) {
            if (data.path) {
                $('#output_file').val(data.path);
            }
        });
    });
    
    // Process control buttons
    $('#stop_btn').click(function() {
        $.get('/stop', function() {
            $('#stop_btn').prop('disabled', true).text('Stopping...');
        });
    });
    
    // Check progress periodically if on the main page
    if ($('.progress-container').length > 0) {
        function checkProgress() {
            $.getJSON('/progress', function(data) {
                if (data.total > 0) {
                    var percent = Math.round((data.current / data.total) * 100);
                    $('.progress-bar').css('width', percent + '%').attr('aria-valuenow', percent).text(percent + '%');
                    
                    // Format message with appropriate icon
                    var icon = data.success ? 'fa-check-circle' : 'fa-info-circle';
                    $('#progress_message').html('<i class="fas ' + icon + ' me-2"></i>' + data.message);
                    $('.progress-container').show();
                    
                    // Show/hide buttons based on completion
                    if (data.complete) {
                        $('#start_btn').hide();
                        $('#stop_btn').hide();
                        $('#complete_btn').show();
                        
                        // Add appropriate class to progress bar when complete
                        if (data.success) {
                            $('.progress-bar').removeClass('bg-primary').addClass('bg-success');
                            $('#progress_message').addClass('text-success').removeClass('text-danger');
                        } else {
                            $('.progress-bar').removeClass('bg-primary').addClass('bg-danger');
                            $('#progress_message').addClass('text-danger').removeClass('text-success');
                        }
                    } else {
                        $('#start_btn').hide();
                        $('#stop_btn').show();
                        $('#complete_btn').hide();
                    }
                }
            });
        }
        
        setInterval(checkProgress, 2000);
        checkProgress(); // Check immediately on page load
    }
    
    // Store current page in session storage to preserve context
    sessionStorage.setItem('lastPage', window.location.pathname);
    
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Form validation
    $('form').submit(function(event) {
        if ($(this).hasClass('needs-validation')) {
            if (!this.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            $(this).addClass('was-validated');
        }
    });
});
