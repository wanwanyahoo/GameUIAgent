import { useState, useEffect, useCallback } from "react";

export type Route = {
  path: string;
  params: Record<string, string>;
};

function parseHash(): Route {
  const hash = window.location.hash.replace(/^#/, "") || "/";
  const [path] = hash.split("?");
  const params: Record<string, string> = {};
  const queryIndex = hash.indexOf("?");
  if (queryIndex !== -1) {
    const queryString = hash.slice(queryIndex + 1);
    new URLSearchParams(queryString).forEach((value, key) => {
      params[key] = value;
    });
  }
  return { path: path || "/", params };
}

export function useHashRouter() {
  const [route, setRoute] = useState<Route>(() => parseHash());

  useEffect(() => {
    const handler = () => setRoute(parseHash());
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  const navigate = useCallback((path: string) => {
    if (window.location.hash === `#${path}`) {
      setRoute(parseHash());
    } else {
      window.location.hash = path;
    }
  }, []);

  return { route, navigate };
}

export function navigateTo(path: string) {
  window.location.hash = path;
}
