# market-news (Streamlit)

Proyecto Streamlit para recopilar noticias macroeconómicas, editar selección editorial y enviar digest por email sin secretos hardcodeados.

## Run

```bash
pip install streamlit pandas feedparser beautifulsoup4 requests
streamlit run app.py
```

## Secrets Checklist

Rellena estas claves (obligatorias salvo mención):

- `EMAIL_SENDER`
- `EMAIL_PASSWORD`
- `EMAIL_RECIPIENT_DEFAULT`
- `SMTP_HOST` (default `smtp.gmail.com`)
- `SMTP_PORT` (default `587`)
- `FRED_API_KEY` (opcional)

### Dónde ponerlas

1. **Preferido (Streamlit):** copia `secrets.toml.example` a `.streamlit/secrets.toml` y reemplaza placeholders.
2. **Fallback:** variables de entorno del sistema.

### Ejemplo export en terminal

```bash
export EMAIL_SENDER="your_sender@example.com"
export EMAIL_PASSWORD="your_app_password"
export EMAIL_RECIPIENT_DEFAULT="your_recipient@example.com"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export FRED_API_KEY="optional_key"
```

## Flujo editorial implementado

1. Fetch/build dataset.
2. Editor con `st.data_editor` (`included`, `title`, `description`, `date`, `region`, `notes`).
3. Add manual item.
4. Preview HTML.
5. Generate HTML (download).
6. Send email (solo habilitado si secrets están completos y scanner limpio).

## Secret hygiene

- No hay emails/passwords/API keys reales hardcodeadas en código.
- Config se resuelve en `src/settings.py` desde `st.secrets` o entorno.
- Antes de export/send corre un scanner de fugas para detectar tokens sospechosos.
