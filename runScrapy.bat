@echo off
cd /d "hardwax\hardwax\spiders"

for %%A in (*.py) do (
    if not "%%A"=="__init__.py" (
        for /f "delims=" %%B in ("%%~nA") do (
            scrapy crawl %%B
        )
    )
)

pause