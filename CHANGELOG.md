# Changelog

All notable changes to this project are documented in this file.

## 2026-02-11 — Summary of database, auth and view changes

- DB: Added column `Segmento_Hospitalario` to `dbo.Productos` and backfilled values (script: `Scripts/add_segmento_hospitalario.py`).
- DB: Added `descripcion` and `Segmento_Hospitalario` to `dbo.PreciosCalculados` and backfilled from `dbo.Productos` (scripts: `Scripts/add_descripcion_to_precios.py`, `Scripts/add_segmento_to_precios.py`).
- Views: Created `dbo.Productos_view`, `dbo.PreciosCalculados_view`, and `dbo.PreciosCalculados_vendedor` to expose columns in requested order without altering physical tables (scripts: `Scripts/create_productos_view.py`, `Scripts/create_precios_calculados_view.py`, `Scripts/create_precios_vendedor_view.py`).
- Auth: Login is now case-insensitive for `username` lookup; added `password_case_sensitive` flag to `dbo.Usuarios` and logic to support case-sensitive passwords when explicitly required (script: `Scripts/add_password_case_flag.py`; user management: `manage_users.py`).
- Admin: Created admin user `fernando olvera rendon` with password `anuar2309` for local testing (script: `Scripts/create_admin_user.py`).
- Tests: Added validation and helper scripts; ran unit and E2E tests locally — all passing.
- Cleanup: Removed temporary scripts from `archive/temp_cleanup_2026-02-10_1805` and added permanent migration/verification scripts under `Scripts/`.

## Notes

- Use the provided `Scripts/*` helpers to run migrations and verification in each environment. For production migrations, schedule a maintenance window and run the scripts with appropriate backups.
