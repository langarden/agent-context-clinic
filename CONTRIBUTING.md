# Contributing

- Keep the library zero-dependency (Python 3.9+ stdlib).
- New features ship with unit tests.
- Transcript parsing must stay tolerant of garbage lines.
- Report thresholds are documented constants — do not move them into hidden
  magic numbers.

```bash
pip install -e .
python -m unittest discover -s tests -v
```