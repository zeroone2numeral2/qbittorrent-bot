import sys

import bot

if sys.version_info[:3] < (3, 6, 2):
    print("Sorry, Python 3.6.2+ is required")
    sys.exit(0)

bot.main()
