from invoke import task

@task
def test(c):
    env = {
        "PYTHONPATH": f"ld_07:tests/mocks"
    }
    c.run("python -m pytest .", env=env)
