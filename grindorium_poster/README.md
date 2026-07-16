# Grindorium Poster — TEK KAYNAK (2026-07-10'da yeniden yazildi)

## BULUT SISTEMI (2026-07-16'dan itibaren, test asamasinda)

PC bagimliligini ve main.py/poster_check.py cift-surec yarisini ortadan
kaldirmak icin GitHub Actions'ta calisan yeni bir yol eklendi:

- `cloud_poster.py` — GitHub Actions'ta (`.github/workflows/grindorium-poster.yml`,
  15 dakikada bir) calisir. Video "tahmin" etmez: STICKLINE'in zaten
  YouTube'a private+publishAt ile yukledigi videolarin takvimini
  (`schedule.json`, video_id -> publishAt+kind) okur, saati gelmis ve
  YouTube'da gercekten public olmus videoyu bulur, indirir, Instagram+
  Facebook'a paylasir. `schedule.json`'da olmayan videolar (STICKLINE
  disi, orn. gercek Grindorium bolumu) icin RSS bazli yedek yakalama da
  var.
- `schedule.json` — `schedule_sync.py` ile PC'de elle/periyodik olarak
  `Desktop\STICKLINE\STICKLINE_RESCHEDULE_STATE.json`'dan uretilir ve
  git'e commit+push edilir. Sir icermez (sadece video_id/tarih/tur).
- `posting_plan.json` — bulut sisteminin TEK durum dosyasi (state.json +
  daily_posted.json'un yerini alir), her calistirmadan sonra git'e
  commit'lenir.
- `build_config.py` — GitHub Actions runner'inda repo secrets'lardan
  gecici (commit edilmeyen) bir config.json olusturur.
- Secrets (GitHub repo Settings > Secrets and variables > Actions):
  `GRINDORIUM_YOUTUBE_CHANNEL_ID`, `GRINDORIUM_IG_ACCESS_TOKEN`,
  `GRINDORIUM_IG_USER_ID`, `GRINDORIUM_FB_PAGE_ID`,
  `GRINDORIUM_FB_PAGE_ACCESS_TOKEN`.
- `platforms/facebook.py` artik `kind="LONG"` icin Reels yerine normal
  Page video postu kullaniyor (Reels'in sure siniri uzun formatlarda
  400 hatasina yol aciyordu).

**Su an PC'deki main.py + Task Scheduler gorevleri hala calisiyor** (cift
paylasim riskini onlemek icin bulut sistemi tam dogrulanana kadar PC
tarafi kapatilmayacak). Plan: `C:\Users\Ali\.claude\plans\replicated-wiggling-balloon.md`.

**Bu dosya guncel gercegi anlatiyor. Daha eski tarihli baska notlar/varsayimlar
gecersizdir — sadece burasi okunsun.** Eskiden bu sistem TikTok/X/Pinterest'i
de kapsayacak sekilde tasarlanmisti ama su an SADECE Instagram + Facebook
aktif (config.json'da tiktok/twitter/pinterest enabled=false). Kod hala o
platformlar icin de hazir (platforms/ klasorunde dosyalari var), ama devrede
degiller.

## Sistem ne yapiyor (kisa ozet)

YouTube kanalindaki (@Grindorium) yeni videolari izler, kisa olanlari (<=3 dk)
indirir, altyazi/hashtag uretir, Instagram Reels + Facebook Reels'e otomatik
paylasir. Iki ayri surec birlikte calisir:

1. **main.py** — 7/24 arka planda surekli calisan ana surec, 10 dakikada bir
   RSS'e bakar.
2. **poster_check.py** — Task Scheduler'in gunde 3 dar pencerede (yayin
   saatlerine gore) tetikledigi yedek/garanti mekanizmasi.

Ikisi de ayni state.json + daily_posted.json dosyalarina yazar, birbirini
gormesi icin ozel bir senkron mekanizmasi var (asagida).

## 1) main.py — surekli surec

