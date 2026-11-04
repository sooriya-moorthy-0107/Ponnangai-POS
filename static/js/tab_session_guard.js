/**
 * Automatic Tab / Browser Close Guard for Ponnangai POS
 * 
 * Rules:
 * 1. While navigating within the POS (clicking links, submitting forms), the session stays alive.
 * 2. If the user hits Reload (F5 or browser refresh), the session stays alive.
 * 3. If the user closes the tab / browser window and comes back later or opens a new tab,
 *    they MUST log in again.
 */
(function() {
    // 1. Identify navigation type using modern PerformanceNavigationTiming API
    const navEntries = window.performance.getEntriesByType('navigation');
    const isReload = navEntries.length > 0 && navEntries[0].type === 'reload';

    // 2. Check if this tab has an active, legitimate in-progress session
    const tabActive = sessionStorage.getItem("pos_session_active");

    if (!tabActive) {
        // If the tab is newly opened or restored after being closed, force logout
        sessionStorage.removeItem("pos_session_active");
        window.location.replace("/logout");
        return;
    }

    // 3. Keep session active for internal link clicks and form submits
    document.addEventListener("click", function(e) {
        const link = e.target.closest("a");
        if (link && link.href && link.href.startsWith(window.location.origin) && !link.href.includes("/logout")) {
            sessionStorage.setItem("pos_session_active", "true");
        }
    });

    document.addEventListener("submit", function() {
        sessionStorage.setItem("pos_session_active", "true");
    });

    // 4. When unloading (leaving page):
    // Use pagehide / beforeunload with navigator.sendBeacon to ensure cookie cleanup on tab close
    window.addEventListener("pagehide", function(event) {
        // If it's not being persisted in the back-forward cache and not a reload
        if (!event.persisted) {
            // Send beacon to invalidate session cookie on server
            navigator.sendBeacon("/api/auth/invalidate-session");
        }
    });
})();
