/**
 * Simple API client for /api routes.
 * Uses same-origin /api when page is served over http(s) so apply and other requests reach the backend.
 */
(function () {
  "use strict";
  function getBase() {
    if (typeof window !== "undefined" && window.location && window.location.origin &&
        window.location.origin !== "file://" && window.location.origin !== "null") {
      return window.location.origin + "/api";
    }
    return "/api";
  }

  function request(method, path, body) {
    var base = getBase();
    var url = base + path;
    var opts = { method: method, headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    return fetch(url, opts).then(function (res) {
      if (!res.ok) {
        return res.json().then(function (data) {
          throw new Error(data.detail || res.statusText);
        }, function () {
          throw new Error(res.statusText);
        });
      }
      if (res.status === 204) return undefined;
      return res.json();
    });
  }

  window.API = {
    get: function (path) { return request("GET", path); },
    post: function (path, body) { return request("POST", path, body); },
    put: function (path, body) { return request("PUT", path, body); },
    delete: function (path) { return request("DELETE", path); }
  };
})();
