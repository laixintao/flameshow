from flameshow.main import main, run_app


run_app(
    3,
    "lucky.log",
    "flamegraph",
    open("/Users/xintao.lai/Downloads/spex--pprof/profile-10seconds.out", "rb"),
    True,
)
