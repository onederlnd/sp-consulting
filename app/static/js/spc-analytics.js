(function () {
  "use strict";

  const script = document.currentScript;
  const orgSlug = script.getAttribute("data-org");
  const endpoint = script.getAttribute("data-endpoint") || "https://yourapp.com/analytics/collect";

  if (!orgSlug) {
    console.warn("[SPC Analytics] Missing data-org attribute.");
    return;
  }

  // ── ID management ──────────────────────────────────────────────────────────

  function uuid() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      const r = (Math.random() * 16) | 0;
      return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
    });
  }

  function getCookie(name) {
    const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
    return match ? match[2] : null;
  }

  function setCookie(name, value, days) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = name + "=" + value + "; expires=" + expires + "; path=/; SameSite=Lax";
  }

  function getVisitorId() {
    let id = getCookie("spc_vid");
    if (!id) {
      id = uuid();
      setCookie("spc_vid", id, 365);
    }
    return id;
  }

  function getSessionId() {
    let id = sessionStorage.getItem("spc_sid");
    if (!id) {
      id = uuid();
      sessionStorage.setItem("spc_sid", id);
    }
    return id;
  }

  // ── UTM parsing ────────────────────────────────────────────────────────────

  function getUtmParams() {
    const params = new URLSearchParams(window.location.search);
    return {
      utm_source: params.get("utm_source"),
      utm_medium: params.get("utm_medium"),
      utm_campaign: params.get("utm_campaign"),
    };
  }

  // ── Event sending ──────────────────────────────────────────────────────────

  function send(eventType, properties) {
    const utms = getUtmParams();
    const payload = {
      org_slug: orgSlug,
      session_id: getSessionId(),
      visitor_id: getVisitorId(),
      event_type: eventType,
      url: window.location.href,
      referrer: document.referrer,
      title: document.title,
      properties: properties || {},
      utm_source: utms.utm_source,
      utm_medium: utms.utm_medium,
      utm_campaign: utms.utm_campaign,
    };

    if (navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify(payload)], {
        type: "application/json",
      });
      navigator.sendBeacon(endpoint, blob);
    } else {
      fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        keepalive: true,
      }).catch(function () {});
    }
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  window.spc = {
    track: function (eventName, properties) {
      send(eventName, properties);
    },
  };

  // ── Auto pageview ──────────────────────────────────────────────────────────

  send("pageview");

  // ── SPA support — track history changes ───────────────────────────────────

  const originalPushState = history.pushState;
  history.pushState = function () {
    originalPushState.apply(this, arguments);
    send("pageview");
  };

  window.addEventListener("popstate", function () {
    send("pageview");
  });
})();
