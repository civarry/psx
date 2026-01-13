// Page reload warning
// Show confirmation dialog when user tries to refresh or leave the page
window.addEventListener('beforeunload', function (e) {
    e.preventDefault();
    e.returnValue = 'You have unsaved data. Are you sure you want to leave? This will clear your current session.';
    return e.returnValue;
});

// Hide Streamlit Cloud branding
(function() {
    const topDoc = window.top.document;

    // Inject CSS into top document
    const css = `
        [class*="_profilePreview_"] { display: none !important; }
        [class*="_profileContainer_"] { display: none !important; }
        a[href*="streamlit.io/cloud"] { display: none !important; }
        [class*="_viewerBadge_"] { display: none !important; }
    `;
    const style = document.createElement('style');
    style.textContent = css;
    try { topDoc.head.appendChild(style); } catch(e) {}

    // Hide elements via JS (backup for CSS)
    function hideElements() {
        try {
            topDoc.querySelectorAll('[class*="_profilePreview_"], [class*="_profileContainer_"]').forEach(el => el.style.display = 'none');
            topDoc.querySelectorAll('a[href*="streamlit.io/cloud"]').forEach(el => el.style.display = 'none');
            topDoc.querySelectorAll('[class*="_viewerBadge_"]').forEach(el => el.style.display = 'none');
        } catch(e) {}
    }

    setInterval(hideElements, 500);
})();