- Her 10 dakikada bir YouTube RSS feed'ini kontrol eder (`utils/youtube_monitor.py`).
- Yeni video bulunca indirir (`utils/downloader.py`, yt-dlp).
- **Sure guvenlik agi**: indirilen dosyanin yt-dlp'den gelen GERCEK suresi
  (`meta["duration"]`) 180 saniyeyi (`SHORT_MAX_SECONDS`) asiyorsa video
  kuyruga hic girmez. Bu, YouTube Data API kotasi patladiginda (403) bile
  calisir — cunku yt-dlp'nin kendi olcumune bakiyor, API'ye bagimli degil.
  (Eskiden SADECE API'ye bakiliyordu; API kota hatasi verince suresi
  "bilinmiyor" sayilip 10 dakikalik bir bolum bile "kisa" saniliyordu — bu
  yuzden antm9DtHFjg adli tam bolum Instagram'a Reels gibi zorlanip surekli
  400 hatasi aliyordu. 2026-07-10'da duzeltildi.)
- Icerik turunu (`grindorium` / `stickline`) belirler — bkz. Bolum 3.
- Claude API varsa (config.json'da `claude.enabled=true` VE gecerli key) ondan
  altyazi ister; yoksa/basarisiz olursa `utils/fallback_formatter.py`
  devreye girer (orijinal YouTube basligi+aciklamasini kirpip hashtag ekler).
  **Su an Claude KAPALI** (`claude.enabled=false`), yani her zaman fallback
  formatter kullaniliyor.
- Videoyu kuyruga ekler, `post_delay_minutes` (30 dk) sonra paylasilmak
  uzere isaretler, ve o an ilk kuyruga girdigi zamani `queued_at` olarak
  kaydeder.
- Kuyruktaki her video icin zamani gelince Instagram + Facebook'a paylasir.
- **Gecikmis kuyruk guvenlik agi (`STALE_QUEUE_HOURS = 3`)**: bir video ilk
  kuyruga girdigi (`queued_at`) andan itibaren 3 saat icinde hala
  paylasilamadiysa (sistem kapaliydi, hata olustu, PC yeniden baslatildi vb.)
  artik paylasilmaz, sessizce (loglanarak) atilir, biriktirilmez. **Neden**:
  main.py uzun sure durup tekrar baslatildiginda, kuyrukta biriken gunler
  onceki videolar hepsi ayni anda "gecikmis" olarak paylasiliyordu — bu da
  Instagram+Facebook'ta 3 farkli videonun art arda, spam gibi gorunecek
  sekilde paylasilmasina yol acti (2026-07-10, sistem yeniden baslatildiktan
  hemen sonra yasandi, Ali fark edip 2 paylasimi elle sildi). Ali'nin acik
  talebiyle ayni gun eklendi: "kesinlikle spam ederiz, boyle kesinlikle
  kabul etmiyorum." Bu kural `poster_check.py`'nin "1 saat icinde
  yakalayamazsan es gec, biriktirme" mantigiyla ayni felsefeyi main.py'nin
  kendi kuyruguna da uygular.
- **Bekleme kilidi (rate limit)**: bir icerik turu (stickline/grindorium)
  basariyla paylasildiktan sonra, o turden bir sonraki paylasim icin
  `stickline_min_hours_between` (6 saat) / `grindorium_min_hours_between`
  (20 saat) bekler. **Onemli**: bu kilit SADECE gercek basarili paylasimdan
  sonra baslar (eskiden paylasim denemesi basarisiz olsa bile kilit
  basliyordu, bu da arkadaki tum videolarin haksiz yere ertelenmesine
  yol aciyordu — 2026-07-10'da duzeltildi).

## 2) poster_check.py — Task Scheduler ile tetiklenen yedek mekanizma

STICKLINE'in yeni yayin programina gore (`Desktop\STICKLINE\STICKLINE_RESCHEDULE_DURUM.md`,
tek kaynak: KAYNAK SAAT DILIMI SADECE America/New_York — TR HICBIR YERDE
KULLANILMIYOR) her gun videolar hep su 3 ET saatinden birinde yayinlaniyor:

| ET saati | Ne yayinlaniyor |
|---|---|
| 12:00 | BAGIMSIZ SHORT (Pzt/Sal/Crs/Cum/Cts) |
| 16:00 | LONG (sadece Persembe + Pazar) |
| 19:00 | ESLI SHORT (LONG ile ayni gun) VEYA BAGIMSIZ SHORT (diger gunler) |

Task Scheduler'da bu 3 saat icin 3 ayri gorev var (`GrindoriumPoster_Midday`,
`GrindoriumPoster_Primetime`, `GrindoriumPoster_Evening`). Her gorev, ilgili
ET saatinden hemen once baslayip ~2 saat 10 dakika suren bir pencerede, her
10 dakikada bir `poster_check.py`'yi calistirir (gunde toplam ~42 calistirma,
24 saat degil).

