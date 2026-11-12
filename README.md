# HEMKAN Telegram starter

This starter receives **new channel posts** from the public Telegram channel `@fxnux` using a Telegram bot webhook and displays them on the HEMKAN page.

## Files
- `app.py` — Flask API + Telegram webhook
- `static/index.html` — HEMKAN page
- `requirements.txt` — Python packages
- `render.yaml` — Render web service blueprint

## Important
- Keep your Telegram bot token private. Never paste it into HTML, GitHub source, screenshots, or a public chat.
- The bot must be an administrator in `@fxnux` and must have permission to read/post channel updates.
- This starter stores received posts in a local SQLite database. On Render's free ephemeral filesystem, data can be lost when the service restarts. For persistent production storage, attach a persistent disk or use a managed database.
- It only receives posts after the webhook is configured; it does not import old channel history.
- Use only content and viewing links you have permission to distribute.

## Deploy outline
1. Upload the project files to a GitHub repository (keep `static/index.html` inside the `static` folder).
2. In Render, create a Web Service from that repository.
3. Add environment variables:
   - `TELEGRAM_BOT_TOKEN` = your bot token (secret; enter only in Render's environment settings)
   - `TELEGRAM_WEBHOOK_SECRET` = a private random string made by you
   - `TELEGRAM_CHANNEL_USERNAME` = `fxnux`
4. After deployment, set the bot webhook to:
   `https://YOUR-RENDER-SERVICE.onrender.com/telegram/webhook`
   Use Telegram's official Bot API `setWebhook` method with the `secret_token` set to the same `TELEGRAM_WEBHOOK_SECRET`.
5. Check `https://YOUR-RENDER-SERVICE.onrender.com/health`.

The HEMKAN page displays new Telegram channel posts with their caption, image (if present), and a link to the original Telegram post. Category/language tagging is not automatically inferred in this starter; it can be added in the next step.
