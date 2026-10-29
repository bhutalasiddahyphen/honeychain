/**
 * HoneyChain - Dashboard Interactions (dashboard.js)
 */

document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("appSidebar");
  const mobileToggle = document.getElementById("mobileToggle");

  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });

    // Close when clicking outside on mobile
    document.addEventListener("click", function (event) {
      if (
        window.innerWidth <= 992 &&
        sidebar.classList.contains("open") &&
        !sidebar.contains(event.target) &&
        !mobileToggle.contains(event.target)
      ) {
        sidebar.classList.remove("open");
      }
    });
  }

  // Quick Copy to Clipboard for hashes
  document.querySelectorAll(".copy-hash-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const hash = this.getAttribute("data-hash");
      if (hash && navigator.clipboard) {
        navigator.clipboard.writeText(hash).then(function () {
          const originalTitle = btn.getAttribute("title") || "Copy";
          btn.setAttribute("title", "Copied!");
          setTimeout(function () {
            btn.setAttribute("title", originalTitle);
          }, 1800);
        });
      }
    });
  });
});