**Neden 2 saat 10 dakika ve neden TR saatine gore sabit degil?** Turkiye 2016'dan
beri yaz saati uygulamiyor (sabit UTC+3), ama ABD hala uyguluyor. Yani
ET->TR farki yaz aylarinda (EDT) +7 saat, kis aylarinda (EST) +8 saat —
yilda 2 kez 1 saat kayiyor. Pencereler bu 1 saatlik belirsizligi + istenen
1 saatlik "yakalama suresi"ni kapsayacak kadar genis tutuldu, boylece yilda
2 kez elle Task Scheduler saatini degistirmeye gerek kalmiyor. Asil dogru
saat karsilastirmasi zaten Python icinde `zoneinfo` ile (DST'yi otomatik
hesaba katarak) yapiliyor — Task Scheduler'in gorevi sadece "scriptin dogru
zaman araliginda calismasini saglamak", asil karar kodun icinde.

Her calistirmada script:
1. Su an bu 3 pencereden birinin icinde mi diye bakar (`_determine_window()`).
   Degilse hicbir sey yapmadan hemen cikar (RSS'e bile gitmez, neredeyse
   bedava).
2. Pencerenin icindeyse: bugun bu pencerede zaten paylasilmis mi diye
   `daily_posted.json`'a bakar (`_already_posted`). Evetse cikar — **ayni
   video iki kez paylasilmaz.**
3. Henuz paylasilmadiysa: RSS'ten bugun gercekten bu ET saatinde
   yayinlanmis bir video arar (`_find_todays_video`, gercek yayin zamanini
   ET'ye cevirip karsilastirir, TR gunu degil ET gunu esas alinir).
4. Bulursa indirir, icerik turunu belirler, paylasir, `daily_posted.json`'a
   isaretler ve durur.
5. **Pencere kapanana kadar (yaklasik 1 saatlik "yakalama suresi" gecene
   kadar) hic bulamazsa: o gunku o dilim tamamen birakilir, bir daha
   denenmez, biriktirilmez.** Elektrik/internet kesintisi olsa bile ertesi
   guine tasinmaz — bu Ali'nin acik talebiydi (2026-07-10).

Yakalama penceresi mantigi ileri-donuk: hedef saatten 5 dakika once baslar,
60 dakika sonrasina kadar surer (`CATCHUP_LEAD_MIN=5`, `CATCHUP_WINDOW_MIN=60`,
`poster_check.py` icinde `_in_catchup()`).

## 3) Icerik turu (grindorium mu stickline mi) nasil belirleniyor

Kod: `utils/content_type.py` (hem main.py hem poster_check.py buradan
import eder, iki yerde ayri ayri mantik tutulmasin diye).

- Yayin saati ET 12:00 veya 19:00'a yakinsa (±20 dk): **kesin `stickline`**
  (o saatlerde sadece BAGIMSIZ_SHORT/ESLI_SHORT var, baska bir sey yok).
- Yayin saati ET 16:00'a yakinsa (±20 dk): **belirsiz** — hem gercek
  Grindorium bolumu hem STICKLINE LONG bu saatte yayinlanabiliyor.
  `Desktop\STICKLINE\STICKLINE_METADATA.json` dosyasindaki YouTube ID
  listesine bakilir: orada varsa `stickline`, yoksa `grindorium`.
- Hicbiri eslesmezse (eski/duzensiz videolar icin): direkt ID listesine
  bakilir (yedek yol).

**Bilinen sinir**: `STICKLINE_METADATA.json` 2026-07-10 itibariyla 370 video
kaydi iceriyor (hepsi youtube_id ile), ama STICKLINE'in 842 videoluk yeni
reschedule dalgasinin tamamini kapsayip kapsamadigi teyit edilemedi. Kapsamayan
videolar icin sistem ET-saat fallback'ine duser (bugunkunden daha kotu olmaz,
metadata guncellendikce otomatik iyilesir).

