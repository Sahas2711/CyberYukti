# CyberYukti — Person 4 Failure Checklist

## Recovery Procedures

| # | Failure Mode | Symptom | Recovery |
|---|---|---|---|
| 1 | Real backend down | Network error, 500s | Toggle `NEXT_PUBLIC_USE_MOCK=true`, restart frontend |
| 2 | AI provider down | AI Analysis returns error | Set `USE_MOCK_AI=true`; mock provider fills panel |
| 3 | AI returns invalid JSON | Validator catches, retries | Retry once; falls back to mock automatically |
| 4 | AI hallucinates | Validator catches unsupported claims | Falls back to mock; logs warning |
| 5 | Injection payload succeeds | AI output changes based on payload | Disable AI panel; show deterministic template |
| 6 | Case not found | 404 page | Return to dashboard; pick valid case ID |
| 7 | Slow dashboard | >5s load time | Use mock provider; skip real fetch |
| 8 | Slow AI analysis | >10s response | Set `USE_MOCK_AI=true` |
| 9 | Audit fetch fails | "Audit unavailable" | Approval still works; audit events not displayed |
| 10 | Approval mutation fails | Error toast | Do not change UI state; retry |
| 11 | Frontend crash | White screen | Restart `npm run dev`; use production build |
| 12 | Docker/backend unavailable | All API calls fail | Mock provider is the fallback; demo continues |
| 13 | Tailwind styles broken | Missing colors/layout | Ensure `tailwind.config.ts` is loaded; restart dev server |
| 14 | TypeScript errors | Build fails | Fix type errors; mock mode bypasses most backend types |

## Pre-Demo Checklist

- [ ] `NEXT_PUBLIC_USE_MOCK=true` in `.env.local`
- [ ] `USE_MOCK_AI=true` in backend `.env`
- [ ] Frontend builds without errors: `npm run build`
- [ ] Backend starts: `uvicorn backend.app.main:app --reload`
- [ ] Dashboard loads with 6 cases
- [ ] All 5 scenarios pass manually
- [ ] No console errors in browser
- [ ] No network requests to external LLM APIs during demo

## Emergency Rollback

If anything breaks mid-demo:
1. Open browser DevTools → Network tab
2. Verify `NEXT_PUBLIC_USE_MOCK=true` (check localStorage or env)
3. Hard-refresh the page (Ctrl+Shift+R)
4. If still broken, switch to pre-recorded demo video
