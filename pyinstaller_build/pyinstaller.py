from contextlib import suppress
import shlex

from WebtoonScraper.__main__ import main

with suppress(BaseException):
    main(["--help"])
print()
print("Welcome to WebtoonScraper shell!")
print("Type 'exit' to quit")
while True:
    command = input(">>> ")
    if command == "exit":
        break
    args = shlex.split(command)
    if args[0].lower() in {"webtoon", "webtoonscraper"}:
        del args[0]
    with suppress(BaseException):
        main(args)