## 4) Iki surecin cakismasi nasil onleniyor (state.json senkron)

`main.py` bellekte state'i tutup her turda diske yaziyor; `poster_check.py`
ayri bir surec olarak kendi basina `seen_video_ids`'e ekleme yapiyor ve
`daily_posted.json`'a yaziyor. Eskiden main.py'nin sirdaki yazmasi
poster_check.py'nin ekledigi ID'leri eziyordu — bu yuzden ayni video gunler
sonra "yeni" saniliyor, tekrar kuyruga giriyor, **gercekten ikinci kez**
paylasiliyordu (2026-07-10'dan once loglarda kanitlandi: pnRiA0qPdH8,
Re9y0apKKKA, 2uNhkziGId4 videolari iki kez paylasilmisti).

Cozum: `utils/youtube_monitor.py::reconcile_seen_ids()` — main.py'nin her
turunda (hem process_new_videos'tan once hem save_state'ten hemen once)
diskteki guncel `seen_video_ids`'i bellektekiyle birlestirir (union). Boylece
iki surec asla birbirinin `seen_video_ids` kaydini ezmez.

`daily_posted.json` icin de benzer bir capraz kontrol var: main.py, bir
stickline videosunu paylasmadan once `daily_posted.json`'da poster_check.py
tarafindan zaten paylasilip paylasilmadigina bakar (`process_queue()` icinde).

## 5) Onemli dosyalar

| Dosya | Ne ise yarar |
|---|---|
| `main.py` | Ana 7/24 surec |
| `poster_check.py` | Task Scheduler tetikli yedek/garanti mekanizmasi |
| `utils/content_type.py` | Ortak icerik-turu tespiti (ET-bazli + ID listesi) |
| `utils/youtube_monitor.py` | RSS okuma, state.json okuma/yazma/senkron |
| `utils/downloader.py` | yt-dlp ile indirme, H.264'e cevirme |
| `utils/ai_rewriter.py` | Claude ile altyazi uretimi (su an KAPALI) |
| `utils/fallback_formatter.py` | Claude olmadan altyazi uretimi (su an AKTIF) |
| `platforms/instagram.py`, `platforms/facebook.py` | Paylasim modulleri (aktif) |
| `platforms/tiktok.py`, `platforms/twitter.py`, `platforms/pinterest.py` | Hazir ama devrede degil |
| `state.json` | Kuyruk, gorulen video ID'leri, son paylasim zamanlari |
| `daily_posted.json` | poster_check.py'nin gunluk paylasim kaydi (cift paylasim onleme) |
| `config.json` | API anahtarlari, platform enabled/disabled, zamanlama ayarlari — **ASLA paylasma/commit'leme** |
| `logs/poster.log` | main.py logu (donen, 5 yedek) |
| `logs/check.log` | poster_check.py logu |
| `state.json.bak_20260710_185018` | 2026-07-10 temizliginden onceki yedek (bozuk/mukerrer kayitlar temizlenmeden once) |

## 6) Task Scheduler gorevleri (Windows)

