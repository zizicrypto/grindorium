export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';

    // .html uzantili istekleri direkt serve et
    if (path.endsWith('.html')) {
      return env.ASSETS.fetch(request);
    }

    // /writings/* - makale slug'lari writings/index.html ile serve edilir
    if (path.startsWith('/writings/') && path.length > '/writings/'.length) {
      const newUrl = new URL('/writings/index.html', url.origin);
      return env.ASSETS.fetch(new Request(newUrl.toString(), {
        method: request.method,
        headers: request.headers,
      }));
    }

    // Temiz URL -> HTML esleme
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
      '/privacy': '/privacy/index.html',
      '/terms': '/terms/index.html',
    };

    if (routes[path]) {
      const newUrl = new URL(routes[path], url.origin);
      return env.ASSETS.fetch(new Request(newUrl.toString(), {
        method: request.method,
        headers: request.headers,
      }));
    }

    return env.ASSETS.fetch(request);
  }
}
