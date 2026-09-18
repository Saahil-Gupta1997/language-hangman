# Language Learning Hangman Login UI

An optional React + TypeScript login client for the local Hangman gateway.

## Run

```bash
npm install
npm run dev
```

Start `python -m src.cli run-auth-gateway` from the project root first.
Open the Vite URL using `localhost` so its login cookie is also available to Streamlit.
The proxy expects the gateway on port 8000; update `vite.config.ts` if using another port.

## Notes

- Registration and sign-in use the real gateway API and redirect to the game.
- The gateway's `/login` page remains the default, with no Node installation required.