| Gorev adi | Ne yapar |
|---|---|
| `GrindoriumPoster` | main.py'yi baslatir (`start_poster.bat` uzerinden), oturum acilinca (logon trigger) |
| `GrindoriumPoster_Midday` | poster_check.py'yi 18:55-21:05 TR arasi her 10 dk calistirir (12:00 ET penceresi) |
| `GrindoriumPoster_Primetime` | poster_check.py'yi 22:55-01:05 TR arasi her 10 dk calistirir (16:00 ET penceresi) |
| `GrindoriumPoster_Evening` | poster_check.py'yi 01:55-04:05 TR arasi her 10 dk calistirir (19:00 ET penceresi) |

Hepsi Ali'nin diger guvenilir otomatik-baslayan sistemleriyle (1DHD_Kuyruk_Takipci,
EP25_RENDER, H8VIDEO) ayni ayari kullaniyor (LogonType=Interactive, Ali
oturum acinca calisiyorlar) — PC kapanip acilinca ekstra bir sey yapmaya
gerek yok.

**Eski gorevler (`GrindoriumPoster_Grindorium`, `GrindoriumPoster_STICKLINE`,
sabit 23:02-23:59 / 03:02-05:00 TR pencereleri) 2026-07-10'da SILINDI —
yeni STICKLINE programiyla uyusmuyorlardi.**

## 7) Sorun giderme

- **"Paylasim yapilmiyor" sikayeti geldiginde once bak**: `logs/poster.log`
  (main.py) ve `logs/check.log` (poster_check.py) — hangi surecin
  calistigini/calismadigini, hangi hatalari verdigini gosterir.
- **Sistem calisiyor mu?**: `Get-Process python` VEYA
  `poster.lock` dosyasinin icindeki PID hala yasiyor mu (`Get-Process -Id <pid>`).
- **Bir video neden paylasilmadi?**: `state.json`'daki `queue` listesine bak
  (`video_id`, `content_type`, `done_platforms`, `attempts`, `publish_at`).
