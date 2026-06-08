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
    if (path.startsWith('/play/') && path.length > '/play/'.length) {
      const newUrl = new URL('/grindorium-play.html', url.origin);
      const response = await env.ASSETS.fetch(new Request(newUrl.toString(), {
        method: request.method,
        headers: request.headers,
      }));
      return addCacheHeaders(addSecurityHeaders(response), path);
    }

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
      '/writings/burnout-silence': '/writings/burnout-silence.html',
      '/writings/your-brain-wasn-t-built-for-this-world': '/writings/your-brain-wasn-t-built-for-this-world.html',
      '/writings/you-re-not-lazy-you-re-overstimulated': '/writings/you-re-not-lazy-you-re-overstimulated.html',
      '/writings/perfectionism-protection': '/writings/perfectionism-protection.html',
      '/writings/productivity-avoidance': '/writings/productivity-avoidance.html',
      '/writings/people-pleasing-cost': '/writings/people-pleasing-cost.html',
      '/writings/rest-is-not-reward': '/writings/rest-is-not-reward.html',
      '/writings/self-worth-output': '/writings/self-worth-output.html',
      '/wiki': '/grindorium-wiki.html',
      '/wiki/burnout': '/wiki/burnout.html',
      '/wiki/procrastination': '/wiki/procrastination.html',
      '/wiki/self-sabotage': '/wiki/self-sabotage.html',
      '/wiki/attachment-styles': '/wiki/attachment-styles.html',
      '/wiki/perfectionism': '/wiki/perfectionism.html',
      '/wiki/anxiety': '/wiki/anxiety.html',
      '/wiki/loneliness': '/wiki/loneliness.html',
      '/wiki/people-pleasing': '/wiki/people-pleasing.html',
      '/wiki/stress': '/wiki/stress.html',
      '/wiki/self-esteem': '/wiki/self-esteem.html',
      '/wiki/discipline': '/wiki/discipline.html',
      '/wiki/emotional-maturity': '/wiki/emotional-maturity.html',
      '/wiki/emotional-numbness': '/wiki/emotional-numbness.html',
      '/tests': '/grindorium-tests.html',
      '/tests/burnout': '/grindorium-burnout.html',
      '/tests/anxiety': '/grindorium-anxiety.html',
      '/tests/procrastination': '/grindorium-procrastination.html',
      '/tests/numbness': '/grindorium-numbness.html',
      '/tests/attachment': '/grindorium-attachment.html',
      '/tests/selfesteem': '/grindorium-selfesteem.html',
      '/tests/perfectionism': '/grindorium-perfectionism.html',
      '/tests/stress': '/grindorium-stress.html',
      '/tests/peoplepleasing': '/grindorium-peoplepleasing.html',
      '/tests/loneliness': '/grindorium-loneliness.html',
      '/tests/selfsabotage': '/grindorium-selfsabotage.html',
      '/tests/discipline': '/grindorium-discipline.html',
      '/tests/emotionalmaturity': '/grindorium-emotionalmaturity.html',
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

  // CSP removed - Lighthouse shows it as needed but causes inline script issues

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
    newHeaders.set('Cache-Control', 'no-cache, no-store, must-revalidate');
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
