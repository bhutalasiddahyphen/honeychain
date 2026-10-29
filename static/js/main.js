/**
 * HoneyChain - Main JavaScript Utilities (main.js)
 */

document.addEventListener("DOMContentLoaded", function () {
  // Auto-dismiss alert notifications after 5 seconds
  const alerts = document.querySelectorAll(".alert-message");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-6px)";
      setTimeout(function () {
        if (alert.parentNode) alert.parentNode.removeChild(alert);
      }, 400);
    }, 5000);
  });

  // Password visibility toggle helpers
  document.querySelectorAll(".toggle-password").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const targetId = this.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (input) {
        const isPassword = input.getAttribute("type") === "password";
        input.setAttribute("type", isPassword ? "text" : "password");
        const icon = this.querySelector("i");
        if (icon) {
          icon.classList.toggle("fa-eye");
          icon.classList.toggle("fa-eye-slash");
        }
      }
    });
  });
});