- **Bugun ne paylasildi?**: `daily_posted.json` (poster_check.py'nin
  kaydettigi) + `logs/poster.log`'da "All platforms done for X" satirlari
  (main.py'nin kaydettigi).
- **Kimlik bilgileri hala gecerli mi?** (gercek paylasim yapmadan test):
  `python check_credentials.py`
- **poster_check.py'yi elle test etmek** (gercek paylasim yapmadan):
  `python poster_check.py --dry-run` (o an bir pencerenin icindeysen bugunun
  videosunu bulup "ne yapardim" der, paylasmaz). Belirli bir pencereyi
  zorlamak icin: `python poster_check.py --dry-run --force-window midday`
  (secenekler: `midday`, `primetime`, `evening`).

## 8) Bilinen kucuk hata (kapsam disi birakildi, 2026-07-10)

`main.py`'deki `pinterest_scheduler()` fonksiyonu `pinterest` modulunu
kullaniyor ama dosyanin basinda import edilmemis (`from platforms import
instagram, facebook` — pinterest yok). Pinterest zaten config.json'da
`enabled=false` oldugu icin fonksiyon en basta `return` ile cikiyor ve bu
hataya hic ulasilmiyor — su an zararsiz. Pinterest ileride aktif edilirse
once bu import eklenmeli.

## 9) Cift paylasim hatasi (2026-07-11'de yasandi, ayni gun duzeltildi)

**Ne oldu**: 2026-07-11 gecesi (TR saatiyle) F5K_V8OWCaI (STICKLINE short)
hem Instagram'a hem Facebook'a **iki kez** paylasildi — biri poster_check.py
tarafindan (evening penceresi, 02:25 TR), biri main.py tarafindan (02:49 TR,
kendi kuyrugundan). Farkli Instagram post ID'leri ve farkli Facebook video
ID'leri uretti (gercek cift paylasim, log hatasi degil).

**Kok neden**: Bolum 4'te anlatilan `daily_posted.json` capraz kontrolu iki
surecte FARKLI SAAT DILIMINDE tarih anahtari kullaniyordu:
- `poster_check.py` (satir ~229): `datetime.now(ET_TZ).date().isoformat()` —
  ABD Dogu saatine gore tarih. Video ET 19:00 civari paylasildigi icin
  anahtar `"2026-07-10"` oldu.
- `main.py`'nin capraz kontrolu (eski hali, satir ~126): `datetime.now().date().isoformat()` —
  **yerel (TR) saatine gore**, timezone cevirisi YOK. TR 02:49'da bu
  `"2026-07-11"` oldu (gece yarisini TR'de gecmis ama ET'de henuz gecmemis).

main.py paylasmadan once `daily_posted.json["2026-07-11"]`'e baktı, orasi
bostu (kayit `"2026-07-10"` altindaydi), "poster_check henuz paylasmamis"
sanip kendisi de paylasti. Iki taraf da kendi mantigina gore dogru
calisiyordu, sadece tarih anahtarlari uyusmuyordu.

**Duzeltme (2026-07-11)**: `main.py`'ye `ET_TZ = ZoneInfo(content_type_util.ET_TZ_NAME)`
eklendi, capraz kontroldeki `today_str` artik `datetime.now(ET_TZ).date().isoformat()`
kullaniyor — poster_check.py ile birebir ayni mantik. Bu, Bolum 4'te
anlatilan senkron mekanizmasinin bir parcasi olarak dusunulmeli: iki surec
`daily_posted.json`'a yazarken/okurken HER ZAMAN ET tarihi kullanmali, TR
tarihi asla kullanilmamali.

**Ders**: 2026-07-10 rebuild'inde "cift paylasim" bug'i (Bolum 4, `seen_video_ids`
senkronu) duzeltilmisti ama `daily_posted.json` tarih anahtarindaki saat
dilimi tutarsizligi gozden kacmisti — ayni sinif hata (iki surecin ayni
dosyaya farkli varsayimla bakmasi) farkli bir yerde tekrar cikti. Ileride
bu dosyalara saat/tarih ekleyen her yeni kod ET_TZ kullanmali, `datetime.now()`
(timezone'suz, yerel saat) STICKLINE ile ilgili hicbir tarih/saat
karsilastirmasinda kullanilmamali.

## 10) Neden 2026-07-10'da yeniden yazildi (gecmis, kisa ozet)

Sistem calisiyordu ama 4 gercek hata + STICKLINE'in yeni program degisikligi
yuzunden duzensiz calisiyordu: (1) uzun bir bolum kisa saniip Instagram'a
Reels gibi zorlaniyor, surekli 400 hatasi aliyordu; (2) basarisiz paylasim
denemesi bile 20 saatlik kilidi baslatip arkadaki videolari haksiz yere
erteliyordu; (3) main.py ve poster_check.py ayni state.json'a yariş halinde
yazdigi icin bazi videolar gunler sonra "yeni" sanilip ikinci kez
paylasiliyordu; (4) STICKLINE'in yeni ET-bazli programi eski sabit TR
saatleriyle uyusmuyordu. Tum bunlar tespit edilip duzeltildi, kuyruktaki
bozuk/mukerrer kayitlar temizlendi, Task Scheduler yeniden kuruldu, sistem
2026-07-10'da yeniden baslatildi.

**Ek olay (ayni gun, restart sonrasi)**: main.py yeniden baslatilinca,
sistem uzun sure durdugu icin kuyrukta biriken (gunler once zamani gelmis
ama hic paylasilamamis) 2 video, tam da poster_check.py'nin planli/zamaninda
bir paylasimiyla ayni birkac dakikaya denk gelip Instagram+Facebook'ta 3
video art arda paylasildi — spam gibi gorundu, Ali 2 tanesini elle sildi.
Kok neden: main.py'nin kendi kuyrugunda "cok gecikmisse artik paylasma"
kurali yoktu (poster_check.py'de vardi ama main.py'ye hic uygulanmamisti).
Ayni gun `STALE_QUEUE_HOURS` eklendi (bkz Bolum 1) ve o an kuyrukta bekleyen,
zaten 16-24 saat gecikmis 6 video da ayni kurala gore temizlendi.
