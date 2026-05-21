__all__ = ["GPFarmQA", "IntentResult"]


def __getattr__(name):
    if name in __all__:
        from .qa import GPFarmQA, IntentResult

        return {"GPFarmQA": GPFarmQA, "IntentResult": IntentResult}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
