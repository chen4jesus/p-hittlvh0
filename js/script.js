document.addEventListener("DOMContentLoaded", () => {
  const hamburger = document.querySelector(".hamburger");
  const navMenu = document.querySelector(".nav-links");

  if (hamburger && navMenu) {
    hamburger.addEventListener("click", () => {
      hamburger.classList.toggle("active");
      navMenu.classList.toggle("active");
    });

    // Close menu when a link is clicked
    document.querySelectorAll(".nav-links a").forEach((n) =>
      n.addEventListener("click", () => {
        hamburger.classList.remove("active");
        navMenu.classList.remove("active");
      })
    );
  }
});

// AI Editor Mode Logic
(function() {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('ai-mode')) {
    sessionStorage.setItem('aiModeEnabled', 'true');
  }

  if (sessionStorage.getItem('aiModeEnabled') === 'true') {
    const script = document.createElement('script');
    script.src = 'js/editor.js';
    document.body.appendChild(script);
  }
})();
