# FALORA — Full-Stack Dark Luxury Marketplace

Falora is a production-oriented **frontend + backend** e-commerce marketplace starter built with **Python / Flask / SQLAlchemy / HTML / CSS / JavaScript**. It is intentionally much more complete than a static landing page: catalogue data is served through APIs, product CRUD is persisted through SQLAlchemy, authentication uses password hashing + sessions, cart state is client-side, and checkout creates real Order + OrderItem records.

## Architecture
- `app.py` — Flask server, SQLAlchemy models, seed data, auth, product CRUD, order API and page routes.
- `templates/` — UI pages: home, shop, product detail, login/register, cart, checkout, orders, admin studio, 404.
- `static/css/style.css` — dark luxury purple design system, responsive layouts, hover/scroll/loader/modal animations.
- `static/js/app.js` — catalogue fetching, search, filters, cart, auth, checkout, orders and admin CRUD interactions.
- `vercel.json` — Vercel Python entrypoint.
- `.env.example` — production configuration template.

## Functional flows
1. **Browse**: home → shop → search/filter/sort → product detail.
2. **Product**: gallery → color/size choices → quantity → add to bag → wishlist interaction.
3. **Cart**: quantity increment/decrement → remove → clear → live totals + free shipping threshold.
4. **Auth**: register → session login → logout API → order history. Passwords are hashed with Werkzeug.
5. **Checkout**: contact → delivery → payment method UI → POST `/api/orders` → stock decrement → order record → orders page.
6. **Admin**: sign in with demo admin → `/admin` → create/read/update/delete products through protected API endpoints.

## Local run
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000`.

### Demo admin
- Email: `admin@falora.test`
- Password: `Falora123!`

Change this immediately for any real deployment.

## Database / Vercel
Local default: SQLite. For persistent production data on a serverless platform, set `DATABASE_URL` to a managed PostgreSQL database. The app already accepts a PostgreSQL URL and uses SQLAlchemy models for `User`, `Product`, `Order`, and `OrderItem`.

## GitHub → Vercel
The provided guide recommends a small, testable workflow, `.gitignore`, Git commits and then GitHub → Vercel deployment. This project is structured to follow that workflow. Before publishing, review secrets, database configuration, payment provider integration, user data handling and image licensing.

## Real payment
The checkout is a **functional order flow with payment-method UI**, but it intentionally does not charge a real card. To accept money, connect a real payment gateway (for example Stripe or a local Indonesian provider) on the backend and verify webhooks server-side.

## Images
Product/editorial visuals use remote Unsplash image URLs as real photography references. For commercial launch, replace or verify every image against a license/source you are entitled to use.
