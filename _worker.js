export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    
    // .html uzantisi varsa direkt serve et - dongu onleme
    if (path.endsWith('.html')) {
      return env.ASSETS.fetch(request);
    }
    
    // Temiz path -> HTML dosyasi esleme
    const cleanPath = path.replace(/\/+$/, '') || '/';
    
    const routes = {
      '/': '/index.html',
      '/anxiety': '/grindorium-anxiety.html',
      '/attachment': '/grindorium-attachment.html',
      '/burnout': '/grindorium-burnout.html',
      '/discipline': '/grindorium-discipline.html',
      '/emotional-maturity': '/grindorium-emotionalmaturity.html',
      '/loneliness': '/grindorium-loneliness.html',
      '/numbness': '/grindorium-numbness.html',
      '/people-pleasing': '/grindorium-peoplepleasing.html',
      '/perfectionism': '/grindorium-perfectionism.html',
      '/self-sabotage': '/grindorium-selfsabotage.html',
      '/writings': '/writings/index.html',
      '/stress': '/grindorium-stress.html',
      '/self-esteem': '/grindorium-selfesteem.html',
      '/procrastination': '/grindorium-procrastination.html',
      '/about': '/grindorium-about.html',
      '/privacy': '/privacy.html',
      '/play': '/grindorium-play.html',
      '/journal': '/grindorium-journal.html',
      '/evening-court': '/grindorium-evening-court.html',
      '/wall': '/grindorium-wall.html',
      '/cli': '/grindorium-cli.html',
      '/terms': '/terms.html',
      '/focus': '/grindorium-pomodoro.html',
    };
    
    if (routes[cleanPath]) {
      // Yeni bir Request olustur, orijinal request yerine
      const assetUrl = new URL(routes[cleanPath], url.origin);
      const assetRequest = new Request(assetUrl.toString(), {
        method: request.method,
        headers: request.headers,
      });
      return env.ASSETS.fetch(assetRequest);
    }
    
    // MP3, PNG vs diger dosyalar - direkt serve et
    return env.ASSETS.fetch(request);
  }
}
