/**
 * HONEYCHAIN - Interactive Client Scripts
 * Handles menu bar opening & closing, mobile drawer, modal, clipboard, and QR helpers.
 */

function updateMenuButtonState(isClosed) {
  const toggleBtn = document.getElementById("menu-toggle-btn");
  const toggleLabel = document.getElementById("menu-toggle-label");
  const toggleIcon = document.getElementById("menu-toggle-icon");

  if (toggleLabel) {
    toggleLabel.textContent = isClosed ? "Open Menu" : "Close Menu";
  }
  if (toggleIcon) {
    if (isClosed) {
      toggleIcon.className = "fa-solid fa-bars";
    } else {
      toggleIcon.className = "fa-solid fa-xmark";
    }
  }
  if (toggleBtn) {
    toggleBtn.title = isClosed ? "Open Menu Bar" : "Close Menu Bar";
  }
}

// Global function to toggle sidebar menu open/close
function toggleSidebarMenu() {
  const sidebar = document.getElementById("sidebar");
  const mainWrapper = document.getElementById("main-wrapper");
  const overlay = document.getElementById("sidebar-overlay");

  if (!sidebar) return;

  if (window.innerWidth <= 992) {
    // Mobile screen behavior
    const isOpen = sidebar.classList.contains("mobile-open");
    if (isOpen) {
      sidebar.classList.remove("mobile-open");
      if (overlay) overlay.classList.remove("active");
      updateMenuButtonState(true);
    } else {
      sidebar.classList.add("mobile-open");
      if (overlay) overlay.classList.add("active");
      updateMenuButtonState(false);
    }
  } else {
    // Desktop screen behavior
    const isClosed = sidebar.classList.contains("closed");
    if (isClosed) {
      sidebar.classList.remove("closed");
      if (mainWrapper) mainWrapper.classList.remove("sidebar-closed");
      localStorage.setItem("honeychain_menu_closed", "false");
      updateMenuButtonState(false);
    } else {
      sidebar.classList.add("closed");
      if (mainWrapper) mainWrapper.classList.add("sidebar-closed");
      localStorage.setItem("honeychain_menu_closed", "true");
      updateMenuButtonState(true);
    }
  }
}

function closeSidebarMenu() {
  const sidebar = document.getElementById("sidebar");
  const mainWrapper = document.getElementById("main-wrapper");
  const overlay = document.getElementById("sidebar-overlay");

  if (!sidebar) return;

  if (window.innerWidth <= 992) {
    sidebar.classList.remove("mobile-open");
    if (overlay) overlay.classList.remove("active");
  } else {
    sidebar.classList.add("closed");
    if (mainWrapper) mainWrapper.classList.add("sidebar-closed");
    localStorage.setItem("honeychain_menu_closed", "true");
  }
  updateMenuButtonState(true);
}

document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("sidebar");
  const mainWrapper = document.getElementById("main-wrapper");
  const overlay = document.getElementById("sidebar-overlay");
  const menuToggleBtn = document.getElementById("menu-toggle-btn");
  const sidebarCloseBtn = document.getElementById("sidebar-close-btn");
  const mobileMenuBtn = document.getElementById("mobile-menu-btn");

  // Restore stored menu preference on desktop
  const isMenuClosed = localStorage.getItem("honeychain_menu_closed") === "true";
  if (isMenuClosed && window.innerWidth > 992 && sidebar) {
    sidebar.classList.add("closed");
    if (mainWrapper) mainWrapper.classList.add("sidebar-closed");
    updateMenuButtonState(true);
  } else {
    updateMenuButtonState(false);
  }

  // Menu bar Open / Close button listeners
  if (menuToggleBtn) {
    menuToggleBtn.addEventListener("click", toggleSidebarMenu);
  }

  if (sidebarCloseBtn) {
    sidebarCloseBtn.addEventListener("click", closeSidebarMenu);
  }

  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener("click", toggleSidebarMenu);
  }

  if (overlay) {
    overlay.addEventListener("click", closeSidebarMenu);
  }

  // Close mobile drawer when clicking any navigation link
  const navLinks = document.querySelectorAll(".sidebar .nav-item");
  navLinks.forEach(function (link) {
    link.addEventListener("click", function () {
      if (window.innerWidth <= 992) {
        closeSidebarMenu();
      }
    });
  });

  // Auto-Dismiss Flash Messages
  const flashMessages = document.querySelectorAll(".flash-message");
  flashMessages.forEach(function (msg) {
    const closeBtn = msg.querySelector(".flash-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", function () {
        msg.style.opacity = "0";
        setTimeout(() => msg.remove(), 250);
      });
    }
    setTimeout(function () {
      if (msg && msg.parentElement) {
        msg.style.opacity = "0";
        setTimeout(() => msg.remove(), 300);
      }
    }, 5000);
  });
});

// Modal Functions (Forgot Password, etc.)
function openForgotPasswordModal() {
  const modal = document.getElementById("forgotPasswordModal");
  if (modal) {
    modal.classList.add("active");
  }
}

function closeForgotPasswordModal() {
  const modal = document.getElementById("forgotPasswordModal");
  if (modal) {
    modal.classList.remove("active");
  }
}

// Copy Hash / Text to Clipboard
function copyHash(text, btnElement) {
  if (!navigator.clipboard) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    showCopyFeedback(btnElement);
    return;
  }
  navigator.clipboard.writeText(text).then(function () {
    showCopyFeedback(btnElement);
  });
}

function showCopyFeedback(btnElement) {
  if (!btnElement) return;
  const originalHtml = btnElement.innerHTML;
  btnElement.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
  btnElement.style.color = "#10b981";
  setTimeout(function () {
    btnElement.innerHTML = originalHtml;
    btnElement.style.color = "";
  }, 1800);
}

// Print Label Helper
function printQrLabel(elementId) {
  const printable = document.getElementById(elementId);
  if (!printable) {
    window.print();
    return;
  }
  const printWindow = window.open("", "_blank");
  printWindow.document.write("<html><head><title>HoneyChain QR Label</title>");
  printWindow.document.write("<style>body{text-align:center;font-family:sans-serif;padding:30px;} img{max-width:240px;} .batch{font-weight:bold;margin-top:10px;font-size:18px;}</style>");
  printWindow.document.write("</head><body>");
  printWindow.document.write(printable.innerHTML);
  printWindow.document.write("</body></html>");
  printWindow.document.close();
  printWindow.focus();
  setTimeout(function () {
    printWindow.print();
    printWindow.close();
  }, 250);
}
