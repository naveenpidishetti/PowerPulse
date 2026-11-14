// PowerPulse Core Client-Side Utilities

document.addEventListener('DOMContentLoaded', () => {
  // Initialize all Bootstrap tooltips if enabled
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach((tooltipTriggerEl) => {
    if (window.bootstrap && window.bootstrap.Tooltip) {
      new window.bootstrap.Tooltip(tooltipTriggerEl);
    }
  });

  // Auto-dismiss standard alerts after 6 seconds (excluding warning/danger alerts)
  const autoAlerts = document.querySelectorAll('.alert-info, .alert-success');
  autoAlerts.forEach((alertEl) => {
    setTimeout(() => {
      if (window.bootstrap && window.bootstrap.Alert) {
        const alertInstance = new window.bootstrap.Alert(alertEl);
        alertInstance.close();
      }
    }, 6000);
  });
});
