# Grindorium

**A behavioral laboratory for the examined life.**

Grindorium is not a productivity app. Not a wellness platform. It is a space to understand what is actually happening in your mind, and to train what needs training.

Live at [grindorium.org](https://grindorium.org)

---

## What it is

17 interactive games built on peer-reviewed psychology research. Each one targets a specific pattern: impulse control, delayed gratification, self-sabotage, emotional dysregulation, procrastination, avoidance. The games do not reward you for winning. They show you something about how you operate.

Supporting that: 21 long-form essays, a micro journal, an evening court based on Stoic practice, a live collective word wall, CLI mode, and a Zen Mode that locks competitive games after 23:00.

---

## Pages

| Path | Description |
|---|---|
| `/` | Home |
| `/play` | 17 behavioral games |
| `/writings` | 21 essays on psychology and discipline |
| `/journal` | Micro Journal (localStorage, no account) |
| `/evening-court` | Three Stoic questions, every evening |
| `/wall` | Live anonymous collective word wall (Supabase) |
| `/cli` | Terminal mode |
| `/about` | About |
| `/privacy` | Privacy Policy |
| `/terms` | Terms of Service |

---

## Games

1. The Weight (sorting, values under load)
2. The Drift (impulse language, swipe left/right)
3. The Loop (branching scenario, 10 levels)
4. The Stack (drag and drop: Carrying / Avoiding / Accepting)
5. The Wait (delayed gratification, 90s, 6 tiers)
6. The Breath (box, 4-7-8, simple)
7. The Feeling (18 emotions, hang on a tree)
8. The Resistance (urge surfing, 3 durations, 4 phases)
9. Micro Journal (3 words, localStorage, monthly map)
10. The Nothing Room (5 minutes, forest grows, do not touch)
11. Evening Court (Epictetus, Marcus Aurelius, Seneca)
12. The Wall (live Supabase word cloud)
13. The Void (once per week, 5 minutes, complete emptiness)
14. Trigger Map (ABC model, 5 steps, 6 insight categories)
15. The Saboteur (reverse psychology, 3 branches, 10 endings)
16. The Chaos Button (synthetic storm audio, DBT urge surfing)
17. The Resistance Room (17 excuses, 8s timer, rationalization training)

---

## Stack

- Pure HTML, CSS, JavaScript. No framework.
- Hosted on Netlify (free tier).
- Supabase for The Wall (anonymous word submissions, 24h rolling window).
- All other data stored in browser localStorage. No user accounts. No tracking beyond Google Analytics and AdSense.

---

## Research foundation

Every game cites its source. The references span:

Baumeister (ego depletion), Linehan (DBT distress tolerance), Bowen and Marlatt (urge surfing), Mischel (delayed gratification), Festinger (cognitive dissonance), Pychyl (procrastination), Crocker and Park (self-worth contingency), Flett and Hewitt (perfectionism), Heriot-Maitland (fear cycles), Eastwood (boredom), Gray (behavioral inhibition), Loewenstein and Thaler (intertemporal choice), McClure (neural systems for reward), Gollwitzer (implementation intentions).

---

## Running locally

No build step required. Clone the repository and open `index.html` in a browser.

```bash
git clone https://github.com/zizicrypto/grindorium.git
cd grindorium
open index.html
```

The Wall feature requires a Supabase project with a `words` table and appropriate RLS policies.

---

## License

Content and design are copyright Grindorium 2026. The underlying research referenced throughout belongs to its respective authors.
