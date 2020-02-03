def strip_args(positional=0, keywords=None):
    keywords = keywords or []

    def _inner(view_func):
        def decorator(*args, **kwargs):
            return view_func(
                *args[positional:],
                **{k: v for k, v in kwargs.items() if k not in keywords},
            )

        return decorator

    return _inner
