export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';

    // Serve .html files directly
    if (path.endsWith('.html')) {
      const response = await env.ASSETS.fetch(request);
      return addCacheHeaders(addSecurityHeaders(response), path);
    }

    // /writings/* - serve via writings/index.html for dynamic routing
    if (path.startsWith('/writings/') && path.length > '/writings/'.length) {
      const newUrl = new URL('/writings/index.html', url.origin);
      const response = await env.ASSETS.fetch(new Request(newUrl.toString(), {
        method: request.method,
        headers: request.headers,
      }));
      return addCacheHeaders(addSecurityHeaders(response), path);
    }

    // Clean URL to HTML mapping
    const routes = {
      '/': '/index.html',
      '/play': '/grindorium-play.html',
      '/about': '/grindorium-about.html',
      '/journal': '/grindorium-journal.html',
      '/wall': '/grindorium-wall.html',
      '/evening-court': '/grindorium-evening-court.html',
      '/focus': '/grindorium-pomodoro.html',
      '/cli': '/grindorium-cli.html',
      '/writings': '/writings/index.html',
      '/anxiety': '/grindorium-anxiety.html',
      '/attachment': '/grindorium-attachment.html',
      '/burnout': '/grindorium-burnout.html',
      '/discipline': '/grindorium-discipline.html',
      '/emotional-maturity': '/grindorium-emotionalmaturity.html',
      '/loneliness': '/grindorium-loneliness.html',
      '/numbness': '/grindorium-numbness.html',
      '/people-pleasing': '/grindorium-peoplepleasing.html',
      '/perfectionism': '/grindorium-perfectionism.html',
      '/procrastination': '/grindorium-procrastination.html',
      '/self-esteem': '/grindorium-selfesteem.html',
      '/self-sabotage': '/grindorium-selfsabotage.html',
      '/stress': '/grindorium-stress.html',
      '/grid': '/grid.html',
      '/privacy': '/privacy/index.html',
      '/terms': '/terms/index.html',
    };

    if (routes[path]) {
      const newUrl = new URL(routes[path], url.origin);
      const response = await env.ASSETS.fetch(new Request(newUrl.toString(), {
        method: request.method,
        headers: request.headers,
      }));
      return addCacheHeaders(addSecurityHeaders(response), path);
    }

    const response = await env.ASSETS.fetch(request);
    return addCacheHeaders(addSecurityHeaders(response), path);
  }
}

function addSecurityHeaders(response) {
  const newHeaders = new Headers(response.headers);

  // HSTS - force HTTPS for 1 year
  newHeaders.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');

  // XFO - prevent clickjacking
  newHeaders.set('X-Frame-Options', 'SAMEORIGIN');

  // XSS protection
  newHeaders.set('X-Content-Type-Options', 'nosniff');

  // COOP - cross-origin opener policy
  newHeaders.set('Cross-Origin-Opener-Policy', 'same-origin-allow-popups');

  // Referrer policy
  newHeaders.set('Referrer-Policy', 'strict-origin-when-cross-origin');

  // Permissions policy
  newHeaders.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

  // CSP - allows Supabase, Google Fonts, Google Ads, inline scripts (needed for the site)
  newHeaders.set('Content-Security-Policy',
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://pagead2.googlesyndication.com https://www.googletagmanager.com; " +
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
    "font-src 'self' https://fonts.gstatic.com; " +
    "img-src 'self' data: https:; " +
    "connect-src 'self' https://nvjznlvrsckdkicyqvpn.supabase.co https://pagead2.googlesyndication.com; " +
    "media-src 'self'; " +
    "frame-src 'none';"
  );

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: newHeaders,
  });
}

function addCacheHeaders(response, path) {
  const newHeaders = new Headers(response.headers);

  // Static assets: cache 1 year (immutable - they have content hashes or rarely change)
  if (/\.(webp|png|jpg|jpeg|gif|svg|ico|woff2|woff|ttf)$/i.test(path)) {
    newHeaders.set('Cache-Control', 'public, max-age=31536000, immutable');
  }
  // Audio files: cache 1 year
  else if (/\.mp3$/i.test(path)) {
    newHeaders.set('Cache-Control', 'public, max-age=31536000, immutable');
  }
  // HTML pages: cache 1 hour, must revalidate
  else if (path.endsWith('.html') || path === '/' || !path.includes('.')) {
    newHeaders.set('Cache-Control', 'public, max-age=3600, must-revalidate');
  }
  // JS/CSS: cache 1 day
  else if (/\.(js|css)$/i.test(path)) {
    newHeaders.set('Cache-Control', 'public, max-age=86400');
  }

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: newHeaders,
  });
}
