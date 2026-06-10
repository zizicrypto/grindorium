# Grindorium Poster

Automatic cross posting system for the Grindorium brand.

## What it does
1. Watches the YouTube channel RSS every 10 minutes.
2. New video appears: downloads it with yt-dlp and pulls the original title, description and tags.
3. Claude API writes platform specific captions. If Claude is unreachable or over quota, the fallback formatter trims and adds hashtags instead. The pipeline never stops.
4. Queues the post and publishes to Instagram, TikTok, Facebook and X at the scheduled time.
5. Pinterest runs separately: 3 quote images per day plus 1 test result image every 2 days, pulled from the local pinterest_assets folders, never repeating until the pool cycles.

## Setup on MAIN
1. pip install -r requirements.txt
2. Copy config.example.json to config.json
3. Fill the API keys as platform approvals arrive. Each platform has its own enabled flag, so the system works with whatever is approved so far.
4. Set pinterest_quotes_dir and pinterest_results_dir to the folders produced by grindorium_image_factory.py
5. python main.py
6. For 24/7 operation register it in Task Scheduler with start at logon.

## Platform notes
- X: free tier write limit is about 500 per month. One Short per day fits easily.
- TikTok: until the app passes the TikTok audit, uploads arrive as drafts. Open the TikTok app and approve them. After the audit, switch privacy_level in platforms/tiktok.py from SELF_ONLY to PUBLIC_TO_EVERYONE.
- Instagram: needs a Business account linked to a Facebook page and an approved Meta app with instagram_content_publish permission.
- Facebook: page access token needs the video publish permission from app review.
- Pinterest: standard access request usually clears within days. Board id is in the board URL or via the API.

## Files
- main.py: orchestrator loop
- utils/youtube_monitor.py: RSS polling and state
- utils/downloader.py: yt-dlp wrapper
- utils/ai_rewriter.py: Claude captions with hard limits per platform
- utils/fallback_formatter.py: no AI fallback
- platforms/: one module per platform
- state.json: created at first run, survives restarts
- logs/poster.log: rotating log

## Going live checklist
1. Fill config.json. Never share these keys in chats or commits. config.json should stay out of git.
2. python check_credentials.py
   Read only test for every enabled platform. Fix anything marked FAILED before going live.
3. Enable platforms one by one in config.json as their credentials pass the check.
4. python main.py and watch logs/poster.log
5. Register in Task Scheduler when stable.

## Token helpers (tools_auth/)
- get_pinterest_token.py: turns App ID + App Secret into an access token through the browser. Works with trial access on your own account, so Pinterest can start BEFORE standard access is approved. Standard access only lifts rate limits and public scope.
- get_tiktok_token.py: same flow for TikTok, use after the app review passes. TikTok tokens expire daily, ask for the auto refresh extension when you reach that stage.

## Meta note
While the Meta app is in Development Mode it already works for accounts that have a role on the app. You are the admin, so posting to your own Page and Instagram works now, before any app review. App review is only needed if other users will ever use the app, which is not the case here.
