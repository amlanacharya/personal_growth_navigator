#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Entry point for the Personal Growth Navigator application.
"""

from src.web.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
