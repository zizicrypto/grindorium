export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';

    // Clean URL to HTML mapping
    const routes = {
      '/': '/index.html',
      '/play': '/grindorium-play.html',
      '/watch': '/watch.html',
      '/about': '/grindorium-about.html',
      '/journal': '/grindorium-journal.html',
      '/wall': '/grindorium-wall.html',
      '/evening-court': '/grindorium-evening-court.html',
      '/focus': '/grindorium-pomodoro.html',
      '/cli': '/grindorium-cli.html',
      '/writings': '/writings/index.html',
      '/writings/discipline-feeling': '/writings/discipline-feeling.html',
      '/writings/numbness': '/writings/numbness.html',
      '/writings/the-version-of-you-nobody-sees': '/writings/the-version-of-you-nobody-sees.html',
      '/writings/grief-has-no-timeline': '/writings/grief-has-no-timeline.html',
      '/writings/the-body-keeps-score': '/writings/the-body-keeps-score.html',
      '/writings/you-dont-need-more-motivation': '/writings/you-dont-need-more-motivation.html',
      '/writings/stopping-is-not-quitting': '/writings/stopping-is-not-quitting.html',
      '/writings/the-inner-critic-is-not-your-conscience': '/writings/the-inner-critic-is-not-your-conscience.html',
      '/writings/you-are-not-behind': '/writings/you-are-not-behind.html',
      '/writings/attachment-pattern': '/writings/attachment-pattern.html',
      '/writings/anger-information': '/writings/anger-information.html',
      '/writings/identity-after-loss': '/writings/identity-after-loss.html',
      '/writings/loneliness-crowd': '/writings/loneliness-crowd.html',
      '/writings/burnout': '/writings/burnout.html',
      '/writings/overstimulation': '/writings/overstimulation.html',
      '/writings/ego-depletion': '/writings/ego-depletion.html',
      '/writings/decision-fatigue': '/writings/decision-fatigue.html',
      '/writings/mental-load': '/writings/mental-load.html',
      '/writings/emotional-avoidance': '/writings/emotional-avoidance.html',
      '/writings/anger': '/writings/anger.html',
      '/writings/grief': '/writings/grief.html',
      '/writings/shame': '/writings/shame.html',
      '/writings/guilt': '/writings/guilt.html',
      '/writings/procrastination': '/writings/procrastination.html',
      '/writings/self-sabotage': '/writings/self-sabotage.html',
      '/writings/people-pleasing': '/writings/people-pleasing.html',
      '/writings/perfectionism': '/writings/perfectionism.html',
      '/writings/avoidance': '/writings/avoidance.html',
      '/writings/rumination': '/writings/rumination.html',
      '/writings/dopamine-dysregulation': '/writings/dopamine-dysregulation.html',
      '/writings/cortisol': '/writings/cortisol.html',
      '/writings/nervous-system-dysregulation': '/writings/nervous-system-dysregulation.html',
      '/writings/fight-or-flight': '/writings/fight-or-flight.html',
      '/writings/hypervigilance': '/writings/hypervigilance.html',
      '/writings/attachment-styles': '/writings/attachment-styles.html',
      '/writings/inner-critic': '/writings/inner-critic.html',
      '/writings/imposter-syndrome': '/writings/imposter-syndrome.html',
      '/writings/identity-loss': '/writings/identity-loss.html',
      '/writings/boundaries': '/writings/boundaries.html',
      '/writings/codependency': '/writings/codependency.html',
      '/writings/emotional-immaturity': '/writings/emotional-immaturity.html',
      '/writings/rest': '/writings/rest.html',
      '/writings/discipline': '/writings/discipline.html',
      '/writings/habit-formation': '/writings/habit-formation.html',
      '/writings/cognitive-distortions': '/writings/cognitive-distortions.html',
      '/writings/self-compassion': '/writings/self-compassion.html',
      '/writings/emotional-regulation': '/writings/emotional-regulation.html',
      '/writings/burnout-silence': '/writings/burnout-silence.html',
      '/writings/your-brain-wasn-t-built-for-this-world': '/writings/your-brain-wasn-t-built-for-this-world.html',
      '/writings/you-re-not-lazy-you-re-overstimulated': '/writings/you-re-not-lazy-you-re-overstimulated.html',
      '/writings/perfectionism-protection': '/writings/perfectionism-protection.html',
      '/writings/productivity-avoidance': '/writings/productivity-avoidance.html',
      '/writings/people-pleasing-cost': '/writings/people-pleasing-cost.html',
      '/writings/rest-is-not-reward': '/writings/rest-is-not-reward.html',
      '/writings/self-worth-output': '/writings/self-worth-output.html',
      '/wiki': '/grindorium-wiki.html',
      '/wiki/burnout': '/grindorium-wiki-burnout.html',
      '/wiki/procrastination': '/grindorium-wiki-procrastination.html',
      '/wiki/self-sabotage': '/grindorium-wiki-self-sabotage.html',
      '/wiki/attachment-styles': '/grindorium-wiki-attachment-styles.html',
      '/wiki/perfectionism': '/grindorium-wiki-perfectionism.html',
      '/wiki/anxiety': '/grindorium-wiki-anxiety.html',
      '/wiki/loneliness': '/grindorium-wiki-loneliness.html',
      '/wiki/people-pleasing': '/grindorium-wiki-people-pleasing.html',
      '/wiki/stress': '/grindorium-wiki-stress.html',
      '/wiki/self-esteem': '/grindorium-wiki-self-esteem.html',
      '/wiki/discipline': '/grindorium-wiki-discipline.html',
      '/wiki/emotional-maturity': '/grindorium-wiki-emotional-maturity.html',
      '/wiki/emotional-numbness': '/grindorium-wiki-emotional-numbness.html',
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

    // Serve .html files directly
    if (path.endsWith('.html')) {
      const response = await env.ASSETS.fetch(request);
      return addCacheHeaders(addSecurityHeaders(response), path);
    }

    // /wiki/* - serve static wiki pages
    if (path.startsWith('/wiki/') && path.length > '/wiki/'.length) {
      const debugInfo = JSON.stringify({path, hasRoute: !!routes[path], routeTarget: routes[path] || null});
      if (routes[path]) {
        const newUrl = new URL(routes[path], url.origin);
        try {
          const response = await env.ASSETS.fetch(new Request(newUrl.toString(), {
            method: request.method,
            headers: request.headers,
          }));
          if (response.status === 403 || response.status === 404) {
            return new Response('DEBUG: ' + debugInfo + ' ASSET_STATUS:' + response.status, {status: 200, headers: {'Content-Type': 'text/plain'}});
          }
          return addCacheHeaders(addSecurityHeaders(response), routes[path]);
        } catch(e) {
          return new Response('DEBUG ERROR: ' + debugInfo + ' ERR:' + e.message, {status: 200, headers: {'Content-Type': 'text/plain'}});
        }
      }
      return new Response('DEBUG NO ROUTE: ' + debugInfo, {status: 200, headers: {'Content-Type': 'text/plain'}});
    }

    // /writings/* - check routes table first, then fall back to index
    if (path.startsWith('/writings/') && path.length > '/writings/'.length) {
      if (routes[path]) {
        const newUrl = new URL(routes[path], url.origin);
        const response = await env.ASSETS.fetch(new Request(newUrl.toString(), {
          method: request.method,
          headers: request.headers,
        }));
        return addCacheHeaders(addSecurityHeaders(response), routes[path]);
      }
      // Fallback: dynamic writing via index.html
      const writingsUrl = new URL('/writings/index.html', url.origin);
      const writingsResponse = await env.ASSETS.fetch(new Request(writingsUrl.toString(), {
        method: request.method,
        headers: request.headers,
      }));
      return addCacheHeaders(addSecurityHeaders(writingsResponse), '/writings/index.html');
    }

    if (path.startsWith('/play/') && path.length > '/play/'.length) {
      const newUrl = new URL('/grindorium-play.html', url.origin);
      const response = await env.ASSETS.fetch(new Request(newUrl.toString(), {
        method: request.method,
        headers: request.headers,
      }));
      return addCacheHeaders(addSecurityHeaders(response), path);
    }



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
