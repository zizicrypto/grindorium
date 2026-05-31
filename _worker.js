export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';
    
    const redirects = {
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
    
    if (redirects[path]) {
      const newUrl = new URL(request.url);
      newUrl.pathname = redirects[path];
      return env.ASSETS.fetch(new Request(newUrl.toString(), request));
    }
    
    return env.ASSETS.fetch(request);
  }
}
