@echo off
echo ============================================================
echo GITHUB PUSH VERIFICATION
echo ============================================================
echo.

echo Checking .gitignore...
if exist .gitignore (
    echo [OK] .gitignore exists
) else (
    echo [ERROR] .gitignore NOT found!
    goto :error
)

echo.
echo Checking .env.example...
if exist .env.example (
    echo [OK] .env.example exists
) else (
    echo [ERROR] .env.example NOT found!
    goto :error
)

echo.
echo Checking .env file...
if exist .env (
    echo [OK] .env exists (will be ignored by git)
) else (
    echo [WARNING] .env NOT found - you'll need to create it
)

echo.
echo ============================================================
echo RUNNING: git status
echo ============================================================
git status

echo.
echo ============================================================
echo VERIFICATION CHECKLIST
echo ============================================================
echo.
echo Check the output above and verify:
echo [ ] .env is NOT listed in git status
echo [ ] venv/ is NOT listed in git status
echo [ ] data/raw/ files are NOT listed
echo [ ] Only source code and docs are listed
echo.
echo If everything looks good, you can safely push!
echo.
echo Next steps:
echo   git add .
echo   git commit -m "Your commit message"
echo   git push
echo.
goto :end

:error
echo.
echo [ERROR] Pre-push verification failed!
echo Please fix the issues above before pushing.
echo.

:end
pause
