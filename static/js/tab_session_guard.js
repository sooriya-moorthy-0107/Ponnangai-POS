// Tab-Scoped Session Guard:
// If a user closes the browser/tab and reopens the URL, sessionStorage is destroyed.
// This guard ensures that an active session flag must be present in this tab.
(function() {
    // If not authenticated in this specific tab, immediately clear session and redirect to /login
    if (!sessionStorage.getItem("pos_tab_authenticated")) {
        // Clear server session cookie via beacon/fetch and redirect to login
        window.location.replace("/logout");
    }
})();

