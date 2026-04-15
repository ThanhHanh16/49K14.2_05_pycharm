# QL_SanTT

## Run project on Windows PowerShell

```powershell
Set-Location 'D:\Download\49K14.2_05_pycharm'
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

## Quick config check

```powershell
python manage.py check
```

## Notes

- `accounts` now has `AppConfig`, `models`, and `views`, so the startup error `ModuleNotFoundError: No module named 'accounts.apps'` is fixed.
- If you change models in `user` or `accounts`, run `makemigrations` and `migrate` again.
